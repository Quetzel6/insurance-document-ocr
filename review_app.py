"""Local synthetic OCR review workflow; independent of frozen evaluation code."""
import argparse
import base64
import binascii
import io
import warnings
import datetime as dt
import difflib
import hashlib
import json
import re
import secrets
import sqlite3
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from review_consistency import check_consistency
from review_suggestions import suggest_fields
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
FIELDS = ('document_id', 'date', 'amount')


def validation(values):
    errors = []
    if not re.fullmatch(r'SYN-\d{6}', values.get('document_id', ''), flags=re.ASCII):
        errors.append('Document ID must be SYN- followed by six digits.')
    date = values.get('date', '')
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date, flags=re.ASCII):
            raise ValueError()
        dt.date.fromisoformat(date)
    except ValueError:
        errors.append('Date must be a valid YYYY-MM-DD calendar date.')
    if not re.fullmatch(r'\d{1,12}\.\d{2}', values.get('amount', ''), flags=re.ASCII):
        errors.append('Amount must be non-negative with exactly two decimals (up to 12 integer digits).')
    return errors


def load_cases(root=ROOT):
    # Only image names/hashes are used from the manifest, never expected labels/matches.
    report_bytes = (root / 'enhanced_output/test_report.json').read_bytes()
    report = json.loads(report_bytes)
    images = {r['id']: r for r in json.loads((root / 'challenge_data/manifest.json').read_text())['records']}
    cases = {}
    for record in report['records']:
        if record['method'] != 'enhanced':
            continue
        image = images[record['id']]
        path = (root / 'challenge_data' / image['image']).resolve()
        if not path.is_relative_to((root / 'challenge_data').resolve()):
            raise ValueError('Invalid image path')
        if hashlib.sha256(path.read_bytes()).hexdigest() != image['sha']:
            raise ValueError('Source image changed: ' + image['image'])
        values = {k: str(record['prediction'].get(k) or '') for k in FIELDS}
        cases[record['id']] = dict(id=record['id'], original=values, text=record['text'],
                                   reasons=validation(values), image_path=path)
    return cases, hashlib.sha256(report_bytes).hexdigest()


def validate_package(package):
    """Import an untrusted local package; never treats imported values as truth."""
    if not isinstance(package, dict) or package.get('format') != 'ocr-review-package-v1':
        raise ValueError('Choose an OCR review package downloaded from Image Reader')
    result = package.get('result')
    if not isinstance(result, dict) or result.get('layout') != 'document' or result.get('field_extraction_enabled') is not True:
        raise ValueError('Only Document ID / Date / Amount mode can enter this queue')
    language = result.get('language')
    if language not in ('eng', 'tha+eng'):
        raise ValueError('Invalid OCR language')
    text, fields = result.get('text'), result.get('fields')
    if not isinstance(text, str) or len(text) > 10000:
        raise ValueError('OCR text must be at most 10000 characters')
    if not isinstance(fields, dict) or set(fields) != set(FIELDS):
        raise ValueError('Invalid OCR fields')
    if any(v is not None and (not isinstance(v, str) or len(v) > 100) for v in fields.values()):
        raise ValueError('Invalid OCR field value')
    encoded = package.get('image_base64')
    if not isinstance(encoded, str) or len(encoded) > 14 * 1024 * 1024:
        raise ValueError('Image is too large')
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError('Invalid image encoding') from exc
    if not raw or len(raw) > 10 * 1024 * 1024:
        raise ValueError('Image must be at most 10 MiB')
    source_sha = hashlib.sha256(raw).hexdigest()
    if result.get('source_sha256') != source_sha:
        raise ValueError('Image hash does not match OCR result')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(raw)) as probe:
                if probe.format not in ('PNG', 'JPEG', 'BMP') or getattr(probe, 'n_frames', 1) != 1:
                    raise ValueError('Use a single PNG/JPG/BMP image')
                if probe.width * probe.height > 12_000_000:
                    raise ValueError('Image exceeds 12 megapixels')
                probe.verify()
            with Image.open(io.BytesIO(raw)) as source:
                image = ImageOps.exif_transpose(source).convert('RGBA')
                background = Image.new('RGBA', image.size, 'white')
                background.alpha_composite(image)
                output = io.BytesIO()
                background.convert('RGB').save(output, format='PNG')
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise ValueError('Cannot decode source image') from exc
    original = {k: fields[k] or '' for k in FIELDS}
    identity = json.dumps([source_sha, language, text, original], sort_keys=True, ensure_ascii=False)
    case_id = 'upload-' + hashlib.sha256(identity.encode()).hexdigest()
    case = dict(id=case_id, original=original, text=text, reasons=validation(original),
                source_sha256=source_sha, language=language, layout='document',
                source_kind='uploaded', provenance='Imported local package; OCR content is not authenticated')
    return case, output.getvalue()


class Store:
    def __init__(self, path, fingerprint):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, version INTEGER, payload TEXT);
CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, id TEXT, version INTEGER, payload TEXT);
CREATE TABLE IF NOT EXISTS archived_runs (run_id TEXT PRIMARY KEY, archived_at TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS uploaded_documents (id TEXT PRIMARY KEY, payload TEXT, image BLOB);''')
        old = self.db.execute("SELECT value FROM metadata WHERE key='report_sha'").fetchone()
        if old and old[0] != fingerprint:
            self.db.close()
            raise ValueError('This database belongs to a different report. Use a new database path.')
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('report_sha', ?)", (fingerprint,))
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('run_id', ?)", (secrets.token_urlsafe(16),))

    def uploaded_cases(self):
        cases = {}
        for row in self.db.execute('SELECT id,payload,image FROM uploaded_documents ORDER BY id'):
            case = json.loads(row['payload'])
            case['image_bytes'] = bytes(row['image'])
            cases[row['id']] = case
        return cases

    def import_package(self, package):
        if self.db.execute("SELECT value FROM metadata WHERE key='report_sha'").fetchone()[0] != 'uploads-v1':
            raise ValueError('Import is only available in the uploaded-image queue')
        case, image = validate_package(package)
        payload = json.dumps(case, ensure_ascii=False)
        with self.db:
            cursor = self.db.execute('INSERT OR IGNORE INTO uploaded_documents VALUES (?,?,?)',
                                     (case['id'], payload, image))
        return case['id'], cursor.rowcount == 1

    def get(self, case_id):
        row = self.db.execute('SELECT payload FROM decisions WHERE id=?', (case_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, case_id, data, original, original_text=""):
        if not isinstance(data, dict):
            raise ValueError('Expected an object')
        values = data.get('values')
        if not isinstance(values, dict) or set(values) != set(FIELDS) or any(not isinstance(v, str) for v in values.values()):
            raise ValueError('All three text fields are required')
        values = {k: v.strip() for k, v in values.items()}
        status = data.get('status')
        if status not in ('approved', 'rejected'):
            raise ValueError('Choose approved or rejected')
        reviewer, note = data.get('reviewer'), data.get('note', '')
        if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 100:
            raise ValueError('Reviewer name is required (max 100 characters)')
        if not isinstance(note, str) or len(note) > 2000 or (status == 'rejected' and not note.strip()):
            raise ValueError('Rejection requires a reason; notes max 2000 characters')
        if status == 'approved' and validation(values):
            raise ValueError(' '.join(validation(values)))
        if type(data.get('version')) is not int:
            raise ValueError('Version is required')
        corrected = data.get('corrected_text', original_text)
        confirmed = data.get('text_confirmed', False)
        if not isinstance(corrected, str) or len(corrected) > 10000:
            raise ValueError('Corrected OCR text must be text, max 10000 characters')
        if type(confirmed) is not bool:
            raise ValueError('Text confirmation must be true or false')
        if status == 'approved' and corrected != original_text and not confirmed:
            raise ValueError('Confirm the edited OCR text against the source image before approval')
        consistency = check_consistency(corrected, values)
        if status == 'approved' and not consistency['passed']:
            raise ValueError(' '.join(consistency['errors']))
        changes = [dict(operation=tag, before=original_text[a:b], after=corrected[c:d])
                   for tag, a, b, c, d in difflib.SequenceMatcher(None, original_text, corrected, autojunk=False).get_opcodes()
                   if tag != 'equal']
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            old = self.get(case_id)
            version = old['version'] if old else 0
            if data['version'] != version:
                raise RuntimeError('Another decision was saved. Reload this case before saving.')
            payload = dict(id=case_id, version=version + 1, status=status, values=values,
                           original=original, original_text=original_text, corrected_text=corrected,
                           text_confirmed=confirmed, text_changes=changes,
                           consistency=consistency,
                           reviewer=reviewer.strip(), note=note.strip(),
                           saved_at=dt.datetime.now(dt.timezone.utc).isoformat())
            encoded = json.dumps(payload, ensure_ascii=False)
            self.db.execute('INSERT OR REPLACE INTO decisions VALUES (?,?,?)', (case_id, version + 1, encoded))
            self.db.execute('INSERT INTO audit(id,version,payload) VALUES (?,?,?)', (case_id, version + 1, encoded))
        return payload

    def run_id(self):
        return self.db.execute("SELECT value FROM metadata WHERE key='run_id'").fetchone()[0]

    def reset(self, expected_run):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if expected_run != self.run_id():
                raise RuntimeError('Review round changed. Reload the page.')
            snapshot = self.export()
            self.db.execute('INSERT INTO archived_runs VALUES (?,?,?)',
                            (self.run_id(), dt.datetime.now(dt.timezone.utc).isoformat(), json.dumps(snapshot, ensure_ascii=False)))
            self.db.execute('DELETE FROM decisions')
            self.db.execute('DELETE FROM audit')
            self.db.execute("UPDATE metadata SET value=? WHERE key='run_id'", (secrets.token_urlsafe(16),))
        return self.run_id()

    def archives(self):
        return [dict(run_id=r[0], archived_at=r[1], export=json.loads(r[2]))
                for r in self.db.execute('SELECT run_id,archived_at,payload FROM archived_runs ORDER BY archived_at')]

    def export(self):
        return dict(queue_kind='uploads' if self.db.execute("SELECT value FROM metadata WHERE key='report_sha'").fetchone()[0] == 'uploads-v1' else 'benchmark',
                    documents=[{k:v for k,v in case.items() if k != 'image_bytes'} for case in self.uploaded_cases().values()],
                    run_id=self.run_id(), report_sha=self.db.execute("SELECT value FROM metadata WHERE key='report_sha'").fetchone()[0],
                    decisions=[json.loads(r[0]) for r in self.db.execute('SELECT payload FROM decisions ORDER BY id')],
                    audit=[json.loads(r[0]) for r in self.db.execute('SELECT payload FROM audit ORDER BY seq')])


def make_handler(cases, store, token, port, uploads=False):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(30)

        def log_message(self, *args):
            pass

        def send(self, code, body, mime='application/json; charset=utf-8'):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def allowed(self):
            return self.headers.get('Host') in (f'127.0.0.1:{port}', f'localhost:{port}')

        def do_GET(self):
            if not self.allowed():
                return self.send(403, {'error': 'Invalid host'})
            if self.path == '/':
                return self.send(200, (ROOT / 'review_ui.html').read_bytes(), 'text/html; charset=utf-8')
            if self.path == '/app.js':
                return self.send(200, (ROOT / 'review_ui.js').read_bytes(), 'text/javascript; charset=utf-8')
            if self.path == '/api/cases':
                rows = []
                for case in cases.values():
                    rows.append({k: v for k, v in case.items() if k not in ('image_path', 'image_bytes')} | {'decision': store.get(case['id'])})
                return self.send(200, dict(cases=rows, token=token, run_id=store.run_id(), queue_kind='uploads' if uploads else 'benchmark'))
            if self.path == '/api/archives':
                return self.send(200, dict(archived_runs=store.archives()))
            if self.path == '/api/export':
                return self.send(200, store.export())
            if self.path.startswith('/image/') and self.path[7:] in cases:
                case = cases[self.path[7:]]
                return self.send(200, case['image_bytes'] if uploads else case['image_path'].read_bytes(), 'image/png' if uploads else 'image/bmp')
            self.send(404, {'error': 'Not found'})

        def do_POST(self):
            if not self.allowed() or self.headers.get('X-Review-Token') != token:
                return self.send(403, {'error': 'Invalid local session'})
            if self.path not in ('/api/decision', '/api/reset', '/api/import', '/api/suggestions'):
                return self.send(404, {'error': 'Not found'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                limit = 15 * 1024 * 1024 if self.path == '/api/import' and uploads else 131072
                if not 0 < length <= limit:
                    raise ValueError('Invalid request length')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Expected an object')
                if data.get('run_id') != store.run_id():
                    raise RuntimeError('Review round changed. Reload the page before saving.')
                if self.path == '/api/import':
                    if not uploads:
                        raise ValueError('Start Review Desk with --uploads to import images')
                    case_id, created = store.import_package(data.get('package'))
                    cases.clear()
                    cases.update(store.uploaded_cases())
                    return self.send(200, dict(id=case_id, created=created))
                if self.path == '/api/reset':
                    return self.send(200, dict(run_id=store.reset(data['run_id'])))
                if data.get('id') not in cases:
                    raise ValueError('Unknown document')
                if self.path == '/api/suggestions':
                    return self.send(200, suggest_fields(data.get('corrected_text')))
                self.send(200, store.save(data['id'], data, cases[data['id']]['original'], cases[data['id']]['text']))
            except (ValueError, TypeError) as exc:
                self.send(400, {'error': str(exc)})
            except RuntimeError as exc:
                self.send(409, {'error': str(exc)})
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--db', type=Path, default=ROOT / 'review_state/decisions.sqlite3')
    parser.add_argument('--uploads', action='store_true', help='Use a separate persistent uploaded-image queue')
    args = parser.parse_args()
    if args.uploads:
        if args.db == ROOT / 'review_state/decisions.sqlite3':
            args.db = ROOT / 'review_state/uploads.sqlite3'
        cases, fingerprint = {}, 'uploads-v1'
    else:
        cases, fingerprint = load_cases()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    store = Store(args.db, fingerprint)
    if args.uploads:
        cases = store.uploaded_cases()
    server = HTTPServer(('127.0.0.1', args.port), make_handler(cases, store, secrets.token_urlsafe(32), args.port, args.uploads))
    print(f'Review {len(cases)} {"uploaded" if args.uploads else "synthetic"} OCR cases at http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        store.db.close()


if __name__ == '__main__':
    main()



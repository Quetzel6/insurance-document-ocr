"""Local synthetic OCR review workflow; independent of frozen evaluation code."""
import argparse
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


class Store:
    def __init__(self, path, fingerprint):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, version INTEGER, payload TEXT);
CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, id TEXT, version INTEGER, payload TEXT);
CREATE TABLE IF NOT EXISTS archived_runs (run_id TEXT PRIMARY KEY, archived_at TEXT, payload TEXT);''')
        old = self.db.execute("SELECT value FROM metadata WHERE key='report_sha'").fetchone()
        if old and old[0] != fingerprint:
            self.db.close()
            raise ValueError('This database belongs to a different report. Use a new database path.')
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('report_sha', ?)", (fingerprint,))
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('run_id', ?)", (secrets.token_urlsafe(16),))

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
        return dict(run_id=self.run_id(), report_sha=self.db.execute("SELECT value FROM metadata WHERE key='report_sha'").fetchone()[0],
                    decisions=[json.loads(r[0]) for r in self.db.execute('SELECT payload FROM decisions ORDER BY id')],
                    audit=[json.loads(r[0]) for r in self.db.execute('SELECT payload FROM audit ORDER BY seq')])


def make_handler(cases, store, token, port):
    class Handler(BaseHTTPRequestHandler):
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
                    rows.append({k: v for k, v in case.items() if k != 'image_path'} | {'decision': store.get(case['id'])})
                return self.send(200, dict(cases=rows, token=token, run_id=store.run_id()))
            if self.path == '/api/archives':
                return self.send(200, dict(archived_runs=store.archives()))
            if self.path == '/api/export':
                return self.send(200, store.export())
            if self.path.startswith('/image/') and self.path[7:] in cases:
                return self.send(200, cases[self.path[7:]]['image_path'].read_bytes(), 'image/bmp')
            self.send(404, {'error': 'Not found'})

        def do_POST(self):
            if not self.allowed() or self.headers.get('X-Review-Token') != token:
                return self.send(403, {'error': 'Invalid local session'})
            if self.path not in ('/api/decision', '/api/reset'):
                return self.send(404, {'error': 'Not found'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 131072:
                    raise ValueError('Invalid request length')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Expected an object')
                if data.get('run_id') != store.run_id():
                    raise RuntimeError('Review round changed. Reload the page before saving.')
                if self.path == '/api/reset':
                    return self.send(200, dict(run_id=store.reset(data['run_id'])))
                if data.get('id') not in cases:
                    raise ValueError('Unknown document')
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
    args = parser.parse_args()
    cases, fingerprint = load_cases()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    store = Store(args.db, fingerprint)
    server = HTTPServer(('127.0.0.1', args.port), make_handler(cases, store, secrets.token_urlsafe(32), args.port))
    print(f'Review {len(cases)} synthetic OCR cases at http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        store.db.close()


if __name__ == '__main__':
    main()

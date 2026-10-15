"""Local upload demo: printed English OCR with synthetic-contract field suggestions."""
import argparse,hashlib,io,json,secrets,shutil,subprocess,tempfile,warnings,time,threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from PIL import Image,ImageOps,UnidentifiedImageError
from enhanced import recognize,prepare
from extraction_candidate import extract_candidate
ROOT=Path(__file__).resolve().parent
MAX_BYTES=10*1024*1024
MAX_PIXELS=12_000_000
OCR_SLOT=threading.BoundedSemaphore(1)


def available_languages():
    if shutil.which('tesseract') is None:return []
    result=subprocess.run(['tesseract','--list-langs'],capture_output=True,text=True,check=True,timeout=10)
    return [line.strip() for line in result.stdout.splitlines() if line.strip() in ('eng','tha')]


def recognize_upload(path,language,layout):
    if language=='eng' and layout=='document':return recognize(path,'enhanced')[0]
    with tempfile.TemporaryDirectory() as tmp:
        if layout=='document':
            im,_=prepare(path);input_path=Path(tmp)/'prepared.png';im.save(input_path)
        else:input_path=path
        psm={'document':'6','general':'3','sparse':'11'}[layout]
        return subprocess.run(['tesseract',str(input_path),'stdout','-l',language,'--psm',psm],capture_output=True,text=True,check=True,timeout=30).stdout


def read_image(raw,language='eng',layout='document'):
    started=time.perf_counter()
    if language not in ('eng','tha+eng') or layout not in ('document','general','sparse'):
        raise ValueError('Invalid language or page layout')
    if not raw or len(raw)>MAX_BYTES:raise ValueError('Select an image up to 10 MiB.')
    with warnings.catch_warnings():
        warnings.simplefilter('error',Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(raw)) as probe:
                if probe.format not in ('PNG','JPEG','BMP'):raise ValueError('Use PNG, JPG or BMP.')
                if probe.width*probe.height>MAX_PIXELS:raise ValueError('Image exceeds 12 megapixels. Resize it first.')
                if getattr(probe,'n_frames',1)!=1:raise ValueError('Use a single-frame image.')
                probe.verify()
            with Image.open(io.BytesIO(raw)) as source:
                im=ImageOps.exif_transpose(source)
                if im.mode in ('RGBA','LA') or 'transparency' in im.info:
                    rgba=im.convert('RGBA');background=Image.new('RGBA',rgba.size,'white');background.alpha_composite(rgba);im=background.convert('L')
                else:im=im.convert('L')
                im.load()
        except (UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning) as exc:
            raise ValueError('Cannot decode this image safely. Export it as PNG/JPG and try again.') from exc
    if shutil.which('tesseract') is None:raise RuntimeError('Tesseract is missing. Run with the existing Docker image; see IMAGE_READER_GUIDE.md.')
    installed=available_languages()
    if any(code not in installed for code in language.split('+')):
        raise ValueError('Selected OCR language is not installed. Build Dockerfile.thai or select English.')
    decoded=time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'input.png';im.save(path)
        text=recognize_upload(path,language,layout)
    recognized=time.perf_counter()
    fields=extract_candidate(text) if layout=='document' else dict(document_id=None,date=None,amount=None)
    return dict(source_sha256=hashlib.sha256(raw).hexdigest(),width=im.width,height=im.height,
                language=language,layout=layout,field_extraction_enabled=layout=='document',
                method='enhanced + experimental extractor' if layout=='document' else 'grayscale page OCR; no structured table reconstruction',text=text,fields=fields,
                needs_human_review=True,
                timing_seconds=dict(decode=round(decoded-started,3),preprocess_and_ocr=round(recognized-decoded,3),total=round(time.perf_counter()-started,3)),
                warnings=['Check every value against the image; no automatic approval.',
                          'Field extraction is designed for the synthetic Document ID / Date / Amount contract. Other document layouts/IDs may return null.',
                          'Thai requires installed tha data. Handwriting, PDF and structured table reconstruction are not supported.'])


def handler(token,port):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(30)
        def log_message(self,*args):pass
        def allowed(self):return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
        def send(self,status,payload,mime='application/json; charset=utf-8'):
            body=payload if isinstance(payload,bytes) else json.dumps(payload,ensure_ascii=False).encode('utf-8')
            self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' blob:; script-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'")
            self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if not self.allowed():return self.send(403,dict(error='Invalid local host'))
            if self.path=='/':return self.send(200,(ROOT/'image_reader.html').read_bytes(),'text/html; charset=utf-8')
            if self.path=='/reader.js':return self.send(200,(ROOT/'image_reader.js').read_bytes(),'text/javascript; charset=utf-8')
            if self.path=='/api/session':
                try:return self.send(200,dict(token=token,languages=available_languages()))
                except subprocess.SubprocessError:return self.send(503,dict(error='Cannot inspect OCR languages'))
            return self.send(404,dict(error='Not found'))
        def do_POST(self):
            if not self.allowed() or self.headers.get('X-Reader-Token')!=token:return self.send(403,dict(error='Invalid local session'))
            if self.path!='/api/read':return self.send(404,dict(error='Not found'))
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=MAX_BYTES:return self.send(413,dict(error='Select an image up to 10 MiB.'))
                raw=self.rfile.read(size)
                if len(raw)!=size:raise ValueError('Incomplete image upload')
                if not OCR_SLOT.acquire(blocking=False):
                    return self.send(429,dict(error='OCR is already running in another tab. Wait for it to finish, then retry.'))
                try:
                    result=read_image(raw,language=self.headers.get('X-OCR-Language','eng'),layout=self.headers.get('X-OCR-Layout','document'))
                finally:
                    OCR_SLOT.release()
                return self.send(200,result)
            except ValueError as exc:return self.send(400,dict(error=str(exc)))
            except (RuntimeError,subprocess.SubprocessError) as exc:
                message=str(exc) if isinstance(exc,RuntimeError) else 'OCR failed or timed out. Try a clearer or smaller image.'
                return self.send(503,dict(error=message))
    return Handler


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8766)
    p.add_argument('--host',choices=['127.0.0.1','0.0.0.0'],default='127.0.0.1');a=p.parse_args()
    server=ThreadingHTTPServer((a.host,a.port),handler(secrets.token_urlsafe(32),a.port))
    print(f'Image reader: http://127.0.0.1:{a.port} (PNG/JPG/BMP; English printed text)',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()

import base64
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from review_app import Store, validate_package

class UploadQueueTests(unittest.TestCase):
    def package(self):
        out=io.BytesIO();Image.new('RGB',(30,20),'white').save(out,format='PNG');raw=out.getvalue()
        return dict(format='ocr-review-package-v1',image_base64=base64.b64encode(raw).decode(),result=dict(
            source_sha256=hashlib.sha256(raw).hexdigest(),language='eng',layout='document',field_extraction_enabled=True,
            text='Document ID: SYN-123456\nDate: 2026-10-15\nAmount: 12.45',
            fields=dict(document_id='SYN-123456',date='2026-10-15',amount='12.45')))
    def test_persistent_import_dedup_review_and_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'uploads.db';s=Store(path,'uploads-v1');package=self.package()
            case_id,created=s.import_package(package);self.assertTrue(created)
            self.assertFalse(s.import_package(package)[1]);self.assertEqual(len(s.uploaded_cases()),1)
            case=s.uploaded_cases()[case_id]
            self.assertTrue(case['image_bytes'].startswith(b'\x89PNG'))
            s.save(case_id,dict(version=0,status='approved',values=case['original'],reviewer='ผู้ตรวจ',note='',corrected_text=case['text'],text_confirmed=True),case['original'],case['text'])
            exported=s.export();self.assertEqual(exported['queue_kind'],'uploads');self.assertEqual(exported['documents'][0]['source_sha256'],package['result']['source_sha256'])
            self.assertNotIn('image_bytes',json.dumps(exported));self.assertNotIn('image_base64',json.dumps(exported))
            s.reset(s.run_id());self.assertIsNone(s.get(case_id));self.assertEqual(len(s.uploaded_cases()),1)
            self.assertEqual(s.archives()[0]['export'],exported);s.db.close()
            s=Store(path,'uploads-v1');self.assertEqual(len(s.uploaded_cases()),1);s.db.close()
    def test_benchmark_cannot_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(Path(tmp)/'state.db','benchmark')
            try:
                with self.assertRaises(ValueError):s.import_package(self.package())
            finally:s.db.close()
    def test_changed_image_hash(self):
        p=self.package();p['result']['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash'):validate_package(p)
    def test_general_layout_rejected(self):
        p=self.package();p['result']['layout']='general'
        with self.assertRaises(ValueError):validate_package(p)
    def test_invalid_image_and_base64(self):
        for raw in [b'not an image',b'']:
            p=self.package();p['image_base64']=base64.b64encode(raw).decode();p['result']['source_sha256']=hashlib.sha256(raw).hexdigest()
            with self.assertRaises(ValueError):validate_package(p)
        p=self.package();p['image_base64']='!!!'
        with self.assertRaises(ValueError):validate_package(p)
    def test_package_type_and_fields(self):
        for p in [None,{},[],dict(format='bad')]:
            with self.assertRaises(ValueError):validate_package(p)
        p=self.package();p['result']['fields']['amount']=123
        with self.assertRaises(ValueError):validate_package(p)
    def test_no_automatic_numeric_repair(self):
        p=self.package();p['result']['fields']['amount']=None
        case,_=validate_package(p);self.assertEqual(case['original']['amount'],'');self.assertTrue(case['reasons'])
    def test_different_ocr_text_is_separate_case(self):
        p=self.package();first,_=validate_package(p);p['result']['text']+='\nService'
        second,_=validate_package(p);self.assertNotEqual(first['id'],second['id'])

class UploadHTTPTests(unittest.TestCase):
    package = UploadQueueTests.package
    # Exercise the real HTTP boundary without rerunning OCR.
    def test_http_token_round_import_image_and_export(self):
        import threading
        import urllib.request
        import urllib.error
        from http.server import HTTPServer
        from review_app import make_handler
        with tempfile.TemporaryDirectory() as tmp:
            ready=threading.Event();state={}
            def serve():
                store=Store(Path(tmp)/'http.db','uploads-v1')
                server=HTTPServer(('127.0.0.1',0),make_handler({},store,'secret',0,True))
                server.RequestHandlerClass=make_handler({},store,'secret',server.server_port,True)
                state.update(server=server);ready.set()
                try:server.serve_forever()
                finally:server.server_close();store.db.close()
            thread=threading.Thread(target=serve);thread.start();self.assertTrue(ready.wait(3))
            url=f"http://127.0.0.1:{state['server'].server_port}"
            def get(path):
                with urllib.request.urlopen(url+path,timeout=3) as response:return response.read(),response.headers
            def post(payload,token='secret'):
                request=urllib.request.Request(url+'/api/import',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Review-Token':token})
                with urllib.request.urlopen(request,timeout=3) as response:return json.load(response)
            try:
                session=json.loads(get('/api/cases')[0]);self.assertEqual(session['queue_kind'],'uploads')
                payload=dict(run_id=session['run_id'],package=self.package())
                for token,run_id,expected in [('wrong',session['run_id'],403),('secret','stale',409)]:
                    with self.assertRaises(urllib.error.HTTPError) as error:post(payload|{'run_id':run_id},token)
                    self.assertEqual(error.exception.code,expected)
                imported=post(payload);self.assertTrue(imported['created'])
                self.assertFalse(post(payload)['created'])
                cases=json.loads(get('/api/cases')[0])['cases'];self.assertEqual(len(cases),1)
                self.assertNotIn('image_bytes',cases[0]);self.assertIsNone(cases[0]['decision'])
                raw,headers=get('/image/'+imported['id']);self.assertEqual(headers['Content-Type'],'image/png');self.assertTrue(raw.startswith(b'\x89PNG'))
                exported=json.loads(get('/api/export')[0]);self.assertEqual(len(exported['documents']),1)
            finally:state['server'].shutdown();thread.join(3)

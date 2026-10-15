import json,socket,threading,unittest,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from image_reader import handler
class ReaderResponsiveTests(unittest.TestCase):
    def setUp(self):
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler('test',0));self.port=self.server.server_port
        self.server.RequestHandlerClass=handler('test',self.port)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(2)
    def get(self):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.port}/api/session',timeout=2) as r:return json.load(r)
    def post(self):
        request=urllib.request.Request(f'http://127.0.0.1:{self.port}/api/read',data=b'x',headers={'X-Reader-Token':'test'})
        with urllib.request.urlopen(request,timeout=4) as r:return json.load(r)
    def test_idle_connection_does_not_block_page(self):
        idle=socket.create_connection(('127.0.0.1',self.port))
        try:self.assertEqual(self.get()['token'],'test')
        finally:idle.close()
    def test_page_responsive_and_other_ocr_busy(self):
        started=threading.Event();release=threading.Event()
        def slow(raw,**options):
            started.set();release.wait(3);return dict(text='done')
        with patch('image_reader.read_image',side_effect=slow),ThreadPoolExecutor(1) as pool:
            future=pool.submit(self.post)
            try:
                self.assertTrue(started.wait(2));self.assertEqual(self.get()['token'],'test')
                with self.assertRaises(urllib.error.HTTPError) as e:self.post()
                self.assertEqual(e.exception.code,429)
            finally:release.set()
            self.assertEqual(future.result()['text'],'done')

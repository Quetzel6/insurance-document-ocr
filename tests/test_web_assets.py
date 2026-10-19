import contextlib
import http.client
from http.server import HTTPServer, BaseHTTPRequestHandler
import io
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import image_reader
import review_app
from web_assets import check_assets, read_asset, WebAssetError


class WebAssetTests(unittest.TestCase):
    def test_missing_directory_or_file_reports_recovery_without_creating_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'moved'
            with self.assertRaises(WebAssetError) as caught:
                read_asset(root, 'review_ui.html')
            self.assertIn('git restore --source=HEAD --worktree -- review_ui.html',str(caught.exception))
            self.assertFalse(root.exists())

    def test_check_reads_every_required_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'review_ui.html').write_bytes(b'<h1>Ready</h1>')
            with self.assertRaises(WebAssetError):
                check_assets(root,('review_ui.html','review_ui.js'))
            (root/'review_ui.js').write_bytes(b'console.log("ready")')
            check_assets(root,('review_ui.html','review_ui.js'))

    def test_startup_stops_before_database_or_socket(self):
        for module in (review_app,image_reader):
            with self.subTest(app=module.__name__),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                with patch.object(module,'ROOT',root),patch('sys.argv',['app']),contextlib.redirect_stderr(io.StringIO()):
                    if module is review_app:
                        with patch.object(module,'Store') as store,patch.object(module,'HTTPServer') as server:
                            with self.assertRaises(SystemExit) as caught:module.main()
                            self.assertEqual(caught.exception.code,2);store.assert_not_called();server.assert_not_called()
                    else:
                        with patch.object(module,'ThreadingHTTPServer') as server:
                            with self.assertRaises(SystemExit) as caught:module.main()
                            self.assertEqual(caught.exception.code,2);server.assert_not_called()
                self.assertEqual(list(root.iterdir()),[])

    def test_missing_live_assets_return_503_and_recover_without_touching_data(self):
        for module,names,urls in ((review_app,('review_ui.html','review_ui.js'),('/','/app.js')),
                                 (image_reader,('image_reader.html','image_reader.js'),('/','/reader.js'))):
            with self.subTest(app=module.__name__),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);snapshot=b'private-review-database';(root/'keep.sqlite3').write_bytes(snapshot)
                server=HTTPServer(('127.0.0.1',0),BaseHTTPRequestHandler);port=server.server_port
                server.RequestHandlerClass=(module.make_handler({},SimpleNamespace(export=lambda:{'decisions':[]}), 'token',port,True)
                                            if module is review_app else module.handler('token',port))
                with patch.object(module,'ROOT',root):
                    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                    try:
                        for name,url in zip(names,urls):
                            connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
                            connection.request('GET',url);response=connection.getresponse();body=response.read().decode()
                            self.assertEqual(response.status,503);self.assertIn(name,body)
                            self.assertEqual(response.getheader('Content-Type'),'text/plain; charset=utf-8')
                            self.assertEqual(response.getheader('Cache-Control'),'no-store');connection.close()
                            (root/name).write_bytes(b'restored file')
                            connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
                            connection.request('GET',url);response=connection.getresponse()
                            self.assertEqual(response.status,200);self.assertEqual(response.read(),b'restored file');connection.close()
                        self.assertEqual((root/'keep.sqlite3').read_bytes(),snapshot)
                    finally:server.shutdown();thread.join();server.server_close()


if __name__=='__main__':unittest.main()

import io,unittest
from unittest.mock import patch
from PIL import Image
from image_reader import read_image
class ImageReaderTests(unittest.TestCase):
    def png(self):
        out=io.BytesIO();Image.new('RGB',(100,80),'white').save(out,format='PNG');return out.getvalue()
    def test_upload_reads_image_without_labels_and_marks_review(self):
        with patch('image_reader.recognize',return_value=('Document ID SYN-123456\nDate 20261015\nAmount 12.45',0)),patch('image_reader.shutil.which',return_value='/usr/bin/tesseract'):
            r=read_image(self.png());self.assertEqual(r['fields']['amount'],'12.45');self.assertTrue(r['needs_human_review']);self.assertEqual(r['width'],100)
    def test_invalid_image(self):
        with self.assertRaises(ValueError):read_image(b'not an image')
    def test_oversize(self):
        with self.assertRaises(ValueError):read_image(b'a'*(10*1024*1024+1))
    def test_missing_engine(self):
        with patch('image_reader.shutil.which',return_value=None):
            with self.assertRaises(RuntimeError):read_image(self.png())

    def test_thai_missing_is_explicit_error(self):
        with patch('image_reader.available_languages',return_value=['eng']):
            with self.assertRaisesRegex(ValueError,'not installed'):read_image(self.png(),language='tha+eng')
    def test_general_mode_disables_document_fields(self):
        with patch('image_reader.available_languages',return_value=['eng']),patch('image_reader.recognize_upload',return_value='Amount 12.45'):
            r=read_image(self.png(),layout='general')
            self.assertFalse(r['field_extraction_enabled']);self.assertTrue(all(v is None for v in r['fields'].values()))
    def test_thai_request_preserves_unicode_when_engine_available(self):
        with patch('image_reader.available_languages',return_value=['eng','tha']),patch('image_reader.recognize_upload',return_value='พนักงาน เขตการขาย') as engine:
            r=read_image(self.png(),language='tha+eng',layout='general')
            self.assertEqual(r['text'],'พนักงาน เขตการขาย');self.assertEqual(engine.call_args.args[1:],('tha+eng','general'))
    def test_invalid_options(self):
        with self.assertRaises(ValueError):read_image(self.png(),language='unexpected')

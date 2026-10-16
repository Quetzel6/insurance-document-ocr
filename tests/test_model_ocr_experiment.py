import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from model_ocr_experiment import model_hashes,ocr_model
class ModelOCRTests(unittest.TestCase):
 def test_wrong_model_hash_stops_evaluation(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'eng.traineddata').write_bytes(b'untrusted model')
   with patch('model_ocr_experiment.MODEL_DIR',p):
    with self.assertRaisesRegex(ValueError,'hash'):model_hashes()
 def test_missing_model_directory_is_explicit(self):
  with patch('model_ocr_experiment.MODEL_DIR',None):
   with self.assertRaisesRegex(ValueError,'best-dir'):model_hashes()
 def test_candidate_passes_model_directory_without_changing_page_mode(self):
  from PIL import Image
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);im=Image.new('L',(10,10),255)
   with patch('model_ocr_experiment.MODEL_DIR',p),patch('model_ocr_experiment.subprocess.run') as run:
    run.return_value.stdout='OCR text'
    self.assertEqual(ocr_model(im,p/'image.png','tessdata_best'),'OCR text')
    args=run.call_args.args[0]
    self.assertEqual(args[-2:],['--tessdata-dir',str(p)])
    self.assertEqual(args[args.index('--oem')+1],'1');self.assertEqual(args[args.index('--psm')+1],'6')

import json,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
from line_ocr_experiment import line_boxes,fingerprints,freeze,evaluate
class LineOCRTests(unittest.TestCase):
 def test_crop_covers_two_separate_ink_lines(self):
  im=Image.new('L',(160,90),255);d=ImageDraw.Draw(im)
  d.rectangle((20,15,90,25),fill=0);d.rectangle((40,55,130,65),fill=0)
  boxes=line_boxes(im);self.assertEqual(len(boxes),2)
  for box,point in zip(boxes,[(20,15),(130,65)]):
   self.assertLessEqual(box[0],point[0]);self.assertLessEqual(box[1],point[1]);self.assertGreater(box[2],point[0]);self.assertGreater(box[3],point[1])
 def test_blank_image_has_no_lines(self):self.assertEqual(line_boxes(Image.new('L',(100,100),255)),[])
 def test_test_requires_frozen_protocol(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'manifest.json').write_text('{"records":[]}')
   with self.assertRaises(FileNotFoundError):evaluate(p,'test')
 def test_frozen_manifest_changes_stop_test_before_ocr(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'manifest.json').write_text('{"records":[]}')
   (p/'dev_report.json').write_text(json.dumps(dict(fingerprints=fingerprints(p))))
   freeze(p,'page_current')
   with self.assertRaises(ValueError):freeze(p,'page_current')
   (p/'manifest.json').write_text('{"records":[],"changed":true}')
   with self.assertRaisesRegex(ValueError,'protocol'):evaluate(p,'test')

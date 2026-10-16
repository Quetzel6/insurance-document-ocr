import unittest
from PIL import Image
from ocr_variant_experiment import METHODS, summarize, otsu
class ExperimentTests(unittest.TestCase):
 def test_wrong_emitted_and_missing_are_separate(self):
  rows=[]
  for method in METHODS:
   rows.append(dict(method=method,condition='blur_lowres',original_id='one',edits=2,chars=10,
    prediction=dict(document_id='SYN-999999',date=None,amount='12.45'),
    matches=dict(document_id=False,date=False,amount=True)))
  result=next(r for r in summarize(rows) if r['method']=='current' and r['condition']=='all')
  self.assertEqual(result['wrong_emitted'],dict(document_id=1,date=0,amount=0))
  self.assertEqual(result['missing'],dict(document_id=0,date=1,amount=0))
  self.assertEqual(result['complete'],0);self.assertEqual(result['cer'],0.2)
 def test_threshold_preserves_size_and_binary_levels(self):
  im=Image.new('L',(4,1));im.putdata([0,50,200,255]);out=otsu(im)
  self.assertEqual(out.size,im.size);self.assertEqual(list(out.tobytes()),[0,0,255,255])

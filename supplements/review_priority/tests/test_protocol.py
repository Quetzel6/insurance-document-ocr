import hashlib,json,tempfile,unittest
from pathlib import Path
from experiment import validate,run

class ProtocolTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.data=self.root/'data';self.data.mkdir();records=[]
  for split in ('dev','test'):
   p=self.data/(split+'.png');p.write_bytes(split.encode());records.append(dict(id=split,original_id=split,layout=split,split=split,image=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
  self.manifest=dict(records=records);self.save()
 def save(self):(self.data/'manifest.json').write_text(json.dumps(self.manifest))
 def test_original_leakage_rejected(self):
  self.manifest['records'][1]['original_id']='dev';self.save()
  with self.assertRaisesRegex(ValueError,'split leakage'):validate(self.data)
 def test_image_tampering_rejected(self):
  (self.data/'dev.png').write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'hash mismatch'):validate(self.data)
 def test_existing_evidence_not_overwritten(self):
  out=self.root/'existing';out.mkdir();(out/'keep').write_text('evidence')
  with self.assertRaisesRegex(ValueError,'Output exists'):run(self.data,out)
  self.assertEqual((out/'keep').read_text(),'evidence')

if __name__=='__main__':unittest.main()

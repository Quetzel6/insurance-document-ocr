import json,tempfile,unittest
from pathlib import Path
from engine_label_experiment import extract_joined_label,run
class JoinedLabelTests(unittest.TestCase):
 def test_joined_label_before_separator(self):
  for label in ['DocumentID:','Document1D=','DocumentI0:']:
   self.assertEqual(extract_joined_label(label+' SYN-123456')['document_id'],'SYN-123456')
 def test_never_repairs_digits_or_missing_decimal(self):
  r=extract_joined_label('DocumentID:SYN-12345O\nAmount 12 45')
  self.assertIsNone(r['document_id']);self.assertIsNone(r['amount'])
 def test_duplicate_invalid_label_stays_ambiguous(self):
  r=extract_joined_label('DocumentID:SYN-123456\nDocumentID:unreadable')
  self.assertIsNone(r['document_id'])
 def test_non_label_text_not_extracted(self):
  self.assertIsNone(extract_joined_label('Account DocumentID:SYN-123456')['document_id'])
 def test_replay_refuses_test_evidence(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'test.json';source.write_text(json.dumps(dict(split='test')))
   with self.assertRaisesRegex(ValueError,'development'):run(source,Path(tmp)/'out.json')

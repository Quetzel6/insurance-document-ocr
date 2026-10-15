import tempfile,unittest
from pathlib import Path
from review_app import Store
class ResetTests(unittest.TestCase):
    def test_reset_archives_and_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'state.db';s=Store(path,'report')
            old=s.run_id();values=dict(document_id='',date='',amount='')
            s.save('a',dict(values=values,status='rejected',reviewer='ผู้ตรวจ',note='ภาพเบลอ',version=0,corrected_text='?',text_confirmed=False),values,'raw')
            snapshot=s.export();new=s.reset(old)
            self.assertNotEqual(old,new);self.assertIsNone(s.get('a'));self.assertEqual(s.export()['audit'],[])
            self.assertEqual(s.archives()[0]['export'],snapshot)
            s.db.close();s=Store(path,'report')
            self.assertEqual(s.run_id(),new);self.assertEqual(s.archives()[0]['export']['decisions'][0]['note'],'ภาพเบลอ');s.db.close()
    def test_stale_reset_cannot_clear_new_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(Path(tmp)/'state.db','report');old=s.run_id();new=s.reset(old)
            with self.assertRaises(RuntimeError):s.reset(old)
            self.assertEqual(s.run_id(),new);self.assertEqual(len(s.archives()),1);s.db.close()

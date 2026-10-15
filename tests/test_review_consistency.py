import unittest
from review_consistency import check_consistency
from review_app import Store
import tempfile
from pathlib import Path

VALUES=dict(document_id='SYN-123456',date='2026-10-15',amount='123.45')
TEXT='Document ID: SYN-123456\nDate: 2026-10-15\nAmount: 123.45'

class ConsistencyTests(unittest.TestCase):
    def test_matching(self):
        self.assertTrue(check_consistency(TEXT,VALUES)['passed'])
    def test_mismatching_date(self):
        r=check_consistency(TEXT,VALUES|{'date':'2026-10-14'})
        self.assertFalse(r['passed'])
        self.assertIn('date:',r['errors'][0])
    def test_no_decimal_guessing(self):
        self.assertFalse(check_consistency(TEXT.replace('123.45','123 45'),VALUES)['passed'])
    def test_duplicate_and_partial(self):
        for extra in ['\nAmount: 99.00','\nAmount: unreadable']:
            self.assertFalse(check_consistency(TEXT+extra,VALUES)['passed'])
        self.assertFalse(check_consistency(TEXT.replace('123.45','123.456'),VALUES)['passed'])
    def test_missing_labels(self):
        self.assertFalse(check_consistency(TEXT.replace('ID:','1D:'),VALUES)['passed'])
    def test_server_blocks_approval_but_allows_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(Path(tmp)/'state.db','test')
            try:
                data=dict(values=VALUES|{'date':'2026-10-14'},status='approved',reviewer='Test',note='',version=0,corrected_text=TEXT,text_confirmed=True)
                with self.assertRaises(ValueError):s.save('a',data,VALUES,TEXT)
                self.assertIsNone(s.get('a'))
                result=s.save('a',data|{'status':'rejected','note':'Cannot verify'},VALUES,TEXT)
                self.assertFalse(result['consistency']['passed'])
            finally:s.db.close()

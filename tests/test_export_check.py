import hashlib,json,unittest
from check_review_export import check_export
class ExportCheckTests(unittest.TestCase):
    def fixture(self):
        text='Document ID: SYN-123456\nDate: 2026-10-15\nAmount: 123.45'
        values=dict(document_id='SYN-123456',date='2026-10-15',amount='123.45')
        raw=json.dumps(dict(records=[dict(id='a',method='enhanced',text=text,prediction=values)])).encode()
        row=dict(id='a',version=1,status='approved',reviewer='ผู้ตรวจ',note='',original=values,values=values.copy(),original_text=text,corrected_text=text,text_confirmed=True)
        return dict(report_sha=hashlib.sha256(raw).hexdigest(),decisions=[row],audit=[row.copy()]),raw
    def test_consistent(self):
        d,r=self.fixture();self.assertEqual(check_export(d,r)['counts']['consistent_review'],1)
    def test_disagreement(self):
        d,r=self.fixture();d['decisions'][0]['values']=d['decisions'][0]['values']|{'date':'2026-10-14'}
        self.assertEqual(check_export(d,r)['counts']['needs_review'],1)
    def test_rejected(self):
        d,r=self.fixture();d['decisions'][0].update(status='rejected',note='ภาพเบลอ',corrected_text='?',text_confirmed=False);d['audit']=[d['decisions'][0].copy()]
        self.assertEqual(check_export(d,r)['counts']['excluded_rejected'],1)
    def test_wrong_source(self):
        d,r=self.fixture();d['report_sha']='wrong'
        with self.assertRaises(ValueError):check_export(d,r)
    def test_legacy_missing_audit(self):
        d,r=self.fixture();d['audit']=[];del d['decisions'][0]['corrected_text']
        self.assertEqual(check_export(d,r)['counts']['needs_review'],1)

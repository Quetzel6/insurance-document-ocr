import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review_app import Store, validation, load_cases
VALID = dict(document_id='SYN-123456', date='2026-10-15', amount='123.45')
TEXT = 'Document ID: SYN-123456\nDate: 2026-10-15\nAmount: 123.45'
class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'decisions.db'
        self.store=Store(self.path,'report-a')
    def tearDown(self):
        self.store.db.close()
        self.tmp.cleanup()
    def data(self,**changes):
        return dict(values=VALID.copy(),status='approved',reviewer='Tester',note='',version=0,corrected_text=TEXT,text_confirmed=True)|changes
    def test_validation(self):
        self.assertEqual(validation(VALID),[])
        self.assertEqual(len(validation(dict(document_id='SYN-12345',date='2026-02-30',amount='NaN'))),3)
        self.assertTrue(validation(VALID|{'amount':'-1.00'}))
    def test_invalid_approval(self):
        with self.assertRaises(ValueError):
            self.store.save('a',self.data(values=VALID|{'date':'2026-02-30'}),VALID)
        self.assertIsNone(self.store.get('a'))
    def test_rejection(self):
        with self.assertRaises(ValueError):
            self.store.save('a',self.data(status='rejected'),VALID)
        d=self.store.save('a',self.data(status='rejected',values=dict.fromkeys(VALID,''),note='Unreadable'),VALID)
        self.assertEqual(d['status'],'rejected')
    def test_persistence_history_conflict(self):
        self.store.save('a',self.data(),VALID)
        with self.assertRaises(RuntimeError):
            self.store.save('a',self.data(note='stale'),VALID)
        self.store.save('a',self.data(version=1,note='Rechecked'),VALID)
        self.store.db.close()
        self.store=Store(self.path,'report-a')
        self.assertEqual(self.store.get('a')['version'],2)
        self.assertEqual(len(self.store.export()['audit']),2)
        self.assertEqual(self.store.export()['audit'][0]['original'],VALID)
    def test_report_binding(self):
        with self.assertRaises(ValueError):Store(self.path,'different-report')
    def test_no_benchmark_labels(self):
        cases,_=load_cases()
        self.assertEqual(len(cases),40)
        for case in cases.values():
            self.assertNotIn('matches',case)
            self.assertNotIn('fields',case)
            self.assertNotIn('condition',case)

    def test_text_edits_require_confirmation_and_preserve_original(self):
        raw='Document 1D: SYN-123456\nAmourt: 123.45'
        fixed=TEXT
        data=self.data(corrected_text=fixed,text_confirmed=False)
        with self.assertRaises(ValueError):self.store.save('a',data,VALID,raw)
        result=self.store.save('a',data|{'text_confirmed':True},VALID,raw)
        self.assertEqual(result['original_text'],raw)
        self.assertEqual(result['corrected_text'],fixed)
        self.assertTrue(result['text_changes'])
        self.assertEqual(result['values'],VALID)
        self.store.db.close()
        self.store=Store(self.path,'report-a')
        self.assertEqual(self.store.get('a')['corrected_text'],fixed)
        self.assertEqual(self.store.export()['audit'][0]['original_text'],raw)
    def test_text_limit_and_rejection(self):
        with self.assertRaises(ValueError):self.store.save('a',self.data(corrected_text='x'*10001),VALID,'raw')
        result=self.store.save('a',self.data(status='rejected',note='Unreadable digits',corrected_text='[unreadable]',text_confirmed=False),VALID,'raw')
        self.assertFalse(result['text_confirmed'])
    def test_old_decision_can_be_updated_without_schema_migration(self):
        import json
        old=dict(id='legacy',version=1,status='approved',values=VALID,original=VALID,reviewer='Old',note='',saved_at='old')
        with self.store.db:self.store.db.execute('INSERT INTO decisions VALUES (?,?,?)',('legacy',1,json.dumps(old)))
        new=self.store.save('legacy',self.data(version=1,corrected_text=TEXT,text_confirmed=True),VALID,'1D')
        self.assertEqual(new['version'],2)
        self.assertEqual(new['original_text'],'1D')

    def test_thai_rejection_persistence_and_export(self):
        import json
        note='ภาพเบลอ อ่านเลขยอดเงินไม่ชัด ขอเอกสารใหม่'
        result=self.store.save('thai',self.data(status='rejected',reviewer='ผู้ตรวจสอบ',note=note,corrected_text='อ่านไม่ออก',text_confirmed=False),VALID,'raw')
        self.assertEqual(result['note'],note)
        self.store.db.close()
        self.store=Store(self.path,'report-a')
        self.assertEqual(self.store.get('thai')['note'],note)
        exported=json.loads(json.dumps(self.store.export(),ensure_ascii=False).encode('utf-8'))
        self.assertEqual(exported['decisions'][0]['note'],note)
        self.assertEqual(exported['audit'][0]['note'],note)
    def test_reject_whitespace_only_reason(self):
        with self.assertRaises(ValueError):
            self.store.save('thai',self.data(status='rejected',note=' \n\t '),VALID,'raw')

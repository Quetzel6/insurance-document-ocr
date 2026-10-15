import unittest
from analyze_reviews import analyze

class AnalysisTests(unittest.TestCase):
    def row(self,**changes):
        values=dict(document_id='SYN-123456',date='2026-10-15',amount='123.45')
        return dict(id='a',status='approved',original=values.copy(),values=values.copy(),original_text='Amourt 1D',corrected_text='Amount ID',text_confirmed=True)|changes
    def test_confirmed_pairs_and_field_changes(self):
        row=self.row();row['values']['amount']='128.45'
        r=analyze(dict(decisions=[row],audit=[row,row]))
        self.assertEqual(r['reviewed_documents'],1)
        self.assertEqual(r['approved_field_changes']['amount'],1)
        self.assertEqual(r['approved_confirmed_text_documents'],1)
        self.assertTrue(r['confirmed_token_edits'])
    def test_rejected_and_unconfirmed_not_used_as_training_truth(self):
        r=analyze(dict(decisions=[self.row(status='rejected'),self.row(id='b',text_confirmed=False)]))
        self.assertEqual(r['confirmed_token_edits'],[])
        self.assertEqual(r['statuses'],dict(rejected=1,approved=1))
    def test_legacy_and_empty(self):
        row=self.row();del row['original_text']
        self.assertEqual(analyze(dict(decisions=[row]))['approved_legacy_without_text'],1)
        self.assertEqual(analyze(dict(decisions=[]))['reviewed_documents'],0)
    def test_duplicate_and_bad_input(self):
        with self.assertRaises(ValueError):analyze(dict(decisions=[self.row(),self.row()]))
        with self.assertRaises(ValueError):analyze([])

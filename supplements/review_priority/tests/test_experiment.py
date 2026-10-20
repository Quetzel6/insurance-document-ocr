import unittest
from experiment import extract,parse_tsv,prioritize,select_dev,summary

def row(correct=True,conf=90,method='raw',complete=True):
 return dict(method=method,original_id='a',prediction={k:'x' if complete else None for k in ('document_id','date','amount')},mean_word_confidence=conf,complete_correct=correct,matches={'document_id':correct,'date':correct,'amount':correct})
class Tests(unittest.TestCase):
 def test_incomplete_never_prioritized(self):self.assertFalse(prioritize(row(complete=False),0))
 def test_missing_confidence_never_prioritized(self):self.assertFalse(prioritize(row(conf=None),0))
 def test_no_priority_has_undefined_error_rate(self):self.assertIsNone(summary([row()], 'raw',101)['priority_error_rate'])
 def test_high_confidence_wrong_value_counted(self):self.assertEqual(summary([row(False,99)],'raw',95)['incorrect_prioritized'],1)
 def test_dev_selection_excludes_observed_errors(self):self.assertEqual(select_dev([row(False,99),row(True,98)])[0]['incorrect_prioritized'],0)
 def test_method_denominator(self):self.assertEqual(summary([row(),row(method='upscale_sharpen')],'raw',0)['images'],1)
 def test_invalid_calendar_date(self):self.assertIsNone(extract('Date: 2026-02-30')['date'])
 def test_no_digit_guessing(self):self.assertIsNone(extract('Amount: 1O0.00')['amount'])
 def test_realistic_fields(self):self.assertEqual(extract('Document ID: SYN-123456\nDate: 2026-10-20\nAmount: 1234.56'),dict(document_id='SYN-123456',date='2026-10-20',amount='1234.56'))
 def test_tsv_only_word_confidence(self):
  text='level\tpage_num\tblock_num\tpar_num\tline_num\tconf\ttext\n1\t1\t0\t0\t0\t-1\t\n5\t1\t1\t1\t1\t90\tDate:\n5\t1\t1\t1\t1\t80\t2026-10-20\n'
  self.assertEqual(parse_tsv(text),('Date: 2026-10-20',85))
if __name__=='__main__':unittest.main()

import unittest
from enhanced import extract_validated
class ValidationTests(unittest.TestCase):
 def test_label_and_spacing(self):self.assertEqual(extract_validated('Document \\D: SYN-207 642')['document_id'],'SYN-207642')
 def test_not_guess_digits(self):self.assertIsNone(extract_validated('Document ID: SYN-2O7642')['document_id'])
 def test_invalid_date(self):self.assertIsNone(extract_validated('Date: 2026-02-30')['date'])
 def test_ambiguous_amount(self):self.assertIsNone(extract_validated('Amount: 123.45\nAmount: 234.56')['amount'])
 def test_amount_suffix_not_partial(self):self.assertIsNone(extract_validated('Amount: 123.45oops')['amount'])

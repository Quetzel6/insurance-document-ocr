import unittest
from project import distance,extract,normalize_text
class MetricsTests(unittest.TestCase):
 def test_edit_cases(self):
  for a,b,n in [('','abc',3),('abc','',3),('kitten','sitting',3),('abc','abc',0)]:self.assertEqual(distance(a,b),n)
 def test_normalization_and_amount(self):
  self.assertEqual(normalize_text(' A\n B '),'a b')
  self.assertEqual(extract('Document ID: SYN-123\nDate: 2026-09-11\nAmount: 12,345.67')['amount'],'12345.67')
 def test_missing_not_invented(self):self.assertIsNone(extract('unreadable')['amount'])

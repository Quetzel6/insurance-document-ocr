import unittest
from extraction_candidate import extract_candidate
class CandidateTests(unittest.TestCase):
    def test_labels_no_colon_and_compact_calendar_date(self):
        r=extract_candidate('Document I0 SYN-123456\nDate 20261015\nAmourt 12.45')
        self.assertEqual(r,dict(document_id='SYN-123456',date='2026-10-15',amount='12.45'))
    def test_missing_decimal_not_inferred(self):
        self.assertIsNone(extract_candidate('Amount 12 45')['amount'])
    def test_no_digit_substitution(self):
        r=extract_candidate('Document ID SYN-12345O\nAmount 12.OO')
        self.assertIsNone(r['document_id']);self.assertIsNone(r['amount'])
    def test_invalid_date(self):
        self.assertIsNone(extract_candidate('Date 20260230')['date'])
    def test_duplicate_including_invalid(self):
        for text in ['Amount 12.45\nAmount 12.45','Amount 12.45\nAmourt unreadable']:
            self.assertIsNone(extract_candidate(text)['amount'])
    def test_full_line_boundaries(self):
        for value in ['12.456','12.45 USD','12.45 extra','1,23.45','-12.45']:
            self.assertIsNone(extract_candidate('Amount '+value)['amount'])
    def test_digits_preserved_and_valid_grouping(self):
        r=extract_candidate('Document 1D: SYN-1 2 3 4 5 6\nDate: 2026-10-15\nAmount: 12,345.67')
        self.assertEqual(r['document_id'],'SYN-123456');self.assertEqual(r['amount'],'12345.67')
    def test_does_not_change_service_or_read_other_numeric_lines(self):
        r=extract_candidate('Service Synthetic reper estirnate\nAccount Amount 999.99')
        self.assertTrue(all(v is None for v in r.values()))


class IDFormatTests(unittest.TestCase):
    def test_supported_label_and_separator_preserve_six_digits(self):
        for label in ('Document ID','Document IO','Document I0','Document 1D'):
            for value in ('SYN-537642','SYN 537642','SYN.537642','SYN - 5 3 7 6 4 2'):
                self.assertEqual(extract_candidate(label+' '+value)['document_id'],'SYN-537642')

    def test_ambiguous_or_non_numeric_ids_stay_missing(self):
        for value in ('SYN537642','SYN-53764','SYN-5376421','SYN-53764O','SYN-537642 extra','SYN/537642'):
            self.assertIsNone(extract_candidate('Document IO '+value)['document_id'])
        self.assertIsNone(extract_candidate('Document IO SYN 537642\nDocument ID unreadable')['document_id'])

    def test_other_values_and_text_do_not_change(self):
        raw='Document IO SYN 537642\nDate 20260913\nAmount 6229645\nService Synthetc repair estmate'
        result=extract_candidate(raw)
        self.assertEqual(result,dict(document_id='SYN-537642',date='2026-09-13',amount=None))
        self.assertIn('Synthetc',raw)

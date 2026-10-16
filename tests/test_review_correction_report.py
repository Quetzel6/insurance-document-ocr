import json
import unittest
from review_correction_report import summarize


def decision(identity='one', before='Currency TH\nAmount 86622 45', after='Currency THB\nAmount: 86622.45', **extra):
    return dict(id=identity, status='approved', original_text=before, corrected_text=after, **extra)


class CorrectionReportTests(unittest.TestCase):
    def test_punctuation_is_not_digit_change(self):
        result = summarize({'decisions': [decision()]})['counts']
        self.assertEqual(result['text_changed'], 1)
        self.assertEqual(result['digit_sequence_changed'], 0)
        self.assertEqual(result['punctuation_sequence_changed'], 1)
        self.assertEqual(result['letter_sequence_changed'], 1)

    def test_digit_change_and_unchanged(self):
        result = summarize({'decisions': [decision(before='Amount: 12.45', after='Amount: 13.45'),
                                        decision('two', before='ไทย ๐', after='ไทย ๐')]})['counts']
        self.assertEqual(result['digit_sequence_changed'], 1)
        self.assertEqual(result['text_unchanged'], 1)

    def test_rejected_and_audit_not_reference(self):
        rejected = decision('rejected'); rejected['status'] = 'rejected'
        result = summarize({'decisions': [decision(), rejected], 'audit': [decision()]})['counts']
        self.assertEqual(result['approved_compared'], 1)
        self.assertEqual(result['rejected'], 1)

    def test_no_private_values_in_report(self):
        result = summarize({'decisions': [decision(reviewer='private-person', note='secret-note',
                                                 values={'document_id': 'secret-id'})]})
        serialized = json.dumps(result)
        for private in ('private-person', 'secret-note', 'secret-id', '86622'):
            self.assertNotIn(private, serialized)

    def test_legacy_and_text_modes(self):
        legacy = decision(); del legacy['original_text']
        result = summarize({'decisions': [legacy, decision('two', review_mode='text')]})
        self.assertEqual(result['counts']['approved_missing_text'], 1)
        self.assertEqual(result['approved_modes'], {'text': 1})

    def test_wrong_file_and_duplicate_rejected(self):
        for payload in ({'format': 'ocr-review-package-v1'}, {'decisions': [decision(), decision()]}):
            with self.assertRaises(ValueError):
                summarize(payload)


if __name__ == '__main__':
    unittest.main()

import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from PIL import Image
from amount_ocr_experiment import numeric_crop, recognize_amount


class AmountCropTests(unittest.TestCase):
    def test_no_crop_or_duplicate_label_skips_ocr(self):
        with patch('amount_ocr_experiment.subprocess.run') as run:
            self.assertEqual(recognize_amount(None, Path('/unused'), 7, 'Amount 12 45'), 'Amount 12 45')
            self.assertEqual(recognize_amount(Image.new('L', (20, 10)), Path('/unused'), 7,
                                             'Amount 12.45\nAmount unreadable'), 'Amount 12.45\nAmount unreadable')
            run.assert_not_called()

    def test_decimal_required_no_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            for result in ('1245', '12 45', '12.456', ''):
                with patch('amount_ocr_experiment.subprocess.run', return_value=SimpleNamespace(stdout=result)):
                    self.assertEqual(recognize_amount(Image.new('L', (20, 10)), Path(tmp)/'in.png', 7,
                                                     'Amount 12 45'), 'Amount 12 45')

    def test_candidate_changes_amount_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('amount_ocr_experiment.subprocess.run', return_value=SimpleNamespace(stdout='76,540.45\n')):
                result=recognize_amount(Image.new('L', (20, 10)), Path(tmp)/'in.png', 13,
                                        'Document ID: SYN-123456\nAmount 716540 45\nDate: 2026-09-12')
                self.assertEqual(result,'Document ID: SYN-123456\nAmount: 76540.45\nDate: 2026-09-12')

    def test_boxes_depend_on_ocr_labels_not_expected_coordinates(self):
        header='level\tpage_num\tblock_num\tpar_num\tline_num\tleft\ttop\twidth\theight\ttext\n'
        rows='5\t1\t1\t1\t1\t10\t20\t25\t10\tAmount:\n5\t1\t1\t1\t1\t40\t20\t30\t10\t12.45\n'
        with tempfile.TemporaryDirectory() as tmp:
            with patch('amount_ocr_experiment.subprocess.run', return_value=SimpleNamespace(stdout=header+rows)):
                crop=numeric_crop(Image.new('L',(100,100)),Path(tmp)/'in.png')
                self.assertEqual(crop.size,(36,18))
            with patch('amount_ocr_experiment.subprocess.run', return_value=SimpleNamespace(stdout=header+rows.replace('Amount:','Other:'))):
                self.assertIsNone(numeric_crop(Image.new('L',(100,100)),Path(tmp)/'in.png'))


if __name__=='__main__':unittest.main()

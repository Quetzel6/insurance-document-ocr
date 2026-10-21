import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import challenge_eval as challenge

class ChallengeProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.dataset=self.root/'dataset'
        if not (Path('/usr/share/fonts/truetype/dejavu')/'DejaVuSerif.ttf').is_file():self.skipTest('Challenge font not installed')
        challenge.generate(self.dataset)
    def test_new_originals_and_fixed_policy(self):
        m=challenge.validate(self.dataset);self.assertEqual(len(m['records']),36)
        self.assertEqual(m['protocol']['method'],'upscale_sharpen');self.assertEqual(m['protocol']['threshold'],0)
    def test_no_overwrite(self):
        with self.assertRaisesRegex(ValueError,'dataset_exists'):challenge.generate(self.dataset)
    def test_changed_image_rejected(self):
        m=challenge.validate(self.dataset);(self.dataset/m['records'][0]['image']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'image_path_or_hash_changed'):challenge.validate(self.dataset)
    def test_policy_change_rejected_before_recognition(self):
        p=self.dataset/'manifest.json';m=json.loads(p.read_text());m['protocol']['threshold']=99;p.write_text(json.dumps(m))
        with patch('challenge_eval.base.recognize') as recognize:
            with self.assertRaisesRegex(ValueError,'frozen_source_or_policy_changed'):challenge.run(self.dataset,self.root/'out')
        recognize.assert_not_called()
    def test_overlapping_output_rejected(self):
        with self.assertRaisesRegex(ValueError,'input_output_overlap'):challenge.run(self.dataset,self.dataset/'out')
    def test_inconsistent_original_labels_rejected(self):
        p=self.dataset/'manifest.json';m=json.loads(p.read_text());m['records'][1]['fields']['amount']='999.00';p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'inconsistent_original_labels'):challenge.validate(self.dataset)

if __name__=='__main__':unittest.main()

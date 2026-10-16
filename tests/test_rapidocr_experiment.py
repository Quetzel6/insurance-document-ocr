import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from importlib import metadata
from rapidocr_experiment import rapid_text,runtime_info,fingerprints,freeze,evaluate
class RapidExperimentTests(unittest.TestCase):
 def test_empty_engine_output(self):
  self.assertEqual(rapid_text(lambda path:(None,None),Path('image.png')),('',[]))
 def test_preserves_raw_text_and_native_scores_without_numeric_repair(self):
  fake=lambda path:([[[], 'Armourt 12 OO',.71],[[], 'Document ID SYN-12345O',.83]],None)
  text,scores=rapid_text(fake,Path('image.png'))
  self.assertEqual(text,'Armourt 12 OO\nDocument ID SYN-12345O');self.assertEqual(scores,[.71,.83])
 def test_missing_optional_package_has_actionable_message(self):
  with patch('importlib.metadata.version',side_effect=metadata.PackageNotFoundError):
   with self.assertRaisesRegex(ValueError,'separate'):runtime_info()
 def test_runtime_change_blocks_test_before_engine_load(self):
  with tempfile.TemporaryDirectory() as tmp,patch('rapidocr_experiment.runtime_info',return_value={'models':'before'}) as runtime:
   folder=Path(tmp);(folder/'manifest.json').write_text('{"records":[]}')
   (folder/'dev_report.json').write_text(json.dumps(dict(fingerprints=fingerprints(folder))))
   freeze(folder,'tesseract_current');runtime.return_value={'models':'after'}
   with self.assertRaisesRegex(ValueError,'protocol'):evaluate(folder,'test')

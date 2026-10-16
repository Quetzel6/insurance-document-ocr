"""Dev-only replay: allow joined DocumentID labels without changing values."""
import argparse,hashlib,json,re
from pathlib import Path
from extraction_candidate import extract_candidate
from rapidocr_experiment import summarize
ROOT=Path(__file__).resolve().parent

def extract_joined_label(text):
 # Only insert whitespace in a line-start label before a visible separator.
 normalized=re.sub(r'(?im)^(\s*Document)(ID|1D|I0)(?=\s*[:=])',r'\1 \2',text)
 return extract_candidate(normalized)

def run(source,out):
 if out.exists():raise ValueError('Output exists; preserve previous evidence')
 report=json.loads(source.read_text())
 if report.get('split')!='dev':raise ValueError('Replay is restricted to development evidence')
 manifest=json.loads((source.parent/'manifest.json').read_text())
 truth={r['id']:r['fields'] for r in manifest['records'] if r['split']=='dev'}
 rows=[]
 for original in report['records']:
  if original['id'] not in truth:raise ValueError('Unexpected non-development record')
  row=original.copy();prediction=extract_joined_label(row['text'])
  row.update(prediction=prediction,matches={k:prediction[k]==truth[row['id']][k] for k in prediction})
  rows.append(row)
 result=dict(split='dev',source_report_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
  manifest_sha256=hashlib.sha256((source.parent/'manifest.json').read_bytes()).hexdigest(),
  parser_sha256=hashlib.sha256((ROOT/'engine_label_experiment.py').read_bytes()).hexdigest(),
  extractor_sha256=hashlib.sha256((ROOT/'extraction_candidate.py').read_bytes()).hexdigest(),
  original_summary=report['summary'],summary=summarize(rows),records=rows,
  limits='Exploratory dev-only parser replay; no OCR rerun or test evaluation. Same rule applied to every engine. Only joined DocumentID/1D/I0 labels before a visible colon/equal are separated. Digits, decimals and OCR text remain unchanged. Not deployed.')
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.source,a.out)

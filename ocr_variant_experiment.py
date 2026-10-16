"""Compare OCR variants on dev only; deployed/frozen code is unchanged."""
import argparse, hashlib, json, platform, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageOps, __version__ as pillow_version
from enhanced import prepare
from extraction_candidate import extract_candidate
from project import distance, normalize_text
ROOT=Path(__file__).resolve().parent
METHODS=('current','prepared_sparse','grayscale_block','prepared_otsu')
FIELDS=('document_id','date','amount')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def otsu(im):
 h=im.histogram();n=sum(h);moment=sum(i*c for i,c in enumerate(h));left=lm=0;best=-1;threshold=127
 for i,c in enumerate(h):
  left+=c;lm+=i*c;right=n-left
  if not left or not right:continue
  score=left*right*(lm/left-(moment-lm)/right)**2
  if score>best:best,threshold=score,i
 return im.point(lambda x:255 if x>threshold else 0)
def summarize(rows):
 summary=[]
 for method in METHODS:
  for condition in ('all',*sorted({r['condition'] for r in rows})):
   g=[r for r in rows if r['method']==method and (condition=='all' or r['condition']==condition)]
   summary.append(dict(method=method,condition=condition,images=len(g),originals=len({r['original_id'] for r in g}),
    cer=sum(r['edits'] for r in g)/sum(r['chars'] for r in g),complete=sum(all(r['matches'].values()) for r in g),
    correct={k:sum(r['matches'][k] for r in g) for k in FIELDS},
    wrong_emitted={k:sum(r['prediction'][k] is not None and not r['matches'][k] for r in g) for k in FIELDS},
    missing={k:sum(r['prediction'][k] is None for r in g) for k in FIELDS}))
 return summary
def run(out):
 if out.exists():raise ValueError('Output exists; select a new directory')
 frozen=('project.py','challenge.py','enhanced.py','challenge_data/manifest.json','enhanced_output/frozen.json','enhanced_output/test_report.json')
 before={n:sha(ROOT/n) for n in frozen}
 records=[r for r in json.loads((ROOT/'challenge_data/manifest.json').read_text())['records'] if r['split']=='dev']
 if not records:raise ValueError('No development images')
 rows=[]
 with tempfile.TemporaryDirectory() as tmp:
  path=Path(tmp)/'input.png'
  for number,r in enumerate(records,1):
   source=(ROOT/'challenge_data'/r['image']).resolve()
   if not source.is_relative_to((ROOT/'challenge_data').resolve()) or sha(source)!=r['sha']:raise ValueError('Image path/hash mismatch')
   prepared,_=prepare(source)
   with Image.open(source) as im:gray=ImageOps.exif_transpose(im).convert('L')
   variants={'current':(prepared,'6'),'prepared_sparse':(prepared,'11'),'grayscale_block':(gray,'6'),'prepared_otsu':(otsu(prepared),'6')}
   for method,(im,psm) in variants.items():
    im.save(path)
    text=subprocess.run(['tesseract',str(path),'stdout','-l','eng','--psm',psm],capture_output=True,text=True,check=True,timeout=30).stdout
    pred=extract_candidate(text);reference=normalize_text(r['text'])
    rows.append(dict(id=r['id'],original_id=r['original_id'],condition=r['condition'],method=method,text=text,prediction=pred,
     matches={k:pred[k]==r['fields'][k] for k in FIELDS},edits=distance(reference,normalize_text(text)),chars=len(reference)))
   print(f'Dev {number}/{len(records)}',flush=True)
 if {n:sha(ROOT/n) for n in frozen}!=before:raise ValueError('Frozen evidence changed')
 language_line=subprocess.run(['tesseract','--list-langs'],capture_output=True,text=True,check=True).stdout.splitlines()[0]
 language_dir=Path(language_line.split('"')[1])
 report=dict(split='dev',python=platform.python_version(),pillow=pillow_version,
  tesseract=subprocess.run(['tesseract','--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0],
  eng_traineddata_sha256=sha(language_dir/'eng.traineddata'),
  fingerprints={n:sha(ROOT/n) for n in ('ocr_variant_experiment.py','extraction_candidate.py',*frozen)},
  summary=summarize(rows),records=rows,
  limitations='Exploratory English synthetic dev only: 40 variants / 10 correlated originals in two layouts. Existing data have been inspected in prior development. Test split is not run. No new generalization claim, deployment change, digit guessing or model training. Timing is not compared.')
 out.mkdir(parents=True);(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 lines=['# Development OCR variants','',report['limitations'],'','| Method | Condition | Images | CER | All fields correct | Wrong ID / date / amount |','| --- | --- | ---: | ---: | ---: | --- |']
 for r in report['summary']:
  lines.append(f"| {r['method']} | {r['condition']} | {r['images']} | {r['cer']:.2%} | {r['complete']}/{r['images']} | "+' / '.join(str(r['wrong_emitted'][k]) for k in FIELDS)+' |')
 lines+=['','All methods use extraction_candidate unchanged. Missing/wrong predictions are separate in report.json.',f"Environment: {report['tesseract']}; Pillow {pillow_version}; Python {report['python']}. Not the user Mac/Docker environment."]
 (out/'results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)

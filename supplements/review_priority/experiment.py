"""Local OCR review-priority experiment; no API and no new model training."""
import argparse,csv,hashlib,html,io,json,math,platform,random,re,subprocess,tempfile,time
from datetime import date,timedelta,datetime,timezone
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter,__version__ as pillow_version
FIELDS=('document_id','date','amount');METHODS=('raw','upscale_sharpen');THRESHOLDS=(0,60,80,90,95,101)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def save(p,data):
 with Path(p).open('x') as f:json.dump(data,f,indent=2)
def generate(folder,font):
 folder=Path(folder)
 if folder.exists():raise ValueError('Dataset exists')
 folder.mkdir(parents=True);rng=random.Random(2026102003);records=[]
 for split in ('dev','test'):
  for n in range(6):
   f=ImageFont.truetype(str(font),(23,27,31)[n%3]);fields=dict(document_id=f'SYN-{rng.randrange(100000,999999)}',date=(date(2025,1,1)+timedelta(days=rng.randrange(600))).isoformat(),amount=f'{rng.randrange(100,90000)}.{rng.randrange(100):02d}')
   order=FIELDS if split=='dev' else ('amount','document_id','date');labels=dict(document_id='Document ID',date='Date',amount='Amount')
   lines=['SYNTHETIC OPERATIONS DOCUMENT','NOT A REAL CUSTOMER RECORD']+[labels[k]+': '+fields[k] for k in order]+['Currency: THB']
   im=Image.new('L',(1000,570),255);draw=ImageDraw.Draw(im)
   for j,line in enumerate(lines):draw.text((45 if split=='dev' else 105,35+j*(65 if split=='dev' else 72)),line,font=f,fill=0)
   oid=f'{split}-{n:02d}'
   for condition in ('clean','blur','skew'):
    if condition=='blur':v=im.resize((350,200),Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(.8)).resize(im.size,Image.Resampling.BICUBIC)
    elif condition=='skew':v=im.rotate(5 if n%2 else -5,resample=Image.Resampling.BICUBIC,expand=True,fillcolor=255)
    else:v=im.copy()
    name=f'{oid}-{condition}.png';v.save(folder/name)
    records.append(dict(id=Path(name).stem,original_id=oid,split=split,layout=split,condition=condition,image=name,sha256=sha(folder/name),fields=fields))
 save(folder/'manifest.json',dict(seed=2026102003,font_sha256=sha(font),pillow=pillow_version,records=records,limits='12 synthetic English originals: six per split, three correlated variants each; shared font family/labels. No Thai, real captures, handwriting or factory documents.'))
def validate(folder):
 folder=Path(folder).resolve();m=json.loads((folder/'manifest.json').read_text());owners={};layouts={};ids=set()
 for r in m['records']:
  if r['id'] in ids:raise ValueError('duplicate image ID')
  ids.add(r['id']);owners.setdefault(r['original_id'],set()).add(r['split']);layouts.setdefault(r['layout'],set()).add(r['split']);p=(folder/r['image']).resolve()
  if not p.is_relative_to(folder) or sha(p)!=r['sha256']:raise ValueError('image path/hash mismatch')
 if any(len(s)!=1 for s in [*owners.values(),*layouts.values()]):raise ValueError('split leakage')
 if {r['split'] for r in m['records']}!={'dev','test'}:raise ValueError('both splits required')
 return m
def extract(text):
 patterns=dict(document_id=r'\bDocument\s+ID\s*:\s*(SYN-\d{6})\b',date=r'\bDate\s*:\s*(\d{4}-\d{2}-\d{2})\b',amount=r'\bAmount\s*:\s*([0-9]+\.[0-9]{2})\b');pred={}
 for k,pattern in patterns.items():
  match=re.search(pattern,text,re.I);pred[k]=match.group(1) if match else None
 if pred['document_id']:pred['document_id']=pred['document_id'].upper()
 if pred['date']:
  try:date.fromisoformat(pred['date'])
  except ValueError:pred['date']=None
 return pred
def parse_tsv(text):
 lines={};confs=[]
 for r in csv.DictReader(io.StringIO(text),delimiter='\t'):
  word=(r.get('text') or '').strip()
  if r.get('level')!='5' or not word:continue
  key=tuple(r[k] for k in ('page_num','block_num','par_num','line_num'));lines.setdefault(key,[]).append(word)
  try:conf=float(r['conf'])
  except (ValueError,TypeError):continue
  if math.isfinite(conf) and 0<=conf<=100:confs.append(conf)
 return '\n'.join(' '.join(v) for v in lines.values()),sum(confs)/len(confs) if confs else None
def recognize(image,method):
 start=time.perf_counter()
 with tempfile.TemporaryDirectory() as td:
  path=Path(td)/'input.png'
  with Image.open(image) as src:im=src.convert('L')
  if method=='upscale_sharpen':im=im.resize((im.width*2,im.height*2),Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1,percent=150,threshold=3))
  elif method!='raw':raise ValueError('unknown method')
  im.save(path);r=subprocess.run(['tesseract',str(path),'stdout','-l','eng','--oem','1','--psm','6','tsv'],capture_output=True,text=True,check=True,timeout=30)
 text,conf=parse_tsv(r.stdout)
 return dict(text=text,prediction=extract(text),mean_word_confidence=conf,elapsed_seconds=time.perf_counter()-start)
def prioritize(r,t):return all(r['prediction'].get(k) is not None for k in FIELDS) and r['mean_word_confidence'] is not None and r['mean_word_confidence']>=t
def summary(rows,method,threshold):
 group=[r for r in rows if r['method']==method];subset=[r for r in group if prioritize(r,threshold)];wrong=sum(not r['complete_correct'] for r in subset)
 return dict(method=method,threshold=threshold,images=len(group),originals=len({r['original_id'] for r in group}),complete_correct=sum(r['complete_correct'] for r in group),wrong_emitted_fields=sum(r['prediction'][k] is not None and not r['matches'][k] for r in group for k in FIELDS),prioritized=len(subset),incorrect_prioritized=wrong,priority_coverage=len(subset)/len(group) if group else None,priority_error_rate=wrong/len(subset) if subset else None,human_review_required=len(group))
def select_dev(rows):
 curve=[summary(rows,m,t) for m in METHODS for t in THRESHOLDS];valid=[r for r in curve if r['incorrect_prioritized']==0]
 return max(valid,key=lambda r:(r['prioritized'],r['complete_correct'],-METHODS.index(r['method']),-r['threshold'])),curve
def environment():
 version=subprocess.run(['tesseract','--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0];langs=subprocess.run(['tesseract','--list-langs'],capture_output=True,text=True,check=True).stdout;match=re.search(r'"([^"]+)"',langs)
 model=Path(match.group(1))/'eng.traineddata' if match else None
 if model is None or not model.is_file():raise ValueError('cannot fingerprint English model')
 return dict(tesseract=version,english_model_sha256=sha(model),python=platform.python_version(),platform=platform.system(),pillow=pillow_version)
def evaluate(dataset,m,split):
 rows=[]
 for r in [r for r in m['records'] if r['split']==split]:
  for method in METHODS:
   observed=recognize(Path(dataset)/r['image'],method);matches={k:observed['prediction'][k]==r['fields'][k] for k in FIELDS}
   rows.append(dict(id=r['id'],original_id=r['original_id'],condition=r['condition'],method=method,**observed,matches=matches,complete_correct=all(matches.values())))
  print(split+': '+r['id'],flush=True)
 return rows
def run(dataset,out):
 dataset=Path(dataset).resolve();out=Path(out).resolve()
 if out.exists():raise ValueError('Output exists; choose a new directory')
 if dataset==out or dataset in out.parents or out in dataset.parents:raise ValueError('input/output overlap')
 m=validate(dataset);out.mkdir(parents=True);fp=dict(source_sha256=sha(__file__),manifest_sha256=sha(dataset/'manifest.json'),environment=environment())
 save(out/'protocol.json',dict(created_utc=now(),fingerprint=fp,thresholds=THRESHOLDS,methods=METHODS,policy='zero observed incorrect prioritized on dev, then max coverage, then complete recovery; all images still human-reviewed'))
 dev=evaluate(dataset,m,'dev');save(out/'dev_predictions.json',dev);selected,curve=select_dev(dev)
 frozen=dict(frozen_utc=now(),fingerprint=fp,selected_method=selected['method'],threshold=selected['threshold'],dev_predictions_sha256=sha(out/'dev_predictions.json'));save(out/'frozen_policy.json',frozen)
 if sha(__file__)!=fp['source_sha256'] or sha(dataset/'manifest.json')!=fp['manifest_sha256'] or environment()!=fp['environment']:raise ValueError('frozen protocol changed')
 validate(dataset);test=evaluate(dataset,m,'test');save(out/'test_predictions.json',test)
 if sha(__file__)!=fp['source_sha256'] or sha(dataset/'manifest.json')!=fp['manifest_sha256'] or sha(out/'dev_predictions.json')!=frozen['dev_predictions_sha256']:raise ValueError('evaluation evidence changed')
 validate(dataset);result=dict(status='evaluated_local',fingerprint=fp,api_calls=0,trained_new_model=False,dev_selected=selected,test_selected=summary(test,selected['method'],selected['threshold']),test_methods=[summary(test,m,0) for m in METHODS],dev_risk_coverage=curve,limits=m['limits'],confidence_warning='Mean word confidence is a heuristic, not a calibrated probability; small correlated cohort gives no error guarantee.',deployment_decision='Research only; all images remain human-reviewed; application default unchanged.');save(out/'results.json',result)
 text='# OCR review-priority evaluation\n\nSelected on dev: '+selected['method']+', threshold '+str(selected['threshold'])+'. Policy frozen before test recognition.\n\n| Test method | Complete exact | Wrong emitted fields |\n| --- | ---: | ---: |\n'
 for r in result['test_methods']:text+=f"| {r['method']} | {r['complete_correct']}/{r['images']} | {r['wrong_emitted_fields']} |\n"
 r=result['test_selected'];text+=f"\nSelected policy prioritized {r['prioritized']}/{r['images']} test images; {r['incorrect_prioritized']} were incorrect complete extractions in that subset. All {r['images']} still require human review.\n\n"+m['limits']+'\n\n'+result['confidence_warning']+'\n\nReproduction of this now-inspected cohort is not a new untouched test. No real-world benefit, new model training or API use is claimed.\n'
 (out/'RESULTS.md').write_text(text);(out/'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>OCR evaluation</title><style>body{max-width:950px;margin:30px auto;padding:20px;font:16px/1.6 system-ui;color:#173b4a}pre{white-space:pre-wrap}</style><h1>OCR review-priority evaluation</h1><pre>'+html.escape(text)+'</pre></html>');return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['generate','run']);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--out',type=Path);p.add_argument('--font',type=Path,default=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));a=p.parse_args()
 if a.stage=='generate':generate(a.dataset,a.font)
 else:
  if not a.out:p.error('--out required')
  print(json.dumps(run(a.dataset,a.out)['test_selected'],indent=2))

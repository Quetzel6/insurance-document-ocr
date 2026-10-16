"""New multi-font synthetic cohort and image-only line OCR experiment."""
import argparse, hashlib, json, platform, random, subprocess, tempfile
from datetime import date, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, __version__ as pillow_version
from enhanced import prepare
from extraction_candidate import extract_candidate
from project import normalize_text, distance
ROOT=Path(__file__).resolve().parent
METHODS=('page_current','line_upscale')
FIELDS=('document_id','date','amount')
SOURCES=('line_ocr_experiment.py','enhanced.py','project.py','extraction_candidate.py')
FONT_NAMES=('DejaVuSans.ttf','DejaVuSerif.ttf','DejaVuSansMono.ttf')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprints(folder):return {n:sha(ROOT/n) for n in SOURCES}|{'manifest':sha(folder/'manifest.json')}
def generate(folder,font_dir):
 if folder.exists():raise ValueError('Dataset exists; choose a new directory')
 fonts=[font_dir/n for n in FONT_NAMES]
 if any(not p.is_file() for p in fonts):raise ValueError('Install fonts-dejavu-core or specify --font-dir')
 rng=random.Random(20261016);records=[];folder.mkdir(parents=True)
 for split in ('dev','test'):
  for f,font_path in enumerate(fonts):
   for n in range(2):
    size=(24,30)[n] if split=='dev' else (26,32)[n]
    font=ImageFont.truetype(str(font_path),size)
    fields=dict(document_id=f'SYN-{rng.randrange(100000,999999)}',date=(date(2024,1,1)+timedelta(days=rng.randrange(1000))).isoformat(),amount=f'{rng.randrange(1000,95000)}.{rng.randrange(100):02d}')
    order=('document_id','date','amount') if split=='dev' else ('amount','document_id','date')
    labels=dict(document_id='Document ID',date='Date',amount='Amount')
    lines=['SYNTHETIC SERVICE RECORD','NOT A REAL CLAIM',*[labels[k]+': '+fields[k] for k in order],'Service: Synthetic repair estimate','Currency: THB']
    im=Image.new('L',(1200,800),255);draw=ImageDraw.Draw(im)
    x=45+f*25 if split=='dev' else 85+f*20
    gap=74 if split=='dev' else 82
    for i,line in enumerate(lines):draw.text((x,45+i*gap),line,font=font,fill=0)
    oid=f'line-{split}-F{f}-{n}'
    for condition in ('clean','blur_mild','blur_strong','shadow'):
     if condition=='clean':image=im.copy()
     elif condition.startswith('blur'):
      scale,radius=(.5,.6) if condition=='blur_mild' else (.25,1.0)
      image=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(radius)).resize(im.size,Image.Resampling.BICUBIC)
     else:
      image=im.copy();w,h=image.size
      image.putdata([round(v*(.40+.60*(i%w)/(w-1))) for i,v in enumerate(image.getdata())])
     name=oid+'-'+condition+'.png';image.save(folder/name)
     records.append(dict(id=name[:-4],original_id=oid,split=split,layout='dev-order' if split=='dev' else 'test-order',font=font_path.name,font_size=size,condition=condition,image=name,sha=sha(folder/name),text='\n'.join(lines),fields=fields))
 manifest=dict(seed=20261016,fonts={p.name:sha(p) for p in fonts},pillow=pillow_version,records=records,
  limits='Synthetic English, 6 originals and 24 correlated variants per split, shared 3 font families. Distinct originals/field orders/positions/sizes per split; not held-out font families, real scans or Thai. Strong blur may destroy source detail. Generation and test labels exist for reproducibility; separation is procedural.')
 (folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
 print('Generated 24 dev and 24 test variants; test not evaluated.',flush=True)
def line_boxes(im):
 # Generic horizontal ink projection: no labels, filenames or expected fields.
 width,height=im.size;pixels=im.tobytes();active=[]
 for y in range(height):
  if sum(v<180 for v in pixels[y*width:(y+1)*width])>=3:active.append(y)
 if not active:return []
 bands=[];start=previous=active[0]
 for y in active[1:]:
  if y-previous>5:bands.append((start,previous+1));start=y
  previous=y
 bands.append((start,previous+1));boxes=[]
 for top,bottom in bands:
  if bottom-top<3:continue
  strip=im.crop((0,top,width,bottom));ink=strip.point(lambda v:255 if v<180 else 0).getbbox()
  if ink:boxes.append((max(0,ink[0]-10),max(0,top-8),min(width,ink[2]+10),min(height,bottom+8)))
 if len(boxes)>50:raise ValueError('Too many line segments; candidate unsuitable')
 return boxes
def ocr(im,path,psm):
 im.save(path)
 return subprocess.run(['tesseract',str(path),'stdout','-l','eng','--psm',str(psm)],capture_output=True,text=True,check=True,timeout=30).stdout

def recognize_lines(im,path):
 lines=[]
 for box in line_boxes(im):
  crop=im.crop(box);crop=crop.resize((crop.width*2,crop.height*2),Image.Resampling.LANCZOS)
  lines.append(ocr(ImageOps.expand(crop,border=12,fill=255),path,7).strip())
 return '\n'.join(lines)
def summarize(rows):
 summary=[]
 for method in METHODS:
  for condition in ('all',*sorted({r['condition'] for r in rows})):
   group=[r for r in rows if r['method']==method and (condition=='all' or r['condition']==condition)]
   summary.append(dict(method=method,condition=condition,images=len(group),originals=len({r['original_id'] for r in group}),cer=sum(r['edits'] for r in group)/sum(r['chars'] for r in group),complete=sum(all(r['matches'].values()) for r in group),correct={k:sum(r['matches'][k] for r in group) for k in FIELDS},wrong_emitted={k:sum(r['prediction'][k] is not None and not r['matches'][k] for r in group) for k in FIELDS},missing={k:sum(r['prediction'][k] is None for r in group) for k in FIELDS}))
 return summary
def freeze(folder,selected):
 target=folder/'frozen_protocol.json'
 if target.exists():raise ValueError('Protocol already frozen')
 report=json.loads((folder/'dev_report.json').read_text())
 if report['fingerprints']!=fingerprints(folder):raise ValueError('Dev evidence changed')
 target.write_text(json.dumps(dict(selected=selected,fingerprints=fingerprints(folder),dev_report_sha=sha(folder/'dev_report.json'),policy='Selected before test. Evaluate both fixed methods once; no tuning after test inspection.'),indent=2))
def evaluate(folder,split):
 out=folder/f'{split}_report.json'
 if out.exists():raise ValueError('Report exists; do not overwrite evaluation evidence')
 fp=fingerprints(folder);protocol=None
 if split=='test':
  protocol=json.loads((folder/'frozen_protocol.json').read_text())
  if protocol['fingerprints']!=fp or protocol['dev_report_sha']!=sha(folder/'dev_report.json'):raise ValueError('Frozen protocol mismatch')
 manifest=json.loads((folder/'manifest.json').read_text());owners={};layouts={}
 for r in manifest['records']:
  owners.setdefault(r['original_id'],set()).add(r['split']);layouts.setdefault(r['layout'],set()).add(r['split'])
 if any(len(s)>1 for s in [*owners.values(),*layouts.values()]):raise ValueError('Split leakage')
 records=[r for r in manifest['records'] if r['split']==split];rows=[]
 with tempfile.TemporaryDirectory() as tmp:
  path=Path(tmp)/'input.png'
  for i,r in enumerate(records,1):
   source=(folder/r['image']).resolve()
   if not source.is_relative_to(folder.resolve()) or sha(source)!=r['sha']:raise ValueError('Image path/hash mismatch')
   im,_=prepare(source)
   # Recognizers see only image pixels; labels are used afterwards for scoring.
   outputs={'page_current':ocr(im,path,6),'line_upscale':recognize_lines(im,path)}
   for method,text in outputs.items():
    prediction=extract_candidate(text);reference=normalize_text(r['text'])
    rows.append(dict(id=r['id'],original_id=r['original_id'],font=r['font'],condition=r['condition'],method=method,text=text,prediction=prediction,matches={k:prediction[k]==r['fields'][k] for k in FIELDS},edits=distance(reference,normalize_text(text)),chars=len(reference)))
   print(f'{split} {i}/{len(records)}',flush=True)
 language_line=subprocess.run(['tesseract','--list-langs'],capture_output=True,text=True,check=True).stdout.splitlines()[0]
 result=dict(split=split,protocol=protocol,fingerprints=fp,python=platform.python_version(),pillow=pillow_version,tesseract=subprocess.run(['tesseract','--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0],eng_traineddata_sha=sha(Path(language_line.split('"')[1])/'eng.traineddata'),limits=manifest['limits'],summary=summarize(rows),records=rows)
 if fingerprints(folder)!=fp:raise ValueError('Source/manifest changed during evaluation')
 out.write_text(json.dumps(result,indent=2))
 lines=[f'# New multi-font cohort: {split}','','| Method | Condition | Images | CER | Complete | Wrong ID/date/amount |','| --- | --- | ---: | ---: | ---: | --- |']
 for r in result['summary']:lines.append(f"| {r['method']} | {r['condition']} | {r['images']} | {r['cer']:.2%} | {r['complete']}/{r['images']} | "+'/'.join(str(r['wrong_emitted'][k]) for k in FIELDS)+' |')
 lines+=['',result['limits'],'','Measured in assistant Linux environment, not Mac/Docker. Same extractor across methods. No confidence calibration, training or automatic value guessing.']
 (folder/f'{split}_results.md').write_text('\n'.join(lines)+'\n')
 return result
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['generate','dev','freeze','test']);parser.add_argument('--dir',type=Path,required=True);parser.add_argument('--font-dir',type=Path,default=Path('/usr/share/fonts/truetype/dejavu'));parser.add_argument('--selected',choices=METHODS,default='page_current');args=parser.parse_args()
 if args.stage=='generate':generate(args.dir,args.font_dir)
 elif args.stage=='freeze':freeze(args.dir,args.selected)
 else:evaluate(args.dir,args.stage)

import argparse,json,random,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps,ImageChops
from project import recognize,extract,distance,normalize_text,digest,FIELDS
from enhanced import recognize as upgraded_recognize, extract_validated
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'challenge_data'; OUT=ROOT/'enhanced_output'
def generate(font):
 DATA.mkdir(exist_ok=True);rng=random.Random(42);records=[]
 for t in range(6):
  split=('train','train','dev','dev','test','test')[t]
  for n in range(5):
   fields={'document_id':f'SYN-{t}{n}7642','date':f'2026-09-{n+10:02d}','amount':f'{rng.randrange(10000,90000)}.45'}
   lines=['SYNTHETIC INVOICE - NOT A REAL CLAIM','Document ID: '+fields['document_id'],'Date: '+fields['date'],'Amount: '+fields['amount'],'Currency: THB','Service: Synthetic repair estimate']
   lines=[lines[0]]+rng.sample(lines[1:],5);im=Image.new('RGB',(1300,850),'white');d=ImageDraw.Draw(im);f=ImageFont.truetype(str(font),26+(t%3)*2)
   for j,line in enumerate(lines):d.text((40+t*15,55+j*(80+t*3)),line,font=f,fill='black')
   for cond in ('clean','blur_lowres','skew','shadow'):
    v=im.copy()
    if cond=='blur_lowres':v=v.resize((390,255)).filter(ImageFilter.GaussianBlur(.9)).resize(im.size)
    if cond=='skew':v=v.rotate(8,resample=Image.Resampling.BICUBIC,fillcolor='white')
    if cond=='shadow':
     g=Image.new('L',im.size);g.putdata([int(55+180*x/(im.width-1)) for y in range(im.height) for x in range(im.width)]);v=ImageChops.multiply(v,g.convert('RGB'))
    path=DATA/f't{t}-{n}-{cond}.bmp';v.save(path);records.append(dict(id=path.stem,original_id=f't{t}-{n}',template=t,split=split,condition=cond,image=path.name,sha=digest(path),text='\n'.join(lines),fields=fields))
 (DATA/'manifest.json').write_text(json.dumps(dict(seed=42,font_sha=digest(font),records=records),indent=2));print('30 originals, 120 variants generated')
def fingerprint():return {p:digest(ROOT/p) for p in ('project.py','challenge.py','enhanced.py','challenge_data/manifest.json')}
def evaluate(split):
 OUT.mkdir(exist_ok=True)
 if split=='test' and (not (OUT/'frozen.json').exists() or json.loads((OUT/'frozen.json').read_text())!=fingerprint()):raise SystemExit('Freeze unchanged protocol before test')
 records=json.loads((DATA/'manifest.json').read_text())['records'];groups={}
 for r in records:
  for key in ('original_id','template'):groups.setdefault((key,r[key]),set()).add(r['split'])
 if any(len(v)!=1 for v in groups.values()):raise ValueError('Split leakage')
 rows=[]
 for r in records:
  if r['split']!=split:continue
  image=DATA/r['image']
  if digest(image)!=r['sha']:raise ValueError('Image checksum mismatch')
  for method in ('raw','grayscale_threshold','raw_validated','enhanced'):
   text,seconds=upgraded_recognize(image,method);pred=extract_validated(text) if method in ('raw_validated','enhanced') else extract(text);ref=normalize_text(r['text']);rows.append(dict(id=r['id'],original_id=r['original_id'],condition=r['condition'],method=method,text=text,prediction=pred,matches={k:pred[k]==r['fields'][k] for k in FIELDS},edits=distance(ref,normalize_text(text)),chars=len(ref),ocr_seconds=seconds))
 summary=[]
 for method in ('raw','grayscale_threshold','raw_validated','enhanced'):
  for cond in ('all','clean','blur_lowres','skew','shadow'):
   rr=[r for r in rows if r['method']==method and (cond=='all' or r['condition']==cond)];summary.append(dict(method=method,condition=cond,images=len(rr),originals=len({r['original_id'] for r in rr}),normalized_cer=sum(r['edits'] for r in rr)/sum(r['chars'] for r in rr),field_match={k:sum(r['matches'][k] for r in rr)/len(rr) for k in FIELDS},document_match=sum(all(r['matches'].values()) for r in rr)/len(rr)))
 report=dict(split=split,fingerprint=fingerprint(),tesseract=subprocess.run(['tesseract','--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0],summary=summary,records=rows);(OUT/f'{split}_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['generate','dev','freeze','test']);p.add_argument('--font',type=Path);a=p.parse_args()
 if a.command=='generate':
  if not a.font or not a.font.is_file():p.error('Provide valid TTF --font')
  generate(a.font)
 elif a.command=='freeze':
  if not (OUT/'dev_report.json').exists():raise SystemExit('Run/review dev first')
  (OUT/'frozen.json').write_text(json.dumps(fingerprint(),indent=2));print('Frozen; never tune on test results')
 else:evaluate(a.command)

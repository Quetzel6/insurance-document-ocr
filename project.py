"""Synthetic OCR baseline. No insurance-company data or training is used."""
import argparse, hashlib, json, re, subprocess, time, random, tempfile
from pathlib import Path
from decimal import Decimal, InvalidOperation
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
ROOT=Path(__file__).resolve().parent
FIELDS=('document_id','date','amount')

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize_text(t):return ' '.join(t.lower().split())
def distance(a,b):
    previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        current=[i]
        for j,y in enumerate(b,1):current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
        previous=current
    return previous[-1]
def extract(t):
    patterns={'document_id':r'Document\s*ID\s*[:=]\s*(SYN-\d+)', 'date':r'Date\s*[:=]\s*(\d{4}-\d{2}-\d{2})','amount':r'Amount\s*[:=]\s*([\d,]+\.\d{2})'}
    result={}
    for key,pattern in patterns.items():
        m=re.search(pattern,t,re.I);result[key]=m.group(1) if m else None
    if result['document_id']:result['document_id']=result['document_id'].upper()
    if result['amount']:
        try:result['amount']=format(Decimal(result['amount'].replace(',','')),'.2f')
        except InvalidOperation:result['amount']=None
    return result

def generate(font_path):
    rng=random.Random(42);out=ROOT/'data';out.mkdir(exist_ok=True);records=[]
    font=ImageFont.truetype(str(font_path),30)
    for template,split in enumerate(('train','dev','test')):
        for n in range(3):
            oid=f't{template}-{n}';labels={'document_id':f'SYN-{template}{n}1234','date':f'2026-09-{n+11:02d}','amount':f'{rng.randrange(10000,90000)}.{rng.randrange(100):02d}'}
            lines=['SYNTHETIC DOCUMENT - NOT A REAL CLAIM','Document ID: '+labels['document_id'],'Date: '+labels['date'],'Amount: '+labels['amount'],'Currency: THB']
            # Layout and field order held out together; font remains fixed.
            if template==1:lines=[lines[0],lines[2],lines[1],lines[4],lines[3]]
            if template==2:lines=[lines[0],lines[3],lines[4],lines[1],lines[2]]
            im=Image.new('RGB',(1200,650),'white');draw=ImageDraw.Draw(im)
            for j,line in enumerate(lines):draw.text((35+template*25,45+j*(75+template*8)),line,font=font,fill='black')
            for condition in ('clean','blur','rotate'):
                variant=im.copy()
                if condition=='blur':variant=variant.filter(ImageFilter.GaussianBlur(1.4))
                if condition=='rotate':variant=variant.rotate(3,resample=Image.Resampling.BICUBIC,expand=False,fillcolor='white')
                path=out/f'{oid}-{condition}.png';variant.save(path)
                records.append({'id':path.stem,'original_id':oid,'template':template,'split':split,'condition':condition,'image':path.name,'image_sha256':digest(path),'text':'\n'.join(lines),'fields':labels})
    payload={'seed':42,'font_sha256':digest(font_path),'records':records}
    (out/'manifest.json').write_text(json.dumps(payload,indent=2));print('Generated 9 originals / 27 images; template-disjoint splits.')

def recognize(image_path,method):
    # This function receives an image only, never ground-truth labels/rotation.
    with tempfile.TemporaryDirectory() as tmp:
        path=image_path
        if method=='grayscale_threshold':
            im=ImageOps.autocontrast(Image.open(image_path).convert('L'));im=im.point(lambda x:255 if x>170 else 0);path=Path(tmp)/'prepared.png';im.save(path)
        start=time.perf_counter()
        r=subprocess.run(['tesseract',str(path),'stdout','-l','eng','--psm','6'],capture_output=True,text=True,timeout=30,check=True)
        return r.stdout,time.perf_counter()-start

def benchmark():
    manifest=ROOT/'data/manifest.json';payload=json.loads(manifest.read_text());records=payload['records'];owners={}
    for r in records:
        owners.setdefault(r['original_id'],set()).add(r['split'])
        if digest(ROOT/'data'/r['image'])!=r['image_sha256']:raise ValueError('Image checksum mismatch')
    if any(len(x)!=1 for x in owners.values()):raise ValueError('Original document leaked across splits')
    groups={}
    for r in records:groups.setdefault(r['template'],set()).add(r['split'])
    if any(len(x)!=1 for x in groups.values()):raise ValueError('Template leaked across splits')
    results=[]
    for r in records:
        if r['split']=='train':continue
        for method in ('raw','grayscale_threshold'):
            text,seconds=recognize(ROOT/'data'/r['image'],method);pred=extract(text);truth=normalize_text(r['text']);actual=normalize_text(text)
            matches={k:pred[k]==r['fields'][k] for k in FIELDS}
            results.append({'id':r['id'],'split':r['split'],'condition':r['condition'],'method':method,'prediction':pred,'ocr_text':text,'edits':distance(truth,actual),'reference_characters':len(truth),'field_matches':matches,'all_fields_match':all(matches.values()),'seconds':seconds})
    summary=[]
    for split in ('dev','test'):
        for method in ('raw','grayscale_threshold'):
            for condition in ('all','clean','blur','rotate'):
                rows=[r for r in results if r['split']==split and r['method']==method and (condition=='all' or r['condition']==condition)]
                summary.append({'split':split,'method':method,'condition':condition,'documents':len(rows),'micro_normalized_cer':sum(r['edits'] for r in rows)/sum(r['reference_characters'] for r in rows),'field_accuracy':{k:sum(r['field_matches'][k] for r in rows)/len(rows) for k in FIELDS},'document_exact_match':sum(r['all_fields_match'] for r in rows)/len(rows),'mean_seconds':sum(r['seconds'] for r in rows)/len(rows)})
    report={'manifest_sha256':digest(manifest),'tesseract':subprocess.run(['tesseract','--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0],'protocol':'Fixed methods; no test-set tuning. CER lowercases and collapses whitespace. Amount normalized using Decimal; ID uppercase. Date exact ISO string.','summary':summary,'results':results}
    out=ROOT/'output';out.mkdir(exist_ok=True);(out/'benchmark.json').write_text(json.dumps(report,indent=2));print(json.dumps([r for r in summary if r['condition']=='all'],indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['generate','benchmark']);p.add_argument('--font',type=Path);a=p.parse_args()
    if a.command=='generate':
        if not a.font or not a.font.is_file():p.error('Provide --font path to a TTF font')
        generate(a.font)
    else:benchmark()

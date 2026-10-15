"""Image-only illumination/deskew and conservative field validation."""
import re,tempfile,subprocess
from pathlib import Path
from datetime import date
from decimal import Decimal
from PIL import Image,ImageFilter
from project import recognize as baseline

def prepare(path):
 im=Image.open(path).convert('L')
 # Estimate local background; divide observed intensity by estimated illumination.
 bg=im.filter(ImageFilter.GaussianBlur(35))
 corrected=Image.new('L',im.size);corrected.putdata([min(255,round(a*255/max(b,1))) for a,b in zip(im.getdata(),bg.getdata())])
 small=corrected.copy();small.thumbnail((325,220))
 def score(angle):
  r=small.rotate(angle,fillcolor=255);w,h=r.size;p=list(r.getdata());s=[sum(255-v for v in p[y*w:(y+1)*w]) for y in range(h)]
  return sum((a-b)**2 for a,b in zip(s,s[1:]))
 angles=range(-12,13);angle=max(angles,key=score)
 if score(angle)<score(0)*1.10:angle=0
 return corrected.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True,fillcolor=255),angle

def recognize(path,method):
 if method!='enhanced':return baseline(path,'raw' if method=='raw_validated' else method)
 import time
 start=time.perf_counter()
 with tempfile.TemporaryDirectory() as tmp:
  im,angle=prepare(path);p=Path(tmp)/'input.png';im.save(p)
  r=subprocess.run(['tesseract',str(p),'stdout','-l','eng','--psm','6'],capture_output=True,text=True,check=True,timeout=30)
 return r.stdout,time.perf_counter()-start

def extract_validated(text):
 result={k:None for k in ('document_id','date','amount')}
 candidates={k:[] for k in result}
 for line in text.splitlines():
  # Accept common OCR label variations, but never substitute value digits.
  if re.match(r'^\s*Document\s+[I1l\\]*D\s*[:=]',line,re.I):
   value=re.split(r'[:=]',line,maxsplit=1)[1].strip();m=re.fullmatch(r'SYN\s*-\s*([0-9 ]+)',value,re.I)
   if m:
    digits=m.group(1).replace(' ','')
    if len(digits)==6:candidates['document_id'].append('SYN-'+digits)
  m=re.match(r'^\s*Date\s*[:=]\s*(\d{4}-\d{2}-\d{2})\s*$',line,re.I)
  if m:
   try:date.fromisoformat(m.group(1));candidates['date'].append(m.group(1))
   except ValueError:pass
  m=re.match(r'^\s*Amount\s*[:=]\s*(\d+(?:,\d{3})*\.\d{2})\s*$',line,re.I)
  if m:candidates['amount'].append(format(Decimal(m.group(1).replace(',','')),'.2f'))
 for key,values in candidates.items():
  if len(values)==1:result[key]=values[0]
 return result

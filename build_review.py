"""Render existing measured reports; never runs OCR or changes frozen source."""
import json,html,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
esc=lambda x:html.escape(str(x))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'review';out.mkdir(exist_ok=True)
 frozen=json.loads((ROOT/'enhanced_output/frozen.json').read_text())
 reports={s:json.loads((ROOT/f'enhanced_output/{s}_report.json').read_text()) for s in ('dev','test')}
 for name,expected in frozen.items():
  if sha(ROOT/name)!=expected:raise ValueError('Frozen file changed: '+name)
 for s,r in reports.items():
  if r['split']!=s or r['fingerprint']!=frozen:raise ValueError('Report/frozen fingerprint mismatch: '+s)
 manifest=json.loads((ROOT/'challenge_data/manifest.json').read_text());truth={r['id']:r for r in manifest['records']}
 parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic OCR evidence review</title><style>body{font:16px system-ui;color:#173045;max-width:1100px;margin:auto;padding:28px;background:#f5f7fa}h1,h2{color:#173045}table{border-collapse:collapse;width:100%;background:white;margin:16px 0}td,th{padding:10px;border-bottom:1px solid #ccd4dd;text-align:left}pre{white-space:pre-wrap;background:#edf1f5;padding:15px}details{background:white;padding:15px;margin:12px 0;border:1px solid #ccd4dd;border-radius:8px}img{max-width:100%;height:auto}input{padding:10px;width:90%}.bad{color:#a52727}.good{color:#206841}</style><h1>Synthetic Insurance Document OCR</h1><p>Personal portfolio benchmark. English synthetic images; no real claims or customer data. Selected method: enhanced, chosen on dev before test.</p><p>40 variants per evaluation split from 10 originals in two layouts. Variants are correlated. This is not real-world insurance accuracy. Blur/low-resolution failures remain. Schema-valid output may still be wrong.</p>']
 summary=[]
 for split,report in reports.items():
  parts.append('<h2>'+split.upper()+' measured results</h2><table><tr><th>Method</th><th>Images / originals</th><th>Normalized CER</th><th>All 3 fields correct</th></tr>')
  for r in report['summary']:
   if r['condition']!='all':continue
   parts.append(f'<tr><td>{esc(r["method"])}</td><td>{r["images"]} / {r["originals"]}</td><td>{r["normalized_cer"]:.2%}</td><td>{r["document_match"]:.2%}</td></tr>');summary.append(dict(split=split,**r))
  parts.append('</table>')
 parts.append('<h2>Test error inspection</h2><p>Results below are evaluated against known synthetic labels. Correctness labels are for evaluation, not a production confidence gate.</p><input id="q" placeholder="Filter: blur_lowres, skew, raw, enhanced, document ID"><div id="cases">')
 for r in reports['test']['records']:
  t=truth[r['id']];im=ROOT/'challenge_data'/t['image']
  if sha(im)!=t['sha']:raise ValueError('Image changed: '+t['image'])
  matches=r['matches'];ok=all(matches.values());tag='PASS' if ok else 'ERROR';search=esc(r['id']+' '+r['method'])
  parts.append(f'<details data-search="{search}"><summary class="'+('good' if ok else 'bad')+f'">{tag} | {esc(r["id"])} | {esc(r["method"])}</summary>')
  # Browser BMP support varies: create a PNG display copy; source remains untouched.
  from PIL import Image
  preview=out/(t['image']+'.png')
  if not preview.exists():Image.open(im).save(preview)
  parts.append(f'<img loading="lazy" src="{esc(preview.name)}" alt="Synthetic source document"><table><tr><th>Field</th><th>Expected</th><th>Predicted</th><th>Match</th></tr>')
  for k in ('document_id','date','amount'):parts.append(f'<tr><td>{k}</td><td>{esc(t["fields"][k])}</td><td>{esc(r["prediction"][k])}</td><td>{matches[k]}</td></tr>')
  parts.append('</table><h3>OCR output</h3><pre>'+esc(r['text'])+'</pre></details>')
 parts.append('</div><h2>Protocol and limits</h2><p>Normalized CER lowercases and collapses whitespace. Exact document match means all three extracted fields equal labels. ID spacing normalization and date/amount validation are contract-specific; no digit guessing. No model fine-tuning, Thai OCR, handwriting or damage detection is implemented. Timings are excluded because recorded timing boundaries differ across methods.</p><p>Frozen code/manifest fingerprints verified against both reports. Environment files are archived as user-recorded metadata; freeze does not bind dependency versions.</p><script>document.getElementById("q").addEventListener("input",e=>{const q=e.target.value.toLowerCase();document.querySelectorAll("details").forEach(x=>x.hidden=!x.dataset.search.toLowerCase().includes(q))})</script></html>')
 (out/'index.html').write_text(''.join(parts));(out/'summary.json').write_text(json.dumps(summary,indent=2))
 files=['enhanced_output/dev_report.json','enhanced_output/test_report.json','enhanced_output/frozen.json','docker-image-id.txt','tesseract-version.txt','pillow-version.txt']
 (out/'evidence_inventory.json').write_text(json.dumps({name:sha(ROOT/name) if (ROOT/name).exists() else 'not provided' for name in files},indent=2))
 print('Created review/index.html; reports and frozen fingerprints verified. No OCR rerun.')
if __name__=='__main__':main()

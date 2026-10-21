"""Evaluate an earlier frozen OCR policy on a new authored font/layout cohort."""
import argparse
from datetime import date,timedelta
import html,json,random
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import experiment as base
ROOT=Path(__file__).resolve().parent
SEED=2026102101
CONDITIONS=('clean','low_resolution','skew')
FONTS=('DejaVuSerif.ttf','DejaVuSansMono.ttf')

def sources():
    p=ROOT/'measured_linux/frozen_policy.json';policy=json.loads(p.read_text())
    return dict(method=policy['selected_method'],threshold=policy['threshold'],original_policy_sha256=base.sha(p),
        experiment_sha256=base.sha(ROOT/'experiment.py'),challenge_source_sha256=base.sha(__file__),
        original_manifest_sha256=base.sha(ROOT/'dataset/manifest.json'))

def generate(folder,font_directory=Path('/usr/share/fonts/truetype/dejavu')):
    folder=Path(folder).resolve();fonts=[Path(font_directory)/n for n in FONTS]
    if folder.exists():raise ValueError('dataset_exists')
    if not all(p.is_file() for p in fonts):raise ValueError('challenge_font_missing')
    old=json.loads((ROOT/'dataset/manifest.json').read_text())
    hashes=[base.sha(f) for f in fonts]
    if len(set(hashes))!=2 or old['font_sha256'] in hashes:raise ValueError('challenge_fonts_not_new_or_distinct')
    used={r['fields']['document_id'] for r in old['records']}
    rng=random.Random(SEED);records=[];folder.mkdir(parents=True)
    for n in range(12):
        font=ImageFont.truetype(str(fonts[n%2]),(25,29,33)[n%3])
        while True:
            doc_id=f'SYN-{rng.randrange(100000,999999)}'
            if doc_id not in used:used.add(doc_id);break
        fields=dict(document_id=doc_id,date=(date(2026,1,1)+timedelta(days=rng.randrange(270))).isoformat(),amount=f'{rng.randrange(100,90000)}.{rng.randrange(100):02d}')
        order=(('date','amount','document_id'),('document_id','amount','date'),('amount','date','document_id'))[n%3]
        labels=dict(document_id='Document ID',date='Date',amount='Amount')
        lines=['SYNTHETIC FIELD REVIEW','NOT A REAL CUSTOMER RECORD']+[labels[k]+': '+fields[k] for k in order]+['Currency: THB']
        im=Image.new('L',(1100,640),255);draw=ImageDraw.Draw(im)
        for i,line in enumerate(lines):draw.text((55+(n%3)*35,38+(n%2)*17+i*78),line,font=font,fill=0)
        oid=f'challenge-{n:02d}'
        for condition in CONDITIONS:
            if condition=='low_resolution':v=im.resize((385,224),Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(.8)).resize(im.size,Image.Resampling.BICUBIC)
            elif condition=='skew':v=im.rotate(7 if n%2 else -7,resample=Image.Resampling.BICUBIC,expand=True,fillcolor=255)
            else:v=im.copy()
            name=f'{oid}-{condition}.png';v.save(folder/name)
            records.append(dict(id=Path(name).stem,original_id=oid,font=FONTS[n%2],condition=condition,image=name,sha256=base.sha(folder/name),fields=fields))
    m=dict(seed=SEED,protocol=sources(),font_sha256={f.name:base.sha(f) for f in fonts},pillow=base.pillow_version,records=records,
        policy='Apply the previously selected method/threshold unchanged. Raw is a descriptive comparator, never used for reselection.',
        primary_metric='Complete exact document ID, date and amount under the earlier frozen policy.',
        limits='12 newly authored synthetic English originals, 2 different font files, 3 correlated variants each. Same field labels/extractor and developer author. No real scans, Thai, handwriting, tables or independent human benchmark. No new model training or measured business savings.')
    base.save(folder/'manifest.json',m);return m

def validate(folder):
    folder=Path(folder).resolve();m=json.loads((folder/'manifest.json').read_text())
    if m['protocol']!=sources():raise ValueError('frozen_source_or_policy_changed')
    if m['seed']!=SEED:raise ValueError('unexpected_seed')
    old=json.loads((ROOT/'dataset/manifest.json').read_text());old_ids={r['fields']['document_id'] for r in old['records']};old_hashes={r['sha256'] for r in old['records']}
    ids=set();groups={};labels={}
    for r in m['records']:
        if r['id'] in ids:raise ValueError('duplicate_image_id')
        ids.add(r['id']);groups.setdefault(r['original_id'],[]).append(r['condition'])
        if labels.setdefault(r['original_id'],r['fields'])!=r['fields']:raise ValueError('inconsistent_original_labels')
        p=(folder/r['image']).resolve()
        if not p.is_relative_to(folder) or base.sha(p)!=r['sha256']:raise ValueError('image_path_or_hash_changed')
        if r['fields']['document_id'] in old_ids or r['sha256'] in old_hashes:raise ValueError('prior_cohort_overlap')
        if set(r['fields'])!=set(base.FIELDS) or r['font'] not in FONTS:raise ValueError('record_contract_changed')
    if len(groups)!=12 or len(ids)!=36 or any(sorted(c)!=sorted(CONDITIONS) for c in groups.values()):raise ValueError('challenge_cohort_incomplete')
    if len({v['document_id'] for v in labels.values()})!=12:raise ValueError('duplicate_original_label')
    return m

def run(dataset,out):
    dataset=Path(dataset).resolve();out=Path(out).resolve()
    if out.exists():raise ValueError('output_exists')
    if dataset==out or dataset in out.parents or out in dataset.parents:raise ValueError('input_output_overlap')
    m=validate(dataset);out.mkdir(parents=True)
    fp=dict(protocol=sources(),manifest_sha256=base.sha(dataset/'manifest.json'),environment=base.environment())
    # Persist the fixed policy before the first OCR call. No selection on this cohort.
    base.save(out/'frozen_protocol.json',dict(frozen_utc=base.now(),fingerprint=fp,selected_method=m['protocol']['method'],threshold=m['protocol']['threshold'],policy=m['policy']))
    rows=[]
    for r in m['records']:
        for method in ('raw',m['protocol']['method']):
            observed=base.recognize(dataset/r['image'],method);matches={k:observed['prediction'][k]==r['fields'][k] for k in base.FIELDS}
            rows.append(dict(id=r['id'],original_id=r['original_id'],condition=r['condition'],font=r['font'],method=method,expected=r['fields'],**observed,matches=matches,complete_correct=all(matches.values())))
        print('challenge: '+r['id'],flush=True)
    if fp['protocol']!=sources() or fp['manifest_sha256']!=base.sha(dataset/'manifest.json') or fp['environment']!=base.environment():raise ValueError('evaluation_fingerprint_changed')
    validate(dataset)
    selected=base.summary(rows,m['protocol']['method'],m['protocol']['threshold'])
    comparisons=[base.summary(rows,method,0) for method in ('raw',m['protocol']['method'])]
    breakdown={d:{v:base.summary([r for r in rows if r[d]==v],m['protocol']['method'],m['protocol']['threshold']) for v in sorted({r[d] for r in rows})} for d in ('font','condition')}
    failures=[{k:r[k] for k in ('id','font','condition','expected','prediction','matches')} for r in rows if r['method']==m['protocol']['method'] and not r['complete_correct']]
    result=dict(status='evaluated_local',api_calls=0,trained_new_model=False,fingerprint=fp,selected_policy=selected,descriptive_comparators=comparisons,breakdown=breakdown,failed_images=failures,limits=m['limits'],human_review_required=36,
        interpretation='Fresh authored challenge of an earlier frozen policy. No retuning or best-method selection on this cohort. Later reruns measure reproducibility, not a new untouched test.')
    base.save(out/'predictions.json',rows);base.save(out/'results.json',result)
    text='# Frozen-policy OCR font/layout challenge\n\n'+m['policy']+'\n\n| Method | Complete exact | Wrong emitted fields |\n| --- | ---: | ---: |\n'
    for c in comparisons:text+=f"| {c['method']} | {c['complete_correct']}/{c['images']} | {c['wrong_emitted_fields']} |\n"
    text+='\n## Selected policy by condition\n\n'
    for value,c in breakdown['condition'].items():text+=f"- {value}: {c['complete_correct']}/{c['images']} complete exact; {c['wrong_emitted_fields']} wrong emitted fields.\n"
    text+='\n## Observed failures\n\n'
    for f in failures:text+='- '+f['id']+': expected '+json.dumps(f['expected'])+'; observed '+json.dumps(f['prediction'])+'\n'
    text+='\n'+m['limits']+'\n\n'+result['interpretation']+' All images still require human verification.\n'
    (out/'RESULTS.md').write_text(text)
    (out/'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Frozen OCR policy challenge</title><style>body{font:16px/1.6 system-ui;max-width:1050px;padding:24px;margin:auto;color:#173e4b}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Frozen OCR policy challenge</h1><pre>'+html.escape(text)+'</pre></html>')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['generate','run']);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--out',type=Path);p.add_argument('--font-directory',type=Path,default=Path('/usr/share/fonts/truetype/dejavu'));a=p.parse_args()
    if a.stage=='generate':print(json.dumps(dict(images=len(generate(a.dataset,a.font_directory)['records'])),indent=2))
    else:
        if not a.out:p.error('--out required')
        print(json.dumps(run(a.dataset,a.out)['selected_policy'],indent=2))

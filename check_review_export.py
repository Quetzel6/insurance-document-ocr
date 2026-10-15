"""Check review export agreement and provenance, without judging image correctness."""
import argparse
import hashlib
import json
from pathlib import Path
from review_app import validation
from review_consistency import check_consistency


def check_export(data, raw):
    digest=hashlib.sha256(raw).hexdigest()
    if not isinstance(data,dict) or not isinstance(data.get('decisions'),list) or not isinstance(data.get('audit'),list):
        raise ValueError('Expected decisions and audit arrays')
    if data.get('report_sha')!=digest:raise ValueError('Export does not match this OCR report')
    source={r['id']:r for r in json.loads(raw)['records'] if r['method']=='enhanced'}
    seen=set();rows=[]
    for row in data['decisions']:
        if not isinstance(row,dict) or not isinstance(row.get('id'),str) or row['id'] in seen:raise ValueError('Decision IDs must be unique strings')
        case=row['id'];seen.add(case);issues=[];status=row.get('status')
        if status not in ('approved','rejected'):issues.append('Unknown status')
        if not isinstance(row.get('reviewer'),str) or not row['reviewer'].strip():issues.append('Missing reviewer')
        note=row.get('note')
        if not isinstance(note,str) or len(note)>2000:issues.append('Invalid note')
        if status=='rejected' and (not isinstance(note,str) or not note.strip()):issues.append('Missing rejection reason')
        record=source.get(case)
        if record is None:issues.append('Unknown source case')
        else:
            original={k:str(record['prediction'].get(k) or '') for k in ('document_id','date','amount')}
            if row.get('original')!=original:issues.append('Original predictions differ from report')
            if 'original_text' in row and row['original_text']!=record['text']:issues.append('Original text differs from report')
        history=[a for a in data['audit'] if isinstance(a,dict) and a.get('id')==case]
        v=row.get('version')
        if type(v) is not int or v<1:issues.append('Invalid version')
        elif [a.get('version') for a in history]!=list(range(1,v+1)):issues.append('Audit versions incomplete or out of order')
        if not history or history[-1]!=row:issues.append('Latest audit differs from current decision')
        if status=='approved':
            values=row.get('values');text=row.get('corrected_text')
            if not isinstance(values,dict) or any(not isinstance(values.get(k),str) for k in ('document_id','date','amount')):issues.append('Missing structured values')
            else:
                issues.extend(validation(values))
                if isinstance(text,str):issues.extend(check_consistency(text,values)['errors'])
            if not isinstance(text,str):issues.append('No corrected text; review older decision again')
            if row.get('text_confirmed') is not True:issues.append('Text not explicitly confirmed')
            if 'original_text' not in row:issues.append('Original text not archived')
        category='needs_review' if issues else ('excluded_rejected' if status=='rejected' else 'consistent_review')
        rows.append(dict(id=case,category=category,issues=issues))
    return dict(reviewed=len(rows),unreviewed_source_cases=len(set(source)-seen),report_sha=digest,cases=rows,
                counts={k:sum(r['category']==k for r in rows) for k in ('consistent_review','excluded_rejected','needs_review')},
                limit='Checks provenance, audit, format and agreement only. Consistent values may still be wrong against the image. No automatic training approval.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('export',type=Path)
    p.add_argument('--out',type=Path,default=Path('review_check'))
    p.add_argument('--report',type=Path,default=Path(__file__).resolve().parent/'enhanced_output/test_report.json')
    a=p.parse_args()
    try:
        raw=a.export.read_bytes();r=check_export(json.loads(raw),a.report.read_bytes())
    except (ValueError,OSError) as e:p.exit(2,f'Cannot check export: {e}\n')
    r['export_sha256']=hashlib.sha256(raw).hexdigest();a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Review export check','',r['limit'],'',f"Reviewed: {r['reviewed']}; unreviewed source cases: {r['unreviewed_source_cases']}",'']
    lines += [f'- {k}: {v}' for k,v in r['counts'].items()]
    for row in r['cases']:
        lines += ['',f"## {row['id']} — {row['category']}",'']
        lines += [f'- {x}' for x in row['issues']] or ['No structural issues detected. Image correctness remains unverified.']
    (a.out/'check.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f"Checked {r['reviewed']} cases. {r['counts']}. Report: {a.out.resolve()}/check.md")


if __name__=='__main__':main()

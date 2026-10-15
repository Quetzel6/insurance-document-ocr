"""Summarize a local Review Desk JSON export without changing OCR or its benchmark."""
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re

FIELDS=('document_id','date','amount')


def analyze(export):
    if not isinstance(export,dict) or not isinstance(export.get('decisions'),list):
        raise ValueError('Expected a Review Desk export with a decisions array')
    decisions=export['decisions']
    ids=set()
    statuses=Counter()
    changed=Counter()
    pairs=Counter()
    confirmed=0
    legacy=0
    edited_documents=0
    for row in decisions:
        if not isinstance(row,dict) or not isinstance(row.get('id'),str) or row['id'] in ids:
            raise ValueError('Decision IDs must be unique strings; export current decisions, not audit events')
        ids.add(row['id'])
        if row.get('status') not in ('approved','rejected'):
            raise ValueError('Unknown decision status')
        statuses[row['status']]+=1
        if row['status']!='approved':
            continue
        for key in ('original','values'):
            if not isinstance(row.get(key),dict) or any(k not in row[key] for k in FIELDS):
                raise ValueError('Approved decisions must contain original and current field values')
        for field in FIELDS:
            if row['original'][field]!=row['values'][field]:changed[field]+=1
        before,after=row.get('original_text'),row.get('corrected_text')
        if not isinstance(before,str) or not isinstance(after,str):
            legacy+=1
            continue
        if before!=after:edited_documents+=1
        if row.get('text_confirmed') is not True:
            continue
        confirmed+=1
        # Preserve case, digits and punctuation; no guessed spelling or replacements.
        old=re.findall(r'\w+|[^\w\s]',before,flags=re.UNICODE)
        new=re.findall(r'\w+|[^\w\s]',after,flags=re.UNICODE)
        for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
            if tag!='equal':pairs[(' '.join(old[a:b]),' '.join(new[c:d]))]+=1
    return dict(report_sha=export.get('report_sha'),reviewed_documents=len(ids),
                statuses=dict(statuses),approved_field_changes={f:changed[f] for f in FIELDS},
                approved_documents_with_text_edits=edited_documents,
                approved_confirmed_text_documents=confirmed,approved_legacy_without_text=legacy,
                confirmed_token_edits=[dict(before=a,after=b,count=n) for (a,b),n in pairs.most_common()],
                limits=['Counts use current decisions, not repeated saves in audit history.',
                        'Human approvals are reviewer assertions, not independently verified ground truth.',
                        'Rejected text is excluded from correction pairs.',
                        'Only explicitly confirmed approved text contributes token-edit pairs.',
                        'Whitespace-only edits are not represented in token-edit pairs.',
                        'No accuracy, confidence threshold or automatic spelling rule is inferred.'])


def markdown(result):
    lines=['# OCR review error analysis','',
           f"Reviewed documents: {result['reviewed_documents']}",
           f"Approved: {result['statuses'].get('approved',0)}; rejected: {result['statuses'].get('rejected',0)}",'',
           '## Structured field edits on approved documents','',
           *[f'- {key}: {count}' for key,count in result['approved_field_changes'].items()],
           '',f"Approved and explicitly text-confirmed documents: {result['approved_confirmed_text_documents']}",
           f"Approved older records without text: {result['approved_legacy_without_text']}",'',
           '## Token edits from confirmed approved text','']
    if result['confirmed_token_edits']:
        for row in result['confirmed_token_edits']:
            # JSON quoting keeps document fragments literal in plain list entries.
            lines.append('- '+json.dumps(row,ensure_ascii=False))
    else:lines.append('No confirmed correction pairs available yet.')
    lines+=['','## Interpretation','',*[f'- {s}' for s in result['limits']]]
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export',type=Path)
    parser.add_argument('--out',type=Path,default=Path('review_analysis'))
    args=parser.parse_args()
    source=args.export.read_bytes()
    result=analyze(json.loads(source))
    result['export_sha256']=hashlib.sha256(source).hexdigest()
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'analysis.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    (args.out/'analysis.md').write_text(markdown(result),encoding='utf-8')
    print(f"Analyzed {result['reviewed_documents']} reviewed documents. Reports: {args.out.resolve()}")


if __name__=='__main__':main()

"""Exploratory synthetic-contract parser; preserves value digits and rejects ambiguity."""
import re
from datetime import date
from decimal import Decimal

FIELDS=('document_id','date','amount')
LABELS={
    'document_id':re.compile(r'^\s*Document\s+(?:ID|1D|I0)\b\s*[:=]?\s*(.*?)\s*$',re.I|re.ASCII),
    'date':re.compile(r'^\s*Date\b\s*[:=]?\s*(.*?)\s*$',re.I|re.ASCII),
    'amount':re.compile(r'^\s*(?:Amount|Amourt)\b\s*[:=]?\s*(.*?)\s*$',re.I|re.ASCII),
}


def parse_value(field,value):
    if field=='document_id':
        m=re.fullmatch(r'SYN\s*-\s*([0-9](?:[0-9 ]*[0-9])?)',value,re.I|re.ASCII)
        if m:
            digits=m.group(1).replace(' ','')
            if len(digits)==6:return 'SYN-'+digits
    elif field=='date':
        # Normalizes separators only; no inferred or substituted digit.
        if re.fullmatch(r'[0-9]{8}',value):value=value[:4]+'-'+value[4:6]+'-'+value[6:]
        if re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',value):
            try:date.fromisoformat(value);return value
            except ValueError:pass
    elif field=='amount':
        # A visible decimal point and exactly two decimal digits are mandatory.
        if re.fullmatch(r'(?:[0-9]{1,12}|[0-9]{1,3}(?:,[0-9]{3})+)\.[0-9]{2}',value):
            normalized=value.replace(',','')
            if len(normalized.split('.')[0])<=12:return format(Decimal(normalized),'.2f')
    return None


def extract_candidate(text):
    occurrences={k:[] for k in FIELDS}
    for line in text.splitlines():
        for field,pattern in LABELS.items():
            m=pattern.fullmatch(line)
            if m:occurrences[field].append(parse_value(field,m.group(1)))
    # Even a malformed duplicate makes the field ambiguous.
    return {k:values[0] if len(values)==1 else None for k,values in occurrences.items()}

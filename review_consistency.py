"""Strict review-form checks; never reads benchmark labels or changes digits."""
import re

PATTERNS = {
    'document_id': r'Document\s+ID\s*:?\s*(SYN-[0-9]{6})',
    'date': r'Date\s*:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
    'amount': r'Amount\s*:?\s*([0-9]{1,12}\.[0-9]{2})',
}


def check_consistency(text, values):
    """Require exactly one complete line per field in this synthetic contract."""
    extracted, errors = {}, []
    for field, pattern in PATTERNS.items():
        matches = []
        for line in text.splitlines():
            match = re.fullmatch(pattern, line.strip(), flags=re.IGNORECASE | re.ASCII)
            if match:
                value = match.group(1)
                matches.append(value.upper() if field == 'document_id' else value)
        # Count label occurrences too, including malformed duplicate lines.
        label = {'document_id': r'Document\s+ID', 'date': 'Date', 'amount': 'Amount'}[field]
        labels = sum(bool(re.match(r'^\s*' + label + r'\b', line, re.I | re.ASCII))
                     for line in text.splitlines())
        if len(matches) != 1 or labels != 1:
            errors.append(f'{field}: corrected text needs exactly one clear label/value line; use Document ID: SYN-123456, Date: YYYY-MM-DD, Amount: 123.45.')
        else:
            extracted[field] = matches[0]
            if matches[0] != values.get(field):
                errors.append(f'{field}: corrected text has {matches[0]}, but field has {values.get(field, "")}. Check the image and make both agree.')
    return {'passed': not errors, 'extracted': extracted, 'errors': errors,
            'policy': 'review-consistency-v1',
            'limit': 'Agreement does not prove correctness against the source image.'}

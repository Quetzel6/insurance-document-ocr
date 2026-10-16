"""Read-only field suggestions from human-edited text; no OCR or digit repair."""
import datetime as dt
import hashlib
from review_consistency import check_consistency
FIELDS = ('document_id', 'date', 'amount')


def suggest_fields(text):
    if not isinstance(text, str) or len(text) > 10000:
        raise ValueError('Corrected text must be text, max 10000 characters')
    # The shared consistency checker rejects malformed/duplicate label lines.
    extracted = check_consistency(text, {})['extracted']
    values = {key: extracted.get(key) for key in FIELDS}
    if values['date'] is not None:
        try:
            dt.date.fromisoformat(values['date'])
        except ValueError:
            values['date'] = None
    return dict(values=values, missing_or_ambiguous=[key for key in FIELDS if values[key] is None],
                text_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
                policy='review-field-suggestions-v1',
                limit='Suggestions only: verify the source image. No digits or decimals are inferred. Nothing is saved until a decision is submitted.')

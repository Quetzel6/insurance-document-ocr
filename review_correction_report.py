"""Summarize human review edits locally; no OCR rerun or accuracy claims."""
import argparse
from collections import Counter
import difflib
import json
from pathlib import Path
import unicodedata


def summarize(export):
    if not isinstance(export, dict) or not isinstance(export.get('decisions'), list):
        raise ValueError('Use Export decisions & history, not an OCR review package')
    counts = Counter()
    modes = Counter()
    seen = set()
    for decision in export['decisions']:
        if not isinstance(decision, dict):
            raise ValueError('Invalid decision')
        identity = decision.get('id')
        if not isinstance(identity, str) or identity in seen:
            raise ValueError('Missing or duplicate decision ID; export one current round')
        seen.add(identity)
        status = decision.get('status')
        if status not in ('approved', 'rejected'):
            raise ValueError('Invalid decision status')
        counts[status] += 1
        if status == 'rejected':
            continue  # Rejected text is not a verified reference.
        before, after = decision.get('original_text'), decision.get('corrected_text')
        if not isinstance(before, str) or not isinstance(after, str):
            counts['approved_missing_text'] += 1
            continue
        if max(len(before), len(after)) > 10000:
            raise ValueError('Text exceeds review limit')
        counts['approved_compared'] += 1
        modes[decision.get('review_mode', 'structured')] += 1
        counts['text_changed'] += before != after
        counts['text_unchanged'] += before == after
        categories = {
            'digit_sequence_changed': lambda c: c.isdecimal(),
            'letter_sequence_changed': lambda c: unicodedata.category(c).startswith(('L', 'M')),
            'punctuation_sequence_changed': lambda c: unicodedata.category(c).startswith('P'),
            'whitespace_sequence_changed': lambda c: c.isspace(),
        }
        for name, predicate in categories.items():
            counts[name] += ''.join(filter(predicate, before)) != ''.join(filter(predicate, after))
        # Non-overlapping alignment spans, not Levenshtein distance or CER.
        for tag, a, b, c, d in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes():
            if tag != 'equal':
                counts['alignment_edit_spans'] += 1
                counts['characters_removed_or_replaced'] += b - a
                counts['characters_added_or_replaced'] += d - c
    keys = ('approved', 'rejected', 'approved_compared', 'approved_missing_text',
            'text_changed', 'text_unchanged', 'digit_sequence_changed',
            'letter_sequence_changed', 'punctuation_sequence_changed',
            'whitespace_sequence_changed', 'alignment_edit_spans',
            'characters_removed_or_replaced', 'characters_added_or_replaced')
    return {'policy': 'review-correction-summary-v1',
            'counts': {key: counts[key] for key in keys}, 'approved_modes': dict(modes),
            'limits': ['Current decisions only; audit revisions are not counted again.',
                       'Only approved text pairs are compared; rejected text is excluded.',
                       'Category counts overlap and count cases, not incorrect characters.',
                       'Measures recorded human edits, not OCR accuracy, CER, time saved or model learning.',
                       'Unchanged approved text does not prove the OCR was correct.',
                       'No reviewer names, notes, document IDs, text or field values are included.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    parser.add_argument('--out', type=Path, default=Path('review_analysis/correction_summary.json'))
    args = parser.parse_args()
    try:
        if args.export.stat().st_size > 50 * 1024 * 1024:
            raise ValueError('Export exceeds 50 MiB')
        if args.export.resolve() == args.out.resolve():
            raise ValueError('Output must differ from input')
        report = summarize(json.loads(args.export.read_text(encoding='utf-8')))
    except (OSError, ValueError) as error:
        parser.exit(2, f'Error: {error}\n')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['counts'], ensure_ascii=False, indent=2))
    print(f'Saved {args.out}')


if __name__ == '__main__':
    main()

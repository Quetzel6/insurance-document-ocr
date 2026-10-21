# Review correction report

Click Export decisions & history in Review Desk. The downloaded decisions JSON is the input, not ocr-review-package.json, which contains only original OCR.

Run from the repository directory, adjusting the downloaded filename:

    python3 review_correction_report.py ~/"Downloads/ocr-review-decisions.json"

The standard-library tool prints counts and writes review_analysis/correction_summary.json. It does not modify decisions, rerun OCR or train a model.

Only current decisions are counted; audit versions are not counted again. Rejected text is excluded from comparisons. Approved legacy records without text pairs are counted separately. Changes to letter, decimal digit, punctuation and whitespace sequences count cases and overlap. Alignment spans and added/removed character totals are not Levenshtein distance or CER.

Example: Amount 86622 45 → Amount: 86622.45 changes punctuation/whitespace while preserving the digit sequence. Changing 86622 to 86682 changes digits too. Reordering text can affect sequence counts.

These are recorded edit counts, not OCR accuracy, effort/time saved or proof that approved text is correct. Manual changes and applied suggestions are combined. Verify images before treating approvals as evaluation references.

Reports omit reviewer names, notes, document IDs, text and field values. Keep source exports local; nothing is published by this command. Tests use synthetic examples.

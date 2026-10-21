# Review export check

Install this small update into your existing insurance-ocr-v05-fixed directory. It adds a command-line checker; it does not change the running app, database, source export or frozen OCR benchmark.

Export decisions & history again after the latest review. Use the actual downloaded filename (browser may append a number):

```bash
python3 check_review_export.py "$HOME/Downloads/ocr-review-decisions.json"
open review_check/check.md
```

Outputs: review_check/check.json and check.md. Re-running overwrites these outputs; use --out another-directory for a separate run. Output includes hashes of the export and matching measured OCR report.

Categories:
- consistent_review: approved, confirmed text, valid matching fields, matching original predictions/text and complete matching audit history. This does NOT verify correctness against the image or authorize automatic training.
- excluded_rejected: rejected with a reason and no provenance/audit issues. Guessed or partial corrected text on rejected cases is not used as an accepted correction.
- needs_review: missing older text, mismatch, incomplete audit or another issue. Each case lists reasons.

The checker reads only enhanced predictions and original OCR text from the matching measured report. No benchmark expected labels or correctness matches are used. It cannot detect wrong values that agree in text and fields. It does not auto-correct any digits or update the database. Manual JSON edits can create audit mismatches; correct decisions through the application and export again.

The provided old export was checked during development: 2 current cases, both need review. This is historical, not a later review state after rejection. 34 unit tests passed across the project. The next recognition experiment should use newly separated development and untouched test cohorts; these inspected cases are development evidence.

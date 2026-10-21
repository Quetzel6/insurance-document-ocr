> Historical development note. For current commands and verification scope, start with [README](../../README.md). Counts and pending items below describe that stage.

# v0.7 review consistency check

Stop the app before installing this update. Extract into the existing v0.5-fixed application directory and restart review_app.py. Existing SQLite decisions/history remain; no migration or automatic rewriting is performed. Older approved records have not been checked retroactively. Reopen and save a case to apply the new checks.

New approvals require exactly one complete line for each field in Corrected OCR text:

```
Document ID: SYN-123456
Date: 2026-10-15
Amount: 123.45
```

These are formatting examples, not values to copy into real cases. Other text lines may remain. Labels are case-insensitive; colons are optional. Date and amount must use the displayed formats. Comma-separated numbers, inline multiple fields and currency suffixes are not supported by this narrow synthetic document contract. Duplicate label lines are rejected. No digit, missing decimal or misspelled label is automatically inferred.

If the text and structured fields differ, approval fails with the field name and both values; the previous saved decision is unchanged. Check the image and edit the appropriate side. The application never chooses a value for you. Rejection with a reason remains available for unreadable documents. The consistency result is saved in decisions/audit/export for new saves.

Consistency is not image verification: wrong values that agree in both places can pass. Benchmark labels are not consulted. OCR recognition and frozen benchmark results are unchanged. This update does not repair previous user decisions or train OCR.

Verification: 27 unit tests passed, including matching values, date mismatch, missing decimal, duplicate labels, malformed numbers, blocked saves and rejection. Frozen benchmark review checks passed. Browser visual acceptance on a Mac remains pending.

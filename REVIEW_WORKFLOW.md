# Local OCR review workflow — v0.5

## Start on your Mac
Extract this package into a new directory. Keep the earlier verified package as benchmark evidence. Open Terminal in the extracted directory and run:

```bash
python3 --version
python3 review_app.py
```

Requires Python 3.10+. No new pip dependencies for this app. Open http://127.0.0.1:8765 in Chrome or Safari. Stop with Control-C. If the port is busy, use `python3 review_app.py --port 8766` and open http://127.0.0.1:8766.

The existing Dockerfile does not publish this local-only app; run it directly with Python on the Mac. Existing Docker benchmark commands remain available separately.

## Acceptance walkthrough
1. The queue loads 40 enhanced OCR predictions. Format-flagged cases appear first. All start pending; none are automatically approved.
2. Inspect the image and original OCR text. Edit Document ID, Date and Amount, enter your reviewer name, then approve. Approval requires a six-digit SYN ID, valid calendar date and non-negative amount with two decimals.
3. For an unreadable document, enter a reason and choose Reject / unreadable. Blank/invalid fields may be rejected. Do not invent missing digits.
4. Use Approved/Rejected filters to find saved decisions. Refresh the page, stop/restart the app and check that the decision remains.
5. Export decisions & history to JSON. Each save records original predictions, edited values, reviewer, UTC timestamp, version and decision. Subsequent saves retain earlier events.
6. In two tabs, open the same case. Save in one, then attempt to save from the older tab. The older save must fail; reload the page to obtain the latest version. Unsaved changes prompt before leaving the page or selecting another case.

## Persistence and boundaries
- State is stored in `review_state/decisions.sqlite3`, outside benchmark evidence. Back up the database while the server is stopped. JSON export is a portable record; import is not implemented.
- The database is bound to the measured test report SHA-256; a changed report requires a separate database (`--db path/to/new.sqlite3`).
- Only enhanced predictions and source images are presented. Expected field labels and correctness matches are not sent to the page. The offline benchmark viewer still exposes labels for evaluation separately.
- Format flags are calculated from predictions, not benchmark matches. Passing format checks does not prove correctness. Blur and valid-but-wrong predictions may need human rejection.
- This is a single-user local synthetic-data demo. Reviewer names are self-reported, not authenticated identities. The application appends audit events but a person with direct database access can modify them; this is not tamper-proof auditing.
- The server binds only to loopback and checks Host plus a per-run save token. No uploads, new-document OCR, production deployment, access roles or calibrated confidence are implemented.
- Source/manifest/report files used by the frozen benchmark are unchanged. Application decisions do not update evaluation scores.

## Verification performed
14 unit tests passed, including persistence, audit retention, conflict handling, report binding, invalid-approval rejection, rejection notes and omission of benchmark labels from cases. HTTP smoke checks covered loading, source image delivery, invalid token rejection, saving, stale version rejection, export and reload. JavaScript syntax checked with Node. Frozen benchmark review rebuilt successfully. Browser visual acceptance and Docker execution were not performed in this environment.

## v0.5 upgrade and text corrections
Stop v0.4 with Control-C before starting v0.5. Extract v0.5 into a new directory. To retain decisions, start v0.5 with the absolute path to your existing database, for example:

```bash
python3 review_app.py --db "$HOME/Documents/insurance-ocr-v04/review_state/decisions.sqlite3"
```

Use that example only if it is the directory where you actually ran v0.4. Otherwise use your actual v0.4 database path. Keep a backup while the old app is stopped. Without --db, v0.5 starts a separate database in its own directory.

Select a case, edit Corrected OCR text to match the source image, inspect the red removed/green added span, then check the image-confirmation checkbox and approve. Editing text again clears confirmation. The preview encloses the span from first to last changed character, so unchanged text between multiple edits may also be highlighted; exports record individual character edits.

If a numeric field was wrong, update the corresponding structured field as well. Text edits and structured edits are separate and not automatically reconciled. For unreadable content, reject with a note; confirmation is not required for rejection. Existing v0.4 approvals remain historical approvals and are not retroactively certified as text-reviewed.

Refresh, inspect the saved corrected text, and export JSON to check original_text, corrected_text, text_changes and text_confirmed. No benchmark scores are recomputed. The v0.5 feature enables manual correction, not improved OCR recognition.

# Review general or sparse OCR text

Image Reader can now download a review package in all three layouts.

1. At port 8766, choose the correct language and General/table or Sparse
   layout, read the image, then click ดาวน์โหลดชุดส่งตรวจ.
2. In the uploaded queue (`python review_app.py --uploads --port 8768`),
   import the downloaded ocr-review-package.json.
3. Compare the source image with the OCR text, correct the text, enter a
   reviewer name and tick the image-check confirmation.
4. Click Approve text, or Reject with a Thai/English reason if unreadable.
5. Export decisions & history as before. Reload/restart preserves the case.

General/sparse imports use text-only review. ID/date/amount inputs and field
suggestion buttons are hidden/disabled. They are not required and must remain
empty. Text approval requires nonempty corrected text and explicit image-check
confirmation even when the original OCR text was not edited. Rejection may
contain empty text but always requires a reason.

Document-layout packages continue to use structured review with all original
format/consistency checks and the explicit field suggestion helper. The server
selects the mode from the stored case, not a client-supplied decision flag.
Switching modes cannot bypass document approval checks. General/sparse
packages must have field_extraction_enabled=false and all three fields null.

Both types coexist in review_state/uploads.sqlite3. Existing document IDs,
decisions and history remain valid without a schema migration. Legacy cases
without review_mode default to structured. General and sparse cases have
distinct identities so their OCR layouts are not conflated.

New saved decisions/audit entries include review_mode. Text-only decisions
mark structured consistency as applicable=false / passed=null, not a false
claim that structured values were validated. Exports retain source SHA,
language, layout, original/corrected text, reviewer, version and history.
They do not embed image bytes; stop the app to back up the SQLite database
if images must be retained elsewhere. Reset archives decisions and makes
existing images pending again; it does not delete stored images.

This adds a review workflow, not a recognition improvement. Tiny/blurred images
may still need a clearer source or rejection. Thai selection requires the
existing Thai language pack. Tables remain plain OCR text, not reconstructed
cells. PDF, HEIC and handwriting are not added. Keep packages/database private;
the application does not send them to GitHub or an external OCR service.

Automated checks cover import flags, persistence/audit/reset, confirmation,
rejection, unchanged structured identity, server mode authority and suggestion
rejection for text-only cases, plus simulated-DOM reader/mixed-mode UI tests.
Actual browser acceptance on a Mac remains separate.

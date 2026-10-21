# Review uploaded images

1. Run Image Reader as described in README.md and open http://127.0.0.1:8766.
2. Select Document ID / Date / Amount, general or sparse layout, read an image, then click
   ดาวน์โหลดชุดส่งตรวจ. Save ocr-review-package.json locally.
3. In another terminal, from the repository directory, run:

       python3 review_app.py --uploads --port 8767

4. Open http://127.0.0.1:8767. Use นำเข้าชุดส่งตรวจ to select the package.
5. Check the image. Document mode reviews OCR text and three fields separately.
   General/sparse modes review text only: confirm against the image, then
   Approve text. Either mode can be rejected with a Thai/English reason.
6. Export decisions & history to retain review results and source provenance.

The uploaded-image queue uses review_state/uploads.sqlite3. It stores the
decoded image, original OCR text, field suggestions and review history.
Closing/restarting preserves them. Importing the same image, language, OCR
text and fields again opens the existing case and preserves its decision.
Changed OCR output creates a separate case. No OCR is rerun during import.

Reset archives the current decisions/history and makes existing images
pending again. It does not delete images. The default synthetic queue at
port 8765 remains separate, with its original database and benchmark files.

Packages contain the original image and OCR text; keep them private. Git
ignores downloaded packages and review_state/. No package is sent to GitHub
by the application. Import verifies image integrity and limits, but a local
JSON package does not authenticate who produced its OCR text.

Exports include source image SHA-256, language, original OCR text and fields;
they do not embed image bytes. Back up the SQLite database with the app
stopped if you need the images as well. Existing report-based
check_review_export.py is for the synthetic benchmark and will reject the
uploaded queue's uploads-v1 fingerprint; do not use it as an accuracy check.

Document-field approval supports only the current synthetic-style SYN- plus
six-digit ID, ISO calendar date and decimal amount contract. General/sparse
packages use text-only approval and do not validate structured fields. See
docs/guides/GENERAL_TEXT_REVIEW.md. PDF, handwriting and arbitrary insurance ID formats
for structured approval are not supported here.
Approval is a human decision, not proof of correctness or model training.

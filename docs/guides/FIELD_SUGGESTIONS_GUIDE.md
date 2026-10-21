# Fill review fields from corrected text

Review Desk now offers a two-step helper after you inspect/correct the text:

1. Click เสนอค่าจากข้อความที่แก้แล้ว to preview old -> proposed values.
2. Check each proposed value against the image, then click
   ใช้ค่าที่เสนอในช่องข้อมูล to fill the valid fields.
3. Check/confirm edited text and submit Approve or Reject as before.

Previewing does not modify any form field, save a decision, or change status.
Applying updates only fields with unambiguous valid suggestions. Missing,
invalid or duplicate label/value lines leave the existing form field intact.
Applying clears the text-confirmation checkbox and still requires explicit
decision submission. Original OCR text/predictions remain unchanged; saved
decisions and audit history retain the actual resulting text/field edits.

Editing the text or form, or selecting another document, invalidates the
preview. A late response from an older text/document is discarded. If another
tab saves first, the existing decision-version check still prevents overwrite.

The helper supports the review contract only: SYN- plus six digits, a valid
YYYY-MM-DD calendar date, and a nonnegative amount with exactly two decimals.
DocumentID and Document ID are both accepted by suggestions and approval
consistency checks. Example corrected text:

    DocumentID: SYN-123456
    Date: 2026-10-16
    Amount: 10425.45

This is an example, not a value to copy into another image. No missing decimal
or digit is inferred; O is never replaced by 0. Misspelled labels, invalid
dates, currency suffixes and grouped amounts such as 10,425.45 need explicit
human correction to the review contract. Other text lines may remain.
Matching text/fields is not proof of correctness against the image.

POST /api/suggestions is read-only and requires the local session token,
current run ID and a known case ID. It uses only the provided corrected text,
never benchmark expected labels or original saved values. It does not rerun
OCR or change stored decisions. Existing decisions are not rewritten.

Verification includes parser/approval checks, a real HTTP read-only/auth/round
test and Node UI interaction tests for preview/apply, missing/zero values,
stale text/field/case responses and absence of automatic save. Node tests use
a simulated DOM; browser acceptance on a Mac remains separate.

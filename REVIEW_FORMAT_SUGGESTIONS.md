# ID/date/amount formatting assistance

This Review Desk helper reduces retyping after a reviewer has checked and entered Document ID, Date and Amount against the source image. It does not improve OCR recognition or discover the intended numeric value.

1. Verify the image and enter correct Document ID / Date / Amount in the structured fields.
2. Click เสนอจัดรูปแบบ ID/วันที่/ยอดเงินจากช่องข้อมูล.
3. Read the proposed line replacements, then click ใช้รูปแบบที่เสนอ if correct.
4. Check the whole text and fields against the image, confirm and approve separately.

Only one recognized line per field is eligible per field. The existing line's digit sequence must exactly match the reviewed field. No digit is inserted, removed or substituted. Date inputs support YYYYMMDD, YYYY-MMDD, YYYYMM-DD or YYYY-MM-DD; reviewed fields must be valid ISO calendar dates (years 0001–9999). Amount text must contain either a visible dot or a space/tab followed by exactly two decimal digits. The reviewed amount requires an explicit decimal point and two digits. Labels Amount/Amourt/Arnrourt/Ammourt are recognized. Output lines use Document ID:, Date: and Amount:.

ID formatting supports Document ID/I0/IO/1D labels and SYN followed by a hyphen, period or whitespace. The reviewed field must be SYN- plus exactly six digits, and those same six digits must appear in the text. No letter-to-digit substitution is supported.

Missing fields, duplicate/malformed lines, invalid dates, differing digits, signed amounts, comma grouping and compact amounts with no decimal separation are skipped. A space is not proof of a decimal point: even eligible proposals can be wrong if the reviewer entered an incorrect field. Compare the image before applying.

Preview changes nothing; apply changes corrected text only, clears image confirmation and invalidates prior field/word proposals. Field values and original OCR stay unchanged. Case, text or field edits invalidate stale proposals. Text-only mode has no formatting action. No save or automatic approval occurs.

Validation includes browser interaction tests for the above guards. Replay of five existing structured approvals produced proposals in two cases and changed zero digit sequences. These observed cases and human-corrected field inputs do not establish held-out accuracy, time saved, or generalization. Private exports are not committed.

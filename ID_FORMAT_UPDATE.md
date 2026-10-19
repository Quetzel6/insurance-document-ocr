# Observed ID format support

Image Reader's synthetic-contract extractor now recognizes Document IO in addition to ID/I0/1D, and SYN followed by a hyphen, period or whitespace before exactly six numeric digits. Existing digit spacing is removed; digits are not inserted, deleted or substituted. Duplicate labels (even malformed ones), unsupported separators and extra trailing content remain ambiguous and return null.

The raw OCR text is preserved. In Review Desk, the existing formatting preview now supports ID too: it uses the reviewed Document ID field only if the text has exactly the same digits. Reviewers still inspect the image, review the preview, apply, confirm and submit separately. Strict approval checks are unchanged. No decimal inference or Amount parser changes.

Observed-case replay: ten distinct synthetic source images from prior uploaded packages, matched to the existing manifest by source SHA. Correct extracted IDs rose from six to nine; wrong extracted IDs remained zero in this small set. Amount outputs did not change. This is development replay of known cases, not a held-out accuracy or real-document claim. Private packages/exports are not committed.

Three new Python tests cover supported variants, ambiguity and preservation of other fields. Browser tests cover preview/apply with matching digits and refusal of differing/ambiguous digits and duplicate lines.

Restart Image Reader after updating code, then read the image again and download a new review package. Existing packages/queue entries are not reprocessed automatically. Review Desk must also restart/reload for the new formatting button. Docker mount users do not need a rebuild because Python dependencies are unchanged.

Real insurance ID formats outside SYN- plus six digits remain unsupported by structured approval. No recognizer/model training or automatic approval was added.

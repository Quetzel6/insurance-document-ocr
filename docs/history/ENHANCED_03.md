> Historical development note. For current commands and verification scope, start with [README](../../README.md). Counts and pending items below describe that stage.

# Development comparison 0.3

Only dev has been evaluated. Dataset remains Challenge 0.2, including untouched test cohort. Use this complete package in a NEW directory so earlier dev evidence is preserved. Do not regenerate data or inspect test samples/labels.

Methods: raw and grayscale_threshold retain Pilot recognition/extraction; raw_validated changes only extraction/validation; enhanced combines image-only illumination correction, projection-based deskew and validated extraction. No filename, condition, known rotation or ground truth is passed to recognition. Deskew searches -12 through +12 degrees and keeps zero when the gain is small. Illumination division uses a Gaussian background estimate; it may amplify image artifacts.

Validated extraction accepts specified label variations and spaces inside a six-digit synthetic ID. It does not substitute confused digits or infer an amount/date. It rejects invalid calendar dates, missing or ambiguous fields and partial amount matches. Six-digit ID is this synthetic document contract, not a general insurance ID standard. Schema-valid output can still be factually wrong; no confidence or human-review gate is implemented.

8 unit tests cover edit metrics and validation rejection cases. Actual OCR dev results are in enhanced_output/dev_report.json. Original comparison is retained in challenge_output/dev_report.json. Method accuracy must be reported separately from normalized CER; a regex improvement changes field match without changing OCR text.

The record key ocr_seconds is historical: enhanced timing includes preprocessing and OCR, while other methods report OCR time only. Do NOT compare it across methods as a speed benchmark. Version pinning, calibrated confidence, real invoices/Thai OCR and model fine-tuning are not implemented.

From the extracted project directory using the project Docker image:
```bash
docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python -m unittest discover -s tests -v
docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python challenge.py dev
```
No rebuild required with this mounted directory. Don't run freeze/test yet. Results are exploratory dev outcomes with 40 correlated variants / 10 originals in two layouts, not business accuracy. Changes must be selected on dev before freezing the new protocol.

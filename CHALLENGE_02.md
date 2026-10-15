# Challenge 0.2 — development first

30 English synthetic originals, 6 layout configurations, 120 variants. Train/dev/test each have 10 originals in 2 layouts; 40 variants are correlated observations, not 40 independent documents. Shared font and labels remain limitations. Conditions: clean, blurred low resolution, 8-degree skew, horizontal shadow. No training is implemented.

The old Pilot test has been inspected. This is a new cohort; only dev is evaluated in the bundled results. Do not inspect test images, labels or run test until development choices are final. The manifest contains labels for reproducibility; this is procedural separation, not access control.

From project directory, using the user's existing image tag:
```bash
docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python challenge.py dev
```
No rebuild needed: source is mounted. Review challenge_output/dev_report.json per condition, missing fields and OCR text. Fixed preprocessing is a comparator, not an asserted improvement.

After development is finished, freeze and run test once:
```bash
docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python challenge.py freeze
docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python challenge.py test
```
Freeze checks source and manifest hashes. It does not lock package versions or enforce one-time testing. Record Docker image identity, Tesseract/Pillow versions and protocol externally; changes after test inspection require a new untouched cohort. Do not overwrite generated images while comparing baseline results. Image hashes are verified for the evaluated split. An image error aborts evaluation rather than silently dropping a case.

CER lowercases and collapses whitespace. ID uppercased, money normalized with Decimal, date compared as ISO text (date validity checking is not implemented). Missing extraction is null. OCR timing excludes preprocessing/extraction and is not end-to-end latency. No confidence calibration, human-review workflow, ML fine-tuning, Thai OCR or damage detection yet.

Next: use dev failures to design stronger extraction/validation and a review queue; freeze choices before test. No 100% pilot result belongs in a real-world accuracy claim.

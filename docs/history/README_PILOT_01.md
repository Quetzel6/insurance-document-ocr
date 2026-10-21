> Historical development note. For current commands and verification scope, start with [README](../../README.md). Counts and pending items below describe that stage.

# Synthetic Insurance Document OCR — Pilot 0.1

A personal portfolio project for document extraction and human review. No actual insurance claims, personal identifiers or customer data are used. English-only printed synthetic documents; no model training/fine-tuning, Thai OCR, handwriting, damage detection or production deployment is implemented.

## Implemented
- Deterministic generation of 9 original documents across 3 layout templates, with clean/blur/rotation variants (27 images).
- Template and original-document disjoint train/dev/test assignments before augmentation. Train is reserved, not used to train Tesseract.
- Tesseract CLI OCR, raw versus fixed grayscale/autocontrast/threshold preprocessing using Pillow. Recognition receives only the image, not ground-truth text/fields or the known rotation.
- Regex field extraction for synthetic document ID, ISO date and amount. Missing matches stay null. Amount normalized with Decimal; ID uppercased; date exact string.
- Normalized character error rate (lowercase, collapsed whitespace), per-field match, all-three-fields document match and OCR-only timing. Timing excludes preprocessing and extraction; it is not end-to-end latency.
- Image hashes checked before evaluation; per-image predictions and OCR text retained in output/benchmark.json.

## Actual pilot results
Executed with local Tesseract on 13 October 2026. Both methods had normalized CER 0 and all three fields correct on all 9 dev and 9 test images. Each split has only 3 independent originals; its 9 variants are correlated, not 9 independent cases. Unit tests: 3 passed.

**This dataset is too small/easy to establish OCR quality or benefit from preprocessing.** These are smoke-test results, not real-world insurance accuracy. The layouts differ mainly in spacing/order; fonts and labels remain shared. No statistical significance, learned generalization or fine-tuning success is claimed. The test cohort has now been inspected: further development must use a new frozen test cohort to avoid tuning to this one.

## Reproduce on Mac with Docker
Docker avoids changing the host Python environment. The provided Dockerfile was not built in the author's execution environment; local verification was pending at that stage. It installs Tesseract/English language data and DejaVu font. Runtime package/image versions can differ; the included measured report records Tesseract and source-image manifest checksums. Image reproduction across environments requires the same font and Pillow version, not only the same seed.

From this project's directory, run separately:
```bash
docker build -t insurance-document-ocr:pilot .
docker run --rm -v "$PWD:/work" insurance-document-ocr:pilot python -m unittest discover -s tests -v
docker run --rm -v "$PWD:/work" insurance-document-ocr:pilot python project.py generate --font /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
docker run --rm -v "$PWD:/work" insurance-document-ocr:pilot python project.py benchmark
```
The generator overwrites its known generated files and manifest; evaluation overwrites output/benchmark.json. Preserve the bundled baseline report separately before rebuilding if comparing environments. Do not put real documents in data/.

Alternatively install Python dependencies and a local Tesseract binary, then use project.py with a supplied TTF font. Official docs: https://tesseract-ocr.github.io/tessdoc/Installation.html and https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html.

## Next acceptance milestone
1. Expand document families, field labels, fonts and independent originals; include challenging capture effects and unreadable/ambiguous fields.
2. Define extraction behavior and image preprocessing using development data only; freeze protocol and create a separate untouched test set.
3. Evaluate on matched cohorts and report per-condition failures, CER and field exact match. Do not force preprocessing to win or silently discard failures.
4. Add schema/date/amount validation and human-review behavior. Validation flags format errors but does not prove OCR text is correct.
5. Build a small demo and role-specific project narrative after that benchmark; the pilot's 100% result does not establish business accuracy.

This is a foundation for an OCR portfolio, not yet a completed Computer Vision Engineer qualification. Implementation claims cover (Python, Pillow, Tesseract, evaluation), not OpenCV/YOLO/PyTorch experience that has not been demonstrated.

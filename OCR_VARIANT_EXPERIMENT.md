# Blur and shadow OCR experiment — 2026-10-16

Decision: keep the deployed recognizer unchanged. None of the three
alternatives improved complete field recovery on this development cohort.

| Method | Complete fields, all images | Complete fields, blur | Overall normalized CER |
| --- | ---: | ---: | ---: |
| Current illumination correction + deskew, PSM 6 | 30/40 | 0/10 | 2.60% |
| Same preparation, sparse PSM 11 | 30/40 | 0/10 | 2.99% |
| Original grayscale, PSM 6 | 10/40 | 0/10 | 28.67% |
| Prepared image + Otsu threshold, PSM 6 | 30/40 | 0/10 | 8.04% |

Current preparation recovered all fields on the 10 shadow variants in this
cohort. That is not evidence that all real shadows are handled. Original
grayscale emitted one wrong date and two wrong amounts on skewed variants.
Other methods emitted no wrong structured values here but still left values
missing, especially on blur. Valid syntax is not a correctness guarantee.

All methods use the same extraction_candidate parser. Recognition changes
are therefore compared without changing extraction rules or guessing digits.
Detailed field errors, OCR text, software versions, English language-data
hash and source hashes are in experiments/ocr_variants_20261016/report.json.
The summary is in the adjacent results.md.

## Reproduce

From the repository directory using the existing Docker environment:

    docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python ocr_variant_experiment.py --out /work/ocr_variant_runs/run-01

Use a new output directory for each run. The script refuses to overwrite
evidence. Its measured report was generated in the assistant's Linux
environment with Tesseract 5.3.4, Pillow 12.3.0 and Python 3.12.14, not on
the user's Mac/Docker environment. Reproductions may differ across versions.
The frozen project.py, challenge.py, enhanced.py, manifest and recorded
enhanced test report are checked before and after the run and not changed.
No test images/labels are evaluated. Normalized CER lowercases/collapses
whitespace; it does not count punctuation or case in the original way.

## Limits and next experiment

The 40 development variants represent only 10 correlated synthetic originals
in two layouts, with shared fonts and labels. This is previously inspected
development data. It is not a new untouched test, Thai evaluation, real
insurance benchmark, speed comparison or model training. Do not treat the
absence of wrong emitted fields in this small cohort as calibrated safety.

Next: compare a new recognition approach on separate development originals
with a broader range of fonts, capture resolutions and blur/shadow levels.
Select a method and freeze software/data before evaluating a new untouched
test cohort. Record wrong emitted digits as well as missing values. Do not
promote an image enhancement or automatic number repair without evidence.

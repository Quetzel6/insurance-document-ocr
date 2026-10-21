# Pinned tessdata_best comparison — 2026-10-16

Decision: record the candidate's modest text improvement, but keep the
application default unchanged. Test complete-field recovery did not improve
and strongly blurred values remain unresolved. No automatic number repair.

| Split / weights | Complete ID + Date + Amount | Normalized CER |
| --- | ---: | ---: |
| Dev / installed | 16/24 | 17.72% |
| Dev / tessdata_best | 18/24 | 16.81% |
| Test / installed | 18/24 | 13.07% |
| Test / tessdata_best | 18/24 | 11.31% |

The candidate was selected on dev and frozen before the single test run.
Both models recovered complete fields on 0/6 strong-blur test variants.
Neither emitted wrong structured values on this small cohort; missing
values still prevent full recovery. This is not a calibrated error bound.

## What changed

Only the English recognition weights differ. Both use the same installed
Tesseract engine, enhanced image preparation, LSTM OEM 1, PSM 6 and unchanged
extraction_candidate. This is not a comparison with an independent OCR
engine or a fine-tuned model. The candidate is upstream tessdata_best:

- Source: https://github.com/tesseract-ocr/tessdata_best
- Pinned commit: e12c65a915945e4c28e237a9b52bc4a8f39a0cec
- eng.traineddata SHA-256: 8280aed0782fe27257a68ea10fe7ef324ca0f8d85bd2fd145d1c2b560bcb66ba
- Upstream license: Apache-2.0; model binary is not redistributed here.

The installed English model SHA-256 was
7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2.
The runner rejects a candidate with a different hash, identical model
weights, or source/manifest/model changes after freezing.

## Dataset and limits

A fresh seed (2026101607) creates new document values and originals, field
orders, positions and font sizes. There are 12 English synthetic originals,
six per split, with clean/mild-blur/strong-blur/shadow variants: 24 dev and
24 test. Three font families are shared across splits. These variants are
correlated and do not represent real captures, new font families or Thai.
Preparation and scoring never use the expected labels during recognition.
Test is now inspected: future tuning requires another untouched cohort.

Evidence in experiments/model_cohort_20261016 records image/font hashes,
per-image output, missing versus wrong fields, frozen protocol and software
versions. Images are generated deterministically and not committed. Matching
image hashes requires matching font binaries and Pillow version. The measured
environment is development Linux/Tesseract 5.3.4, not Mac/Docker.
No latency or real-world accuracy improvement is claimed. CI checks code
guards and the app; it does not download models or repeat full OCR.

## Reproduce

From the repository directory, download the pinned model explicitly:

    mkdir -p .ocr_models/tessdata_best
    curl -fL --retry 2 -o .ocr_models/tessdata_best/eng.traineddata https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/e12c65a915945e4c28e237a9b52bc4a8f39a0cec/eng.traineddata

The runner verifies its SHA-256 before OCR. Use a new output directory:

    docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python model_ocr_experiment.py generate --dir /work/ocr_model_runs/run01
    docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python model_ocr_experiment.py dev --dir /work/ocr_model_runs/run01 --best-dir /work/.ocr_models/tessdata_best
    docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python model_ocr_experiment.py freeze --dir /work/ocr_model_runs/run01 --best-dir /work/.ocr_models/tessdata_best --selected tessdata_best
    docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python model_ocr_experiment.py test --dir /work/ocr_model_runs/run01 --best-dir /work/.ocr_models/tessdata_best

This reproduces an inspected cohort, not a new untouched test. Output files
and freeze records cannot be overwritten. Models and local run outputs are
ignored by Git. Keep human review for uncertain values; improved CER alone
does not justify automatic approval or decimal/digit substitution.

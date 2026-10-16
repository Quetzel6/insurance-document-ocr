# Independent RapidOCR engine: development screening — 2026-10-16

Decision: retain the application's Tesseract default. RapidOCR's page text
is modestly better in aggregate on this dev cohort, but complete structured
field recovery is not better after accounting for joined-label formatting.
Strong blur still yields no complete document. No model training or deploy.

## Engine comparison with the same existing extractor

| Method | Complete ID + Date + Amount | Normalized CER |
| --- | ---: | ---: |
| Tesseract current preparation | 18/24 | 15.42% |
| RapidOCR on original image | 12/24 | 14.74% |
| RapidOCR on current prepared image | 9/24 | 18.09% |

This compares RapidOCR's PP-OCRv4 detection/recognition pipeline with
Tesseract, rather than just changing Tesseract weights. RapidOCR uses its
bundled Chinese/English models, orientation classifier, default text_score
0.5 and CPU with intra_op_num_threads=2 / inter_op_num_threads=1. No Thai
model is evaluated. Output order and segment scores are retained as returned
by the package. Scores are not calibrated probabilities of correctness.

## Separate label-only replay on development text

Several missing IDs were caused by text such as DocumentID:SYN-123456,
where the existing parser requires a space in Document ID. A separate
experimental parser inserts that space only in a line-start label followed
by a visible colon/equal. It does not alter values, infer a decimal, repair
digits or rewrite the stored OCR text. The same rule is applied to all
engines; no OCR is rerun for the replay.

| Method after joined-label parser | Complete fields | Correct ID / Date / Amount |
| --- | ---: | ---: |
| Tesseract current | 18/24 | 18 / 18 / 18 |
| RapidOCR original | 18/24 | 19 / 19 / 18 |
| RapidOCR prepared | 18/24 | 18 / 19 / 18 |

No wrong structured field was emitted in this limited development cohort.
Missing values remain. Strong-blur complete recovery is 0/6 for every
method. The replay is exploratory parser development, not an independent
recognition gain or evidence of safe automatic approval. Neither the engine
nor parser changes are added to the application.

## Data and provenance

New seed 2026101611: 3 shared font families, 12 synthetic originals, with
6 originals/24 correlated variants per split. Clean, mild blur, strong blur
and shadow are included. Values, sizes, positions and field order differ
between splits. This remains a small synthetic English sample, with shared
fonts and no real capture geometry. It is not a real insurance/Thai benchmark.
The test split has NOT been evaluated or used for method selection. No
frozen_protocol.json is supplied. A future test needs a finalized engine
AND parser protocol, frozen before test. Do not treat this dev replay as test.

Evidence in experiments/rapidocr_cohort_20261016 includes the manifest,
initial dev report, separate joined-label replay and environment/model hashes.
Images are generated, not committed; matching hashes requires the recorded
font binaries and Pillow version. Existing benchmark sources are unchanged.

RapidOCR package version is pinned to rapidocr-onnxruntime 1.4.4. All three
bundled ONNX hashes and config/package versions are verified/recorded before
and after measurement. The exact tested dependency versions are in
requirements-rapid-experiment.txt; these are optional experiment dependencies,
not additions to the running application's requirements.txt. Measurements
are from a separate assistant Linux/Python 3.12 environment. Mac/Docker
compatibility and end-to-end latency have not been established here.

Official source: https://github.com/RapidAI/RapidOCR
Package metadata identifies Apache-2.0. Upstream describes the models as
PaddleOCR-derived. Model binaries are not redistributed in this repository.

## Reproduce in a separate Python 3.12 environment

Requires local Tesseract English data and DejaVu fonts as for earlier runs.

    python3.12 -m venv .venv-rapid
    source .venv-rapid/bin/activate
    python -m pip install -r requirements-rapid-experiment.txt
    python rapidocr_experiment.py generate --dir ocr_model_runs/rapid01
    python rapidocr_experiment.py dev --dir ocr_model_runs/rapid01
    python engine_label_experiment.py ocr_model_runs/rapid01/dev_report.json --out ocr_model_runs/rapid01/dev_label_rescore.json

The files are protected against overwriting. The runner verifies bundled
model hashes and does not call an external OCR service. Do not change the
production environment to run this experiment. CI tests adapter/parser and
protocol guards with mocks; it does not install RapidOCR or repeat full OCR.

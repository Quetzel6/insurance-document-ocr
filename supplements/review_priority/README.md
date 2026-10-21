# OCR review-priority evaluation — 20 October 2026

Separate experimental supplement to the Insurance OCR portfolio. It does not alter the application, existing benchmarks, review databases or default OCR settings. No API key, credits, network request or new model training is involved.

## Measured result (development Linux environment)

| Fixed method | Test complete ID + date + amount | Wrong emitted fields |
| --- | ---: | ---: |
| Raw grayscale input | 11/18 | 0 |
| 2x Lanczos + fixed unsharp mask | 13/18 | 0 |

Twelve new synthetic English originals are split six dev / six test; each has clean, blur/low-resolution and skew variants (18 images per split). Original IDs and the field-order/position layout do not cross splits. Font family and labels are shared. The 18 test images are correlated, not 18 independent documents.

The fixed method/threshold policy is specified before dev recognition. It maximizes coverage with zero observed incorrect prioritized dev extractions, then complete recovery, with fixed tie-breaking. The selected method and evidence hashes are written to `frozen_policy.json` **before test recognition**. Test is evaluated once; no changes were made to the experiment source after observing results.

Dev selected upscale/sharpen with **confidence threshold 0**: 14/18 dev extractions and 13/18 test extractions were complete and exact. This means confidence filtering adds no evidence of value over field completeness on this small cohort. A zero observed error count is not a calibrated error guarantee. All 18 test images remain subject to human verification; there is no automatic approval, measured productivity gain or deployment decision.

Observed missing fields and per-image predictions, confidence and durations are retained in `measured_linux/*_predictions.json`. Neither method emitted a wrong nonmissing field on this small cohort; extraction omissions account for the incomplete cases. This is not evidence that wrong fields cannot occur.

## Open the existing report

Open `measured_linux/report.html` locally, or read `measured_linux/RESULTS.md` and `results.json`. This measured result used Linux, Python 3.12.14, Pillow 12.3.0 and Tesseract 5.3.4; the English model SHA-256 is recorded in the results. It is **not** a Mac/Docker result.

## Reproduce on your Mac using the existing Docker OCR image

From the repository root, keep Docker Desktop running and use the existing OCR image:

```bash
docker run --rm -v "$PWD:/work" -w /work/supplements/review_priority insurance-document-orc:pilot python -m unittest discover -s tests -q
docker run --rm -v "$PWD:/work" -w /work/supplements/review_priority insurance-document-orc:pilot python experiment.py run --dataset dataset --out mac_run_01
open supplements/review_priority/mac_run_01/report.html
```

Expected: 19 current unit tests (the original suite contained 13). The OCR command performs 72 real Tesseract recognitions (36 images x 2 fixed methods). Results can differ by Pillow/Tesseract/model version. The command refuses to overwrite an existing output directory. Choose `mac_run_02` only for a separate intentional reproduction and preserve the earlier evidence.

If the image is missing, `docker image inspect insurance-document-orc:pilot` will fail; do not rebuild the old application or install a different model just to force a match. Supply the exact error so the existing environment can be checked first. A local installation can also run `python3 experiment.py run --dataset dataset --out local_run_01` if Pillow and the Tesseract executable/English model are installed.

The bundled cohort is now inspected. Repeating its evaluation checks reproducibility across environments; it is **not a new untouched test**, and must not be used to tune methods while retaining the original held-out claim. Use a separately authored, untouched cohort for future tuning or broader generalization.

## Verification coverage

The original 13 unit tests cover invalid dates, avoiding digit guessing, incomplete-field rejection, missing confidence, undefined risk for empty priority groups, high-confidence wrong values, method-specific denominators, TSV word-confidence parsing, dev-policy selection, original-document leakage, changed-image detection and refusal to overwrite evidence. These code tests are distinct from the 72 actual OCR calls recorded in this release.

Recognition receives image pixels/path and fixed method only. Expected labels and degradation conditions are used afterwards for scoring, not passed into recognition. Both methods use identical extraction rules and the same installed English model with OEM 1 / PSM 6. The script fingerprints code, manifest, image bytes and runtime/model identity, and checks evidence consistency around evaluation. This is reproducibility evidence, not tamper-proof attestation.

## Capabilities and limits

- **Computer vision and data engineering:** image preprocessing, use of an existing neural OCR recognizer, structured field extraction, reproducible experimental protocol and validation. Not a trained custom computer-vision model, a factory connector, TensorFlow/PyTorch implementation or professional experience tenure.
- **Document review and operations:** a measured document-review use case, explicit risk/coverage analysis and human-review boundary. Not GenAI, agentic AI, actual adoption or quantified business benefit.
- No Thai documents, handwriting, tables, real insurance/logistics records, unseen font families or production-scale evaluation. All data are synthetic.
- Tesseract mean word confidence is not a probability of correct ID/date/amount. Source-matched fields and complete fields still need checking against the image.

## References

Official Tesseract TSV/engine options:
https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html

Methods use pretrained installed English weights and a fixed image transformation; this is inference/evaluation, not model training. Upstream Tesseract: Apache-2.0; Pillow: HPND. No model or font binaries are redistributed in this ZIP. Synthetic rendered images, code and test evidence are included.

## Additional frozen-policy font/layout challenge

The earlier policy was applied unchanged to [36 new images from 12 authored originals](challenge_font_dataset/manifest.json), using two different font files and changed field layouts. [Protocol](CHALLENGE_PROTOCOL.md) and source were committed before recognition. On the development Linux host, the earlier upscale/sharpen policy had **18/36 complete exact extractions and 6 wrong emitted fields**; raw input had **22/36 complete exact extractions and 7 wrong emitted fields**. These are a new cohort and descriptive comparison, not a demonstrated improvement or a reason to retune this cohort.

The selected policy was complete and exact on 12/12 clean, 5/12 low-resolution and 1/12 skew images. The 6 wrong emitted fields were dates in incomplete records. Raw input also produced one complete-but-incorrect extraction. Completeness and syntactic date validity are insufficient for automatic acceptance. All images still require human review. [Recorded results and failures](measured_font_challenge/RESULTS.md) | [Business interpretation](CHALLENGE_FINDINGS.md).

To reproduce with the existing Docker image, from the repository root:

```bash
docker run --rm -v "$PWD:/work" -w /work/supplements/review_priority insurance-document-orc:pilot python -m unittest discover -s tests -v
docker run --rm -v "$PWD:/work" -w /work/supplements/review_priority insurance-document-orc:pilot python challenge_eval.py run --dataset challenge_font_dataset --out mac_font_challenge_01
```

Expected: 19 tests, then actual OCR calls. Never overwrite an existing result; use a new directory for a deliberate repeat. The current 19-test suite passed on development Linux and in [CI](https://github.com/Quetzel6/insurance-document-orc/actions/runs/39538383242). The author reported the same 18/36 and six wrong-field summary from Docker on a Mac; see [transcribed author evidence](AUTHOR_VERIFICATION_M6.json). The new 19-test suite was not reported from the author Mac terminal. Container versions and image ID were not supplied with that report. Original experiments and application defaults are unchanged.

# Frozen-policy font/layout challenge

Protocol authored 21 October 2026, before the first OCR run on this cohort.

## Question and fixed decision

How does the earlier dev-selected policy perform on newly generated document values, different font files and changed field positions? Apply `measured_linux/frozen_policy.json` unchanged: 2x Lanczos plus the existing fixed unsharp mask, threshold 0, same Tesseract English weights and extraction rules. Raw is a descriptive comparator. There is no reselection, tuning, acceptance threshold or new model training on this cohort.

## Authored cohort

- Seed 2026102101; 12 new synthetic English originals.
- Two font files: DejaVuSerif.ttf and DejaVuSansMono.ttf. Their hashes must differ from each other and the original font file.
- Three correlated variants per original: clean, fixed low resolution/blur, and +/-7 degree skew. Total 36 images, not 36 independent originals.
- New document IDs do not overlap the earlier cohort. Field labels and valid ID/date/amount formats remain shared. Three field orders and changed margins/spacing are specified in the generator.
- Same developer-authored labels and generator, not an independently collected dataset or human adjudication.

## Measurement

Primary: complete exact document ID, date and amount for the earlier selected policy. Also retain wrong emitted fields, omitted fields, descriptive raw comparison and selected-policy breakdowns by font and degradation. All images require human review even when complete. Mean word confidence is a heuristic, not a calibrated probability.

The manifest freezes source, old policy, original cohort, image and font hashes. `frozen_protocol.json` records runtime/model identity and the manifest hash before the first recognition call. Recognition receives pixels and a method only; expected values are used afterwards for scoring. Both methods use the same installed model, OEM 1 and PSM 6. Later repeats check reproducibility, not a new untouched test.

No result is promised to improve on the earlier 13/18 result. Cohorts differ; rates must not be pooled or treated as a controlled before/after improvement. This is a synthetic challenge, not real-document or Thai accuracy, production readiness or business impact.

## Reproduce

From `supplements/review_priority`, with Pillow, Tesseract English and fonts-dejavu-core installed:

```bash
python challenge_eval.py generate --dataset challenge_font_dataset
python challenge_eval.py run --dataset challenge_font_dataset --out challenge_font_run
```

Existing output is never overwritten. Keep both generated data and outputs from the first run. Original `experiment.py`, its cohort, measured results and the application's defaults remain intact. Do not edit the protocol to chase a score after inspecting this challenge.

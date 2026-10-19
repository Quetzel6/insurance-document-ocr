# Amount crop OCR experiment (2026-10-19)

Decision: retain page_current. This isolated experiment does not change Image Reader, Review Desk, extraction rules, requirements, frozen benchmark sources or auto-approval behavior.

## Method

Page OCR uses the existing illumination/deskew preparation and Tesseract English PSM 6. A separate TSV pass locates exactly one line whose first word is Amount/Amourt/Arnrourt/Ammourt. The candidate crops the union of subsequent word boxes, upsamples 3x with Lanczos and adds a white border. PSM 7 and PSM 13 numeric-whitelist OCR are compared separately. Only a syntactically valid decimal result replaces the amount line; otherwise baseline text is retained. Expected values, template positions and filenames are not provided to the recognizer. A valid-looking crop result can still contain wrong digits.

## Evaluation

A new seed 20261019 generates six originals per split, three shared font families, and clean/mild blur/strong blur/shadow variants: 24 dev and 24 test images. Field order, position and sizes differ by split. Dev results tied at 18/24 complete, so page_current was frozen before test. All three fixed methods were then scored once on test.

| Test method | Complete ID/date/amount | Wrong amounts emitted | CER |
| --- | ---: | ---: | ---: |
| page_current | 18/24 | 0 | 12.25% |
| amount_crop_7 | 15/24 | 3 | 12.33% |
| amount_crop_13 | 18/24 | 0 | 12.25% |

PSM 7 introduced wrong amounts in three correlated variants. PSM 13 offered no improvement. All methods failed complete extraction on the six strong-blur variants. The previously observed t4-2-blur_lowres case was also checked diagnostically after protocol freeze: neither crop supplied a valid amount. That observed case is not held-out evidence and is not part of these scores.

## Reproduction

Run in the repository's OCR environment with Pillow, Tesseract English and DejaVu fonts:

    python amount_ocr_experiment.py generate --dir /tmp/amount-reproduction
    python amount_ocr_experiment.py dev --dir /tmp/amount-reproduction
    python amount_ocr_experiment.py freeze --dir /tmp/amount-reproduction --selected page_current
    python amount_ocr_experiment.py test --dir /tmp/amount-reproduction

The existing output directory is refused on generate, reports cannot be overwritten, and protocol/source/manifest/dev report fingerprints are checked before test. Recorded evidence is in experiments/amount_cohort_20261019. Generated images are reproducible and not committed; hashes and font hashes are recorded. Equivalent font files and Pillow version are needed for identical pixels.

## Limits

Synthetic English only; six independent originals per split, with correlated variants and shared font families. This is not real-world, Thai, handwriting or held-out-font validation. Split separation is procedural; labels are present for scoring/reproduction. Measured in assistant Linux, not user Mac/Docker. The numeric locator depends on recognizing a supported Amount label; failed/misrecognized labels can prevent a crop. Whitelisting does not establish confidence or correctness. No model was trained. No private images, reviewer names or decisions exports are committed.

Four deterministic tests cover missing/duplicate labels, decimal refusal, amount-only replacement and image-box localization. They do not assert that OCR itself is accurate. CI reruns tests and original benchmark checks; it does not regenerate these OCR experiment scores.

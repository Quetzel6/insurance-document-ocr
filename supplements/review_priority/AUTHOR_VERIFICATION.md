# Author-provided Docker/Mac verification — 20 October 2026

The author ran 13 unit tests with the existing insurance-document-orc:pilot Docker image; all passed. A separate OCR evaluation printed all 18 dev image IDs and all 18 test image IDs. Each image is recognized using two fixed methods (72 recognition calls total).

The supplied selected-policy result: upscale_sharpen; threshold 0; test images 18, originals 6, complete_correct 13, wrong_emitted_fields 0, prioritized 13, incorrect_prioritized 0, priority_coverage 0.7222222222222222, human_review_required 18.

The author did not provide the full mac_run_01 JSON artifacts for inclusion here; preserve those locally. The committed measured_linux files are the development-environment run, not substituted Mac output. No browser appearance certification or real-document generalization is claimed. This reproduces an inspected synthetic cohort and is not a new independent held-out test.

## Font/layout challenge and current test suite - 21 October 2026

Docker on Mac reproduced the frozen policy on 36 images from 12 originals: 18 complete exact extractions, six wrong emitted fields, and human review required for all 36 images. The current 19-test suite passed in 2.137 seconds with no skips. [Transcribed terminal evidence](AUTHOR_VERIFICATION_M6.json) records the supplied scope. The owner subsequently supplied the five [raw font-challenge artifacts](mac_font_challenge_01/RESULTS.md) in `supplements.zip`. The [artifact verification record](MAC_ARTIFACT_VERIFICATION.json) contains their SHA-256 hashes. All 72 prediction records were checked against the frozen source, dataset and labels; aggregate scores and condition/font breakdowns were recomputed. Extracted fields match the development Linux run for all 72 records, while OCR text differs in two and mean word confidence in 39.

The supplied container fingerprint reports Linux, Python 3.13.16, Tesseract 5.5.0 and Pillow 12.3.0. Linux is expected inside Docker on a Mac; the host context comes from the owner's command and report. The image ID and host OS version remain unavailable. These files substantiate result reproducibility on an inspected cohort, not a new independent accuracy test. The earlier 18-image `mac_run_01` artifacts are still unavailable; that earlier result remains terminal-reported.

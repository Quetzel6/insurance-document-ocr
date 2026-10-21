# Author-provided Docker/Mac verification — 20 October 2026

The author ran 13 unit tests with the existing insurance-document-orc:pilot Docker image; all passed. A separate OCR evaluation printed all 18 dev image IDs and all 18 test image IDs. Each image is recognized using two fixed methods (72 recognition calls total).

The supplied selected-policy result: upscale_sharpen; threshold 0; test images 18, originals 6, complete_correct 13, wrong_emitted_fields 0, prioritized 13, incorrect_prioritized 0, priority_coverage 0.7222222222222222, human_review_required 18.

The author did not provide the full mac_run_01 JSON artifacts for inclusion here; preserve those locally. The committed measured_linux files are the development-environment run, not substituted Mac output. No browser appearance certification or real-document generalization is claimed. This reproduces an inspected synthetic cohort and is not a new independent held-out test.

## Font/layout challenge and current test suite - 21 October 2026

Docker on Mac reproduced the frozen policy on 36 images from 12 originals: 18 complete exact extractions, six wrong emitted fields, and human review required for all 36 images. The current 19-test suite passed in 2.137 seconds with no skips. [Transcribed terminal evidence](AUTHOR_VERIFICATION_M6.json) records the supplied scope. Full Mac output files have not been supplied to this repository; the development Linux files are not relabeled as Mac evidence.

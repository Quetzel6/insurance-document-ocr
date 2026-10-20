# OCR review-priority evaluation

Selected on dev: upscale_sharpen, threshold 0. Policy frozen before test recognition.

| Test method | Complete exact | Wrong emitted fields |
| --- | ---: | ---: |
| raw | 11/18 | 0 |
| upscale_sharpen | 13/18 | 0 |

Selected policy prioritized 13/18 test images; 0 were incorrect complete extractions in that subset. All 18 still require human review.

12 synthetic English originals: six per split, three correlated variants each; shared font family/labels. No Thai, real captures, handwriting or factory documents.

Mean word confidence is a heuristic, not a calibrated probability; small correlated cohort gives no error guarantee.

Reproduction of this now-inspected cohort is not a new untouched test. No real-world benefit, new model training or API use is claimed.

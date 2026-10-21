# New multi-font cohort: dev

| Method | Condition | Images | CER | Complete | Wrong ID/date/amount |
| --- | --- | ---: | ---: | ---: | --- |
| page_current | all | 24 | 14.12% | 18/24 | 0/0/0 |
| page_current | blur_mild | 6 | 0.00% | 6/6 | 0/0/0 |
| page_current | blur_strong | 6 | 56.48% | 0/6 | 0/0/0 |
| page_current | clean | 6 | 0.00% | 6/6 | 0/0/0 |
| page_current | shadow | 6 | 0.00% | 6/6 | 0/0/0 |
| line_upscale | all | 24 | 20.35% | 17/24 | 0/0/0 |
| line_upscale | blur_mild | 6 | 0.11% | 5/6 | 0/0/0 |
| line_upscale | blur_strong | 6 | 81.29% | 0/6 | 0/0/0 |
| line_upscale | clean | 6 | 0.00% | 6/6 | 0/0/0 |
| line_upscale | shadow | 6 | 0.00% | 6/6 | 0/0/0 |

Synthetic English, 6 originals and 24 correlated variants per split, shared 3 font families. Distinct originals/field orders/positions/sizes per split; not held-out font families, real scans or Thai. Strong blur may destroy source detail. Generation and test labels exist for reproducibility; separation is procedural.

Measured in the development Linux environment. No Mac reproduction of this experiment is recorded. Same extractor across methods. No confidence calibration, training or automatic value guessing.

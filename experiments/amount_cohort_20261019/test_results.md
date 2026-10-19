# New multi-font cohort: test

| Method | Condition | Images | CER | Complete | Wrong ID/date/amount |
| --- | --- | ---: | ---: | ---: | --- |
| page_current | all | 24 | 12.25% | 18/24 | 0/0/0 |
| page_current | blur_mild | 6 | 0.00% | 6/6 | 0/0/0 |
| page_current | blur_strong | 6 | 48.99% | 0/6 | 0/0/0 |
| page_current | clean | 6 | 0.00% | 6/6 | 0/0/0 |
| page_current | shadow | 6 | 0.00% | 6/6 | 0/0/0 |
| amount_crop_7 | all | 24 | 12.33% | 15/24 | 0/0/3 |
| amount_crop_7 | blur_mild | 6 | 0.11% | 5/6 | 0/0/1 |
| amount_crop_7 | blur_strong | 6 | 48.99% | 0/6 | 0/0/0 |
| amount_crop_7 | clean | 6 | 0.11% | 5/6 | 0/0/1 |
| amount_crop_7 | shadow | 6 | 0.11% | 5/6 | 0/0/1 |
| amount_crop_13 | all | 24 | 12.25% | 18/24 | 0/0/0 |
| amount_crop_13 | blur_mild | 6 | 0.00% | 6/6 | 0/0/0 |
| amount_crop_13 | blur_strong | 6 | 48.99% | 0/6 | 0/0/0 |
| amount_crop_13 | clean | 6 | 0.00% | 6/6 | 0/0/0 |
| amount_crop_13 | shadow | 6 | 0.00% | 6/6 | 0/0/0 |

Synthetic English, 6 originals and 24 correlated variants per split, shared 3 font families. Distinct originals/field orders/positions/sizes per split; not held-out font families, real scans or Thai. Strong blur may destroy source detail. Generation and test labels exist for reproducibility; separation is procedural.

Measured in assistant Linux environment, not Mac/Docker. Same extractor across methods. Amount crops use page OCR boxes and recognized labels; no expected value or template coordinates enter recognition. No confidence calibration, training or missing decimal inference. Wrong numeric outputs remain possible; experimental only.

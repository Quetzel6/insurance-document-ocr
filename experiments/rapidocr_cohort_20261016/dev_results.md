# Independent engine comparison: dev

| Method | Condition | Images | CER | Complete | Wrong ID/date/amount |
| --- | --- | ---: | ---: | ---: | --- |
| tesseract_current | all | 24 | 15.42% | 18/24 | 0/0/0 |
| tesseract_current | blur_mild | 6 | 0.00% | 6/6 | 0/0/0 |
| tesseract_current | blur_strong | 6 | 61.67% | 0/6 | 0/0/0 |
| tesseract_current | clean | 6 | 0.00% | 6/6 | 0/0/0 |
| tesseract_current | shadow | 6 | 0.00% | 6/6 | 0/0/0 |
| rapid_raw | all | 24 | 14.74% | 12/24 | 0/0/0 |
| rapid_raw | blur_mild | 6 | 7.33% | 2/6 | 0/0/0 |
| rapid_raw | blur_strong | 6 | 49.27% | 0/6 | 0/0/0 |
| rapid_raw | clean | 6 | 2.14% | 4/6 | 0/0/0 |
| rapid_raw | shadow | 6 | 0.23% | 6/6 | 0/0/0 |
| rapid_prepared | all | 24 | 18.09% | 9/24 | 0/0/0 |
| rapid_prepared | blur_mild | 6 | 7.22% | 1/6 | 0/0/0 |
| rapid_prepared | blur_strong | 6 | 61.10% | 0/6 | 0/0/0 |
| rapid_prepared | clean | 6 | 2.03% | 4/6 | 0/0/0 |
| rapid_prepared | shadow | 6 | 2.03% | 4/6 | 0/0/0 |

Synthetic English, 6 originals and 24 correlated variants per split, shared 3 font families. Distinct originals/field orders/positions/sizes per split; not held-out font families, real scans or Thai. Strong blur may destroy source detail. Generation and test labels exist for reproducibility; separation is procedural.

Measured in assistant Linux environment, not Mac/Docker. Same extractor across methods. RapidOCR scores are uncalibrated, not correctness probabilities. No training or automatic value guessing.

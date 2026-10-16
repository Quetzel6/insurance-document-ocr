# Pinned English model comparison: test

| Method | Condition | Images | CER | Complete | Wrong ID/date/amount |
| --- | --- | ---: | ---: | ---: | --- |
| installed | all | 24 | 13.07% | 18/24 | 0/0/0 |
| installed | blur_mild | 6 | 0.00% | 6/6 | 0/0/0 |
| installed | blur_strong | 6 | 52.27% | 0/6 | 0/0/0 |
| installed | clean | 6 | 0.00% | 6/6 | 0/0/0 |
| installed | shadow | 6 | 0.00% | 6/6 | 0/0/0 |
| tessdata_best | all | 24 | 11.31% | 18/24 | 0/0/0 |
| tessdata_best | blur_mild | 6 | 0.00% | 6/6 | 0/0/0 |
| tessdata_best | blur_strong | 6 | 45.24% | 0/6 | 0/0/0 |
| tessdata_best | clean | 6 | 0.00% | 6/6 | 0/0/0 |
| tessdata_best | shadow | 6 | 0.00% | 6/6 | 0/0/0 |

Synthetic English, 6 originals and 24 correlated variants per split, shared 3 font families. Distinct originals/field orders/positions/sizes per split; not held-out font families, real scans or Thai. Strong blur may destroy source detail. Generation and test labels exist for reproducibility; separation is procedural.

Measured in assistant Linux environment, not Mac/Docker. Same extractor across methods. No confidence calibration, training or automatic value guessing.

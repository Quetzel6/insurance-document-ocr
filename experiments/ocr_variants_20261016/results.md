# Development OCR variants

Exploratory English synthetic dev only: 40 variants / 10 correlated originals in two layouts. Existing data have been inspected in prior development. Test split is not run. No new generalization claim, deployment change, digit guessing or model training. Timing is not compared.

| Method | Condition | Images | CER | All fields correct | Wrong ID / date / amount |
| --- | --- | ---: | ---: | ---: | --- |
| current | all | 40 | 2.60% | 30/40 | 0 / 0 / 0 |
| current | blur_lowres | 10 | 10.42% | 0/10 | 0 / 0 / 0 |
| current | clean | 10 | 0.00% | 10/10 | 0 / 0 / 0 |
| current | shadow | 10 | 0.00% | 10/10 | 0 / 0 / 0 |
| current | skew | 10 | 0.00% | 10/10 | 0 / 0 / 0 |
| prepared_sparse | all | 40 | 2.99% | 30/40 | 0 / 0 / 0 |
| prepared_sparse | blur_lowres | 10 | 11.96% | 0/10 | 0 / 0 / 0 |
| prepared_sparse | clean | 10 | 0.00% | 10/10 | 0 / 0 / 0 |
| prepared_sparse | shadow | 10 | 0.00% | 10/10 | 0 / 0 / 0 |
| prepared_sparse | skew | 10 | 0.00% | 10/10 | 0 / 0 / 0 |
| grayscale_block | all | 40 | 28.67% | 10/40 | 0 / 1 / 2 |
| grayscale_block | blur_lowres | 10 | 11.40% | 0/10 | 0 / 0 / 0 |
| grayscale_block | clean | 10 | 0.00% | 10/10 | 0 / 0 / 0 |
| grayscale_block | shadow | 10 | 99.93% | 0/10 | 0 / 0 / 0 |
| grayscale_block | skew | 10 | 3.36% | 0/10 | 0 / 1 / 2 |
| prepared_otsu | all | 40 | 8.04% | 30/40 | 0 / 0 / 0 |
| prepared_otsu | blur_lowres | 10 | 32.17% | 0/10 | 0 / 0 / 0 |
| prepared_otsu | clean | 10 | 0.00% | 10/10 | 0 / 0 / 0 |
| prepared_otsu | shadow | 10 | 0.00% | 10/10 | 0 / 0 / 0 |
| prepared_otsu | skew | 10 | 0.00% | 10/10 | 0 / 0 / 0 |

All methods use extraction_candidate unchanged. Missing/wrong predictions are separate in report.json.
Environment: tesseract 5.3.4; Pillow 12.3.0; Python 3.12.14. Not the user Mac/Docker environment.

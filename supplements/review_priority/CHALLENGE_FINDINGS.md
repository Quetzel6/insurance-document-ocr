# Interpreting the font/layout challenge

## Observed evidence

Same Tesseract model, extraction rules and earlier selected policy; new synthetic documents, font files and layouts. There was no policy reselection. The protocol/source commit was created before the first recognition. The cohort now becomes inspected; later reruns establish reproducibility only.

| Input method | Complete exact, all fields | Wrong emitted fields | Complete but incorrect prioritized images |
| --- | ---: | ---: | ---: |
| Raw comparator | 22/36 | 7 | 1 |
| Earlier frozen upscale/sharpen policy | 18/36 | 6 | 0 |

The earlier selected policy was not the better method by complete recovery on this new cohort. It remains the prespecified primary policy; raw is not reselected for deployment from this result. There is no single score to pool with the earlier 13/18 cohort.

By degradation, the frozen policy recovered all fields on 12/12 clean, 5/12 low-resolution and 1/12 skew images. These are 3 variants of each of 12 originals, not 36 independent documents.

## Error examples and operational implication

- `challenge-00-skew`: expected 2026-08-20, extracted 2026-08-29. Other fields were missing. A valid-looking calendar date can still be incorrect.
- `challenge-03-skew`: expected 2026-03-19, extracted 5926-03-19. Python calendar parsing accepts that year; business plausibility needs a separately specified date policy.
- `challenge-09-low_resolution`: expected 2026-07-15, extracted 2626-07-15. An amount was present but does not validate the date or the missing ID.

All six wrong emitted fields for the selected policy were dates, in incomplete outputs. The raw comparator also had one complete-but-incorrect output, showing why field completeness cannot authorize automatic approval. The absence of complete-but-wrong selected outputs in this small cohort is not a future error guarantee. Confidence threshold 0 adds no demonstrated confidence-filter benefit.

## Proposed workflow, not demonstrated business savings

1. Present the source image and extracted values side by side to the reviewer.
2. Highlight missing fields and require visual verification of dates, IDs and amounts.
3. Request a better scan or manual correction when unreadable. Keep the original output and an explicit correction history.
4. Any business date-range policy must come from real process requirements; it has not been added merely to fix this benchmark.
5. Treat deskew/recognition changes as a later experiment with separate development and untouched evaluation data. Do not retune this inspected cohort and retain a holdout claim.

This report does not show that a new routing policy or preprocessing change improves review time. The existing review application supports human correction/export, but the challenge itself evaluates the experiment recognizer, not an integrated production UI or a trained custom model. No model, API, Thai-accuracy or business-impact claim is added.

# Frozen-policy OCR font/layout challenge

Apply the previously selected method/threshold unchanged. Raw is a descriptive comparator, never used for reselection.

| Method | Complete exact | Wrong emitted fields |
| --- | ---: | ---: |
| raw | 22/36 | 7 |
| upscale_sharpen | 18/36 | 6 |

## Selected policy by condition

- clean: 12/12 complete exact; 0 wrong emitted fields.
- low_resolution: 5/12 complete exact; 1 wrong emitted fields.
- skew: 1/12 complete exact; 5 wrong emitted fields.

## Observed failures

- challenge-00-low_resolution: expected {"document_id": "SYN-377116", "date": "2026-08-20", "amount": "72605.91"}; observed {"document_id": "SYN-377116", "date": null, "amount": null}
- challenge-00-skew: expected {"document_id": "SYN-377116", "date": "2026-08-20", "amount": "72605.91"}; observed {"document_id": null, "date": "2026-08-29", "amount": null}
- challenge-01-low_resolution: expected {"document_id": "SYN-732115", "date": "2026-02-20", "amount": "13864.08"}; observed {"document_id": "SYN-732115", "date": "2026-02-20", "amount": null}
- challenge-01-skew: expected {"document_id": "SYN-732115", "date": "2026-02-20", "amount": "13864.08"}; observed {"document_id": null, "date": null, "amount": null}
- challenge-02-skew: expected {"document_id": "SYN-605831", "date": "2026-04-14", "amount": "49584.61"}; observed {"document_id": null, "date": "2026-04-14", "amount": null}
- challenge-03-low_resolution: expected {"document_id": "SYN-353560", "date": "2026-03-19", "amount": "24872.35"}; observed {"document_id": null, "date": null, "amount": "24872.35"}
- challenge-03-skew: expected {"document_id": "SYN-353560", "date": "2026-03-19", "amount": "24872.35"}; observed {"document_id": null, "date": "5926-03-19", "amount": null}
- challenge-04-low_resolution: expected {"document_id": "SYN-612384", "date": "2026-09-25", "amount": "49344.56"}; observed {"document_id": "SYN-612384", "date": "2026-09-25", "amount": null}
- challenge-04-skew: expected {"document_id": "SYN-612384", "date": "2026-09-25", "amount": "49344.56"}; observed {"document_id": null, "date": "2026-09-25", "amount": null}
- challenge-05-skew: expected {"document_id": "SYN-833060", "date": "2026-04-28", "amount": "14751.20"}; observed {"document_id": null, "date": "5926-04-28", "amount": "14751.20"}
- challenge-06-low_resolution: expected {"document_id": "SYN-562034", "date": "2026-05-31", "amount": "62120.19"}; observed {"document_id": null, "date": "2026-05-31", "amount": "62120.19"}
- challenge-07-skew: expected {"document_id": "SYN-537431", "date": "2026-01-12", "amount": "2179.32"}; observed {"document_id": null, "date": "5926-01-12", "amount": "2179.32"}
- challenge-08-low_resolution: expected {"document_id": "SYN-927395", "date": "2026-02-02", "amount": "28369.84"}; observed {"document_id": "SYN-927395", "date": "2026-02-02", "amount": null}
- challenge-08-skew: expected {"document_id": "SYN-927395", "date": "2026-02-02", "amount": "28369.84"}; observed {"document_id": null, "date": null, "amount": null}
- challenge-09-low_resolution: expected {"document_id": "SYN-254648", "date": "2026-07-15", "amount": "2704.37"}; observed {"document_id": null, "date": "2626-07-15", "amount": "2704.37"}
- challenge-09-skew: expected {"document_id": "SYN-254648", "date": "2026-07-15", "amount": "2704.37"}; observed {"document_id": null, "date": "3926-07-19", "amount": "2704.37"}
- challenge-10-skew: expected {"document_id": "SYN-202757", "date": "2026-03-19", "amount": "80491.23"}; observed {"document_id": null, "date": "2026-03-19", "amount": "80491.23"}
- challenge-11-skew: expected {"document_id": "SYN-602548", "date": "2026-03-23", "amount": "1884.29"}; observed {"document_id": "SYN-602548", "date": null, "amount": "1884.29"}

12 newly authored synthetic English originals, 2 different font files, 3 correlated variants each. Same field labels/extractor and developer author. No real scans, Thai, handwriting, tables or independent human benchmark. No new model training or measured business savings.

Fresh authored challenge of an earlier frozen policy. No retuning or best-method selection on this cohort. Later reruns measure reproducibility, not a new untouched test. All images still require human verification.

# OCR analytical pipeline

Run the commands in the root [README](../../README.md). `make pipeline` recognizes the inspected font challenge; `make analytics` loads archived reports without OCR. Both are local and make no remote API calls.

## Tables and grain

| Table | Grain / key | Meaning |
|---|---|---|
| runs | run_id | Report/manifest hashes, cohort, split and execution scope |
| images | cohort_id + image_id | Original, variant condition, font and image hash verification |
| predictions | run_id + image_id + method | OCR text and optional confidence |
| field_results | prediction key + field | Expected and predicted value; correct/wrong/missing |
| review_decisions | review_round + prediction key | Actual exported decision version, status and time |
| review_fields | decision key + field | Actual corrected value and whether it changed |

[DDL](../../sql/analytics/schema.sql) uses foreign keys, non-null constraints and outcome checks. No JSON payload column substitutes for these queryable fields. Empty emitted strings normalize to missing. Field correctness uses exact synthetic labels, not semantic similarity. A review edit is not proof that the new value is correct.

## Six SQL questions

1. Which method recovers all three fields, by cohort and split?
2. Which conditions and fields emit errors or omit values? Error-rate denominator is emitted fields; no emissions yields NULL.
3. Which fields were changed most often in supplied human decisions? With no export this result is empty, not a fabricated zero-error study.
4. Which images have missing fields or lower available OCR confidence? The prospective queue uses predictions only, never hidden expected values or correctness labels.
5. Are all manifest images represented for every declared method?
6. Which complete extractions are nevertheless wrong? This is retrospective evaluation, not an inference-time signal.

SQL lives under [sql/analytics](../../sql/analytics). CSV exports preserve full rows; HTML previews at most 120 rows per query, with full query results in JSON.

## Data quality and failure behavior

Inputs are checked before opening the database: manifest uniqueness, image path containment, available image hashes, exact image/method coverage, three-field schema, lineage, finite confidence and recomputed scores. Historical line/model images are explicitly unavailable; their `image_bytes_verified` flag is zero. The remaining committed image bytes must match their hashes.

All reports load in one SQLite transaction. Repeated report/manifest content produces the same run ID; replay reconciles stored predictions and fields before accepting a duplicate. Dimension conflicts, modified stored values and foreign-key violations fail. An unrelated existing database is rejected. Downstream report failure does not claim the earlier database commit was rolled back.

Every pipeline call creates a new output folder. Source directories and existing output directories are rejected. Integrity and frozen-source hashes are checked. This is batch orchestration in Python, not Airflow/dbt, a distributed warehouse, or a production migration.

To include a real benchmark Review Desk export:

```bash
python -m ocr_analytics.pipeline --review-export /absolute/path/to/decisions.json
```

The export must match a loaded benchmark report hash. Uploaded private-document queues are not supported. Reviewer identities and free-text notes are not copied into analytical tables. A conflicting snapshot for the same review round is rejected; run into a fresh output directory to analyze a newer export. Default demonstration tables contain no fabricated decisions.

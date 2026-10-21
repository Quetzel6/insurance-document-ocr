PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(
 run_id TEXT PRIMARY KEY, cohort_id TEXT NOT NULL, report_sha TEXT NOT NULL,
 manifest_sha TEXT NOT NULL, split TEXT NOT NULL, scope TEXT NOT NULL,
 UNIQUE(run_id,cohort_id));
CREATE TABLE IF NOT EXISTS images(
 cohort_id TEXT NOT NULL, image_id TEXT NOT NULL, original_id TEXT NOT NULL,
 split TEXT NOT NULL, condition TEXT NOT NULL, font TEXT,
 image_sha TEXT NOT NULL CHECK(length(image_sha)=64), image_bytes_verified INTEGER NOT NULL CHECK(image_bytes_verified IN (0,1)),
 PRIMARY KEY(cohort_id,image_id));
CREATE TABLE IF NOT EXISTS predictions(
 run_id TEXT NOT NULL, cohort_id TEXT NOT NULL, image_id TEXT NOT NULL,
 method TEXT NOT NULL, ocr_text TEXT NOT NULL, confidence REAL,
 PRIMARY KEY(run_id,image_id,method),
 FOREIGN KEY(run_id,cohort_id) REFERENCES runs(run_id,cohort_id),
 FOREIGN KEY(cohort_id,image_id) REFERENCES images(cohort_id,image_id),
 CHECK(confidence IS NULL OR confidence BETWEEN 0 AND 100));
CREATE TABLE IF NOT EXISTS field_results(
 run_id TEXT NOT NULL, image_id TEXT NOT NULL, method TEXT NOT NULL,
 field TEXT NOT NULL CHECK(field IN ('document_id','date','amount')),
 expected_value TEXT NOT NULL CHECK(length(expected_value)>0), predicted_value TEXT,
 outcome TEXT NOT NULL CHECK(outcome IN ('correct','wrong','missing')),
 PRIMARY KEY(run_id,image_id,method,field),
 FOREIGN KEY(run_id,image_id,method) REFERENCES predictions(run_id,image_id,method),
 CHECK((outcome='missing' AND predicted_value IS NULL) OR
       (outcome='correct' AND predicted_value IS NOT NULL AND predicted_value=expected_value) OR
       (outcome='wrong' AND predicted_value IS NOT NULL AND predicted_value<>expected_value)));
CREATE TABLE IF NOT EXISTS review_decisions(
 review_round TEXT NOT NULL, run_id TEXT NOT NULL, image_id TEXT NOT NULL, method TEXT NOT NULL,
 version INTEGER NOT NULL CHECK(version>0), status TEXT NOT NULL CHECK(status IN ('approved','rejected','needs_review')),
 saved_at TEXT NOT NULL,
 PRIMARY KEY(review_round,run_id,image_id,method),
 FOREIGN KEY(run_id,image_id,method) REFERENCES predictions(run_id,image_id,method));
CREATE TABLE IF NOT EXISTS review_fields(
 review_round TEXT NOT NULL, run_id TEXT NOT NULL, image_id TEXT NOT NULL, method TEXT NOT NULL,
 field TEXT NOT NULL CHECK(field IN ('document_id','date','amount')), corrected_value TEXT NOT NULL,
 changed INTEGER NOT NULL CHECK(changed IN (0,1)),
 PRIMARY KEY(review_round,run_id,image_id,method,field),
 FOREIGN KEY(review_round,run_id,image_id,method) REFERENCES review_decisions(review_round,run_id,image_id,method));
CREATE INDEX IF NOT EXISTS field_method_outcome ON field_results(run_id,method,outcome);

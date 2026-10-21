-- Retrospective evaluation: completeness is not correctness, even when confidence is high.
WITH documents AS (
 SELECT run_id,image_id,method,SUM(predicted_value IS NULL) AS missing,SUM(outcome='wrong') AS wrong
 FROM field_results GROUP BY run_id,image_id,method
)
SELECT r.cohort_id,r.split,d.run_id,d.method,COUNT(*) AS images,
 SUM(missing=0) AS complete,SUM(missing=0 AND wrong>0) AS complete_but_wrong
FROM documents d JOIN runs r USING(run_id)
GROUP BY r.cohort_id,r.split,d.run_id,d.method;

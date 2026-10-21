-- Uses only observed predictions/confidence. Never uses expected values or outcome labels.
-- All images require review. This missing-field heuristic is not a validated time-saving policy.
SELECT r.cohort_id,r.split,p.run_id,p.image_id,p.method,
 SUM(f.predicted_value IS NULL) AS missing_fields,p.confidence
FROM predictions p JOIN runs r USING(run_id)
JOIN field_results f USING(run_id,image_id,method)
GROUP BY p.run_id,p.image_id,p.method
ORDER BY missing_fields DESC,(p.confidence IS NULL) DESC,p.confidence,p.run_id,p.image_id,p.method;

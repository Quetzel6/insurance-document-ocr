-- Exact document recovery, separately for each cohort/split/run and method.
WITH documents AS (
 SELECT run_id,image_id,method,MIN(outcome='correct') AS exact
 FROM field_results GROUP BY run_id,image_id,method
)
SELECT r.cohort_id,r.split,d.run_id,d.method,COUNT(*) AS images,SUM(exact) AS complete_exact,
 ROUND(100.0*SUM(exact)/COUNT(*),2) AS exact_percent
FROM documents d JOIN runs r USING(run_id)
GROUP BY r.cohort_id,r.split,d.run_id,d.method ORDER BY r.cohort_id,r.split,d.method;

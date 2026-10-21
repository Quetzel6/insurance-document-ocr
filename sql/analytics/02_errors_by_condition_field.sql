-- Missing and wrong emitted values have separate denominators.
SELECT r.cohort_id,r.split,f.run_id,f.method,i.condition,f.field,COUNT(*) AS expected_fields,
 SUM(f.outcome='missing') AS missing,SUM(f.outcome='wrong') AS wrong_emitted,
 ROUND(100.0*SUM(f.outcome='wrong')/NULLIF(SUM(f.outcome<>'missing'),0),2) AS wrong_percent_of_emitted
FROM field_results f JOIN runs r USING(run_id)
JOIN images i ON i.cohort_id=r.cohort_id AND i.image_id=f.image_id
GROUP BY r.cohort_id,r.split,f.run_id,f.method,i.condition,f.field;

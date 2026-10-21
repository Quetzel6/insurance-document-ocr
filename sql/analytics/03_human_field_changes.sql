-- Latest exported decision per review round; edits are not proof of correctness.
SELECT r.cohort_id,r.split,f.field,d.status,COUNT(*) AS reviewed_fields,SUM(f.changed) AS changed_fields
FROM review_fields f JOIN review_decisions d USING(review_round,run_id,image_id,method)
JOIN runs r USING(run_id)
GROUP BY r.cohort_id,r.split,f.field,d.status ORDER BY changed_fields DESC;

-- One prediction per manifest image per method is required by the loader.
SELECT r.cohort_id,r.split,r.run_id,p.method,COUNT(*) AS predictions,
 COUNT(DISTINCT p.image_id) AS unique_images,COUNT(DISTINCT i.original_id) AS originals
FROM predictions p JOIN runs r USING(run_id)
JOIN images i ON i.cohort_id=p.cohort_id AND i.image_id=p.image_id
GROUP BY r.cohort_id,r.split,r.run_id,p.method;

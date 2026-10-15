# Next OCR experiment protocol

Status: proposed experiment; no new OCR results measured.

1. Export current human decisions and run analyze_reviews.py. Keep the exported JSON and analysis locally. Use current approved, text-confirmed decisions as error examples, not unquestioned truth.
2. Treat the inspected v0.3 test cohort and its corrections as development evidence from now on. Preserve the original v0.3 frozen reports and scores.
3. Create new independent originals with separate dev and test layouts before augmentation. Increase fonts, labels and capture variability. Do not split augmented versions of the same original across cohorts. Include ambiguous and unreadable examples.
4. Improve image preprocessing and label extraction using dev only. Compare the frozen baseline and candidate on the same new dev images. Report recognition CER separately from field extraction exact match. Do not replace numeric characters without image evidence.
5. Before viewing new test outputs, freeze candidate source hashes, dataset/image hashes, environment, selected method and extraction contract. Predefine reported metrics: CER, per-field exact match, all-field match, missing/ambiguous extraction counts, per-condition failures and number of independent originals. Use consistent timing boundaries if comparing latency.
6. Evaluate new test once and retain every case. If results inform more changes, that cohort becomes development evidence and a further untouched test cohort is required.
7. Automatic acceptance needs a separately validated decision policy. Valid syntax and human correction frequency alone do not establish safe acceptance or calibrated confidence. Keep human review for now.

Corrections such as Amourt -> Amount or 1D -> ID can inform contextual label handling. Do not add unrestricted whole-document replacement rules, and do not count extraction-only improvements as better recognition. The analyzer does not generate rules or train a model.

# Finish the frozen OCR portfolio

Run build_review.py AFTER dev, freeze and test. It checks frozen source/manifest hashes and both report fingerprints, reads actual local results and builds review/index.html. It does not change project.py/challenge.py/enhanced.py or rerun OCR. Display PNG copies are separate from the hashed original BMPs. JavaScript filters error cases offline.

From the actual user's project directory:
```bash
docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python build_review.py
open review/index.html
```
If fingerprint validation fails, do not rerun freeze to conceal a mismatch. Investigate which source/report changed. Preserve original benchmark evidence.

## Repository presentation
README should lead with the question: can image preparation and conservative extraction improve this synthetic document cohort, and where does it fail? Show baseline/comparator/selected-method results; dataset, split rules, frozen evaluation and failure examples; installation; and scope limits.
The old Pilot README describes an earlier cohort. Do not claim that its perfect smoke-test result is the current challenging benchmark. Use the local summary.json for current numbers. Store measured reports, frozen protocol and environment files; never commit customer documents.

## Interview story
Business scenario: document entry needs accurate IDs, dates and amounts. I created synthetic documents, kept originals/templates separated across splits, compared raw OCR and threshold preprocessing, then improved illumination and deskew based on dev failures. I separately measured extraction changes so regex improvement was not mistaken for better OCR. After freezing the code and manifest, I ran test. On my reported test cohort, enhanced extracted all three fields correctly on 30/40 variants versus 10/40 for raw, with normalized CER 2.12% versus 27.45%. This cohort contains only 10 originals and shared English labels/fonts. Blur remained a complete document-level failure; I would require review rather than claim reliable automation. I have not fine-tuned a model or built damage detection.

## Dhipaya application scope
Project demonstrates Python, image processing, OCR, synthetic dataset preparation and comparative evaluation. It does not yet demonstrate OpenCV, YOLO, PyTorch, TensorFlow, learned computer vision or model research beyond baseline evaluation. Keep those claims out of a resume until implemented. Apply as intern or full-time only according to the actual opening and your availability. Job salary expectations do not automatically apply to internships.

## Next after benchmark closure
Add a real review workflow as a new application feature with explicit rules and validation; do not infer a confidence threshold from inspected test results. Any model/preprocessing tuning requires a new untouched test cohort. A demo showing errors is more defensible than presenting only successful documents.

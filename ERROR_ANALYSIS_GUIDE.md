# Analyze your review corrections

This update adds error analysis to the v0.5 app. It does not change recognition, predictions, saved decisions or the frozen benchmark.

1. In Review Desk, save corrected examples after checking the image. For approved text corrections, tick the confirmation checkbox. Reject unreadable content with a reason.
2. Click Export decisions & history. Save the JSON as ocr-review-decisions.json in Downloads.
3. In the application directory run:

```bash
python3 analyze_reviews.py "$HOME/Downloads/ocr-review-decisions.json"
open review_analysis/analysis.md
```

Outputs: review_analysis/analysis.json and analysis.md. The JSON includes the source export SHA-256 so the analysis can be traced to the exact input file. Default output reports are overwritten on rerun; use --out another-directory to retain separate runs.

Counts use latest decisions, not audit events, so repeated saves are not double-counted. The report counts approved field edits separately from token edits in approved and explicitly confirmed corrected text. Rejections and unconfirmed text are not used as correction pairs. Older v0.4 decisions without text are counted separately. There are no accuracy percentages or automatic word/digit replacements.

No user correction export was provided during implementation. Tests use temporary artificial examples; their results are not your measured correction counts. Send the exported JSON if you want the actual reviewed errors analyzed here.

Follow NEXT_OCR_EVALUATION.md before changing the recognition pipeline. This analysis is preparation for the next OCR experiment, not proof of improved OCR quality.

PYTHON ?= python3

.PHONY: pipeline analytics test lint verify-frozen docs-check
pipeline:
	$(PYTHON) -m ocr_analytics.pipeline --live
analytics:
	$(PYTHON) -m ocr_analytics.pipeline
test:
	$(PYTHON) -m unittest discover -s tests -v
	cd supplements/review_priority && $(PYTHON) -m unittest discover -s tests -v
verify-frozen:
	$(PYTHON) -c "from ocr_analytics.pipeline import verify_frozen; print('Verified', verify_frozen(), 'frozen files')"
	$(PYTHON) build_review.py
lint:
	$(PYTHON) -m ruff check ocr_analytics scripts tests/test_analytics.py
	$(PYTHON) -m ruff format --check ocr_analytics scripts tests/test_analytics.py

docs-check:
	$(PYTHON) -m scripts.check_evidence_docs
	$(PYTHON) -m scripts.verify_mac_evidence

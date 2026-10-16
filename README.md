# Insurance Document OCR

Local OCR prototype using Python, Tesseract and Pillow.

## Features

- Review Desk: correct text and fields, approve/reject, export decisions
  and history, and reset review rounds.
- Image Reader: upload PNG/JPG/BMP and select English or Thai + English.
- Document, general and sparse text layouts.
- Document ID, date and amount extraction in document mode.
- Review consistency checks and export analysis.

## Setup

Requires Python and Docker. Run from the repository directory:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    docker build -t insurance-document-orc:pilot .
    docker build -f Dockerfile.thai -t insurance-ocr-reader:thai .

## Review Desk

In each new terminal, activate the project environment first:

    source .venv/bin/activate

    python3 review_app.py

Open http://127.0.0.1:8765

Decisions persist in review_state/. Reset archives the previous review
round and starts a new round.

## Image Reader

Run in a separate terminal from the repository directory:

    docker run --rm -p 127.0.0.1:8766:8766 -v "$PWD:/work" insurance-ocr-reader:thai

Open http://127.0.0.1:8766

Images are processed temporarily. Download results to retain them.
Results do not automatically enter the Review Desk queue.

## Review uploaded images

In Document mode, click Download review package after reading OCR. The
package includes the source image and OCR output; keep it private.

Start the separate uploaded-image queue (activate .venv in this terminal):

    source .venv/bin/activate
    python3 review_app.py --uploads --port 8767

Open http://127.0.0.1:8767 and import ocr-review-package.json. Compare the
image, correct both text and fields, approve/reject, and export decisions.
The database is review_state/uploads.sqlite3; it persists images and history.
Reset archives decisions and makes the existing images pending again; it
does not delete stored images. General/sparse text is not supported by this
structured review queue. See UPLOAD_REVIEW_GUIDE.md.

## Verification

    docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python -m unittest discover -s tests -q
    docker run --rm -v "$PWD:/work" insurance-document-orc:pilot python build_review.py

build_review.py verifies recorded reports and frozen fingerprints.
It does not rerun OCR.

## Automated checks

GitHub Actions builds the Docker environments, runs unit tests, verifies
recorded benchmark fingerprints, checks browser JavaScript syntax, and checks
that English and Thai language packs are installed. Language availability
checks do not measure OCR accuracy.

## Documentation

This README describes the consolidated application. Versioned update guides
record earlier development stages; their historical test counts, installation
paths and statements about missing features may no longer apply.

## Limitations

Benchmark images are synthetic. Results do not establish accuracy on real
insurance documents or Thai documents. Thai language installation enables
recognition but does not validate its accuracy.

Human verification is required, especially for dates, IDs and amounts.
Corrections do not automatically train a model.
PDF, handwriting and structured table reconstruction are not supported.

Keep private review databases, exports and uploads outside version control.
See the included guides for workflow details.


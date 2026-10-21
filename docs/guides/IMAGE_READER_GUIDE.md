# Upload a new image for OCR

This standalone local demo accepts PNG/JPG/BMP, up to 10 MiB and 12 megapixels. Select a clear printed-English image, click Read OCR, inspect original text/field suggestions, and download JSON. It does not automatically approve anything or add documents to the existing Review Desk. Images are processed in temporary files, removed after the request. No external OCR service is called. Browser preview/result disappears on reload unless JSON was downloaded.

## Run with your existing Docker image
Extract the package into a NEW folder, then run from that folder:

```bash
docker run --rm -p 127.0.0.1:8766:8766 -v "$PWD:/work" insurance-document-orc:pilot python image_reader.py --host 0.0.0.0
```

Open http://127.0.0.1:8766 (HTTP, not HTTPS). Keep Terminal open; stop with Control-C. Port 8766 keeps the original Review Desk on 8765 separate. The Docker port is published only on host loopback. The app binds all container interfaces for this mapping; do not publish it on a public interface.

Alternatively, with local Tesseract and Pillow installed, run `python3 image_reader.py`; it binds to 127.0.0.1 by default. Python 3.10+ is required. Existing Docker image supplies dependencies; no rebuild is required because the source is mounted.

## What is supported
- Printed English OCR using the existing enhanced illumination/deskew pipeline.
- Experimental extraction of Document ID, Date and Amount under the synthetic project contract. IDs require SYN- plus six digits; dates require ISO or eight compact digits; amounts require a decimal point and two decimal places. Other document types may still produce OCR text but return missing fields.
- Original uploaded-file SHA-256, dimensions, OCR text, suggestions and explicit human-review flag in downloadable JSON.
- Clear error messages for unsupported/corrupt/oversized images, missing Tesseract and OCR failures.

Thai UI/notes do not imply Thai OCR. Thai recognition, handwriting, PDF, multiple files, automatic spelling/number repair, uploads into the persistent review queue and saved decisions are not implemented here. Clearer source images help; lost detail in blurred images cannot be assumed recoverable. Null means no accepted match, not zero. Every output value must be checked against the image.

## Verification
51 unit tests in the originating project passed. JavaScript syntax checked. Live HTTP smoke verified page/session, invalid token rejection, invalid image rejection and one actual image processed with local Tesseract. This is functional verification, not a new accuracy benchmark; no claim of new-document generalization is made. Browser visual/interaction acceptance and Docker execution on a Mac remain to be done. Frozen benchmark code is included unchanged as dependencies, with no report/dataset overwrite.

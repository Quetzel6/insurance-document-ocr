# OCR language and page layout

Stop port 8766 first. Extract into /Users/sierra6/Documents; updates are nested under insurance-ocr-image-reader. Existing Review Desk is unaffected. Restart and hard-reload the page.

English continues to work with insurance-document-orc:pilot. To install Thai support, build the additional Dockerfile from the image-reader directory:

```bash
docker build -f Dockerfile.thai -t insurance-ocr-reader:thai .
docker run --rm -p 127.0.0.1:8766:8766 -v "$PWD:/work" insurance-ocr-reader:thai
```

The build requires the existing local base image and network access for Debian packages. It was not executed in the assistant environment. English-only mode requires no new image. New server reads installed Tesseract languages; Thai+English is disabled until both tha and eng are installed. A direct request for missing Thai returns a clear error; no silent English fallback. Language flags are whitelisted.

Layout options:
- Document: prior enhanced illumination/deskew and single-block PSM 6; experimental synthetic-contract fields are extracted.
- General/table text: grayscale input with automatic page segmentation PSM 3; no invoice fields extracted. It does not reconstruct table cells or guarantee row/column order.
- Sparse text: grayscale input with PSM 11; finds scattered text with no guaranteed reading order. No invoice fields extracted.

These are explicit user-selected alternatives, not an automatic accuracy improvement. For your table image, try General/table and Thai+English once the new image is installed. Download image-ocr-result.json and compare with the original. Current engine may still misread Thai combining marks, small characters, grid lines or numbers. Handwriting/PDF and structured table export remain unsupported.

Reset, single-job limit, responsive page requests and elapsed timings remain. Changing a selector clears previous results so you must rerun OCR; JSON records actual selected language/layout. Source recognition benchmark is unchanged.

Verification: 59 originating-project unit tests passed and JavaScript syntax checked. Actual general English OCR was executed. Thai availability rejection, option forwarding and Unicode handling were tested with mocks; real Thai recognition, new Docker build and user-browser interaction have NOT been tested here. There is no measured Thai accuracy claim.

> Historical development note. For current commands and verification scope, start with [README](../../README.md). Counts and pending items below describe that stage.

# Responsive image reader update

Stop the image-reader Docker process with Control-C, extract this ZIP into /Users/sierra6/Documents, then restart the same image-reader command. Reload the browser to obtain the new JavaScript. Existing Review Desk data and its server are unaffected.

The previous HTTPServer served one connection at a time; idle/preconnected browser sockets and running OCR could delay page/session requests. This update uses ThreadingHTTPServer and socket read timeouts. OCR is restricted to one concurrent job to avoid competing CPU/memory use; another OCR request receives HTTP 429. Static page and session requests remain available during OCR. It does not speed up the underlying enhanced OCR algorithm or claim that this caused every observed delay on a Mac.

The UI displays elapsed request time. Completed JSON includes decode, combined preprocessing/OCR, and total server duration. Request time also includes upload/network/response overhead. No confidence estimate is inferred from timing. Limits and OCR field extraction stay the same. Existing Reset is retained.

Verification: 55 unit tests passed across the originating project, including an idle socket while another request completes, page response during a controlled OCR job, and rejection of a second concurrent OCR job. Actual OCR of a sample in the development environment completed with timing and extracted fields; this is not a performance guarantee for Mac/Docker or uploaded table image. JavaScript syntax checked. No frozen benchmark source/report was modified. Visual browser acceptance remains to be done on the local machine.

# Reset update

Extract this ZIP into /Users/sierra6/Documents. It contains only updates under insurance-ocr-v05-fixed and insurance-ocr-image-reader. Stop running servers first and reload browser pages after restart. Existing datasets and SQLite database are not overwritten by extraction.

Review Desk (8765): the new ↺ button archives the current round inside the same SQLite database and starts an empty round; all 40 fixed sample cases are Pending again. A confirmation explains unsaved edits will be discarded. Download old rounds from the archive link, and export the active round as usual. Archived rounds include original decisions/audit and Thai notes. No restore-to-active UI is provided. Reset changes statuses, not the source images. Selecting Approved/Rejected/All cases remains sufficient if you only want to inspect another case without starting a new round. Old tabs are blocked from saving to the new round until reloaded. Only use the new UI with the updated backend: API saves now require the round ID.

Image Reader (8766): ↺ clears the selected file, preview, OCR result and downloadable JSON, ready for another image. It is disabled while OCR runs. Download results first if you want to keep them. This page does not store a persistent review queue. The initial empty preview is hidden to avoid a broken-image icon.

Closing Review Desk preserves current round deliberately; restarting is not a reset. To retain round archives in backups, back up the stopped app database. New upload images are still separate from the fixed Review Desk examples.

53 originating-project unit tests passed. HTTP reset smoke confirmed archived data retained, all active cases Pending and stale-tab saves rejected. JavaScript syntax checked. Browser interaction acceptance on the user's Mac remains pending. Frozen OCR recognition code/reports are unchanged.

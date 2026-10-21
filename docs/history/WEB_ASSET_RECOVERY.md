> Historical development note. For current commands and verification scope, start with [README](../../README.md). Counts and pending items below describe that stage.

# Missing web files

Review Desk needs review_ui.html and review_ui.js beside review_app.py. Image Reader needs image_reader.html and image_reader.js beside image_reader.py. Both import web_assets.py.

Startup now checks these files before opening a socket or creating a review database. A missing/unreadable file stops startup with its name and recovery guidance. If a file disappears while the server runs, the page/script endpoint returns HTTP 503 with plain text instead of an empty response traceback. No automatic file restoration, deletion, reset or database migration occurs.

## Recovery

1. Stop the affected server with Ctrl+C.
2. Check that the project directory still exists and has not been moved/renamed. Restarting from its actual location is necessary after a move.
3. From the correct Git repository, run git status --short. For an accidentally deleted tracked file, restore only that file, for example:

       git restore --source=HEAD --worktree -- review_ui.html

4. Activate the environment and restart:

       source .venv/bin/activate
       python review_app.py --uploads --port 8768

5. Reload the page. Review decisions are stored separately in review_state/ and are not reset by restoring the HTML file.

Do not run restore against a modified file whose edits you want to keep. The tool only prints guidance; it never executes Git commands. If the folder path does not exist, locate the actual project first. File permission problems require checking readability, not assuming deletion.

This handles unavailable static assets. It does not guarantee recovery of deleted databases, missing source images or arbitrary damaged project files. Tests cover missing directories/files, startup before socket/database creation, live 503 responses and restored-file serving for both apps.

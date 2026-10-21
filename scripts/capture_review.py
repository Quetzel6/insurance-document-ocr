"""Capture the actual synthetic Review Desk with an isolated empty review database."""

import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = ROOT / "artifacts/review-desk.png"
    destination.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        server = subprocess.Popen(
            [
                sys.executable,
                "review_app.py",
                "--port",
                "8875",
                "--db",
                str(Path(directory) / "review.sqlite3"),
            ],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
        )
        try:
            for _ in range(100):
                try:
                    urllib.request.urlopen("http://127.0.0.1:8875", timeout=1).close()
                    break
                except OSError:
                    time.sleep(0.1)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
                page.goto("http://127.0.0.1:8875")
                page.locator("#queue button").first.wait_for()
                page.locator("#queue button").first.click()
                page.wait_for_function("document.querySelector('#image').naturalWidth > 0")
                page.screenshot(path=str(destination), full_page=True)
                browser.close()
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    main()

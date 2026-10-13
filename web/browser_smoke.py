"""End-to-end browser smoke test for the static ECG calculator.

Run after installing Playwright and its Chromium browser:
    python -m pip install playwright
    python -m playwright install chromium
    python web/browser_smoke.py
"""
from __future__ import annotations

import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


def main() -> None:
    web_root = Path(__file__).resolve().parent
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(web_root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        url = f"http://127.0.0.1:{server.server_port}/"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(accept_downloads=True)
            failures = []
            page.on("pageerror", lambda exc: failures.append(str(exc)))
            response = page.goto(url, wait_until="load")
            assert response is not None and response.status == 200
            assert page.title() == "ECG Axis Calculator — Frontal QRS Axis"

            page.locator("#value-1").fill("1")
            page.locator("#value-2").fill("-0.1")
            page.locator("#pair-form button[type=submit]").click()
            assert page.locator("#axis-class").inner_text() == "Normal axis"
            assert page.locator("#axis-value").inner_text() == "-5.7°"

            page.locator("#tab-multi").click()
            page.locator("#multi-I").fill("0.8660254")
            page.locator("#multi-aVF").fill("0.5")
            page.locator("#multi-form button[type=submit]").click()
            assert page.locator("#axis-value").inner_text() == "30.0°"

            page.locator("#csv-file").set_input_files({
                "name": "sample.csv",
                "mimeType": "text/csv",
                "buffer": b"lead_i_net,lead_avf_net\\n1,-0.1\\n0,0\\n",
            })
            with page.expect_download() as pending:
                page.locator("#csv-run").click()
            download = pending.value
            assert download.suggested_filename == "ecg-axis-results.csv"
            output = Path(download.path()).read_text(encoding="utf-8")
            assert "normal" in output
            assert "indeterminate" in output
            assert "2 rows processed; 0 rows with errors" in page.locator("#csv-status").inner_text()
            assert not failures, "Browser console errors: " + str(failures)
            browser.close()
        print("Browser UI, axis modes, CSV download, and error checks passed.")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()

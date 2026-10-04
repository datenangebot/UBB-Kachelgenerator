"""Optional final browser artifact and byte-for-byte archive check."""
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(accept_downloads=True)
    page.goto('http://localhost:8080/')
    page.locator('#fields textarea').first.wait_for()
    page.locator('#export-open').click()
    page.locator('#export-name').fill('UBB-Testexport')
    with page.expect_download(timeout=120000) as pending:
        page.locator('#export-submit').click()
    downloaded = Path(pending.value.path()).read_bytes()
    browser.close()

sidecar = sorted(Path('storage/exports').glob('**/UBB-Testexport.png.json'))[-1]
metadata = json.loads(sidecar.read_text())
archived = sidecar.with_suffix('').read_bytes()
assert hashlib.sha256(downloaded).digest() == hashlib.sha256(archived).digest()
assert metadata['width'] == metadata['height'] == 1138
print('Downloaded and archived PNG are byte-identical:', sidecar)

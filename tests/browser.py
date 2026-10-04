"""Optional E2E: PYTHONPATH=/tmp/ubb-playwright python3 tests/browser.py."""
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = 'http://localhost:8080/'
errors = []

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(accept_downloads=True, viewport={'width': 1600, 'height': 1000})
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(BASE)
    page.locator('#template-select option').first.wait_for(state='attached')
    page.locator('#fields textarea').first.wait_for()
    text = page.locator('#fields textarea').first
    text.fill('150 Jahre\nNeuwittenbek')
    page.wait_for_timeout(250)
    assert page.locator('#canvas').get_by_text('150 Jahre').count() > 0
    normal_size = page.locator('#canvas .tile-text-content').first.evaluate('(e) => parseFloat(getComputedStyle(e).fontSize)')
    text.fill('Sehr langes Veranstaltungsjubiläum und noch viel mehr Worte ' * 20)
    page.locator('#warnings').wait_for(state='visible')
    small_size = page.locator('#canvas .tile-text-content').first.evaluate('(e) => parseFloat(getComputedStyle(e).fontSize)')
    assert small_size <= normal_size, (small_size, normal_size)
    text.fill('150 Jahre Neuwittenbek')
    page.locator('#warnings').wait_for(state='hidden')

    page.locator('#upload-open').click()
    page.locator('#upload-file').set_input_files('reference/UBB-150-J-Neuwittenbek_v1.png')
    page.locator('#upload-submit').click()
    page.locator('#upload-modal').wait_for(state='hidden')
    assert page.locator('#canvas .tile-photo img').count() == 1
    page.locator('#photo-zoom').fill('1.2')
    assert page.locator('#canvas .tile-photo img').evaluate('(e) => e.style.transform') == 'scale(1.2)'

    for fmt in ['png', 'jpg']:
        for scale in ['1', '2']:
            page.locator('#export-open').click()
            page.locator('#export-name').fill(f'Browser-Test-{fmt}-{scale}x')
            page.locator('#export-format').select_option(fmt)
            page.locator('#export-scale').select_option(scale)
            if fmt == 'jpg':
                page.locator('#export-quality').fill('70')
            with page.expect_download(timeout=120000) as download_info:
                page.locator('#export-submit').click()
            download = download_info.value
            assert download.suggested_filename.endswith('.' + fmt)
            assert Path(download.path()).stat().st_size > 1000
            page.locator('#export-modal').wait_for(state='hidden')
            page.locator('#result-modal').wait_for(state='visible')
            assert page.locator('#result-download').get_attribute('href')
            page.locator('#result-modal [data-bs-dismiss="modal"]').last.click()
            page.locator('#result-modal').wait_for(state='hidden')

    page.goto(BASE + 'exports.php')
    page.locator('#export-list .archive-card').first.wait_for()
    assert page.locator('#export-list .archive-card').count() >= 4
    page.locator('#export-search').fill('Browser-Test-jpg-2x')
    assert page.locator('#export-list .archive-card').count() == 1
    page.locator('#export-list img').first.wait_for()

    page.goto(BASE + 'templates.php?id=standard-magenta')
    page.locator('#editor-view').wait_for(state='visible')
    page.locator('#editor-elements .editor-layer').first.click()
    page.locator('#editor-properties input').first.wait_for()
    assert not errors, errors
    print('Browser E2E passed: text fit, overflow, upload, crop, PNG/JPG 1x/2x, archive, editor; no JS errors')
    browser.close()

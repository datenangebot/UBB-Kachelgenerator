"""Optional layer regression test: Playwright, Pillow, PyMuPDF; localhost:8080.

Checks deletion/insertion collisions, sparse and equal zIndex values, manual
layer edits, saved templates, generator rendering and PNG/JPG/PDF exports.
Creates and removes only its own uniquely named test data.
"""
import io
import json
import os
from pathlib import Path
import secrets

import fitz
from PIL import Image
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('UBB_TEST_URL', 'http://localhost:8080/')
KEY = 'layers-' + secrets.token_hex(5)
BLUE, GREEN, RED = (0, 0, 255), (0, 255, 0), (255, 0, 0)
created = set()


def shape(id, color, z):
    return dict(id=id, name=id, type='shape', x=0, y=0, width=400,
                height=400, rotation=0, opacity=1, zIndex=z,
                fillColor=color, borderRadius=0)


try:
    with sync_playwright() as pw:
        options = {'headless': True}
        if os.environ.get('BROWSER_EXECUTABLE'):
            options['executable_path'] = os.environ['BROWSER_EXECUTABLE']
        browser = pw.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 1600, 'height': 1100}, accept_downloads=True)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        # Fixture changes intentionally discard the previous editor draft.
        page.on('dialog', lambda dialog: dialog.accept() if dialog.type == 'beforeunload' else dialog.dismiss())
        page.goto(BASE + 'templates.php')

        def api(action, data=None):
            endpoint = BASE + 'api/index.php?action=' + action
            if data is None:
                response = page.request.get(endpoint)
            else:
                response = page.request.post(endpoint, data=data, headers={
                    'X-CSRF-Token': page.locator('meta[name=csrf-token]').get_attribute('content')})
            result = response.json()
            assert response.ok and result['ok'], result
            return result['data']

        def open_editor(elements):
            template = dict(schemaVersion=1, id=KEY, name=KEY, width=400,
                            height=400, fields=[], elements=elements)
            api('templates.save', template)
            created.add(ROOT / 'storage/templates' / (KEY + '.json'))
            page.goto(BASE + 'templates.php?id=' + KEY)
            expect(page.locator('.editor-layer')).to_have_count(len(elements))

        def pixel(canvas, color):
            page.locator(canvas).locator('img').evaluate_all('(images) => Promise.all(images.map(image => image.decode()))')
            image = Image.open(io.BytesIO(page.locator(canvas).screenshot())).convert('RGB')
            actual = image.getpixel((200, 150))
            assert actual == color, ('Visible layer', actual, 'expected', color)

        def add_image():
            page.locator('[data-add=image]').click()
            image = io.BytesIO()
            Image.new('RGB', (80, 80), RED).save(image, format='PNG')
            page.get_by_role('button', name='Bild auswählen', exact=True).click()
            with page.expect_response('**/api/index.php?action=assets.upload') as response:
                page.locator('#asset-picker-upload').set_input_files({
                    'name': KEY+'.png', 'mimeType': 'image/png', 'buffer': image.getvalue()})
            asset = response.value.json()['data']['asset']
            created.add(ROOT / asset)
            page.wait_for_function("asset => !!document.querySelector('#editor-canvas img[src$=\"'+asset+'\"]')", arg=asset)
            return asset

        def save():
            with page.expect_response('**/api/index.php?action=templates.save') as response:
                page.locator('#editor-save').click()
            assert response.value.ok
            return response.value.json()['data']

        def rows():
            return page.locator('.editor-layer').all_text_contents()

        # Removing layer 2 used to leave layer 3; the new image also received 3.
        open_editor([shape('base', '#0000ff', 1), shape('middle', '#ffffff', 2), shape('front', '#00ff00', 3)])
        page.locator('.editor-layer').filter(has_text='middle').click()
        page.get_by_role('button', name='Element löschen', exact=True).click()
        add_image()
        pixel('#editor-canvas', RED)
        page.get_by_role('button', name='Ebene ↓', exact=True).click()
        pixel('#editor-canvas', GREEN)
        assert rows() == ['front · shape', 'Bild · image', 'base · shape'], rows()
        saved = save()
        assert len({e['zIndex'] for e in saved['elements']}) == 3
        page.reload()
        expect(page.locator('.editor-layer')).to_have_count(3)
        pixel('#editor-canvas', GREEN)
        page.locator('.editor-layer').filter(has_text='Bild · image').click()
        page.get_by_role('button', name='Ebene ↑', exact=True).click()
        pixel('#editor-canvas', RED)
        # Direct numeric edits update both the visible canvas and the layer list.
        page.locator('#editor-properties label').filter(has_text='Ebene').locator('input').fill('0')
        page.locator('#editor-properties label').filter(has_text='Ebene').locator('input').dispatch_event('change')
        expect(page.locator('.editor-layer').last).to_have_text('Bild · image')
        pixel('#editor-canvas', GREEN)
        save()

        # Sparse/large layer values must not cause a new image to appear behind.
        open_editor([shape('base', '#0000ff', -5), shape('front', '#00ff00', 100)])
        add_image()
        expect(page.locator('.editor-layer').first).to_have_text('Bild · image')
        pixel('#editor-canvas', RED)
        page.get_by_role('button', name='Ebene ↓', exact=True).click()
        pixel('#editor-canvas', GREEN)
        page.get_by_role('button', name='Ebene ↓', exact=True).click()
        pixel('#editor-canvas', GREEN)
        assert rows() == ['front · shape', 'base · shape', 'Bild · image']
        # At the back boundary, moving down is a no-op; moving up works again.
        page.get_by_role('button', name='Ebene ↓', exact=True).click()
        assert rows()[-1] == 'Bild · image'
        page.get_by_role('button', name='Ebene ↑', exact=True).click()
        assert rows() == ['front · shape', 'Bild · image', 'base · shape']
        save()

        # Old templates with equal zIndex values show the actual paint order.
        open_editor([shape('base', '#0000ff', 0), shape('first', '#ff0000', 7), shape('last', '#00ff00', 7)])
        pixel('#editor-canvas', GREEN)
        assert rows() == ['last · shape', 'first · shape', 'base · shape'], rows()
        page.locator('.editor-layer').filter(has_text='last').click()
        page.get_by_role('button', name='Ebene ↓', exact=True).click()
        pixel('#editor-canvas', RED)

        # Verify an image behind the green shape across preview and all exports.
        open_editor([shape('base', '#0000ff', 1), shape('front', '#00ff00', 3)])
        add_image()
        page.get_by_role('button', name='Ebene ↓', exact=True).click()
        save()
        page.goto(BASE + '?template=' + KEY)
        expect(page.locator('#canvas .tile-element')).to_have_count(3)
        pixel('#canvas', GREEN)
        for kind in ['png', 'jpg', 'pdf']:
            page.locator('#export-open').click()
            page.locator('#export-name').fill(KEY)
            page.locator('#export-format').select_option(kind)
            with page.expect_download(timeout=120000) as download:
                page.locator('#export-submit').click()
            content = Path(download.value.path()).read_bytes()
            page.locator('#result-modal').wait_for(state='visible')
            item = next(x for x in api('exports.list') if x['filename'] == download.value.suggested_filename)
            for path in [item['url'], item['url']+'.json', item.get('previewUrl', item['url'])]:
                created.add(ROOT / path)
            if kind == 'pdf':
                with fitz.open(stream=content, filetype='pdf') as doc:
                    raster = doc[0].get_pixmap(matrix=fitz.Matrix(4/3, 4/3))
                    image = Image.frombytes('RGB', (raster.width, raster.height), raster.samples)
            else:
                image = Image.open(io.BytesIO(content)).convert('RGB')
            actual = image.getpixel((200, 150))
            assert all(abs(a-b) <= 2 for a, b in zip(actual, GREEN)), (kind, actual)
            page.locator('#result-modal .btn-close').click()
            page.locator('#result-modal').wait_for(state='hidden')
        assert not errors, errors
        page.context.close()
        browser.close()
finally:
    for path in created:
        path.unlink(missing_ok=True)
        if (ROOT / 'assets/template-assets') in path.parents:
            Path(str(path)+'.json').unlink(missing_ok=True)

print('Layer insertion, reordering, equal/sparse indices, persistence and PNG/JPG/PDF rendering passed')

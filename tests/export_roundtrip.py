"""Optional integration checks: Playwright, Pillow, PyMuPDF; app on localhost:8080.

Creates and removes only uniquely named test data. Existing archive files are hashed
before and after the test. BROWSER_EXECUTABLE can select an installed Chromium.
"""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import secrets

import fitz
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('UBB_TEST_URL', 'http://localhost:8080/')
KEY = 'roundtrip-' + secrets.token_hex(5)


def archive_hashes():
    return {p: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / 'storage/exports').rglob('*') if p.is_file()}


original = archive_hashes()
created = set()
errors = []

try:
    with sync_playwright() as pw:
        options = {'headless': True}
        if os.environ.get('BROWSER_EXECUTABLE'):
            options['executable_path'] = os.environ['BROWSER_EXECUTABLE']
        browser = pw.chromium.launch(**options)
        page = browser.new_page(accept_downloads=True, viewport={'width': 1440, 'height': 1100})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(BASE)
        page.locator('#fields textarea').first.wait_for()

        def api(action, data=None, files=None, expected=200):
            token = page.locator('meta[name=csrf-token]').get_attribute('content')
            args = {'headers': {'X-CSRF-Token': token}}
            if files:
                args['multipart'] = dict(data or {}, **files)
                response = page.request.post(BASE + 'api/index.php?action=' + action, **args)
            elif data is not None:
                response = page.request.post(BASE + 'api/index.php?action=' + action, data=data, **args)
            else:
                response = page.request.get(BASE + 'api/index.php?action=' + action)
            result = response.json()
            assert response.status == expected, (action, response.status, result)
            return result.get('data', result)

        def png(color, size):
            out = io.BytesIO()
            # A grid makes crop/zoom/rotation differences visible.
            img = Image.new('RGB', size, color)
            for x in range(size[0]):
                for y in range(size[1]):
                    if (x // 35 + y // 35) % 2:
                        img.putpixel((x, y), (25, 80, 140))
            img.save(out, format='PNG')
            return out.getvalue()

        def file(name, content, mime='image/png'):
            return {'name': name, 'mimeType': mime, 'buffer': content}

        def export(kind, scale=1):
            # Visibility starts before Bootstrap's transition finishes. Wait for
            # lifecycle events so a rapid next click cannot be ignored.
            def watch(selector, event):
                page.evaluate("""({selector,event}) => {
                    window.ubbModalTransition = new Promise(resolve => document.querySelector(selector).addEventListener(event, () => resolve(true), {once:true}));
                }""", {'selector':selector, 'event':event})

            def wait_transition():
                page.evaluate("""() => Promise.race([window.ubbModalTransition, new Promise((_,reject) => setTimeout(() => reject(Error('Modal transition timed out')), 5000))])""")

            watch('#export-modal','shown.bs.modal')
            page.locator('#export-open').click()
            wait_transition()
            page.locator('#export-name').fill(KEY)
            page.locator('#export-format').select_option(kind)
            page.locator('#export-scale').select_option(str(scale))
            watch('#result-modal','shown.bs.modal')
            page.locator('#export-submit').click()
            page.wait_for_function("""() => document.querySelector('#result-modal').classList.contains('show') || !document.querySelector('#export-error').classList.contains('d-none')""", timeout=120000)
            assert not page.locator('#export-error').is_visible(), page.locator('#export-error').inner_text()
            page.locator('#result-modal').wait_for(state='visible')
            wait_transition()
            name = page.locator('#result-name').inner_text()
            item = next(x for x in api('exports.list') if x['filename'] == name)
            created.add(ROOT / item['url'])
            created.add(ROOT / (item['url'] + '.json'))
            if item.get('previewUrl') != item['url']:
                created.add(ROOT / item['previewUrl'])
            assert item['canRestore'] is True
            watch('#result-modal','hidden.bs.modal')
            page.locator('#result-modal .btn-close').click()
            wait_transition()
            page.locator('#result-modal').wait_for(state='hidden')
            return item

        template = api('templates.get&id=standard-magenta')
        template.update(id=KEY, name=KEY)
        asset_bytes = png((210, 170, 30), (350, 250))
        asset = api('assets.upload', files={'image': file(KEY + '.png', asset_bytes)})
        created.add(ROOT / asset['asset'])
        # Duplicate file names never replace an existing default image.
        second = api('assets.upload', files={'image': file(KEY + '.png', asset_bytes)})
        created.add(ROOT / second['asset'])
        assert asset['asset'] != second['asset']
        api('assets.upload', files={'image': file('bad.svg', b'<svg/>', 'image/svg+xml')}, expected=400)
        api('assets.upload', files={'image': file('bad.png', b'not an image')}, expected=400)
        photo = next(e for e in template['elements'] if e['type'] == 'photo')
        photo['asset'] = asset['asset']
        photo['crop'] = {'positionX': 34, 'positionY': 61, 'zoom': 1.2}
        template['elements'].append(dict(id='uploaded-logo', name='Logo', type='image',
                                         asset=asset['asset'], x=850, y=420, width=150,
                                         height=100, rotation=23, opacity=.7, zIndex=12,
                                         objectFit='contain'))
        # Extra text covers wrapping, multiple fonts, rotation, color and opacity.
        text = copy.deepcopy(next(e for e in template['elements'] if e['type'] == 'text'))
        text.update(id='extra-text', name='Mehrzeilig', x=170, y=790, width=680, height=290,
                    rotation=13, fontFamily='Liberation Serif', fontWeight=400,
                    binding={'type': 'static', 'text': 'Ä Ö Ü ä ö ü ß €\nZweite Zeile AV fi'},
                    minFontSize=35, maxFontSize=54, lineHeight=1.2, maxLines=4,
                    textAlign='right', verticalAlign='bottom', letterSpacing=2.5,
                    opacity=.8, zIndex=15, color='#ffec00')
        template['elements'].append(text)
        api('templates.save', template)
        created.add(ROOT / 'storage/templates' / (KEY + '.json'))

        # Upload through both editor controls, then save and check persisted defaults.
        page.goto(BASE + 'templates.php?id=' + KEY)
        page.locator('#editor-view').wait_for(state='visible')
        for layer in ['Konzertfoto', 'Logo · image']:
            page.locator('.editor-layer').filter(has_text=layer).click()
            page.get_by_role('button', name='Bild auswählen', exact=True).click()
            with page.expect_response('**/api/index.php?action=assets.upload') as response:
                page.locator('#asset-picker-upload').set_input_files(file(KEY+'.png', asset_bytes))
            assert response.value.status == 200
            uploaded = response.value.json()['data']['asset']
            created.add(ROOT / uploaded)
            page.wait_for_function("asset => !!document.querySelector('#editor-canvas img[src$=\"' + asset + '\"]')", arg=uploaded)
            expect(page.locator('#asset-picker-modal')).to_be_hidden()
        with page.expect_response('**/api/index.php?action=templates.save'):
            page.locator('#editor-save').click()
        template = api('templates.get&id=' + KEY)
        photo = next(e for e in template['elements'] if e['type'] == 'photo')
        assert photo['asset'] in [str(p.relative_to(ROOT)) for p in created]
        page.goto(BASE + '?template=' + KEY)
        page.locator('#fields textarea').first.wait_for()
        assert page.locator('.tile-photo img').get_attribute('src').endswith(photo['asset'])
        # The default photo supports the same direct dragging as a gallery photo.
        position_before = page.locator('#photo-x').input_value()
        box = page.locator('#canvas .tile-photo').bounding_box()
        page.mouse.move(box['x'] + box['width']*.9, box['y'] + box['height']*.9)
        page.mouse.down()
        page.mouse.move(box['x'] + box['width']*.9 + 30, box['y'] + box['height']*.9 + 15, steps=4)
        page.mouse.up()
        assert page.locator('#photo-x').input_value() != position_before
        page.locator('[data-field-id=headline]').fill('Neue Variante mit ÄÖÜ und ß')
        page.locator('[data-field-id=maintext]').fill('Wieder laden & ändern')
        for selector, value in [('#photo-zoom', '1.73'), ('#photo-x', '27'), ('#photo-y', '68')]:
            page.locator(selector).evaluate("(input, value) => { input.value=value; input.dispatchEvent(new Event('input', {bubbles:true})); }", value)
        page.locator('#fields .btn').first.click()
        page.locator('#adjust-mode').select_option('manual')
        page.locator('#adjust-mode').dispatch_event('input')
        page.locator('#adjust-size').fill('53')
        page.locator('#adjust-x').fill('17')
        page.locator('#adjust-y').fill('-8')
        page.locator('#adjust-modal .btn-close').click()
        page.locator('#adjust-modal').wait_for(state='hidden')

        first = export('png')
        first_digest = hashlib.sha256((ROOT / first['url']).read_bytes()).digest()
        metadata = api('exports.get&id=' + first['id'])
        saved_state = metadata['generatorState']
        assert saved_state['fields']['headline'] == 'Neue Variante mit ÄÖÜ und ß'
        assert saved_state['version'] == 2
        assert saved_state['photos']['photo'] == {'background': None, 'zoom': 1.73, 'positionX': 27, 'positionY': 68}
        assert saved_state['textOverrides']['headline']['x'] == 17
        pdf = export('pdf')
        assert api('exports.get&id=' + pdf['id'])['generatorState'] == saved_state
        document = fitz.open(ROOT / pdf['url'])
        assert len(document) == 1
        assert abs(document[0].rect.width - template['width'] * .75) < .01
        extracted = document[0].get_text()
        assert 'Neue Variante' in extracted, extracted
        assert 'Ä Ö Ü' in extracted and 'ß €' in extracted, extracted
        for pdf_font in document[0].get_fonts():
            assert document.extract_font(pdf_font[0])[3], ('Font not embedded', pdf_font)
        raster = document[0].get_pixmap(matrix=fitz.Matrix(4/3,4/3), alpha=False)
        pdf_image = Image.frombytes('RGB', [raster.width, raster.height], raster.samples)
        png_image = Image.open(ROOT / first['url']).convert('RGB')
        assert pdf_image.size == png_image.size
        diff = ImageChops.difference(pdf_image, png_image)
        mean = sum(ImageStat.Stat(diff).mean) / 3
        # Different text antialiasing is expected, layout differences are not.
        if mean >= 2.5 or os.environ.get('UBB_TEST_ARTIFACTS'):
            png_image.save('/tmp/ubb-export-png.png')
            pdf_image.save('/tmp/ubb-export-pdf.png')
            diff.save('/tmp/ubb-export-difference.png')
        assert mean < 2.5, ('PNG/PDF visual difference', mean)
        print('PNG/PDF mean channel difference:', round(mean, 4))
        document.close()
        pdf2 = export('pdf', 2)
        assert pdf2['width'] == pdf2['height'] == 2276
        with fitz.open(ROOT / pdf2['url']) as document:
            assert abs(document[0].rect.width - template['width'] * 1.5) < .01
            assert 'Neue Variante' in document[0].get_text()
            assert all(document.extract_font(f[0])[3] for f in document[0].get_fonts())

        # A real background override must survive restoration too.
        bg = api('backgrounds.upload', files={'image': file(KEY+'.png', png((90, 180, 20), (400, 300)))})
        created.add(ROOT / bg['url'])
        page.reload()
        page.locator('#fields textarea').first.wait_for()
        page.locator('[data-photo-choice=photo]').click()
        page.locator('#gallery-search').fill(bg['filename'])
        page.locator('#gallery-grid .gallery-item').click()
        expect(page.locator('#gallery-modal')).to_be_hidden()
        with_background = export('jpg', 2)
        with_background_state = api('exports.get&id='+with_background['id'])['generatorState']
        assert with_background_state['photos']['photo']['background'] == bg['filename']

        # Deleting the source template must not affect snapshots or future exports.
        api('templates.delete', {'id': KEY})
        page.goto(BASE + 'exports.php')
        page.locator('#export-search').fill(KEY)
        card = page.locator('.archive-card').filter(has_text=first['filename'])
        card.get_by_role('link', name='Im Generator laden').click()
        page.locator('#fields textarea').first.wait_for()
        assert page.locator('[data-field-id=headline]').input_value() == saved_state['fields']['headline']
        assert page.locator('#photo-zoom').input_value() == '1.73'
        assert page.locator('#template-select option:checked').inner_text().endswith('(Archivstand)')
        restored = export('png')
        assert restored['url'] != first['url']
        assert (ROOT / restored['url']).read_bytes() == (ROOT / first['url']).read_bytes()
        page.locator('[data-field-id=headline]').fill('Angepasste Variante')
        changed = export('png')
        assert api('exports.get&id='+changed['id'])['generatorState']['fields']['headline'] == 'Angepasste Variante'
        page.goto(BASE + '?export=' + with_background['id'])
        page.locator('#fields textarea').first.wait_for()
        assert page.locator('.tile-photo img').get_attribute('src').endswith(bg['filename'])
        # Empty PHP/JSON maps can arrive as []; subsequent named overrides must
        # still be serialized as an object, rather than lost on an Array.
        assert not with_background_state['textOverrides']
        page.locator('#fields .btn').first.click()
        page.locator('#adjust-x').fill('9')
        page.locator('#adjust-modal .btn-close').click()
        page.locator('#adjust-modal').wait_for(state='hidden')
        edited_background = export('jpg', 2)
        assert api('exports.get&id='+edited_background['id'])['generatorState']['textOverrides']['headline']['x'] == 9
        page.locator('#background-default').click()
        assert page.locator('.tile-photo img').get_attribute('src').endswith(photo['asset'])
        assert hashlib.sha256((ROOT / first['url']).read_bytes()).digest() == first_digest

        # Simulate old metadata without a snapshot, and without generator values.
        for old_state in [{}, {'fields': saved_state['fields']}]:
            legacy = dict(metadata, id=secrets.token_hex(6), filename=KEY+'-legacy.png',
                          url=first['url'], generatorState=old_state)
            sidecar = ROOT / (first['url']+'.legacy-'+legacy['id']+'.json')
            sidecar.write_text(json.dumps(legacy))
            created.add(sidecar)
            item = next(x for x in api('exports.list') if x['id'] == legacy['id'])
            assert not item['canRestore']
            api('exports.get&id='+legacy['id'], expected=409)
        page.goto(BASE + 'exports.php')
        page.locator('#export-search').fill(KEY+'-legacy')
        expect(page.locator('.archive-card')).to_have_count(2)
        assert page.get_by_role('link', name='Im Generator laden').count() == 0
        assert page.get_by_role('link', name='Herunterladen').count() == 2

        # Reject a tampered state and PDF without creating any archive artifacts.
        invalid = copy.deepcopy(saved_state)
        invalid['photos']['photo']['background'] = '../secret.png'
        api('exports.save', {'metadata': json.dumps(dict(format='png', scale=1, templateId=KEY, generatorState=invalid))},
            {'image': file('export.png', (ROOT / first['url']).read_bytes())}, expected=400)
        api('exports.save', {'metadata': json.dumps(dict(format='pdf', scale=1, templateId=KEY, generatorState=saved_state))},
            {'image': file('export.png', (ROOT / first['url']).read_bytes()), 'document': file('bad.pdf', b'%PDF-1.7\nbroken\n%%EOF', 'application/pdf')}, expected=400)
        assert not errors, errors
        page.context.close()
        browser.close()
finally:
    for path in created:
        path.unlink(missing_ok=True)
        if (ROOT / 'assets/template-assets') in path.parents:
            Path(str(path)+'.json').unlink(missing_ok=True)
    for path, digest in original.items():
        assert path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == digest, ('Existing archive changed', path)

print('Uploads, embedded PDF text, visual comparison, legacy archive and export roundtrip passed')

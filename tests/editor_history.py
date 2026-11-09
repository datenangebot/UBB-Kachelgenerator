"""Optional editor undo/navigation regression test; Playwright and Pillow.

App on localhost:8080. Creates and removes only uniquely named test data.
"""
import io
import os
from pathlib import Path
import secrets

from PIL import Image
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('UBB_TEST_URL', 'http://localhost:8080/')
KEY = 'history-' + secrets.token_hex(5)
created = set()

try:
    with sync_playwright() as pw:
        options = {'headless': True}
        if os.environ.get('BROWSER_EXECUTABLE'):
            options['executable_path'] = os.environ['BROWSER_EXECUTABLE']
        browser = pw.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 1600, 'height': 1100})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(BASE + 'templates.php')

        def api(action, data=None):
            endpoint = BASE + 'api/index.php?action=' + action
            response = page.request.get(endpoint) if data is None else page.request.post(endpoint, data=data, headers={
                'X-CSRF-Token': page.locator('meta[name=csrf-token]').get_attribute('content')})
            result = response.json()
            assert response.ok and result['ok'], result
            return result['data']

        def clean(undo_available=False):
            expect(page.locator('#editor-status')).to_have_text('Gespeichert')
            if undo_available:
                expect(page.locator('#editor-undo')).to_be_enabled()
            else:
                expect(page.locator('#editor-undo')).to_be_disabled()

        def dirty():
            expect(page.locator('#editor-status')).to_have_text('Ungespeicherte Änderungen')
            expect(page.locator('#editor-undo')).to_be_enabled()

        def undo():
            page.locator('#editor-undo').click()
            clean()

        def select(name):
            page.locator('#tab-elements').click()
            page.locator('.editor-layer').filter(has_text=name).click()

        def save():
            with page.expect_response('**/api/index.php?action=templates.save') as response:
                page.locator('#editor-save').click()
            assert response.value.ok
            clean(undo_available=True)

        def cancel(dialog):
            assert dialog.type == 'confirm', dialog.type
            assert 'ungespeicherte' in dialog.message.lower()
            dialog.dismiss()

        geometry = dict(x=100, y=100, width=160, height=80, rotation=0, opacity=1)
        template = dict(schemaVersion=1, id=KEY, name=KEY, width=400, height=400,
                        fields=[dict(id=id, label=id, inputType='text', defaultValue='Text', order=i*10)
                                for i, id in enumerate(['headline', 'unbound'])], elements=[
                            dict(geometry, id='base', name='base', type='shape', x=0, y=0, width=400, height=400, zIndex=1, fillColor='#222222', borderRadius=0),
                            dict(geometry, id='photo', name='photo', type='photo', x=200, y=220, zIndex=2, crop=dict(positionX=50, positionY=50, zoom=1)),
                            dict(geometry, id='movable', name='movable', type='shape', zIndex=3, fillColor='#00ff00', borderRadius=0),
                            dict(geometry, id='text', name='text', type='text', y=310, zIndex=4,
                                 binding=dict(type='field', fieldId='headline'), fontFamily='Liberation Sans', fontWeight=400,
                                 minFontSize=12, maxFontSize=30, maxLines=2, lineHeight=1.1, color='#ffffff', wrap=True)
                        ])
        api('templates.save', template)
        created.add(ROOT / 'storage/templates' / (KEY+'.json'))
        page.goto(BASE + 'templates.php?id=' + KEY)
        expect(page.locator('.editor-layer')).to_have_count(4)
        clean()
        select('movable')
        clean()  # Selection and tab changes are not editing steps.

        page.locator('[data-add=shape]').click()
        expect(page.locator('.editor-layer')).to_have_count(5)
        dirty(); undo()
        expect(page.locator('.editor-layer')).to_have_count(4)
        page.locator('[data-add=shape]').click()
        page.locator('[data-add=shape]').press('Control+z')
        clean()
        expect(page.locator('.editor-layer')).to_have_count(4)

        page.locator('#editor-name').fill('')
        page.locator('#editor-name').press_sequentially('Ein kompletter Eingabeschritt')
        dirty(); undo()
        expect(page.locator('#editor-name')).to_have_value(KEY)

        # Returning to the same field starts a distinct editing step.
        page.locator('#editor-name').fill('Erste Eingabe')
        page.locator('#editor-name').press('Tab')
        page.locator('#editor-name').fill('Zweite Eingabe')
        page.locator('#editor-undo').click()
        expect(page.locator('#editor-name')).to_have_value('Erste Eingabe')
        expect(page.locator('#editor-status')).to_have_text('Ungespeicherte Änderungen')
        expect(page.locator('#editor-undo')).to_be_disabled()
        page.locator('#editor-name').fill(KEY)
        expect(page.locator('#editor-status')).to_have_text('Gespeichert')
        page.reload()
        clean()

        select('movable')
        page.locator('#editor-properties').get_by_label('X', exact=True).fill('145')
        # Dirty state must be visible before blur or a change event.
        dirty(); undo()
        expect(page.locator('#editor-properties').get_by_label('X', exact=True)).to_have_value('100')
        order = page.locator('.editor-layer').all_text_contents()
        page.get_by_role('button', name='Ebene ↓', exact=True).click()
        dirty(); undo()
        assert page.locator('.editor-layer').all_text_contents() == order
        page.get_by_role('button', name='Element löschen', exact=True).click()
        expect(page.locator('.editor-layer')).to_have_count(3)
        dirty(); undo()
        expect(page.locator('.editor-layer.active')).to_have_text('movable · shape')

        node = page.locator('#editor-canvas [data-element-id=movable]')
        box = node.bounding_box()
        page.mouse.move(box['x']+20, box['y']+20); page.mouse.down()
        page.mouse.move(box['x']+100, box['y']+60, steps=10); page.mouse.up()
        dirty(); undo()
        assert node.evaluate('(n)=>[n.style.left,n.style.top]') == ['100px', '100px']
        box = node.locator('.resize-handle').bounding_box()
        page.mouse.move(box['x']+6, box['y']+6); page.mouse.down()
        page.mouse.move(box['x']+66, box['y']+36, steps=10); page.mouse.up()
        dirty(); undo()
        assert node.evaluate('(n)=>[n.style.width,n.style.height]') == ['160px', '80px']

        page.locator('#tab-fields').click()
        page.locator('#field-add').click()
        dirty(); undo()
        expect(page.locator('.editor-field')).to_have_count(2)
        page.locator('.editor-field').filter(has_text='unbound').click()
        page.get_by_role('button', name='Feld löschen', exact=True).click()
        dirty(); undo()
        expect(page.locator('.editor-field.active')).to_have_text('unbound')
        page.locator('#editor-properties').get_by_label('Standardwert', exact=True).fill('Andere Vorgabe')
        dirty(); undo()
        expect(page.locator('#editor-properties').get_by_label('Standardwert', exact=True)).to_have_value('Text')

        select('text')
        page.get_by_label('Textart', exact=True).select_option('static')
        dirty(); undo()
        expect(page.get_by_label('Textart', exact=True)).to_have_value('field')
        page.get_by_label('Text umbrechen', exact=True).uncheck()
        dirty(); undo()
        expect(page.get_by_label('Text umbrechen', exact=True)).to_be_checked()
        page.locator('#editor-properties').get_by_label('Schrift', exact=True).select_option('Liberation Serif')
        dirty(); undo()
        expect(page.locator('#editor-properties').get_by_label('Schrift', exact=True)).to_have_value('Liberation Sans')

        image = io.BytesIO(); Image.new('RGB', (50, 50), '#ff0000').save(image, format='PNG')
        upload = {'name':KEY+'.png', 'mimeType':'image/png', 'buffer':image.getvalue()}
        select('photo')
        pending = []
        hold = lambda route: pending.append(route)
        page.route('**/api/index.php?action=assets.upload', hold)
        page.get_by_role('button', name='Bild auswählen', exact=True).click()
        page.locator('#asset-picker-upload').set_input_files(upload)
        expect(page.locator('#editor-status')).to_have_text('Bild wird hochgeladen …')
        expect(page.locator('#editor-save')).to_be_disabled()
        with page.expect_event('dialog') as dialog:
            page.evaluate('setTimeout(()=>location.reload(),0)')
        assert dialog.value.type == 'beforeunload'
        dialog.value.dismiss()
        expect(page.locator('#editor-view')).to_be_visible()
        with page.expect_response('**/api/index.php?action=assets.upload') as response:
            pending.pop().continue_()
        created.add(ROOT / response.value.json()['data']['asset'])
        page.unroute('**/api/index.php?action=assets.upload', hold)
        expect(page.locator('#asset-picker-modal')).to_be_hidden()
        dirty(); undo()
        expect(page.locator('#editor-canvas [data-element-id=photo] img')).to_have_count(0)

        # Abandoned uploads must not alter a newly opened editor session.
        page.route('**/api/index.php?action=assets.upload', hold)
        page.get_by_role('button', name='Bild auswählen', exact=True).click()
        page.locator('#asset-picker-upload').set_input_files(upload)
        expect(page.locator('#editor-status')).to_have_text('Bild wird hochgeladen …')
        page.keyboard.press('Escape')
        expect(page.locator('#asset-picker-modal')).to_be_hidden()
        page.once('dialog', lambda dialog: dialog.accept())
        page.locator('#editor-close').click()
        expect(page.locator('#template-list-view')).to_be_visible()
        page.locator('.card').filter(has=page.get_by_text(KEY, exact=True)).get_by_role('button', name='Bearbeiten', exact=True).click()
        clean()
        with page.expect_response('**/api/index.php?action=assets.upload') as response:
            pending.pop().continue_()
        created.add(ROOT / response.value.json()['data']['asset'])
        page.unroute('**/api/index.php?action=assets.upload', hold)
        clean()
        expect(page.locator('#editor-canvas [data-element-id=photo] img')).to_have_count(0)

        page.locator('#editor-name').fill('Nicht gespeichert')
        page.once('dialog', cancel)
        page.locator('#editor-close').click()
        expect(page.locator('#editor-view')).to_be_visible()
        page.once('dialog', cancel)
        page.get_by_role('link', name='Bisherige Exporte', exact=True).click()
        expect(page.locator('#editor-name')).to_have_value('Nicht gespeichert')
        with page.expect_event('dialog') as dialog:
            page.evaluate('setTimeout(()=>location.reload(),0)')
        assert dialog.value.type == 'beforeunload'
        dialog.value.dismiss()
        expect(page.locator('#editor-name')).to_have_value('Nicht gespeichert')

        # Failure must not clear the dirty flag or undo snapshot.
        fail_save = lambda route: route.fulfill(status=400, json={'ok':False, 'message':'Absichtlicher Testfehler', 'requestId':'test'})
        page.route('**/api/index.php?action=templates.save', fail_save)
        page.locator('#editor-save').click()
        expect(page.locator('#app-toast .toast-body')).to_contain_text('Absichtlicher Testfehler')
        dirty()
        page.unroute('**/api/index.php?action=templates.save', fail_save)
        undo()

        # Accepting a menu warning triggers exactly one dialog, not two.
        page.locator('#editor-name').fill('Verwerfen')
        dialogs = []
        def accept(dialog):
            dialogs.append(dialog.type)
            dialog.accept()
        page.on('dialog', accept)
        page.get_by_role('link', name='Generator', exact=True).click()
        page.wait_for_url('**/index.php')
        assert dialogs == ['confirm'], dialogs
        page.remove_listener('dialog', accept)
        page.goto(BASE+'templates.php?id='+KEY)
        clean()
        expect(page.locator('#editor-name')).to_have_value(KEY)
        page.locator('#editor-name').fill(KEY+' gespeichert')
        save()
        assert api('templates.get&id='+KEY)['name'] == KEY+' gespeichert'
        # Saving sets the baseline, while undo still restores the last edit.
        page.locator('#editor-undo').click()
        expect(page.locator('#editor-name')).to_have_value(KEY)
        expect(page.locator('#editor-status')).to_have_text('Ungespeicherte Änderungen')
        expect(page.locator('#editor-undo')).to_be_disabled()
        page.locator('#editor-name').fill(KEY+' gespeichert')
        save()

        # Duplicate the current draft without discarding unsaved edits.
        select('movable')
        page.locator('#editor-properties').get_by_label('X', exact=True).fill('137')
        page.locator('#editor-name').fill('Kopie des aktuellen Entwurfs')
        copy_id = KEY+'-copy'
        page.once('dialog', lambda dialog: dialog.accept(copy_id))
        with page.expect_response('**/api/index.php?action=templates.save'):
            page.locator('#editor-duplicate').click()
        created.add(ROOT/'storage/templates'/(copy_id+'.json'))
        clean()
        assert api('templates.get&id='+KEY)['name'] == KEY+' gespeichert'
        assert next(e for e in api('templates.get&id='+copy_id)['elements'] if e['id']=='movable')['x'] == 137
        assert next(e for e in api('templates.get&id='+KEY)['elements'] if e['id']=='movable')['x'] == 100
        expect(page.locator('#editor-name')).to_have_value(copy_id)
        page.on('dialog', accept)
        page.get_by_role('link', name='Templates', exact=True).click()
        page.wait_for_url('**/templates.php')
        assert dialogs == ['confirm'], dialogs  # No warning after saving.
        page.remove_listener('dialog', accept)

        # Even an empty new template is unsaved and protected when leaving.
        prompts = iter([KEY+' neu', 'leer', '400', '400'])
        handle_prompt = lambda dialog: dialog.accept(next(prompts))
        page.on('dialog', handle_prompt)
        page.locator('#new-template').click()
        page.remove_listener('dialog', handle_prompt)
        expect(page.locator('#editor-status')).to_have_text('Ungespeicherte Änderungen')
        expect(page.locator('#editor-undo')).to_be_disabled()
        page.once('dialog', cancel)
        page.locator('#editor-close').click()
        expect(page.locator('#editor-view')).to_be_visible()
        page.once('dialog', lambda dialog: dialog.accept())
        page.locator('#editor-close').click()
        expect(page.locator('#template-list-view')).to_be_visible()
        assert not errors, errors
        page.context.close(); browser.close()
finally:
    for path in created:
        path.unlink(missing_ok=True)
        if (ROOT / 'assets/template-assets') in path.parents:
            Path(str(path)+'.json').unlink(missing_ok=True)

print('Single-step undo, grouped typing/dragging, uploads, save failures and navigation warnings passed')

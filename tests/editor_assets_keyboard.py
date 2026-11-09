"""Optional visual asset picker/icon/keyboard regression: Playwright + Pillow.

Creates and removes only uniquely named test files. App on localhost:8080.
"""
import io
import json
import os
from pathlib import Path
import secrets

from PIL import Image
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('UBB_TEST_URL', 'http://localhost:8080/')
KEY = 'picker-' + secrets.token_hex(5)
created = set()

try:
    folder = ROOT/'assets/template-assets'
    assets = {}
    for key, filename, color, added, name in [
        ('alpha', KEY+'-file-a.png', '#ff0000', '2025-01-01T12:00:00+00:00', KEY+'-Alpha original.png'),
        ('beta', KEY+'-Beta-Fördebühne #1.png', '#00ff00', None, None),
        ('zeta', KEY+'-file-z.png', '#0000ff', '2020-01-01T12:00:00+00:00', KEY+'-Zeta.png')
    ]:
        path = folder/filename
        Image.new('RGB', (60, 40), color).save(path)
        created.add(path);assets[key] = str(path.relative_to(ROOT))
        os.utime(path, (1640995200, 1640995200))  # 2022: only the legacy asset uses mtime.
        if added:
            meta = Path(str(path)+'.json')
            meta.write_text(json.dumps({'name':name,'addedAt':added}))
            created.add(meta)
    svg = folder/(KEY+'-middle.svg')
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="60" height="40"><rect width="60" height="40" fill="orange"/></svg>')
    created.add(svg);assets['mu'] = str(svg.relative_to(ROOT))
    meta = Path(str(svg)+'.json');meta.write_text(json.dumps({'name':KEY+'-Mu.svg','addedAt':'2023-01-01T12:00:00+00:00'}));created.add(meta)
    invalid = folder/(KEY+'-invalid.png');invalid.write_text('not an image');created.add(invalid)
    escape = folder/(KEY+'-escape.png');escape.symlink_to(ROOT/'README.md');created.add(escape)

    with sync_playwright() as pw:
        options = {'headless':True}
        if os.environ.get('BROWSER_EXECUTABLE'):
            options['executable_path'] = os.environ['BROWSER_EXECUTABLE']
        browser = pw.chromium.launch(**options)
        page = browser.new_page(viewport={'width':1600,'height':1100})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(BASE+'templates.php')

        def api(action, data=None):
            endpoint = BASE+'api/index.php?action='+action
            response = page.request.get(endpoint) if data is None else page.request.post(endpoint, data=data, headers={
                'X-CSRF-Token':page.locator('meta[name=csrf-token]').get_attribute('content')})
            result = response.json()
            assert response.ok and result['ok'], result
            return result['data']

        items = [x for x in api('assets.list') if KEY in x['asset']]
        assert {x['asset'] for x in items} == set(assets.values())
        assert next(x for x in items if x['asset']==assets['alpha'])['addedAt'].startswith('2025')
        assert '%23' in next(x for x in items if x['asset']==assets['beta'])['url']
        geometry = dict(x=100,y=100,width=100,height=100,rotation=0,opacity=1)
        template = dict(schemaVersion=1,id=KEY,name=KEY,width=400,height=400,
                        fields=[dict(id='headline',label='headline',inputType='text',defaultValue='Text',order=10)],elements=[
                            dict(geometry,id='base',name='base',type='shape',x=0,y=0,width=400,height=400,zIndex=1,fillColor='#ffffff',borderRadius=0),
                            dict(geometry,id='image',name='image',type='image',zIndex=2,asset=assets['alpha'],objectFit='contain'),
                            dict(geometry,id='photo',name='photo',type='photo',y=230,zIndex=3,asset=assets['zeta'],crop=dict(positionX=50,positionY=50,zoom=1)),
                            dict(geometry,id='text',name='text',type='text',x=20,y=340,width=250,height=50,zIndex=4,binding=dict(type='field',fieldId='headline'),fontFamily='Liberation Sans',fontWeight=400,minFontSize=12,maxFontSize=30,maxLines=2,lineHeight=1.1,color='#000000')
                        ])
        api('templates.save',template);created.add(ROOT/'storage/templates'/(KEY+'.json'))
        page.goto(BASE+'templates.php?id='+KEY)
        expect(page.locator('.editor-layer')).to_have_count(4)

        def select(name):
            page.locator('#tab-elements').click()
            page.locator('.editor-layer').filter(has_text=name+' ·').click()

        def position():
            return page.locator('#editor-canvas [data-element-id=image]').evaluate('(n)=>[parseFloat(n.style.left),parseFloat(n.style.top)]')

        def clean():
            expect(page.locator('#editor-status')).to_have_text('Gespeichert')

        def open_picker(count=4):
            page.get_by_role('button',name='Bild auswählen',exact=True).click()
            expect(page.locator('#asset-picker-modal')).to_be_visible()
            page.locator('#asset-picker-search').fill(KEY)
            expect(page.locator('.asset-choice')).to_have_count(count)

        def choose_asset(key):
            buttons = page.locator('.asset-choice')
            for i in range(buttons.count()):
                if buttons.nth(i).get_attribute('data-asset') == assets[key]:
                    buttons.nth(i).click();break
            else:
                raise AssertionError(('Asset not found',key))
            expect(page.locator('#asset-picker-modal')).to_be_hidden()

        def order():
            return page.locator('.asset-choice').evaluate_all('(buttons)=>buttons.map(b=>b.dataset.asset)')

        select('image')
        undo = page.locator('#editor-undo')
        assert undo.inner_text() == '' and undo.locator('svg').count()==1
        assert undo.get_attribute('aria-label') == 'Rückgängig'
        edge = undo.evaluate('(b)=>({button:b.getBoundingClientRect().right,parent:b.parentElement.getBoundingClientRect().right})')
        assert abs(edge['button']-edge['parent']) < 1, edge
        assert page.locator('#editor-properties input[aria-label^=Assetpfad]').count()==0
        layer = page.get_by_label('Ebene',exact=True).bounding_box()
        up = page.get_by_role('button',name='Ebene ↑',exact=True)
        down = page.get_by_role('button',name='Ebene ↓',exact=True)
        assert up.inner_text()==down.inner_text()==''
        assert up.locator('svg').count()==down.locator('svg').count()==1
        assert up.bounding_box()['x'] > layer['x']+layer['width']
        assert down.bounding_box()['x'] > up.bounding_box()['x']
        assert up.bounding_box()['width'] == down.bounding_box()['width'] == 30

        open_picker()
        assert order()==[assets[k] for k in ['alpha','mu','beta','zeta']], order()
        page.screenshot(path='/tmp/ubb-editor-asset-picker.png')
        page.locator('#asset-picker-sort').select_option('oldest')
        assert order()==[assets[k] for k in ['zeta','beta','mu','alpha']]
        page.locator('#asset-picker-sort').select_option('name-asc')
        assert order()==[assets[k] for k in ['alpha','beta','mu','zeta']]
        page.locator('#asset-picker-sort').select_option('name-desc')
        assert order()==[assets[k] for k in ['zeta','mu','beta','alpha']]
        clean()  # Browsing, searching and sorting never change the template.
        page.locator('.asset-choice').first.focus();page.keyboard.press('ArrowRight')
        assert position()==[100,100]
        page.locator('#asset-picker-search').fill('FÖRDEBÜHNE')
        expect(page.locator('.asset-choice')).to_have_count(1)
        page.locator('.asset-choice img').evaluate('(img)=>img.decode()')
        page.locator('#asset-picker-search').press('ArrowDown')
        assert position()==[100,100]
        choose_asset('beta')
        image = page.locator('#editor-canvas [data-element-id=image] img')
        image.evaluate('(img)=>img.decode()')
        assert '%23' in image.get_attribute('src')
        expect(page.locator('#editor-status')).to_have_text('Ungespeicherte Änderungen')
        page.locator('#editor-undo').click();clean()
        image.evaluate('(img)=>img.decode()')
        assert image.get_attribute('src').endswith(assets['alpha'])

        open_picker()
        page.locator('#asset-picker-search').fill(KEY+'-no-match')
        expect(page.locator('.asset-choice')).to_have_count(0)
        expect(page.locator('#asset-picker-status')).to_have_text('Keine passenden Bilder gefunden.')
        page.keyboard.press('Escape');expect(page.locator('#asset-picker-modal')).to_be_hidden();clean()
        select('photo');open_picker();choose_asset('alpha')
        assert page.locator('#editor-canvas [data-element-id=photo] img').get_attribute('src').endswith(assets['alpha'])
        page.locator('#editor-undo').click();clean()

        select('image')
        for key, expected in [('ArrowRight',[101,100]),('ArrowLeft',[99,100]),('ArrowDown',[100,101]),('ArrowUp',[100,99])]:
            page.keyboard.press(key)
            assert position()==expected, (key,position())
            page.locator('#editor-undo').click();clean();assert position()==[100,100]
        page.keyboard.down('ArrowRight');page.keyboard.down('ArrowRight');page.keyboard.down('ArrowRight');page.keyboard.up('ArrowRight')
        assert position()==[103,100]
        page.locator('#editor-undo').click();clean();assert position()==[100,100]
        x = page.get_by_label('X',exact=True)
        x.focus();page.keyboard.press('ArrowRight');assert position()==[100,100]
        page.keyboard.press('ArrowUp');assert position()==[101,100]  # Number input changes once, not twice.
        page.locator('#editor-undo').click();clean()
        page.locator('#tab-fields').click();page.keyboard.press('ArrowDown');assert position()==[100,100]
        select('image');page.set_viewport_size({'width':850,'height':900})
        page.wait_for_function("Number(document.querySelector('#editor-wrap').dataset.scale)<1")
        page.keyboard.press('ArrowRight');assert position()==[101,100]
        page.locator('#editor-undo').click();clean()
        page.set_viewport_size({'width':1600,'height':1100})

        # Uploads appear under the original filename, with a stable addition timestamp.
        buffer = io.BytesIO();Image.new('RGB',(20,20),'purple').save(buffer,format='PNG')
        page.get_by_role('button',name='Bild auswählen',exact=True).click()
        with page.expect_response('**/api/index.php?action=assets.upload') as response:
            page.locator('#asset-picker-upload').set_input_files({'name':KEY+'-Upload.png','mimeType':'image/png','buffer':buffer.getvalue()})
        uploaded = response.value.json()['data']['asset'];created.add(ROOT/uploaded)
        expect(page.locator('#editor-status')).to_have_text('Ungespeicherte Änderungen')
        expect(page.locator('#asset-picker-modal')).to_be_hidden()
        page.get_by_role('button',name='Bild auswählen',exact=True).click()
        page.locator('#asset-picker-search').fill(KEY+'-Upload')
        expect(page.locator('.asset-choice')).to_have_count(1)
        expect(page.locator('.asset-choice')).to_have_attribute('aria-pressed','true')
        assert page.locator('.asset-choice span').inner_text()==KEY+'-Upload.png'
        page.keyboard.press('Escape');expect(page.locator('#asset-picker-modal')).to_be_hidden()
        page.locator('#editor-undo').click();clean()
        open_picker(count=5);choose_asset('beta')
        with page.expect_response('**/api/index.php?action=templates.save'):
            page.locator('#editor-save').click()
        clean();page.reload();clean()
        select('image')
        image.evaluate('(img)=>img.decode()')
        assert next(e for e in api('templates.get&id='+KEY)['elements'] if e['id']=='image')['asset']==assets['beta']
        assert '%23' in image.get_attribute('src')
        assert not errors, errors
        page.context.close();browser.close()
finally:
    for path in created:
        path.unlink(missing_ok=True)
        if (ROOT/'assets/template-assets') in path.parents:
            Path(str(path)+'.json').unlink(missing_ok=True)

print('Icon placement, searchable/sortable asset thumbnails, legacy assets and 1px keyboard movement passed')

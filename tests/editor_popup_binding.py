"""Optional popup upload, automatic naming and property layout acceptance.

Needs Playwright and Pillow, app on localhost:8080. Removes its own test data.
"""
import io
import os
from pathlib import Path
import secrets

from PIL import Image
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('UBB_TEST_URL','http://localhost:8080/')
KEY = 'binding-' + secrets.token_hex(5)
created = set()

try:
    with sync_playwright() as pw:
        options = {'headless':True}
        if os.environ.get('BROWSER_EXECUTABLE'):
            options['executable_path'] = os.environ['BROWSER_EXECUTABLE']
        browser = pw.chromium.launch(**options)
        page = browser.new_page(viewport={'width':1600,'height':1100})
        errors = []
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(BASE+'templates.php')

        def api(action, data=None, files=None):
            args = {'headers':{'X-CSRF-Token':page.locator('meta[name=csrf-token]').get_attribute('content')}}
            endpoint = BASE+'api/index.php?action='+action
            if files:
                response = page.request.post(endpoint,multipart=files,**args)
            elif data is not None:
                response = page.request.post(endpoint,data=data,**args)
            else:
                response = page.request.get(endpoint)
            result = response.json()
            assert response.ok and result['ok'],result
            return result['data']

        def file(name=KEY+'.png',content=None):
            if content is None:
                buffer = io.BytesIO();Image.new('RGB',(50,40),'purple').save(buffer,format='PNG');content=buffer.getvalue()
            return {'name':name,'mimeType':'image/png','buffer':content}

        asset = api('assets.upload',files={'image':file()})['asset'];created.add(ROOT/asset)
        geometry = dict(x=20,y=80,width=260,height=40,rotation=0,opacity=1)
        text = dict(geometry,type='text',binding={'type':'static','text':'Originalinhalt'},fontFamily='Liberation Sans',fontWeight=400,minFontSize=12,maxFontSize=30,maxLines=2,lineHeight=1.1,color='#000000')
        template = dict(schemaVersion=1,id=KEY,name=KEY,width=400,height=400,
                        fields=[dict(id=id,label=label,inputType='text',defaultValue=label,order=i*10)
                                for i,(id,label) in enumerate([('headline','Überschrift'),('date','Datum'),('location','Ort')])],
                        elements=[
                            dict(geometry,id='headline',name='Grundfläche',type='shape',x=0,y=0,width=400,height=400,zIndex=1,fillColor='#ffffff',borderRadius=0),
                            dict(geometry,id='photo',name='Foto',type='photo',x=220,y=250,width=150,height=100,zIndex=2,crop=dict(positionX=50,positionY=50,zoom=1)),
                            dict(geometry,id='image',name='Bild',type='image',y=260,width=120,height=100,zIndex=3,asset=asset,objectFit='contain'),
                            dict(text,id='text',name='Text',zIndex=4),
                            dict(text,id='legacy-id',name='Alter eigener Name',y=160,zIndex=5,binding={'type':'field','fieldId':'headline'})
                        ])
        api('templates.save',template);created.add(ROOT/'storage/templates'/(KEY+'.json'))
        page.goto(BASE+'templates.php?id='+KEY)
        expect(page.locator('.editor-layer')).to_have_count(5)

        def select(name):
            page.locator('.editor-layer').filter(has_text=name+' ·').click()

        def identity(id,name):
            expect(page.get_by_label('ID',exact=True)).to_have_value(id)
            expect(page.get_by_label('Name',exact=True)).to_have_value(name)

        def save():
            with page.expect_response('**/api/index.php?action=templates.save') as response:
                page.locator('#editor-save').click()
            assert response.value.ok
            expect(page.locator('#editor-status')).to_have_text('Gespeichert')

        def linked(value):
            page.get_by_label('Feldverknüpfung',exact=True).select_option(value)

        select('Text')
        expect(page.get_by_label('Textart',exact=True)).to_have_value('static')
        page.get_by_label('Textart',exact=True).select_option('field')
        identity('headline-2','Überschrift')  # The existing shape's ID cannot be overwritten.
        before = page.get_by_label('Feldverknüpfung',exact=True).evaluate("select=>!!(select.compareDocumentPosition(document.querySelector('[aria-label=\"ID\"]'))&Node.DOCUMENT_POSITION_FOLLOWING)")
        assert before
        linked('date');identity('date','Datum')
        page.locator('#editor-undo').click();identity('headline-2','Überschrift')
        expect(page.get_by_label('Feldverknüpfung',exact=True)).to_have_value('headline')
        page.get_by_label('ID',exact=True).fill('eigene-id')
        linked('date');identity('eigene-id','Datum')
        page.get_by_label('Name',exact=True).fill('Eigener Textname')
        linked('location');identity('eigene-id','Eigener Textname')
        save();page.reload();select('Eigener Textname')
        linked('headline');identity('eigene-id','Eigener Textname')
        stored = next(e for e in api('templates.get&id='+KEY)['elements'] if e['id']=='eigene-id')
        assert stored['naming']=={'id':'manual','name':'manual'}
        save()

        # Existing descriptive identities, without the new flags, remain intact.
        select('Alter eigener Name');linked('date');identity('legacy-id','Alter eigener Name')
        page.locator('#editor-undo').click();identity('legacy-id','Alter eigener Name')
        page.locator('[data-add=text]').click();identity('headline-2','Überschrift')
        page.get_by_label('Name',exact=True).fill('Temporär manuell')
        page.locator('#editor-undo').click();identity('headline-2','Überschrift')
        linked('date');identity('date','Datum')  # Undo also restored automatic naming.
        page.get_by_label('Name',exact=True).fill('Nur eigener Name')
        linked('headline');identity('headline-2','Nur eigener Name')
        save();page.reload();select('Nur eigener Name')
        linked('date');identity('date','Nur eigener Name')
        linked('headline');identity('headline-2','Nur eigener Name')
        page.locator('[data-add=text]').click();identity('headline-3','Überschrift')
        ids = [node['id'] for node in api('templates.get&id='+KEY)['elements']]
        assert len(ids)==len(set(ids))
        save()
        ids = [node['id'] for node in api('templates.get&id='+KEY)['elements']]
        assert len(ids)==len(set(ids))

        headings = page.locator('#editor-properties .editor-property-section h3').all_text_contents()
        assert headings==['Canvas-Eigenschaften','Textfeld-Eigenschaften','Positionierung','Größe','Schriftformate','Aktionen'],headings
        separator = page.locator('.editor-property-section').nth(1).evaluate("section=>{const css=getComputedStyle(section,':before');return {width:parseFloat(css.width),parent:section.clientWidth,line:css.borderTopWidth,color:css.borderTopColor,margin:parseFloat(css.marginTop)}}")
        assert 0 < separator['width'] < separator['parent'] and separator['line']=='1px' and separator['margin']>10,separator
        page.locator('#editor-properties').evaluate('(node)=>node.parentElement.scrollTop=0')
        page.screenshot(path='/tmp/ubb-editor-properties.png')

        # All image uploads now live in the popup and select the uploaded image.
        for name,element_id in [('Bild','image'),('Foto','photo')]:
            select(name)
            assert page.locator('#editor-properties input[type=file]').count()==0
            if element_id=='photo':
                expect(page.locator('#editor-canvas [data-element-id=photo] .photo-empty')).to_have_text('Platzhalter')
            page.get_by_role('button',name='Bild auswählen',exact=True).click()
            expect(page.locator('#asset-picker-upload')).to_be_visible()
            if element_id=='image':
                page.screenshot(path='/tmp/ubb-editor-popup-upload.png')
            with page.expect_response('**/api/index.php?action=assets.upload') as response:
                page.locator('#asset-picker-upload').set_input_files(file(KEY+'-'+element_id+'.png'))
            created.add(ROOT/response.value.json()['data']['asset'])
            expect(page.locator('#asset-picker-modal')).to_be_hidden()
            expect(page.locator('#editor-canvas [data-element-id='+element_id+'] img')).to_have_count(1)
            expect(page.locator('#editor-status')).to_have_text('Ungespeicherte Änderungen')
            page.locator('#editor-undo').click()
            expect(page.locator('#editor-status')).to_have_text('Gespeichert')
        expect(page.locator('#editor-canvas [data-element-id=photo] .photo-empty')).to_have_text('Platzhalter')

        # Upload errors stay in the popup and leave the template untouched.
        page.get_by_role('button',name='Bild auswählen',exact=True).click()
        with page.expect_response('**/api/index.php?action=assets.upload') as response:
            page.locator('#asset-picker-upload').set_input_files(file('bad.png',b'not an image'))
        assert response.value.status==400
        expect(page.locator('#asset-picker-upload-status')).to_contain_text('kein erlaubtes Bild')
        expect(page.locator('#asset-picker-modal')).to_be_visible()
        page.keyboard.press('Escape')
        expect(page.locator('#editor-status')).to_have_text('Gespeichert')

        # Closing the popup during an upload cancels assignment, not the library upload.
        pending=[]
        hold=lambda route:pending.append(route)
        page.route('**/api/index.php?action=assets.upload',hold)
        page.get_by_role('button',name='Bild auswählen',exact=True).click()
        page.locator('#asset-picker-upload').set_input_files(file(KEY+'-cancelled.png'))
        expect(page.locator('#editor-status')).to_have_text('Bild wird hochgeladen …')
        page.keyboard.press('Escape')
        with page.expect_response('**/api/index.php?action=assets.upload') as response:
            pending.pop().continue_()
        created.add(ROOT/response.value.json()['data']['asset'])
        page.unroute('**/api/index.php?action=assets.upload',hold)
        expect(page.locator('#editor-status')).to_have_text('Gespeichert')
        expect(page.locator('#editor-canvas [data-element-id=photo] img')).to_have_count(0)
        page.goto(BASE+'?template='+KEY)
        expect(page.locator('#canvas [data-element-id=photo] .photo-empty')).to_have_text('Platzhalter')
        assert not errors,errors
        page.context.close();browser.close()
finally:
    for path in created:
        path.unlink(missing_ok=True)
        if (ROOT/'assets/template-assets') in path.parents:
            Path(str(path)+'.json').unlink(missing_ok=True)

print('Popup uploads, placeholder, field-derived naming, manual overrides, persistence and property sections passed')

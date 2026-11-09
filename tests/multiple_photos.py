"""Optional multi-photo acceptance: Playwright, Pillow, PyMuPDF; localhost:8080.

Uses uniquely named test data and hashes existing archives before and after.
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

ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('UBB_TEST_URL','http://localhost:8080/')
KEY='photos-'+secrets.token_hex(5)
created=set()
original={path:hashlib.sha256(path.read_bytes()).digest() for path in (ROOT/'storage/exports').rglob('*') if path.is_file()}


def png(color):
    image=Image.new('RGB',(300,180),color)
    for x in range(300):
        for y in range(180):
            if (x//30+y//30)%2:
                image.putpixel((x,y),(35,60,95))
    buffer=io.BytesIO();image.save(buffer,format='PNG');return buffer.getvalue()


def file(name,content):
    return {'name':name,'mimeType':'image/png','buffer':content}


try:
    with sync_playwright() as pw:
        launch={'headless':True}
        if os.environ.get('BROWSER_EXECUTABLE'):
            launch['executable_path']=os.environ['BROWSER_EXECUTABLE']
        browser=pw.chromium.launch(**launch)
        page=browser.new_page(viewport={'width':1600,'height':1100},accept_downloads=True)
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(BASE)

        def api(action,data=None,files=None,expected=200):
            args={'headers':{'X-CSRF-Token':page.locator('meta[name=csrf-token]').get_attribute('content')}}
            endpoint=BASE+'api/index.php?action='+action
            if files:
                response=page.request.post(endpoint,multipart=dict(data or {},**files),**args)
            elif data is not None:
                response=page.request.post(endpoint,data=data,**args)
            else:
                response=page.request.get(endpoint)
            result=response.json();assert response.status==expected,(action,response.status,result)
            return result.get('data',result)

        def keep(item):
            for path in [item['url'],item['url']+'.json',item.get('previewUrl',item['url'])]:
                created.add(ROOT/path)
            return item

        def export(kind='png',scale=1):
            def watch(selector,event):
                page.evaluate("""({selector,event})=>{window.photoTestModal=new Promise(resolve=>document.querySelector(selector).addEventListener(event,()=>resolve(true),{once:true}))}""",{'selector':selector,'event':event})
            def wait():
                page.evaluate("""()=>Promise.race([window.photoTestModal,new Promise((_,reject)=>setTimeout(()=>reject(Error('Modal transition timed out')),5000))])""")
            watch('#export-modal','shown.bs.modal');page.locator('#export-open').click();wait()
            page.locator('#export-name').fill(KEY);page.locator('#export-format').select_option(kind);page.locator('#export-scale').select_option(str(scale))
            watch('#result-modal','shown.bs.modal');page.locator('#export-submit').click()
            page.wait_for_function("()=>document.querySelector('#result-modal').classList.contains('show')||!document.querySelector('#export-error').classList.contains('d-none')",timeout=120000)
            assert not page.locator('#export-error').is_visible(),page.locator('#export-error').inner_text()
            wait();name=page.locator('#result-name').inner_text()
            item=keep(next(item for item in api('exports.list') if item['filename']==name))
            assert item['canRestore']
            watch('#result-modal','hidden.bs.modal');page.locator('#result-modal .btn-close').click();wait()
            return item,api('exports.get&id='+item['id'])['generatorState']

        def select(id):
            page.locator('[data-photo-id='+id+']').click()

        def crop(x,y,zoom):
            for selector,value in [('#photo-x',x),('#photo-y',y),('#photo-zoom',zoom)]:
                page.locator(selector).evaluate('(input,value)=>{input.value=value;input.dispatchEvent(new Event("input",{bubbles:true}))}',str(value))

        def choose(id,background):
            page.locator('[data-photo-choice='+id+']').click()
            page.locator('#gallery-search').fill(background['filename'])
            expect(page.locator('#gallery-grid .gallery-item')).to_have_count(1)
            page.locator('#gallery-grid .gallery-item').click()
            expect(page.locator('#gallery-modal')).to_be_hidden()

        def open_upload(id):
            page.locator('[data-photo-choice='+id+']').click()
            page.locator('#gallery-upload').click()
            expect(page.locator('#upload-modal')).to_be_visible()

        def source(id):
            return page.locator('#canvas [data-element-id='+id+'] img').get_attribute('src')

        def appearance(id):
            return page.locator('#canvas [data-element-id='+id+'] img').evaluate('(img)=>({src:img.src,position:img.style.objectPosition,zoom:img.style.transform})')

        red=api('assets.upload',files={'image':file(KEY+'-red.png',png('#df3040'))})['asset'];created.add(ROOT/red)
        blue=api('assets.upload',files={'image':file(KEY+'-blue.png',png('#2070ef'))})['asset'];created.add(ROOT/blue)
        backgrounds=[]
        for name,color in [('a','#20d060'),('b','#f0c020'),('c','#20c0d0')]:
            background=api('backgrounds.upload',files={'image':file(KEY+'-'+name+'.png',png(color))})
            created.add(ROOT/background['url']);backgrounds.append(background)
        a,b,c=backgrounds
        geometry=dict(y=20,width=250,height=140,rotation=0,opacity=1)
        template=dict(schemaVersion=1,id=KEY,name=KEY,width=600,height=400,
                      fields=[dict(id='title',label='Titel',inputType='text',defaultValue='Viele Fotos',order=10)],elements=[
                          dict(id='base',name='Fläche',type='shape',x=0,y=0,width=600,height=400,rotation=0,opacity=1,zIndex=1,fillColor='#eeeeee',borderRadius=0),
                          dict(geometry,id='left',name='Links',type='photo',x=20,zIndex=2,asset=red,crop=dict(positionX=10,positionY=20,zoom=1.1)),
                          dict(geometry,id='right',name='Rechts',type='photo',x=330,zIndex=3,asset=blue,crop=dict(positionX=80,positionY=70,zoom=1.2)),
                          dict(geometry,id='extra',name='Zusatz',type='photo',x=20,y=230,zIndex=4,crop=dict(positionX=50,positionY=50,zoom=1)),
                          dict(id='fixed',name='Festes Bild',type='image',x=330,y=230,width=90,height=70,rotation=0,opacity=1,zIndex=5,asset=red,objectFit='contain'),
                          dict(id='title',name='Titel',type='text',x=330,y=315,width=250,height=50,rotation=0,opacity=1,zIndex=6,binding=dict(type='field',fieldId='title'),fontFamily='Liberation Sans',fontWeight=400,minFontSize=20,maxFontSize=32,maxLines=1,lineHeight=1.1,color='#111111')
                      ])
        api('templates.save',template);created.add(ROOT/'storage/templates'/(KEY+'.json'))
        page.goto(BASE+'?template='+KEY)
        expect(page.locator('[data-photo-id]')).to_have_count(3)
        expect(page.get_by_role('heading',name='Foto-Element auswählen',exact=True)).to_be_visible()
        assert page.locator('#background-mini,#gallery-open,#upload-open').count()==0
        expect(page.locator('[data-photo-choice]')).to_have_count(3)
        expect(page.locator('#photo-settings-heading')).to_have_text('Einstellungen für: Links')
        select('right')
        expect(page.locator('#photo-settings-heading')).to_have_text('Einstellungen für: Rechts')
        expect(page.locator('#photo-tools')).to_have_attribute('data-active-photo-id','right')
        colors=page.evaluate("""()=>{
            const card=document.querySelector('.generator-photo-card.active'),tools=document.querySelector('#photo-tools');
            return [getComputedStyle(card).backgroundColor,getComputedStyle(tools).backgroundColor,getComputedStyle(card).borderTopColor,getComputedStyle(tools).borderTopColor];
        }""")
        assert colors[0]==colors[1] and colors[2]==colors[3],colors
        assert source('left').endswith(red) and source('right').endswith(blue)
        assert appearance('left')['position']=='10% 20%' and appearance('right')['zoom']=='scale(1.2)'
        expect(page.locator('#canvas [data-element-id=extra] .photo-empty')).to_have_text('Platzhalter')
        choose('left',a);crop(14,81,1.8);left=appearance('left')
        assert source('right').endswith(blue)
        choose('right',b);crop(89,17,1.4);assert appearance('left')==left
        open_upload('extra')
        page.locator('#upload-file').set_input_files(file(KEY+'-extra.png',png('purple')))
        with page.expect_response('**/api/index.php?action=backgrounds.upload') as response:
            page.locator('#upload-submit').click()
        extra=response.value.json()['data'];created.add(ROOT/extra['url'])
        expect(page.locator('#upload-modal')).to_be_hidden();crop(30,55,2.1)
        assert source('extra').endswith(extra['filename']) and source('left').endswith(a['filename']) and source('right').endswith(b['filename'])
        assert source('fixed').endswith(red)
        select('right');page.locator('#background-default').click()
        assert source('right').endswith(blue) and appearance('right')['position']=='80% 70%'
        assert appearance('left')==left and source('extra').endswith(extra['filename'])
        choose('right',b);crop(89,17,1.4);page.locator('#photo-reset').click()
        assert source('right').endswith(b['filename']) and appearance('right')['zoom']=='scale(1)'
        assert appearance('left')==left
        crop(89,17,1.4);select('left')
        box=page.locator('#canvas [data-element-id=right]').bounding_box()
        page.mouse.move(box['x']+40,box['y']+40);page.mouse.down();page.mouse.move(box['x']+70,box['y']+55,steps=4);page.mouse.up()
        expect(page.locator('[data-photo-id=right]')).to_have_attribute('aria-pressed','true')
        assert appearance('right')['position']=='99% 22%' and appearance('left')==left
        page.screenshot(path='/tmp/ubb-generator-multiple-photos.png')
        first,saved=export()
        assert saved['version']==2 and set(saved['photos'])=={'left','right','extra'}
        assert saved['photos']['left']==dict(background=a['filename'],positionX=14,positionY=81,zoom=1.8)
        assert saved['photos']['right']==dict(background=b['filename'],positionX=99,positionY=22,zoom=1.4)
        assert saved['photos']['extra']==dict(background=extra['filename'],positionX=30,positionY=55,zoom=2.1)
        pdf,pdf_state=export('pdf');assert pdf_state==saved
        with fitz.open(ROOT/pdf['url']) as document:
            assert 'Viele Fotos' in document[0].get_text()
            assert document[0].get_fonts() and all(document.extract_font(font[0])[3] for font in document[0].get_fonts())
            raster=document[0].get_pixmap(matrix=fitz.Matrix(4/3,4/3))
            image=Image.frombytes('RGB',(raster.width,raster.height),raster.samples)
            diff=ImageChops.difference(image,Image.open(ROOT/first['url']).convert('RGB'))
            assert sum(ImageStat.Stat(diff).mean)/3<2.5
        _,jpg_state=export('jpg',2);assert jpg_state==saved
        api('templates.delete',{'id':KEY})
        page.goto(BASE+'?export='+first['id']);expect(page.locator('[data-photo-id]')).to_have_count(3)
        for id in ['left','right','extra']:
            select(id)
            assert page.locator('#photo-zoom').input_value()==str(saved['photos'][id]['zoom'])
            assert source(id).endswith(saved['photos'][id]['background'])
        restored,restored_state=export();assert restored_state==saved
        assert (ROOT/restored['url']).read_bytes()==(ROOT/first['url']).read_bytes()
        select('left');crop(14,81,1.93)
        _,changed=export();assert changed['photos']['right']==saved['photos']['right'] and changed['photos']['extra']==saved['photos']['extra']
        assert changed['photos']['left']['zoom']==1.93

        # Real legacy v1 variants retain the global photo appearance on load.
        for global_background in [c,None]:
            for id in ['left','right','extra']:
                if global_background:
                    choose(id,global_background)
                else:
                    select(id);page.locator('#background-default').click()
                crop(12,77,1.6)
            visual,visual_state=export()
            legacy=dict(version=1,template=visual_state['template'],fields=visual_state['fields'],background=global_background['filename'] if global_background else None,
                        photo=dict(positionX=12,positionY=77,zoom=1.6),textOverrides=visual_state['textOverrides'])
            item=keep(api('exports.save',{'metadata':json.dumps(dict(format='png',scale=1,filename=KEY+'-legacy',templateId=KEY,generatorState=legacy))},
                          {'image':file('export.png',(ROOT/visual['url']).read_bytes())}))
            sidecar=ROOT/(item['url']+'.json');digest=hashlib.sha256(sidecar.read_bytes()).digest()
            page.goto(BASE+'?export='+item['id']);expect(page.locator('[data-photo-id]')).to_have_count(3)
            for id in ['left','right','extra']:
                select(id);assert page.locator('#photo-zoom').input_value()=='1.6'
                if global_background:
                    assert source(id).endswith(global_background['filename'])
                elif id!='extra':
                    assert appearance(id)['position']=='12% 77%'
            converted,new_state=export();assert new_state['version']==2
            assert (ROOT/converted['url']).read_bytes()==(ROOT/visual['url']).read_bytes()
            assert hashlib.sha256(sidecar.read_bytes()).digest()==digest

        # Every photo slot must be present and reference only a valid background.
        for change in ['missing','unknown','path','zoom','version']:
            invalid=copy.deepcopy(saved)
            if change=='missing': del invalid['photos']['extra']
            if change=='unknown': invalid['photos']['unknown']=invalid['photos'].pop('extra')
            if change=='path': invalid['photos']['left']['background']='../secret.png'
            if change=='zoom': invalid['photos']['left']['zoom']=99
            if change=='version': invalid['version']=99
            api('exports.save',{'metadata':json.dumps(dict(format='png',scale=1,templateId=KEY,generatorState=invalid))},
                {'image':file('export.png',(ROOT/first['url']).read_bytes())},expected=400)

        # An upload keeps its original target even if another photo is selected meanwhile.
        select('left');before_right=appearance('right');pending=[]
        hold=lambda route:pending.append(route)
        page.route('**/api/index.php?action=backgrounds.upload',hold)
        open_upload('left');page.locator('#upload-file').set_input_files(file(KEY+'-late.png',png('orange')))
        page.locator('#upload-submit').click();expect(page.locator('#upload-submit')).to_be_disabled()
        page.locator('#upload-modal .btn-close').click();select('right')
        with page.expect_response('**/api/index.php?action=backgrounds.upload') as response:
            pending.pop().continue_()
        late=response.value.json()['data'];created.add(ROOT/late['url'])
        page.unroute('**/api/index.php?action=backgrounds.upload',hold)
        page.wait_for_function("filename=>document.querySelector('#canvas [data-element-id=left] img').src.endsWith(filename)",arg=late['filename'])
        assert appearance('right')==before_right
        static=dict(template,id=KEY+'-static',fields=[],elements=[template['elements'][0],template['elements'][4]])
        api('templates.save',static);created.add(ROOT/'storage/templates'/(static['id']+'.json'))
        page.goto(BASE+'?template='+static['id'])
        expect(page.locator('#photo-empty-message')).to_be_visible();expect(page.locator('#photo-tools')).to_be_hidden()
        expect(page.locator('[data-photo-id]')).to_have_count(0)
        _,empty=export();assert not empty['photos'] and empty['version']==2
        assert not errors,errors
        page.context.close();browser.close()
finally:
    for path in created:
        path.unlink(missing_ok=True)
        if (ROOT/'assets/template-assets') in path.parents:
            Path(str(path)+'.json').unlink(missing_ok=True)
    for path,digest in original.items():
        assert path.exists() and hashlib.sha256(path.read_bytes()).digest()==digest,('Existing archive changed',path)

print('Independent photos/crops/uploads, PNG/JPG/PDF, restoration, legacy v1 and empty-photo templates passed')

"""Unicode asset path and containment test; run while Docker serves localhost:8080."""
import base64
import http.cookiejar
import json
import re
import uuid
import urllib.error
import urllib.request
from pathlib import Path

root=Path(__file__).resolve().parents[1]
asset=root/'assets/template-assets/2026_UBB-KiWo-Fördebühne.png'
created=not asset.exists()
if created:
    asset.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/CwAAAABJRU5ErkJggg=='))
escape=asset.parent/'__asset-escape.png'
escape_created=not escape.exists() and not escape.is_symlink()
if escape_created:
    escape.symlink_to(root/'README.md')

opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
base='http://localhost:8080/'
html=opener.open(base).read().decode()
token=re.search(r'name="csrf-token" content="([^"]+)',html).group(1)

def request(action,data=None):
    headers={'X-CSRF-Token':token}
    body=None
    if data is not None:
        body=json.dumps(data,ensure_ascii=False).encode()
        headers['Content-Type']='application/json'
    req=urllib.request.Request(base+'api/index.php?action='+action,data=body,headers=headers)
    try:
        with opener.open(req) as response:return response.status,json.load(response)
    except urllib.error.HTTPError as error:return error.code,json.load(error)

template_id='asset-unicode-'+uuid.uuid4().hex[:8]
try:
    status,result=request('templates.get&id=standard-magenta')
    assert status==200,result
    template=result['data']
    template['id']=template_id
    template['name']='Unicode Asset Test'
    template['elements'].append({'id':'unicode-image','name':'Unicode Bild','type':'image',
        'asset':'assets/template-assets/2026_UBB-KiWo-Fördebühne.png','objectFit':'contain',
        'x':0,'y':0,'width':100,'height':100,'rotation':0,'opacity':1,'zIndex':999})
    template['createOnly']=True
    status,result=request('templates.save',template)
    assert status==200,result
    assert result['data']['elements'][-1]['asset'].endswith('Fördebühne.png')

    for bad in ('assets/template-assets/../escape.png','assets/template-assets-evil/logo.png',
                'assets/template-assets/__asset-escape.png'):
        rejected=dict(template,createOnly=False)
        rejected['elements']=[*template['elements'][:-1],dict(template['elements'][-1],asset=bad)]
        status,result=request('templates.save',rejected)
        assert status==400 and result['error']=='INVALID_ASSET',(bad,status,result)

    status,result=request('templates.get&id='+template_id)
    assert status==200 and result['data']['elements'][-1]['asset'].endswith('Fördebühne.png')
    print('Unicode asset saved; invalid paths rejected without damaging template')
finally:
    request('templates.delete',{'id':template_id})
    if created:asset.unlink()
    if escape_created:escape.unlink()

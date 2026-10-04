"""Run with: python3 tests/smoke.py (Docker application on localhost:8080)."""
import http.cookiejar
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

BASE = 'http://localhost:8080/'
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
html = opener.open(BASE).read().decode()
token = re.search(r'name="csrf-token" content="([^"]+)', html).group(1)


def call(action, data=None, files=None, expected=200):
    headers = {'X-CSRF-Token': token}
    if files:
        boundary = 'UBBTestBoundary'
        chunks = []
        for key, value in (data or {}).items():
            chunks += [f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode()]
        for key, (name, mime, content) in files.items():
            chunks += [f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'.encode() + content + b'\r\n']
        body = b''.join(chunks) + f'--{boundary}--\r\n'.encode()
        headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
    elif data is not None:
        body = json.dumps(data).encode()
        headers['Content-Type'] = 'application/json'
    else:
        body = None
    request = urllib.request.Request(BASE + 'api/index.php?action=' + action, data=body, headers=headers)
    try:
        with opener.open(request) as response:
            status, result = response.status, json.load(response)
    except urllib.error.HTTPError as error:
        status, result = error.code, json.load(error)
    assert status == expected, (action, status, result)
    assert result['ok'] == (expected < 400), result
    assert result['requestId'], result
    return result.get('data', result)


templates = call('templates.list')
assert any(x['id'] == 'standard-magenta' for x in templates)
standard = call('templates.get&id=standard-magenta')
assert standard['width'] == standard['height'] == 1138
copy = dict(standard, id='smoke-test', name='Smoke Test')
call('templates.save', copy)
assert call('templates.get&id=smoke-test')['name'] == 'Smoke Test'
call('templates.duplicate', {'sourceId': 'smoke-test', 'id': 'smoke-test-copy', 'name': 'Smoke Test Copy'})
call('templates.delete', {'id': 'smoke-test-copy'})
call('templates.delete', {'id': 'smoke-test'})

image = Path('reference/UBB-150-J-Neuwittenbek_v1.png').read_bytes()
uploaded = call('backgrounds.upload', files={'image': ('test-über.jpg', 'image/jpeg', image)})
assert uploaded['filename'].endswith('.png')
call('backgrounds.upload', files={'image': ('bad.png', 'image/png', b'not an image')}, expected=400)
assert any(x['filename'] == uploaded['filename'] for x in call('backgrounds.list'))

metadata = {'filename': 'API-Smoke', 'format': 'png', 'scale': 1, 'templateId': 'standard-magenta'}
saved = call('exports.save', {'metadata': json.dumps(metadata)}, {'image': ('export.png', 'image/png', image)})
assert saved['width'] == saved['height'] == 1138
assert saved['filename'].endswith('.png')
assert any(x['id'] == saved['id'] for x in call('exports.list'))
Path('storage/backgrounds', uploaded['filename']).unlink()
Path(saved['url']).unlink()
Path(saved['url'] + '.json').unlink()
print('API smoke tests passed')

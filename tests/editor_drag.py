"""Optional canvas interaction: PYTHONPATH=/tmp/ubb-playwright python3 tests/editor_drag.py."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

path=Path('storage/templates/editor-test.json')
original=json.loads(path.read_text())
before=next(x for x in original['elements'] if x['id']=='text')
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1600,'height':1000})
    page.goto('http://localhost:8080/templates.php?id=editor-test')
    page.locator('#editor-elements .editor-layer').filter(has_text='Text').click()
    node=page.locator('#editor-canvas [data-element-id="text"]')
    box=node.bounding_box()
    page.mouse.move(box['x']+30,box['y']+30)
    page.mouse.down()
    page.mouse.move(box['x']+60,box['y']+50,steps=3)
    page.mouse.up()
    handle=page.locator('#editor-canvas .editor-selected .resize-handle').bounding_box()
    page.mouse.move(handle['x']+5,handle['y']+5)
    page.mouse.down()
    page.mouse.move(handle['x']+25,handle['y']+25,steps=3)
    page.mouse.up()
    page.locator('#editor-save').click()
    page.get_by_text('Template gespeichert').first.wait_for()
    browser.close()
after=json.loads(path.read_text())
changed=next(x for x in after['elements'] if x['id']=='text')
assert changed['x']!=before['x'] and changed['y']!=before['y'], (before,changed)
assert changed['width']!=before['width'] and changed['height']!=before['height'], (before,changed)
print('Editor drag and resize saved:',changed['x'],changed['y'],changed['width'],changed['height'])

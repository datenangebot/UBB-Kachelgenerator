"""Optional editor workflow: PYTHONPATH=/tmp/ubb-playwright python3 tests/editor.py."""
from playwright.sync_api import sync_playwright
from uuid import uuid4

name='Editor Test '+uuid4().hex[:6]
template_id=name.lower().replace(' ','-')

with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1600,'height':1000})
    errors=[]
    page.on('pageerror',lambda error: errors.append(str(error)))
    page.goto('http://localhost:8080/templates.php')
    prompts=iter([name,'leer','600','600'])
    page.on('dialog',lambda dialog: dialog.accept(next(prompts,'')))
    page.locator('#new-template').click()
    page.locator('#editor-view').wait_for(state='visible')
    page.locator('[data-add="shape"]').click()
    page.locator('[data-add="text"]').click()
    page.locator('#editor-save').click()
    page.get_by_text('Template gespeichert').first.wait_for()
    page.reload()
    page.locator('#editor-view').wait_for(state='visible') if 'id=' in page.url else None
    page.goto('http://localhost:8080/templates.php?id='+template_id)
    page.locator('#editor-elements .editor-layer').first.wait_for()
    assert page.locator('#editor-elements .editor-layer').count()==2
    assert not errors, errors
    result=page.evaluate('''async id => {const response=await fetch('api/index.php?action=templates.delete',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content},body:JSON.stringify({id})});return await response.json()}''',template_id)
    assert result['ok'],result
    browser.close()
    print('Editor create/add/save/reload passed')

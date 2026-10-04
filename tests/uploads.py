"""Optional upload acceptance: PYTHONPATH=/tmp/ubb-playwright python3 tests/uploads.py."""
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True)
    page=browser.new_page()
    page.goto('http://localhost:8080/')
    page.locator('#template-select option').first.wait_for(state='attached')
    page.locator('#template-select').select_option('standard-magenta')
    page.locator('#fields textarea').first.wait_for()
    for mime, ext in [('image/jpeg','jpg'),('image/webp','webp')]:
        result=page.evaluate('''async ({mime,ext}) => {
          const canvas=document.createElement('canvas');canvas.width=8;canvas.height=8;
          canvas.getContext('2d').fillRect(0,0,8,8);
          const blob=await new Promise(resolve=>canvas.toBlob(resolve,mime));
          const form=new FormData();form.append('image',blob,'../format-test.'+ext);
          const response=await fetch('api/index.php?action=backgrounds.upload',{method:'POST',headers:{'X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content},body:form});
          return {status:response.status,result:await response.json()};
        }''',{'mime':mime,'ext':ext})
        assert result['status']==200,result
        filename=result['result']['data']['filename']
        assert filename.endswith('.'+ext) and '/' not in filename, filename
        Path('storage/backgrounds',filename).unlink()
    oversized=page.evaluate('''async () => {
      const form=new FormData();form.append('image',new Blob([new Uint8Array(21*1024*1024)],{type:'image/png'}),'large.png');
      const response=await fetch('api/index.php?action=backgrounds.upload',{method:'POST',headers:{'X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content},body:form});
      return {status:response.status,result:await response.json()};
    }''')
    assert oversized['status']==413,oversized
    browser.close()
    print('JPEG/WebP uploads, safe filename, and 20 MB rejection passed')

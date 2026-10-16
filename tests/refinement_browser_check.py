"""v4 regression checks: conservative UI, recovery, keyboard and tab ownership."""
import io
import json
from pathlib import Path
import sys
from PIL import Image
from playwright.sync_api import sync_playwright

URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:18738'
OUT=Path(__file__).parent/'artifacts';OUT.mkdir(exist_ok=True)
data=io.BytesIO();Image.new('RGB',(1200,900),(100,145,95)).save(data,'PNG')
files=[{'name':f'Revisao-{i}.png','mimeType':'image/png','buffer':data.getvalue()} for i in range(1,4)]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    context=browser.new_context(viewport={'width':1366,'height':768})
    page=context.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(URL);page.wait_for_function("!document.querySelector('[data-template=square]').disabled")
    assert page.locator('select').count()==0
    assert page.locator('[data-template]').count()==4
    page.locator('#files').set_input_files(files)
    page.wait_for_function("document.querySelector('#count').textContent==='3'&&!document.querySelector('#export').disabled")
    page.wait_for_timeout(650)
    layout=page.evaluate('''()=>{const p=document.getElementById('tile-frame').getBoundingClientRect(),e=document.getElementById('export').getBoundingClientRect();return {previewWidth:p.width,previewBottom:p.bottom,exportBottom:e.bottom,height:innerHeight}}''')
    assert layout['previewWidth']>=350,layout
    assert layout['previewBottom']<layout['height'],layout
    assert layout['exportBottom']<layout['height'],layout
    page.screenshot(path=str(OUT/'v4-desktop-1366.png'),full_page=True)
    page.get_by_role('button',name='Remover foto Revisao-3.png').press('Enter')
    page.wait_for_function("document.querySelector('#count').textContent==='2'")
    page.get_by_role('button',name='Mover para baixo Revisao-1.png').press('Space')
    page.wait_for_function("document.querySelector('.photo-detail strong').textContent==='Revisao-2.png'")
    page.locator('#brightness-number').fill('17');page.locator('#brightness-number').press('Enter')
    page.get_by_role('button',name='Button Redondo M',exact=True).click()
    page.wait_for_timeout(600)
    before=page.evaluate('JSON.parse(localStorage.getItem("moldura-session"))')
    page.route('**/api/preview',lambda route:route.fulfill(status=503,content_type='application/json',body='{"error":"Falha temporária simulada"}'))
    page.reload();page.wait_for_function("document.querySelector('#count').textContent==='2'&&!document.querySelector('[data-template=round_m]').disabled")
    assert page.locator('#retry-preview').is_visible()
    assert page.locator('#brightness-number').input_value()=='17'
    assert page.evaluate('JSON.parse(localStorage.getItem("moldura-session")).photos.length')==2
    page.unroute('**/api/preview');page.locator('#retry-preview').click()
    page.wait_for_function("document.querySelector('#retry-preview').hidden")
    second=context.new_page();second.on('pageerror',lambda error:errors.append(str(error)));second.goto(URL)
    second.wait_for_function("document.querySelector('#count').textContent==='2'")
    assert second.locator('#session-banner').is_visible()
    assert second.locator('#brightness-number').is_disabled()
    # Programmatic input on a read-only tab must also be ignored by the handler.
    second.locator('#brightness-number').evaluate("e=>{e.value='99';e.dispatchEvent(new Event('input',{bubbles:true}));}")
    saved=second.evaluate('JSON.parse(localStorage.getItem("moldura-session"))')
    assert round((saved['photos'][0]['edits']['brightness']-1)*100)==0  # Selected photo is the second item.
    selected=next(photo for photo in saved['photos'] if photo['id']==saved['selected'])
    assert round((selected['edits']['brightness']-1)*100)==17
    second.locator('#takeover').click()
    second.wait_for_function("!document.querySelector('#brightness-number').disabled")
    assert page.locator('#brightness-number').is_disabled()
    second.locator('#brightness-number').fill('25');second.locator('#brightness-number').press('Enter')
    try:
        page.wait_for_function("document.querySelector('#brightness-number').value==='25'",timeout=6000)
    except Exception:
        print('TAB STATE',page.evaluate('({sessionRevision,restoring,pendingRestore,editingAllowed,photos})'))
        print('STORAGE',second.evaluate('JSON.parse(localStorage.getItem("moldura-session"))'))
        raise
    page.close();second.wait_for_timeout(200)
    saved=second.evaluate('JSON.parse(localStorage.getItem("moldura-session"))')
    selected=next(photo for photo in saved['photos'] if photo['id']==saved['selected'])
    assert round((selected['edits']['brightness']-1)*100)==25
    second.locator('#guides').click();assert second.locator('#safe-guide').is_hidden()
    second.locator('#guides').click();assert second.locator('#safe-guide').is_visible()
    second.locator('#zoom-number').fill('1.65');second.locator('#zoom-number').press('Enter')
    second.locator('#center').click();saved=second.evaluate('JSON.parse(localStorage.getItem("moldura-session"))');selected=next(photo for photo in saved['photos'] if photo['id']==saved['selected'])
    assert selected['edits']['cx']==selected['edits']['cy']==.5 and selected['edits']['zoom']==1.65 and selected['edits']['brightness']==1.25
    second.wait_for_timeout(700);second.get_by_role('button',name='Ampliar folha 1',exact=True).click()
    assert second.locator('#sheet-dialog').is_visible();second.keyboard.press('Escape');assert not second.locator('#sheet-dialog').is_visible()
    second.locator('#help').click();assert second.locator('#help-dialog').is_visible();second.keyboard.press('Escape')
    mobile=[]
    for width in (740,600,390,320):
        second.set_viewport_size({'width':width,'height':844});second.wait_for_timeout(150)
        assert second.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
        assert second.locator('.adjustment label').evaluate_all('''labels=>labels.every(label=>{
          const node=[...label.childNodes].find(n=>n.nodeType===Node.TEXT_NODE&&n.textContent.trim());
          const range=document.createRange();range.selectNodeContents(node);
          return label.querySelector('input').getBoundingClientRect().left>=range.getBoundingClientRect().right+3;
        })'''),('Label and number overlap',width)
        mobile.append(width)
    second.evaluate('window.scrollTo(0,0)');second.wait_for_timeout(100)
    second.screenshot(path=str(OUT/'v4-mobile-320.png'),full_page=True)
    second.emulate_media(reduced_motion='reduce')
    assert second.locator('main').evaluate("e=>getComputedStyle(e).animationName")=='none'
    assert not errors,errors
    print(json.dumps({'layout':layout,'keyboard':'OK','transient_failure_keeps_photos':'OK','tab_takeover_and_stale_close':'OK','guides_center_dialogs':'OK','mobile_widths':mobile,'reduced_motion':'OK','browser_errors':errors}))
    browser.close()

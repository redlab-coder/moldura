"""Version and updater indicator, including compact header and accessibility."""
import io
import json
from pathlib import Path
import sys
from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from version import VERSION

URL=sys.argv[1]
OUT=Path(__file__).parent/'artifacts';OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1366,'height':768})
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    state={'state':'disabled','version':None}
    page.route('**/api/heartbeat',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps({'ok':True,'version':VERSION,'update':state})))
    page.goto(URL)
    assert page.locator('#app-version').inner_text()=='v'+VERSION
    assert page.locator('.local').count()==0
    assert page.locator('#update-status').is_hidden()
    checked=[]
    for phase,label in [('idle',None),('available','Atualização disponível'),('downloading','Baixando atualização'),('ready','Atualização disponível')]:
        state={'state':phase,'version':'1.0.2' if phase!='idle' else None}
        page.evaluate('refreshAppStatus()')
        assert page.locator('#update-status').is_visible()==(label is not None)
        if label:
            assert page.locator('#update-label').inner_text()==label
            assert '1.0.2' in page.locator('#update-status').get_attribute('aria-label')
        checked.append(phase)
    assert 'ao encerrar' in page.locator('#update-status').get_attribute('title')
    page.screenshot(path=str(OUT/'header-ready-desktop.png'))
    data=io.BytesIO();Image.new('RGB',(500,500),'#729269').save(data,'PNG')
    page.locator('#files').set_input_files([{'name':'Demonstração.png','mimeType':'image/png','buffer':data.getvalue()}])
    page.wait_for_function("document.querySelector('#count').textContent==='1'&&!document.querySelector('#export').disabled")
    for width in (740,421,420,390,320):
        page.set_viewport_size({'width':width,'height':844})
        assert page.locator('#app-version').is_visible()
        assert page.locator('#update-status').is_visible()
        assert page.locator('#export').is_visible()
        assert page.locator('#export').get_attribute('aria-label')=='Exportar 1 folha'
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
        assert page.evaluate("document.querySelector('.brand').getBoundingClientRect().right<=document.querySelector('.header-actions').getBoundingClientRect().left"),width
    page.screenshot(path=str(OUT/'header-ready-mobile.png'))
    page.emulate_media(reduced_motion='reduce')
    assert page.locator('#update-status').evaluate("e=>getComputedStyle(e).animationName")=='none'
    state={'state':'idle','version':None}
    page.evaluate('refreshAppStatus()')
    assert page.locator('#update-status').is_hidden()
    assert page.locator('#count').inner_text()=='1'
    assert not errors,errors
    print(json.dumps({'version':VERSION,'states':checked,'mobile_widths':[740,421,420,390,320],'no_header_overlap':True,'session_preserved':True,'browser_errors':errors}))
    browser.close()

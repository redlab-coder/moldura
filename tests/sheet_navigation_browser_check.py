"""Focused v5 coverage: export exactly the open sheet and scoped arrow navigation."""
import io
import json
from pathlib import Path
import sys
from PIL import Image
from PIL.JpegImagePlugin import get_sampling
from playwright.sync_api import sync_playwright

URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:18740'
OUT=Path(__file__).parent/'artifacts';OUT.mkdir(exist_ok=True)
colors=[(200,50,30),(30,165,70),(30,70,210),(230,160,25),(170,50,190),(25,175,175),(215,75,130)]
files=[]
for index,color in enumerate(colors):
    data=io.BytesIO();Image.new('RGB',(1200,900),color).save(data,'PNG')
    files.append({'name':f'Foto-{index+1}.png','mimeType':'image/png','buffer':data.getvalue()})

with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1366,'height':768})
    errors=[];requests=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('request',lambda request:requests.append(request) if request.url.endswith('/api/export') else None)
    page.goto(URL);page.wait_for_function("!document.querySelector('[data-template=square]').disabled")
    page.locator('#files').set_input_files(files)
    page.wait_for_function("document.querySelector('#count').textContent==='7'&&!document.querySelector('#export').disabled")
    page.wait_for_function("document.querySelectorAll('.sheet-card img').length===4&&[...document.querySelectorAll('.sheet-card img')].every(i=>i.complete&&i.naturalWidth>0)")
    initial=page.evaluate('JSON.parse(localStorage.getItem("moldura-session"))')
    original_ids=[photo['id'] for photo in initial['photos']]
    page.get_by_role('button',name='Editar Foto-1.png',exact=True).click()
    y_before=page.evaluate('scrollY')
    for _ in range(10):page.keyboard.press('ArrowDown')
    page.wait_for_function("document.querySelector('#selected-name').textContent==='Foto-7.png'")
    assert page.locator('#photo-list').evaluate('e=>e.scrollTop')>0
    assert page.evaluate('scrollY')==y_before
    assert page.evaluate('document.activeElement.closest("#photo-list")!==null')
    for _ in range(10):page.keyboard.press('ArrowUp')
    assert page.locator('#selected-name').inner_text()=='Foto-1.png'
    # Container focus also starts from the current selection and keeps order intact.
    page.locator('#photo-list').focus();page.keyboard.press('ArrowDown');page.keyboard.press('ArrowDown')
    assert page.locator('#selected-name').inner_text()=='Foto-3.png'
    after=page.evaluate('JSON.parse(localStorage.getItem("moldura-session"))')
    assert [photo['id'] for photo in after['photos']]==original_ids
    page.locator('#brightness-number').focus();page.keyboard.press('ArrowUp')
    assert page.locator('#selected-name').inner_text()=='Foto-3.png'
    assert page.locator('#brightness-number').input_value()=='1'
    page.locator('#zoom-number').fill('1.50');page.locator('#zoom-number').press('Enter')
    before=page.evaluate('JSON.parse(localStorage.getItem("moldura-session"))')
    page.locator('#tile-frame').focus();page.keyboard.press('ArrowDown')
    after=page.evaluate('JSON.parse(localStorage.getItem("moldura-session"))')
    assert after['selected']==before['selected']
    assert after['photos'][2]['edits']['cy']!=before['photos'][2]['edits']['cy']
    page.wait_for_timeout(850)
    page.get_by_role('button',name='Ampliar folha 2',exact=True).click()
    assert page.locator('#sheet-dialog-title').inner_text()=='Folha 2'
    page.screenshot(path=str(OUT/'v5-folha-download.png'))
    with page.expect_download() as event:page.locator('#download-sheet').click()
    download=event.value;assert download.suggested_filename=='Moldura-02.jpg'
    download.save_as(str(OUT/'v5-folha-02.jpg'))
    payload=json.loads(requests[-1].post_data)
    assert [photo['id'] for photo in payload['items']]==original_ids[2:4]
    assert payload['template']=='square'
    image=Image.open(OUT/'v5-folha-02.jpg')
    assert image.size==(1795,1205) and image.info['dpi']==(300,300)
    assert get_sampling(image)==0 and image.info['icc_profile']
    assert image.getpixel((450,600))[2]>image.getpixel((450,600))[0]+100
    assert image.getpixel((1300,600))[0]>200
    page.keyboard.press('Escape')
    page.get_by_role('button',name='Button Redondo P',exact=True).click()
    page.wait_for_function("document.querySelectorAll('.sheet-card img').length===2&&document.querySelector('#tile-image').width===531")
    page.wait_for_timeout(850)
    page.get_by_role('button',name='Ampliar folha 2',exact=True).click()
    with page.expect_download() as event:page.locator('#download-sheet').click()
    event.value.save_as(str(OUT/'v5-redondo-p-02.jpg'))
    payload=json.loads(requests[-1].post_data)
    assert payload['template']=='round_p' and len(payload['items'])==1
    assert payload['items'][0]['id']==original_ids[-1]
    image=Image.open(OUT/'v5-redondo-p-02.jpg')
    assert image.size==(1795,1205) and image.info['dpi']==(300,300)
    assert image.getpixel((200,600))==(255,255,255)
    assert image.getpixel((897,602))[0]>200 and image.getpixel((897,602))[1]<100
    page.keyboard.press('Escape')
    page.set_viewport_size({'width':390,'height':844})
    page.get_by_role('button',name='Ampliar folha 2',exact=True).click()
    assert page.locator('#download-sheet').is_visible()
    assert page.locator('#sheet-dialog').evaluate('e=>e.scrollWidth<=e.clientWidth')
    assert not errors,errors
    print(json.dumps({'arrow_navigation':'OK','selection_order_and_scroll':'OK','number_and_crop_arrows_preserved':'OK','square_sheet_2':'full-quality JPEG, 1795x1205, 300 DPI, sRGB','small_round_last_sheet':'single centered photo','mobile_dialog':'OK','browser_errors':errors}))
    browser.close()

"""Manual end-to-end verification; requires Playwright and installed Edge."""
import io
import json
import sys
import base64
import urllib.request
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

HERE=Path(__file__).parent
OUT=HERE/'artifacts'
OUT.mkdir(exist_ok=True)
URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:18731'


def fixtures():
    paths=[]
    for index,colors in enumerate([('#e5c6a8','#799488','#385851'),('#ece0c9','#b5b994','#66876b'),('#bdcbd0','#899fa4','#415b64')]):
        image=Image.new('RGB',(1600,1000),colors[0]);draw=ImageDraw.Draw(image)
        draw.ellipse((1090,110,1230,250),fill='#faf1d8')
        draw.polygon([(0,780),(390,430),(790,800),(1130,470),(1600,840),(1600,1000),(0,1000)],fill=colors[1])
        draw.polygon([(0,890),(550,700),(1010,910),(1600,650),(1600,1000),(0,1000)],fill=colors[2])
        draw.text((70,80),f'IMAGEM DE TESTE {index+1}',fill=colors[2])
        path=OUT/f'Paisagem-{index+1}.png';image.save(path);paths.append(str(path))
    return paths


with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1150},device_scale_factor=1)
    page=context.new_page()
    errors=[]
    requests=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('request',lambda request:requests.append(request.url))
    page.goto(URL);page.wait_for_selector('#empty-editor')
    page.screenshot(path=str(OUT/'01-vazio.png'),full_page=True)
    page.locator('#files').set_input_files(fixtures())
    page.wait_for_function("document.querySelector('#count').textContent === '3' && !document.querySelector('#export').disabled")
    page.wait_for_function("[...document.querySelectorAll('.sheet-card img')].length===2 && [...document.querySelectorAll('.sheet-card img')].every(i=>i.complete&&i.naturalWidth>0)")
    page.locator('#zoom').evaluate("e=>{e.value='1.35';e.dispatchEvent(new Event('input',{bubbles:true}));}")
    page.locator('#brightness').evaluate("e=>{e.value='1.12';e.dispatchEvent(new Event('input',{bubbles:true}));}")
    page.locator('#saturation').evaluate("e=>{e.value='0.85';e.dispatchEvent(new Event('input',{bubbles:true}));}")
    page.wait_for_timeout(700)
    preview_start=sum(url.endswith('/api/preview') for url in requests)
    frame=page.locator('#tile-frame').bounding_box()
    page.mouse.move(frame['x']+frame['width']/2,frame['y']+frame['height']/2)
    page.mouse.down();page.mouse.move(frame['x']+frame['width']/2-45,frame['y']+frame['height']/2+15,steps=8);page.mouse.up()
    page.wait_for_timeout(900)
    preview_drag=sum(url.endswith('/api/preview') for url in requests)-preview_start
    assert preview_drag<=2,('Too many server previews during drag',preview_drag)
    page.locator('#rotate').click();page.wait_for_timeout(900)
    assert page.locator('#zoom-value').inner_text()=='1,35×'
    page.locator('#contrast-number').fill('17')
    assert page.locator('#contrast-value').inner_text()=='+17'
    page.locator('#contrast-zero').click()
    assert page.locator('#contrast-number').input_value()=='0'
    assert page.locator('#brightness-number').input_value()=='12'
    page.locator('#sharpness-number').fill('31')
    page.locator('#sharpness-number').press('ArrowUp')
    assert page.locator('#sharpness-number').input_value()=='32'
    page.locator('#sharpness-zero').click()
    assert page.locator('#sharpness-number').input_value()=='0'
    page.locator('#zoom-number').fill('1.42')
    page.locator('#zoom-number').press('Enter')
    assert page.locator('#zoom-value').inner_text()=='1,42×'
    page.locator('#tile-frame').focus();page.keyboard.press('ArrowLeft')
    page.wait_for_timeout(900)
    page.get_by_role('button',name='Mover para baixo Paisagem-1.png').click()
    page.wait_for_timeout(900)
    assert page.locator('.photo-detail strong').first.inner_text()=='Paisagem-2.png'
    before=page.evaluate('JSON.parse(localStorage.getItem("moldura-session"))')
    page.reload()
    page.wait_for_function("document.querySelector('#count').textContent === '3' && !document.querySelector('#export').disabled")
    assert page.locator('#zoom-number').input_value()=='1.42'
    assert page.locator('#brightness-number').input_value()=='12'
    assert page.locator('.photo-detail strong').first.inner_text()=='Paisagem-2.png'
    page.wait_for_timeout(900)
    token=page.locator('meta[name=moldura-token]').get_attribute('content')
    selected=next(photo for photo in before['photos'] if photo['id']==before['selected'])
    req=urllib.request.Request(URL+'/api/preview',data=json.dumps({'id':selected['id'],'edits':selected['edits']}).encode(),headers={'X-Moldura-Token':token,'Content-Type':'application/json'})
    reference=Image.open(io.BytesIO(urllib.request.urlopen(req).read())).convert('RGB')
    actual=Image.open(io.BytesIO(base64.b64decode(page.locator('#tile-image').evaluate('canvas=>canvas.toDataURL().split(",")[1]')))).convert('RGB')
    assert actual.tobytes()==reference.tobytes(),'Final canvas must match export processing exactly'
    second=page.context.new_page();second.goto(URL)
    second.wait_for_function("document.querySelector('#count').textContent === '3'")
    assert second.locator('#brightness-number').input_value()=='12'
    second.close()
    page.screenshot(path=str(OUT/'02-editor.png'),full_page=True)
    with page.expect_download() as event:page.locator('#export').click()
    download=event.value;download.save_as(str(OUT/'folhas.zip'))
    with zipfile.ZipFile(OUT/'folhas.zip') as archive:
        assert archive.namelist()==['Moldura-01.jpg','Moldura-02.jpg']
        for name in archive.namelist():
            image=Image.open(io.BytesIO(archive.read(name)))
            assert image.size==(1795,1205) and image.info['dpi']==(300,300)
    page.get_by_role('button',name='Remover foto Paisagem-3.png').click()
    page.wait_for_function("document.querySelector('#count').textContent === '2'")
    with page.expect_download() as event:page.locator('#export').click()
    event.value.save_as(str(OUT/'folha.jpg'))
    image=Image.open(OUT/'folha.jpg');assert image.size==(1795,1205) and image.info['dpi']==(300,300)
    page.locator('#reset').click();page.wait_for_timeout(700)
    assert page.locator('#zoom-value').inner_text()=='1,00×'
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'03-mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    assert not errors,errors
    print(json.dumps({'status':'OK','browser_errors':errors,'server_previews_per_drag':preview_drag,'reload_and_second_tab':'OK','exact_controls':'OK','final_canvas_matches_engine':True,'pages':2,'jpg_size':image.size,'dpi':image.info['dpi'],'screenshots':str(OUT)},ensure_ascii=False))
    browser.close()

"""Exercise all models, guides, fast crop, model recovery and 6/7-photo exports."""
import base64
import io
import json
from pathlib import Path
import sys
import urllib.request
import zipfile
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:18735'
OUT=Path(__file__).parent/'artifacts';OUT.mkdir(exist_ok=True)
paths=[]
for index in range(7):
    image=Image.new('RGB',(1600,1100),('#e6d0b3','#cad8c2','#b9ccd0')[index%3])
    draw=ImageDraw.Draw(image);draw.ellipse((1100,120,1260,280),fill='#faf1d8')
    draw.polygon([(0,800),(400,400),(850,850),(1200,500),(1600,800),(1600,1100),(0,1100)],fill='#7d9984')
    draw.polygon([(0,950),(500,770),(1000,960),(1600,700),(1600,1100),(0,1100)],fill='#3e6251')
    path=OUT/f'Round-{index+1}.png';image.save(path);paths.append(str(path))

with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1200})
    page=context.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(URL)
    page.locator('#files').set_input_files(paths)
    page.wait_for_function("document.querySelector('#count').textContent==='7' && !document.querySelector('#export').disabled")
    models=[('square',827,4),('round_g',833,4),('round_m',650,4),('round_p',531,2)]
    for key,size,sheets in models:
        page.locator(f'[data-template="{key}"]').click()
        page.wait_for_function("([size,sheets])=>document.querySelector('#tile-image').width===size && document.querySelectorAll('.sheet-card img').length===sheets && [...document.querySelectorAll('.sheet-card img')].every(i=>i.complete&&i.naturalWidth>0)",arg=[size,sheets])
        page.wait_for_timeout(700)
        expected_badge={'square':'7 × 7 cm','round_g':'Ø 7,05 cm','round_m':'Ø 5,5 cm','round_p':'Ø 4,5 cm'}[key]
        assert page.locator('#template-badge').inner_text()==expected_badge
        if key!='square':
            assert page.locator('#safe-guide').is_visible()
            page.locator('#zoom-number').fill('1.65');page.locator('#zoom-number').press('Enter')
            frame=page.locator('#tile-frame').bounding_box();x=frame['x']+frame['width']/2;y=frame['y']+frame['height']/2
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-25,y+20,steps=6);page.mouse.up()
            page.wait_for_timeout(800)
            # Exact final pixels must match the backend for every model.
            snapshot=page.evaluate('JSON.parse(localStorage.getItem("moldura-session"))')
            photo=next(photo for photo in snapshot['photos'] if photo['id']==snapshot['selected'])
            token=page.locator('meta[name=moldura-token]').get_attribute('content')
            req=urllib.request.Request(URL+'/api/preview',data=json.dumps({'id':photo['id'],'edits':photo['edits'],'template':key}).encode(),headers={'X-Moldura-Token':token,'Content-Type':'application/json'})
            with urllib.request.urlopen(req) as response:reference=Image.open(io.BytesIO(response.read())).convert('RGB')
            actual=Image.open(io.BytesIO(base64.b64decode(page.locator('#tile-image').evaluate('c=>c.toDataURL().split(",")[1]')))).convert('RGB')
            assert actual.tobytes()==reference.tobytes(),key
        else:
            assert not page.locator('#safe-guide').is_visible()
        page.screenshot(path=str(OUT/f'model-{key}.png'),full_page=True)
    with page.expect_download() as event:page.locator('#export').click()
    event.value.save_as(str(OUT/'redondo-p-7.zip'))
    with zipfile.ZipFile(OUT/'redondo-p-7.zip') as archive:
        assert len(archive.namelist())==2
        for name in archive.namelist():
            image=Image.open(io.BytesIO(archive.read(name)));assert image.size==(1795,1205) and image.info['dpi']==(300,300)
    page.reload();page.wait_for_function("document.querySelector('#count').textContent==='7' && !document.querySelector('[data-template=round_p]').disabled")
    assert page.locator('[data-template="round_p"]').get_attribute('aria-pressed')=='true'
    assert page.locator('#zoom-number').input_value()=='1.65'
    page.get_by_role('button',name='Remover foto Round-7.png').click();page.wait_for_function("document.querySelector('#count').textContent==='6'")
    with page.expect_download() as event:page.locator('#export').click()
    assert event.value.suggested_filename=='Moldura-01.jpg';event.value.save_as(str(OUT/'redondo-p-6.jpg'))
    page.wait_for_timeout(700);page.screenshot(path=str(OUT/'model-round_p-six.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'model-mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert not errors,errors
    print(json.dumps({'models':4,'final_pixels_match':True,'seven_photos':'2 JPEG pages in ZIP','six_photos':'1 JPEG','session_model_restored':True,'browser_errors':errors}))
    browser.close()

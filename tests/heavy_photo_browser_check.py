"""Real large-photo workload. Usage: script URL photo1 photo2 photo3.

Does not save photographs or exports to the test artifacts directory.
"""
import io
import json
from pathlib import Path
import statistics
import sys
import threading
import time
import urllib.request
import zipfile

from PIL import Image
import psutil
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import load_image, render_tile, compose_page, jpeg_bytes

URL = sys.argv[1]
paths = [Path(value).resolve() for value in sys.argv[2:]]
assert paths
health = json.load(urllib.request.urlopen(URL + '/health'))
process = psutil.Process(health['pid'])
memory = []
stop = threading.Event()
def sample_memory():
    while not stop.wait(.05):
        try: memory.append(process.memory_info().rss / 1024**2)
        except psutil.Error: return
sampler = threading.Thread(target=sample_memory, daemon=True)
sampler.start()
report = {}
uploaded = []
token = None
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width':1366,'height':768})
        page = context.new_page()
        page.set_default_timeout(120000)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(URL)
        token = page.locator('meta[name=moldura-token]').get_attribute('content')
        page.wait_for_function("!document.querySelector('[data-template=square]').disabled")
        started = time.perf_counter()
        retained = []
        count = 0
        for batch in range(4):
            page.locator('#files').set_input_files([str(path) for path in paths])
            count += len(paths)
            page.wait_for_function("count=>document.querySelector('#count').textContent===String(count)&&!document.querySelector('#export').disabled", arg=count)
            uploaded = page.evaluate('photos.map(photo=>photo.id)')
            retained.append(round(process.memory_info().rss / 1024**2, 1))
        report['photos_imported'] = count
        report['import_seconds'] = round(time.perf_counter() - started, 2)
        report['retained_mib_after_each_batch'] = retained
        # 12 x 30 MP formerly exceeded the 512 MiB decoded-photo limit.
        assert count >= 6
        assert retained[-1] - retained[0] < 160, retained
        page.wait_for_function("[...document.querySelectorAll('.sheet-open')].every(button=>!button.disabled)", timeout=120000)
        assert page.locator('.photo-row img').evaluate_all('images=>images.every(image=>image.naturalWidth<=128)')
        page.locator('#zoom-number').fill('4.25')
        page.locator('#zoom-number').press('Enter')
        page.wait_for_timeout(900)
        page.evaluate('''()=>{window.liveDraws=0;window.originalDraw=CanvasRenderingContext2D.prototype.drawImage;CanvasRenderingContext2D.prototype.drawImage=function(...args){if(this.canvas.id==='tile-image')window.liveDraws++;return window.originalDraw.apply(this,args);};}''')
        page.evaluate('''()=>{window.frameTimes=[];window.frameRunning=true;let previous=performance.now();function tick(now){window.frameTimes.push(now-previous);previous=now;if(window.frameRunning)requestAnimationFrame(tick);}requestAnimationFrame(tick);}''')
        frame = page.locator('#tile-frame').bounding_box()
        start = (frame['x']+frame['width']/2, frame['y']+frame['height']/2)
        previews = []
        page.on('request',lambda request:previews.append(request.url) if request.url.endswith('/api/preview') else None)
        page.mouse.move(*start);page.mouse.down()
        for index in range(30):
            page.mouse.move(start[0]+index*2,start[1]+index)
            page.wait_for_timeout(16)
        page.mouse.up()
        page.evaluate('window.frameRunning=false')
        report['live_canvas_draws_during_drag'] = page.evaluate('window.liveDraws')
        page.evaluate('()=>{CanvasRenderingContext2D.prototype.drawImage=window.originalDraw;}')
        intervals = page.evaluate('window.frameTimes')
        ordered = sorted(intervals)
        report['drag_frame_median_ms'] = round(statistics.median(intervals), 1)
        report['drag_frame_p95_ms'] = round(ordered[int(len(ordered)*.95)], 1)
        report['server_previews_during_drag'] = len(previews)
        assert statistics.median(intervals) < 40, report
        assert report['drag_frame_p95_ms'] < 100, report
        assert report['live_canvas_draws_during_drag'] >= 10, report
        assert len(previews) <= 2
        page.wait_for_timeout(1000)
        saved = page.evaluate('JSON.parse(localStorage.getItem("moldura-session"))')
        first = saved['photos'][0]
        # Individual export must be byte-identical to rendering the original,
        # even at high zoom where an editing proxy would lose fine details.
        token = page.locator('meta[name=moldura-token]').get_attribute('content')
        payload = {'items':[first], 'template':'square'}
        req = urllib.request.Request(URL+'/api/export',data=json.dumps(payload).encode(),headers={'X-Moldura-Token':token,'Content-Type':'application/json'})
        actual = urllib.request.urlopen(req,timeout=120).read()
        original = load_image(paths[0].read_bytes())
        expected = jpeg_bytes(compose_page([render_tile(original,first['edits'],'square')],'square'))
        original.close()
        actual_image = Image.open(io.BytesIO(actual))
        expected_image = Image.open(io.BytesIO(expected))
        # Independently generated sRGB profiles include different creation times;
        # compare actual JPEG pixels and printing metadata across processes.
        assert actual_image.tobytes() == expected_image.tobytes(), 'Export must use full original, never the editing proxy'
        assert actual_image.size==(1795,1205) and actual_image.info['dpi']==(300,300) and actual_image.info['icc_profile']
        report['high_zoom_export_pixels_match_original'] = True
        with page.expect_download(timeout=120000) as event:
            page.locator('#export').click()
        # Browser's temporary download is removed with its context.
        with zipfile.ZipFile(event.value.path()) as archive:
            assert len(archive.namelist()) == (count+1)//2
            for name in archive.namelist():
                with Image.open(io.BytesIO(archive.read(name))) as image:
                    assert image.size == (1795,1205) and image.info['dpi'] == (300,300)
        report['all_sheets_exported'] = (count+1)//2
        page.reload()
        page.wait_for_function("count=>document.querySelector('#count').textContent===String(count)&&!document.querySelector('#export').disabled",arg=count)
        assert page.locator('#zoom-number').input_value()=='4.25'
        assert not errors, errors
        # Remove test records, including their temporary originals, without
        # touching any photo in another process or browser session.
        page.evaluate('''async()=>{for(const photo of photos)await api('delete',{id:photo.id});localStorage.removeItem('moldura-session');}''')
        report['browser_errors'] = errors
        browser.close()
finally:
    for id_ in uploaded:
        try:
            request=urllib.request.Request(URL+'/api/delete',data=json.dumps({'id':id_}).encode(),headers={'X-Moldura-Token':token,'Content-Type':'application/json'})
            urllib.request.urlopen(request,timeout=10).close()
        except OSError: pass
    stop.set();sampler.join(timeout=2)
    report['server_peak_mib'] = round(max(memory, default=0), 1)
print(json.dumps(report))

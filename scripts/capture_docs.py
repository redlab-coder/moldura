"""Reproduce documentation screenshots using original demo artwork only.

Requires Playwright and Microsoft Edge. Starts its own isolated local server;
does not connect to the user's running application or read their photographs.
"""
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs' / 'images'
DEMO = ROOT / '.tools' / 'docs-demo'


def artwork(title, background, ink, leaf):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200">
    <rect width="1200" height="1200" fill="{background}"/>
    <defs><g id="branch" fill="{leaf}">
      <path d="M0 220C-36 87 42-45 0-245" fill="none" stroke="{leaf}" stroke-width="4"/>
      <path d="M-3 164C-73 158-111 106-101 61C-42 76-7 109-3 164ZM3 78C74 57 102 8 79-29C28-8 5 31 3 78ZM10-24C-52-35-85-88-65-124C-15-103 8-66 10-24ZM8-129C56-147 67-186 45-214C13-188 3-157 8-129Z"/>
    </g></defs>
    <g opacity=".75">
      <use href="#branch" transform="translate(265 772) rotate(-28) scale(1.05)"/>
      <use href="#branch" transform="translate(943 745) rotate(29) scale(.88)"/>
      <use href="#branch" transform="translate(594 1097) rotate(74) scale(.75)"/>
    </g>
    <g fill="none" stroke="{leaf}" stroke-width="2" opacity=".4">
      <circle cx="600" cy="600" r="390"/><circle cx="600" cy="600" r="406"/>
    </g>
    <g fill="{ink}" text-anchor="middle">
      <text x="600" y="451" font-family="Segoe UI,Arial,sans-serif" font-size="19" letter-spacing="7">FEITO PARA GUARDAR</text>
      <text x="600" y="615" font-family="Georgia,serif" font-style="italic" font-size="107">{title}</text>
      <path d="M566 667H634" stroke="{ink}" stroke-width="2" opacity=".6"/>
      <text x="600" y="719" font-family="Segoe UI,Arial,sans-serif" font-size="24" letter-spacing="1">o que importa fica.</text>
    </g>
    </svg>'''


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    DEMO.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen([sys.executable, str(ROOT/'app.py'), '--isolated', '--no-browser', '--no-tray'], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    url = server.stdout.readline().strip()
    if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]+', url):
        raise RuntimeError('A instância isolada de documentação não iniciou.')
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            context = browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1)
            render = context.new_page()
            files = []
            for title, background, ink, leaf in [('Memórias','#f4f0e5','#365e43','#a4b38e'),('Afeto','#e7eddf','#3e5b3f','#9ba982'),('Instantes','#365e43','#f4f0e5','#6f8d6b')]:
                render.set_content('<body style="margin:0">'+artwork(title,background,ink,leaf)+'</body>')
                path = DEMO / (title+'.png')
                render.locator('svg').screenshot(path=str(path))
                files.append(str(path))
            render.close()
            page = context.new_page()
            page.emulate_media(reduced_motion='reduce')
            errors = []
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(url)
            page.wait_for_function("!document.querySelector('[data-template=square]').disabled")
            page.locator('#files').set_input_files(files)
            page.wait_for_function("document.querySelector('#count').textContent==='3'&&!document.querySelector('#export').disabled")
            page.locator('[data-template=round_g]').click()
            page.wait_for_function("document.querySelector('#tile-image').width===833&&[...document.querySelectorAll('.sheet-open')].every(button=>!button.disabled)")
            page.wait_for_timeout(500)
            page.wait_for_function("document.querySelector('#toast').hidden")
            page.screenshot(path=str(OUTPUT/'workspace.png'),full_page=True)
            page.get_by_role('button',name='Ampliar folha 1',exact=True).click()
            page.locator('#sheet-dialog-image').evaluate('image=>image.decode()')
            page.locator('#sheet-dialog').screenshot(path=str(OUTPUT/'sheet.png'))
            assert not errors,errors
            browser.close()
    finally:
        html=urllib.request.urlopen(url).read().decode()
        token=re.search('name="moldura-token" content="([^"]+)',html).group(1)
        urllib.request.urlopen(urllib.request.Request(url+'/api/quit',data=b'{}',headers={'X-Moldura-Token':token,'Content-Type':'application/json'})).close()
        server.wait(timeout=10)
    print('Capturas atualizadas: docs/images/workspace.png e sheet.png')


if __name__ == '__main__':
    main()

"""Loopback-only desktop companion. No cloud or external assets."""
import argparse
import io
import json
import secrets
import sys
import threading
import tempfile
import time
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote
from PIL import UnidentifiedImageError, Image
from engine import load_image, render_tile, compose_page, jpeg_bytes, template_info, TEMPLATES
from desktop import SingleInstance, run_tray
from photo_store import PhotoRecord, PhotoCache
from updater import Updater, installed_directory
from version import VERSION, PORTABLE_NAMESPACE, INSTALLED_NAMESPACE, INSTALLED_MUTEX

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
TOKEN = secrets.token_urlsafe(24)
INSTANCE = secrets.token_hex(16)
IMAGES = {}
LOCK = threading.Lock()
LAST_ACTIVE = time.monotonic()
CACHE = PhotoCache()
MAX_STORAGE = 4 * 1024**3


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if not getattr(sys, 'frozen', False):
            super().log_message(format, *args)

    def reply(self, data, content_type='application/json', status=200, filename=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def json_reply(self, value, status=200):
        self.reply(json.dumps(value, ensure_ascii=False).encode(), status=status)

    def authorized_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

    def do_GET(self):
        if not self.authorized_host():
            return self.json_reply({'error': 'Acesso inválido.'}, 403)
        path = urlparse(self.path).path
        if path == '/health':
            return self.json_reply({'product': 'Moldura', 'instance': INSTANCE, 'pid': __import__('os').getpid(), 'version': VERSION})
        if path == '/':
            html = (ROOT / 'ui' / 'index.html').read_text(encoding='utf-8').replace('__TOKEN__', TOKEN)
            html = html.replace('__TEMPLATES__', json.dumps({key: template_info(key) for key in TEMPLATES}, ensure_ascii=False))
            return self.reply(html.encode(), 'text/html; charset=utf-8')
        if path in ('/app.js', '/icons.js', '/style.css'):
            return self.reply((ROOT / 'ui' / path[1:]).read_bytes(), 'text/javascript; charset=utf-8' if path.endswith('js') else 'text/css; charset=utf-8')
        if path == '/favicon.ico':
            from desktop import icon_image
            output = io.BytesIO()
            icon_image().save(output, 'ICO')
            return self.reply(output.getvalue(), 'image/x-icon')
        self.json_reply({'error': 'Não encontrado.'}, 404)

    def do_POST(self):
        global LAST_ACTIVE
        origin = self.headers.get('Origin')
        expected = f'http://127.0.0.1:{self.server.server_port}'
        if not self.authorized_host() or self.headers.get('X-Moldura-Token') != TOKEN or (origin and origin != expected):
            return self.json_reply({'error': 'Acesso inválido.'}, 403)
        LAST_ACTIVE = time.monotonic()
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 0 or length > (50 * 1024 * 1024 if path == '/api/upload' else 1024 * 1024):
                raise ValueError('O arquivo excede 50 MB ou a solicitação é muito grande.')
            body = self.rfile.read(length)
            if path == '/api/upload':
                with CACHE.lock:
                    with LOCK:
                        self.check_capacity(length)
                    CACHE.clear()
                    record = PhotoRecord(body)
                    with LOCK:
                        self.check_capacity(length)
                        id_ = secrets.token_hex(12)
                        IMAGES[id_] = {'record': record}
                return self.json_reply({'id': id_, 'width': record.width, 'height': record.height, 'name': unquote(self.headers.get('X-Filename', 'Foto'))})
            payload = json.loads(body or b'{}')
            if not isinstance(payload, dict):
                raise ValueError('Solicitação inválida.')
            if path == '/api/templates':
                return self.json_reply([template_info(key) for key in TEMPLATES])
            if path == '/api/heartbeat':
                return self.json_reply({'ok': True})
            if path == '/api/quit':
                self.json_reply({'ok': True})
                stop = getattr(self.server, 'request_shutdown', self.server.shutdown)
                threading.Thread(target=stop, daemon=True).start()
                return
            if path == '/api/delete':
                with LOCK:
                    removed = IMAGES.pop(payload['id'], None)
                if removed:
                    CACHE.discard(removed['record'])
                return self.json_reply({'ok': True})
            if path in ('/api/preview', '/api/thumbnail'):
                item = payload
                record = self.record(item['id'])
                with CACHE.lock:
                    source = CACHE.get(record, full=path == '/api/preview')
                    tile = render_tile(source, item.get('edits', {}), item.get('template', 'square'))
                    del source
                if path == '/api/thumbnail':
                    tile.thumbnail((128, 128), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                tile.save(output, 'PNG')
                return self.reply(output.getvalue(), 'image/png')
            if path == '/api/source':
                record = self.record(payload['id'])
                return self.reply(record.live.read_bytes(), 'image/jpeg')
            if path in ('/api/sheet', '/api/export'):
                items = payload['items']
                template = payload.get('template', 'square')
                capacity = template_info(template)['capacity']
                if not isinstance(items, list) or not 1 <= len(items) <= 100:
                    raise ValueError('Selecione entre 1 e 100 imagens.')
                # Keep original references for the entire operation, even if
                # another tab removes a photo while a large export is running.
                with LOCK:
                    records = [(IMAGES[item['id']]['record'], item.get('edits', {})) for item in items]
                def compose(records_for_page):
                    tiles = []
                    for record, edits in records_for_page:
                        with CACHE.lock:
                            source = CACHE.get(record, full=path == '/api/export')
                            tiles.append(render_tile(source, edits, template))
                            del source
                    return compose_page(tiles, template)
                if path == '/api/sheet':
                    if len(items) > capacity:
                        raise ValueError('A prévia excede a capacidade deste gabarito.')
                    page = compose(records)
                    page.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                    output = io.BytesIO()
                    page.save(output, 'PNG')
                    return self.reply(output.getvalue(), 'image/png')
                if len(items) <= capacity:
                    page = compose(records)
                    return self.reply(jpeg_bytes(page), 'image/jpeg', filename='Moldura-01.jpg')
                # Large ZIPs spill to disk and are sent in chunks instead of
                # duplicating the entire archive in server memory.
                with tempfile.SpooledTemporaryFile(max_size=8 * 1024**2) as output:
                    with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED) as archive:
                        for start in range(0, len(items), capacity):
                            page = compose(records[start:start + capacity])
                            archive.writestr(f'Moldura-{start // capacity + 1:02}.jpg', jpeg_bytes(page))
                    size = output.tell()
                    output.seek(0)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/zip')
                    self.send_header('Content-Length', str(size))
                    self.send_header('Content-Disposition', 'attachment; filename="Moldura-folhas.zip"')
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('X-Content-Type-Options', 'nosniff')
                    self.end_headers()
                    while chunk := output.read(256 * 1024):
                        self.wfile.write(chunk)
                return
            self.json_reply({'error': 'Não encontrado.'}, 404)
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError, UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
            message = str(error) if isinstance(error, ValueError) else 'Não foi possível processar a imagem ou a solicitação. Use JPG, PNG, WebP, BMP ou TIFF.'
            self.json_reply({'error': message}, 400)

    @staticmethod
    def check_capacity(length):
        if len(IMAGES) >= 100:
            raise ValueError('O lote aceita até 100 fotos. Exporte e inicie um novo lote.')
        if sum(value['record'].bytes for value in IMAGES.values()) + length > MAX_STORAGE:
            raise ValueError('O lote atingiu 4 GB de arquivos temporários. Exporte e remova algumas fotos para continuar.')

    def record(self, id_):
        with LOCK:
            return IMAGES[id_]['record']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--no-tray', action='store_true')
    parser.add_argument('--isolated', action='store_true', help='Instância separada apenas para testes.')
    parser.add_argument('--no-updates', action='store_true', help='Não consultar atualizações nesta execução.')
    args = parser.parse_args()
    install_dir = installed_directory() if not args.isolated else None
    instance = None if args.isolated else SingleInstance(INSTALLED_NAMESPACE if install_dir else PORTABLE_NAMESPACE, mutex_name=INSTALLED_MUTEX if install_dir else None)
    if instance and not instance.owner:
        existing = instance.existing_url()
        instance.close()
        if existing:
            if not args.no_browser:
                webbrowser.open(existing)
            if sys.stdout:
                print(existing, flush=True)
        elif sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, 'O Moldura já está iniciando ou encerrando. Aguarde alguns segundos e tente novamente.', 'Moldura', 0x40)
        return
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError:
        if instance:
            instance.close()
        raise
    server.daemon_threads = True
    updates = None
    if install_dir and not args.no_updates:
        try:
            updates = Updater(install_dir)
            updates.start()
        except OSError:
            pass  # An update failure must never prevent local editing.
    url = f'http://127.0.0.1:{server.server_port}'
    if instance:
        instance.publish(url, INSTANCE)
    stopped = threading.Event()
    tray = None
    def request_shutdown():
        if stopped.is_set():
            return
        stopped.set()
        server.shutdown()
        if tray:
            tray.stop()
    server.request_shutdown = request_shutdown
    if sys.platform == 'win32' and not args.no_tray:
        tray = run_tray(url, request_shutdown, lambda: bool(IMAGES), updates)
    if not args.no_browser:
        webbrowser.open(url)
    if sys.stdout:
        print(url, flush=True)
    # With a tray icon, the session deliberately stays available until explicit exit.
    if not tray:
        def idle_monitor():
            while not stopped.wait(20):
                if time.monotonic() - LAST_ACTIVE > 300:
                    request_shutdown()
                    return
        threading.Thread(target=idle_monitor, daemon=True).start()
    try:
        if tray:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                tray.run()
            finally:
                request_shutdown()
                thread.join(timeout=5)
        else:
            server.serve_forever()
    finally:
        server.server_close()
        with LOCK:
            IMAGES.clear()
        CACHE.clear()
        if instance:
            instance.close()
        if updates:
            updates.install_on_exit()


if __name__ == '__main__':
    main()

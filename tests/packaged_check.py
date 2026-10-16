"""Actual Windows EXE, tray window, duplicate launch and clean shutdown."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

heavy_only='--heavy-only' in sys.argv
if heavy_only:sys.argv.remove('--heavy-only')
exe=Path(sys.argv[1] if len(sys.argv)>1 else 'dist/Moldura-v7.exe').resolve()
metadata=Path(os.environ['LOCALAPPDATA'])/'Moldura-v7'/'runtime.json'
first=subprocess.Popen([str(exe),'--no-browser'],creationflags=subprocess.CREATE_NO_WINDOW)
url=None
try:
    deadline=time.monotonic()+25
    while time.monotonic()<deadline:
        try:
            state=json.loads(metadata.read_text())
            url=state['url']
            health=json.load(urllib.request.urlopen(url+'/health',timeout=1))
            if health['instance']==state['instance']:break
        except (OSError,ValueError,KeyError):pass
        time.sleep(.15)
    else:raise AssertionError('Packaged server did not start')
    # The Win32 tray uses a hidden native window to receive shell callbacks.
    user32=ctypes.windll.user32
    callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    windows=[]
    def visit(hwnd,lparam):
        pid=wintypes.DWORD();user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value==state['pid']:
            name=ctypes.create_unicode_buffer(256);user32.GetClassNameW(hwnd,name,256);windows.append(name.value)
        return True
    callback=callback_type(visit)
    user32.EnumWindows(callback,0)
    assert windows,('Native tray window missing',state)
    before=metadata.read_bytes()
    second=subprocess.Popen([str(exe),'--no-browser'],creationflags=subprocess.CREATE_NO_WINDOW)
    assert second.wait(timeout=20)==0
    assert first.poll() is None
    assert metadata.read_bytes()==before,'Duplicate launch must reuse existing metadata'
    if not heavy_only:
        subprocess.run([sys.executable,str(Path(__file__).parent/'browser_check.py'),url],check=True)
        subprocess.run([sys.executable,str(Path(__file__).parent/'round_browser_check.py'),url],check=True)
        subprocess.run([sys.executable,str(Path(__file__).parent/'refinement_browser_check.py'),url],check=True)
        subprocess.run([sys.executable,str(Path(__file__).parent/'sheet_navigation_browser_check.py'),url],check=True)
    if len(sys.argv)>2:
        subprocess.run([sys.executable,str(Path(__file__).parent/'heavy_photo_browser_check.py'),url,*sys.argv[2:]],check=True)
    html=urllib.request.urlopen(url).read().decode()
    token=re.search('name="moldura-token" content="([^"]+)',html).group(1)
    request=urllib.request.Request(url+'/api/quit',data=b'{}',headers={'X-Moldura-Token':token,'Content-Type':'application/json'})
    urllib.request.urlopen(request).close()
    assert first.wait(timeout=15)==0
    assert not metadata.exists(),'Runtime metadata must be removed on exit'
    print(json.dumps({'packaged':'OK','single_instance':'OK','tray_native_windows':windows,'shutdown':'OK','size_mb':round(exe.stat().st_size/1024/1024,1)}))
finally:
    if first.poll() is None:
        # Stop only the exact test instance through its own authenticated API.
        if url:
            try:
                html=urllib.request.urlopen(url).read().decode()
                token=re.search('name="moldura-token" content="([^"]+)',html).group(1)
                urllib.request.urlopen(urllib.request.Request(url+'/api/quit',data=b'{}',headers={'X-Moldura-Token':token,'Content-Type':'application/json'})).close()
                first.wait(timeout=10)
            except (OSError,ValueError,subprocess.TimeoutExpired):pass

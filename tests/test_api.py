import io
import json
import threading
import unittest
import urllib.request
import urllib.error
import zipfile
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from PIL import Image
import app


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def request(self,path,data,raw=False,token=app.TOKEN,origin=None):
        headers={'X-Moldura-Token':token,'Content-Type':'application/octet-stream' if raw else 'application/json'}
        if origin:headers['Origin']=origin
        req=urllib.request.Request(self.url+'/api/'+path,data=data if raw else json.dumps(data).encode(),headers=headers)
        return urllib.request.urlopen(req)

    def test_full_three_photo_export_and_delete(self):
        items=[]
        for color in ('red','green','blue'):
            stream=io.BytesIO();Image.new('RGB',(800,1100),color).save(stream,'PNG')
            with self.request('upload',stream.getvalue(),True) as response:photo=json.load(response)
            items.append({'id':photo['id'],'edits':{'zoom':1.2,'brightness':1.1}})
        with self.request('preview',items[0]) as response:
            self.assertEqual(Image.open(io.BytesIO(response.read())).size,(827,827))
        with self.request('source',{'id':items[0]['id']}) as response:
            self.assertEqual(Image.open(io.BytesIO(response.read())).size,(800,1100))
        with self.request('sheet',{'items':items[:2]}) as response:
            self.assertEqual(Image.open(io.BytesIO(response.read())).size,(1000,671))
        with self.request('export',{'items':items}) as response:
            archive=zipfile.ZipFile(io.BytesIO(response.read()))
            self.assertEqual(archive.namelist(),['Moldura-01.jpg','Moldura-02.jpg'])
            for filename in archive.namelist():
                image=Image.open(io.BytesIO(archive.read(filename)))
                self.assertEqual(image.size,(1795,1205));self.assertEqual(image.info['dpi'],(300,300))
            last=Image.open(io.BytesIO(archive.read('Moldura-02.jpg')))
            self.assertGreater(last.getpixel((897,602))[2],240)
            self.assertEqual(last.getpixel((200,602)),(255,255,255))
        with self.request('export',{'items':items[:1]}) as response:
            self.assertEqual(response.headers['Content-Type'],'image/jpeg')
        for item in items:
            with self.request('delete',{'id':item['id']}) as response:self.assertTrue(json.load(response)['ok'])

    def test_invalid_input_and_access_rejected(self):
        for path,data,raw,token,origin,status in [
            ('upload',b'not an image',True,app.TOKEN,None,400),
            ('export',{'items':[]},False,app.TOKEN,None,400),
            ('heartbeat',{},False,'invalid',None,403),
            ('heartbeat',{},False,app.TOKEN,'https://other.example',403),
            ('heartbeat',[],False,app.TOKEN,None,400),
            ('preview',{'id':'missing'},False,app.TOKEN,None,400),
            ('export',{'items':[{'id':'missing'}],'template':'invalid'},False,app.TOKEN,None,400),
        ]:
            with self.assertRaises(urllib.error.HTTPError) as caught:
                self.request(path,data,raw,token,origin)
            self.assertEqual(caught.exception.code,status)
            caught.exception.close()

    def test_small_round_six_per_page_and_overflow(self):
        stream=io.BytesIO();Image.new('RGB',(1000,800),'red').save(stream,'PNG')
        with self.request('upload',stream.getvalue(),True) as response:photo=json.load(response)
        item={'id':photo['id'],'edits':{}}
        try:
            with self.request('templates',{}) as response:models=json.load(response)
            self.assertEqual([m['capacity'] for m in models],[2,2,2,6])
            for count,expected_type in [(6,'image/jpeg'),(7,'application/zip')]:
                with self.request('export',{'items':[item]*count,'template':'round_p'}) as response:
                    self.assertEqual(response.headers['Content-Type'],expected_type)
                    data=response.read()
                if count==7:
                    archive=zipfile.ZipFile(io.BytesIO(data));self.assertEqual(len(archive.namelist()),2)
                    page=Image.open(io.BytesIO(archive.read('Moldura-02.jpg')))
                    self.assertGreater(page.getpixel((897,602))[0],240)
                    self.assertLess(page.getpixel((897,602))[1],10)
            with self.request('sheet',{'items':[item]*6,'template':'round_p'}) as response:
                self.assertEqual(Image.open(io.BytesIO(response.read())).size,(1000,671))
        finally:
            with self.request('delete',{'id':photo['id']}):pass

    def test_export_keeps_sources_if_removed_during_processing(self):
        stream=io.BytesIO();Image.new('RGB',(100,100),'blue').save(stream,'PNG')
        with self.request('upload',stream.getvalue(),True) as response:photo=json.load(response)
        original_render=app.render_tile
        def remove_then_render(source,edits,template):
            with app.LOCK:app.IMAGES.pop(photo['id'],None)
            return original_render(source,edits,template)
        with patch('app.render_tile',side_effect=remove_then_render):
            with self.request('export',{'items':[{'id':photo['id']}]*7,'template':'round_p'}) as response:
                archive=zipfile.ZipFile(io.BytesIO(response.read()))
                self.assertEqual(len(archive.namelist()),2)


if __name__ == '__main__':unittest.main()

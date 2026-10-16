import io
import unittest
from PIL import Image
from engine import template_info, render_tile, reflected_region, page_positions, compose_page, jpeg_bytes, PAGE


class RoundTemplateTests(unittest.TestCase):
    def test_confirmed_dimensions(self):
        expected={'round_g':(58,70.5,685,833,2),'round_m':(44,55,520,650,2),'round_p':(32,45,378,531,6)}
        for key,values in expected.items():
            spec=template_info(key)
            self.assertEqual(tuple(spec[k] for k in ('visible_mm','cut_mm','visible_px','cut_px','capacity')),values)
            for mm,px in [(spec['visible_mm'],spec['visible_px']),(spec['cut_mm'],spec['cut_px'])]:
                self.assertLessEqual(abs(mm-px*25.4/300),25.4/300/2)
        with self.assertRaises(ValueError):template_info('unknown')

    def test_reflect_only_missing_parts(self):
        image=Image.new('RGB',(40,40))
        image.putdata([(x*4,y*4,20) for y in range(40) for x in range(40)])
        actual=reflected_region(image,(-10,-10,50,50),60)
        for x in (0,9,10,25,49,50,59):
            for y in (0,9,10,30,49,50,59):
                sx=9-x if x<10 else 89-x if x>=50 else x-10
                sy=9-y if y<10 else 89-y if y>=50 else y-10
                self.assertEqual(actual.getpixel((x,y)),image.getpixel((sx,sy)))
        natural=reflected_region(image,(5,5,35,35),30)
        self.assertEqual(natural.tobytes(),image.crop((5,5,35,35)).tobytes())

    def test_natural_bleed_not_reflection_of_visible_crop(self):
        image=Image.new('RGB',(1000,1000))
        image.putdata([(round(x*255/999),round(y*255/999),100) for y in range(1000) for x in range(1000)])
        tile=render_tile(image,{'zoom':2},'round_g')
        # Entire requested circle fits the original. Its leftmost source x is
        # about 198, while the visible crop begins at 250. No mirror is needed.
        self.assertAlmostEqual(tile.getpixel((2,413))[0],51,delta=2)
        self.assertAlmostEqual(tile.getpixel((413,413))[0],128,delta=2)

    def test_round_mask_rotation_and_adjustments(self):
        source=Image.new('RGB',(1100,800),(60,120,180))
        original=source.tobytes()
        for key in ('round_g','round_m','round_p'):
            size=template_info(key)['cut_px']
            tile=render_tile(source,{'zoom':1,'rotation':90},key)
            self.assertEqual(tile.size,(size,size))
            self.assertEqual(tile.getpixel((0,0)),(255,255,255))
            self.assertEqual(tile.getpixel((size//2,size//2)),(60,120,180))
            black=render_tile(source,{'brightness':0},key)
            self.assertEqual(black.getpixel((size//2,size//2)),(0,0,0))
        self.assertEqual(source.tobytes(),original)

    def test_all_partial_and_full_layouts(self):
        for key in ('round_g','round_m','round_p'):
            spec=template_info(key);size=spec['cut_px']
            for count in range(1,spec['capacity']+1):
                positions=page_positions(count,key)
                self.assertEqual(len(positions),count)
                for x,y in positions:
                    self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
                    self.assertLessEqual(x+size,PAGE[0]);self.assertLessEqual(y+size,PAGE[1])
                for i,(x,y) in enumerate(positions):
                    for x2,y2 in positions[i+1:]:
                        self.assertTrue(x+size<=x2 or x2+size<=x or y+size<=y2 or y2+size<=y)
                for y in {position[1] for position in positions}:
                    row=sorted(x for x,py in positions if py==y)
                    self.assertLessEqual(abs(row[0]-(PAGE[0]-row[-1]-size)),1)
                if count==1:
                    self.assertLessEqual(abs(positions[0][1]-(PAGE[1]-positions[0][1]-size)),1)
                page=compose_page([render_tile(Image.new('RGB',(300,300),'red'),{},key)]*count,key)
                output=Image.open(io.BytesIO(jpeg_bytes(page)))
                self.assertEqual(output.size,PAGE);self.assertEqual(output.info['dpi'],(300,300))


if __name__=='__main__':unittest.main()

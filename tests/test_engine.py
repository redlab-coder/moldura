import io
import unittest
from PIL import Image, ImageOps
from engine import PHOTO, TILE, PAGE, BORDER, load_image, crop_geometry, prepare_photo, mirror_tile, compose_page, page_positions, jpeg_bytes


class TemplateTests(unittest.TestCase):
    def test_physical_dimensions(self):
        self.assertEqual((PHOTO, TILE, PAGE, BORDER), (591, 827, (1795, 1205), 118))
        for cm, px in [(5, PHOTO), (7, TILE), (15.2, PAGE[0]), (10.2, PAGE[1])]:
            self.assertLessEqual(abs(px * 2.54 / 300 - cm), 2.54 / 300 / 2)

    def test_all_reflections_and_corners(self):
        photo = Image.new('RGB', (PHOTO, PHOTO))
        photo.putdata([((x * 7) % 256, (y * 3) % 256, (x + y) % 256) for y in range(PHOTO) for x in range(PHOTO)])
        tile = mirror_tile(photo)
        self.assertEqual(tile.crop((118, 118, 709, 709)).tobytes(), photo.tobytes())
        def reflect(value):
            if value < BORDER:
                return BORDER - 1 - value
            if value >= BORDER + PHOTO:
                return PHOTO - 1 - (value - BORDER - PHOTO)
            return value - BORDER
        for x in [0, 45, 117, 118, 400, 708, 709, 780, 826]:
            for y in [0, 60, 117, 118, 300, 708, 709, 750, 826]:
                self.assertEqual(tile.getpixel((x,y)), photo.getpixel((reflect(x),reflect(y))))

    def test_symmetric_layout(self):
        positions = page_positions(2)
        left = positions[0][0]
        gap = positions[1][0] - left - TILE
        right = PAGE[0] - positions[1][0] - TILE
        self.assertLessEqual(max(left,gap,right)-min(left,gap,right),1)
        self.assertLessEqual(abs(PAGE[1] - 2 * positions[0][1] - TILE),1)
        x,y = page_positions(1)[0]
        self.assertLessEqual(abs(PAGE[0]-2*x-TILE),1)
        self.assertEqual(y,189)
        page = compose_page([Image.new('RGB',(TILE,TILE),'red'),Image.new('RGB',(TILE,TILE),'blue')])
        self.assertEqual(page.getpixel((left,189)),(255,0,0))
        self.assertEqual(page.getpixel((positions[1][0],189)),(0,0,255))
        self.assertEqual(page.getpixel((left+TILE,189)),(255,255,255))

    def test_crop_never_leaves_image(self):
        for size in [(1800,900),(900,1800),(10,10)]:
            for zoom in (1,2.3,5):
                for cx,cy in [(0,0),(1,1),(.5,.5)]:
                    x1,y1,x2,y2 = crop_geometry(size,dict(zoom=zoom,cx=cx,cy=cy))
                    self.assertGreaterEqual(x1,0);self.assertGreaterEqual(y1,0)
                    self.assertLessEqual(x2,size[0]);self.assertLessEqual(y2,size[1])
                    self.assertAlmostEqual(x2-x1,y2-y1)

    def test_adjustments_and_original_preserved(self):
        original = Image.new('RGB',(1000,800),(120,80,40))
        before = original.tobytes()
        self.assertEqual(prepare_photo(original,{'brightness':0}).getpixel((200,200)),(0,0,0))
        gray = prepare_photo(original,{'saturation':0}).getpixel((200,200))
        self.assertEqual(gray[0],gray[1]);self.assertEqual(gray[1],gray[2])
        self.assertEqual(original.tobytes(),before)

    def test_exif_and_transparency(self):
        image = Image.new('RGB',(100,200),'red'); exif=image.getexif();exif[274]=6
        stream=io.BytesIO();image.save(stream,'JPEG',exif=exif)
        self.assertEqual(load_image(stream.getvalue()).size,(200,100))
        transparent=Image.new('RGBA',(20,20),(255,0,0,0));stream=io.BytesIO();transparent.save(stream,'PNG')
        self.assertEqual(load_image(stream.getvalue()).getpixel((0,0)),(255,255,255))

    def test_jpeg_metadata_and_chroma(self):
        from PIL.JpegImagePlugin import get_sampling
        page = compose_page([Image.new('RGB',(TILE,TILE),'green')])
        image = Image.open(io.BytesIO(jpeg_bytes(page)))
        self.assertEqual(image.size,PAGE)
        self.assertEqual(image.info['dpi'],(300,300))
        self.assertEqual(get_sampling(image),0)
        self.assertTrue(image.info['icc_profile'])

    def test_reject_invalid_numeric_adjustment(self):
        with self.assertRaises(ValueError): crop_geometry((1000,800),{'zoom':float('nan')})
        with self.assertRaises(ValueError): prepare_photo(Image.new('RGB',(20,20)),{'rotation':31})


if __name__ == '__main__':
    unittest.main()

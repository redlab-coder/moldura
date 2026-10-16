"""Physical photo template and non-destructive image processing."""
import io
import math
from PIL import Image, ImageCms, ImageEnhance, ImageOps, ImageDraw

DPI = 300
PHOTO = round(5 / 2.54 * DPI)
TILE = round(7 / 2.54 * DPI)
PAGE = (round(15.2 / 2.54 * DPI), round(10.2 / 2.54 * DPI))
BORDER = (TILE - PHOTO) // 2
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
TEMPLATES = {
    'square': {'name': 'Button Quadrado', 'visible_mm': 50, 'cut_mm': 70, 'safe_mm': None, 'columns': 2, 'rows': 1},
    'round_g': {'name': 'Button Redondo G', 'visible_mm': 58, 'cut_mm': 70.5, 'safe_mm': [48, 50], 'columns': 2, 'rows': 1},
    'round_m': {'name': 'Button Redondo M', 'visible_mm': 44, 'cut_mm': 55, 'safe_mm': [36, 38], 'columns': 2, 'rows': 1},
    'round_p': {'name': 'Button Redondo P', 'visible_mm': 32, 'cut_mm': 45, 'safe_mm': [26, 28], 'columns': 3, 'rows': 2},
}


def template_info(key='square'):
    if key not in TEMPLATES:
        raise ValueError('Modelo de gabarito inválido.')
    spec = TEMPLATES[key]
    return dict(spec, id=key, visible_px=round(spec['visible_mm'] / 25.4 * DPI),
                cut_px=round(spec['cut_mm'] / 25.4 * DPI), capacity=spec['columns'] * spec['rows'])


def load_image(data):
    with Image.open(io.BytesIO(data)) as source:
        if source.width * source.height > 60_000_000:
            raise ValueError('A imagem excede 60 megapixels. Reduza seu tamanho antes de importar.')
        source.load()
        profile = source.info.get('icc_profile')
        # Most professional exports already have orientation 1. Avoid a full
        # extra RGB copy before ICC conversion for those large photographs.
        image = ImageOps.exif_transpose(source) if source.getexif().get(274, 1) != 1 else source
        alpha = image.convert('RGBA').getchannel('A') if 'A' in image.getbands() or image.mode == 'P' else None
        if profile:
            try:
                color = image.convert('RGB') if image.mode in ('RGBA', 'P', 'LA') else image
                image = ImageCms.profileToProfile(color, ImageCms.ImageCmsProfile(io.BytesIO(profile)), SRGB, outputMode='RGB')
            except (ValueError, OSError, ImageCms.PyCMSError):
                image = image.convert('RGBA' if 'A' in image.getbands() else 'RGB')
        if alpha is not None:
            image.putalpha(alpha)
        if 'A' in image.getbands() or image.mode == 'P':
            rgba = image.convert('RGBA')
            background = Image.new('RGBA', image.size, 'white')
            image = Image.alpha_composite(background, rgba)
        if image.mode != 'RGB':
            return image.convert('RGB')
        return image.copy() if image is source else image


def number(edits, key, default, low, high):
    value = float(edits.get(key, default))
    if not math.isfinite(value):
        raise ValueError('Ajuste inválido.')
    return max(low, min(high, value))


def crop_geometry(size, edits):
    width, height = size
    side = min(width, height) / number(edits, 'zoom', 1, 1, 5)
    cx = number(edits, 'cx', .5, 0, 1) * width
    cy = number(edits, 'cy', .5, 0, 1) * height
    cx = max(side / 2, min(width - side / 2, cx))
    cy = max(side / 2, min(height - side / 2, cy))
    return (cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2)


def prepare_photo(source, edits):
    rotation = int(number(edits, 'rotation', 0, 0, 270))
    if rotation % 90:
        raise ValueError('Rotação inválida.')
    image = source.rotate(-rotation, expand=True) if rotation else source
    box = crop_geometry(image.size, edits)
    image = image.resize((PHOTO, PHOTO), Image.Resampling.LANCZOS, box=box)
    for key, enhancer in [('brightness', ImageEnhance.Brightness), ('contrast', ImageEnhance.Contrast), ('saturation', ImageEnhance.Color)]:
        image = enhancer(image).enhance(number(edits, key, 1, 0, 2))
    image = ImageEnhance.Sharpness(image).enhance(number(edits, 'sharpness', 1, 0, 3))
    return image


def mirror_tile(photo):
    # Reflect horizontal edges, then vertical edges including all four corners.
    horizontal = Image.new('RGB', (TILE, PHOTO))
    horizontal.paste(photo, (BORDER, 0))
    horizontal.paste(ImageOps.mirror(photo.crop((0, 0, BORDER, PHOTO))), (0, 0))
    horizontal.paste(ImageOps.mirror(photo.crop((PHOTO - BORDER, 0, PHOTO, PHOTO))), (BORDER + PHOTO, 0))
    tile = Image.new('RGB', (TILE, TILE))
    tile.paste(horizontal, (0, BORDER))
    tile.paste(ImageOps.flip(horizontal.crop((0, 0, TILE, BORDER))), (0, 0))
    tile.paste(ImageOps.flip(horizontal.crop((0, PHOTO - BORDER, TILE, PHOTO))), (0, BORDER + PHOTO))
    return tile


def reflected_region(source, box, output_size):
    """Use original pixels within bounds; reflect only portions outside the source.

    Each axis has at most three segments. Resize those directly, without creating
    an enormous padded copy of the original image.
    """
    def segments(start, end, limit):
        scale = output_size / (end - start)
        result = []
        boundaries = [start] + [point for point in (0, limit) if start < point < end] + [end]
        for low, high in zip(boundaries, boundaries[1:]):
            a = round((low - start) * scale)
            b = round((high - start) * scale)
            if a == b:
                continue
            flip = high <= 0 or low >= limit
            if high <= 0:
                src_low, src_high = -high, -low
            elif low >= limit:
                src_low, src_high = 2 * limit - high, 2 * limit - low
            else:
                src_low, src_high = low, high
            result.append((a, b, max(0, src_low), min(limit, src_high), flip))
        return result
    result = Image.new('RGB', (output_size, output_size))
    for x0, x1, sx0, sx1, flip_x in segments(box[0], box[2], source.width):
        for y0, y1, sy0, sy1, flip_y in segments(box[1], box[3], source.height):
            patch = source.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS, box=(sx0, sy0, sx1, sy1))
            if flip_x:
                patch = ImageOps.mirror(patch)
            if flip_y:
                patch = ImageOps.flip(patch)
            result.paste(patch, (x0, y0))
    return result


def render_tile(source, edits, template='square'):
    spec = template_info(template)
    if template == 'square':
        return mirror_tile(prepare_photo(source, edits))
    rotation = int(number(edits, 'rotation', 0, 0, 270))
    if rotation % 90:
        raise ValueError('Rotação inválida.')
    image = source.rotate(-rotation, expand=True) if rotation else source
    x0, y0, x1, y1 = crop_geometry(image.size, edits)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # Crop and zoom refer to the VISIBLE diameter; the extra ring uses the
    # continuation of the original photo, with reflection as a fallback.
    half = (x1 - x0) * spec['cut_mm'] / spec['visible_mm'] / 2
    image = reflected_region(image, (cx - half, cy - half, cx + half, cy + half), spec['cut_px'])
    for key, enhancer in [('brightness', ImageEnhance.Brightness), ('contrast', ImageEnhance.Contrast), ('saturation', ImageEnhance.Color), ('sharpness', ImageEnhance.Sharpness)]:
        image = enhancer(image).enhance(number(edits, key, 1, 0, 3 if key == 'sharpness' else 2))
    # Supersampled mask prevents a jagged white edge on circular cuts.
    size = spec['cut_px']
    mask = Image.new('L', (size * 3, size * 3))
    ImageDraw.Draw(mask).ellipse((0, 0, size * 3 - 1, size * 3 - 1), fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)
    tile = Image.new('RGB', (size, size), 'white')
    tile.paste(image, (0, 0), mask)
    return tile


def page_positions(count, template='square'):
    spec = template_info(template)
    if template != 'square':
        if not 1 <= count <= spec['capacity']:
            raise ValueError('Quantidade incompatível com o gabarito.')
        size = spec['cut_px']
        cols = min(spec['columns'], count)
        rows = math.ceil(count / spec['columns'])
        gap_y = (PAGE[1] - rows * size) / (rows + 1)
        positions = []
        for row in range(rows):
            row_count = min(cols, count - row * spec['columns'])
            gap_x = (PAGE[0] - row_count * size) / (row_count + 1)
            for col in range(row_count):
                positions.append((round(gap_x + col * (size + gap_x)), round(gap_y + row * (size + gap_y))))
        return positions
    if count not in (1, 2):
        raise ValueError('Cada folha precisa ter uma ou duas fotos.')
    y = round((PAGE[1] - TILE) / 2)
    if count == 1:
        return [(round((PAGE[0] - TILE) / 2), y)]
    gap = (PAGE[0] - TILE * 2) / 3
    return [(round(gap), y), (round(gap * 2 + TILE), y)]


def compose_page(tiles, template='square'):
    page = Image.new('RGB', PAGE, 'white')
    for tile, position in zip(tiles, page_positions(len(tiles), template)):
        page.paste(tile, position)
    return page


def jpeg_bytes(page):
    output = io.BytesIO()
    page.save(output, 'JPEG', quality=100, subsampling=0, optimize=True, dpi=(DPI, DPI), icc_profile=SRGB.tobytes())
    return output.getvalue()

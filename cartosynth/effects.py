"""
Stage 3: degrade the glyphs (opacity, frayed edges, blur).
Stage 4: put the background image behind the labels and set the canvas to its size.
"""
import base64
import os
import random
import re

from PIL import Image

from .config import resolve

MIME_TYPES = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg'}
FILTERS_PER_FILE = 10


def glyph_filters(effects_cfg):
    """<defs> with FILTERS_PER_FILE random filters: optional fractal-noise displacement + blur."""
    defs = '<defs id="defs1">\n'
    for i in range(FILTERS_PER_FILE):
        blur = round(random.uniform(*effects_cfg["blur"]), 2)
        roughness = round(random.uniform(*effects_cfg["roughness"]), 2)
        primitives = ""
        source = "SourceGraphic"
        if roughness > 0:
            # frayed edges: shift the outline by up to `roughness` px along fractal noise
            primitives += f'''
        <feTurbulence type="fractalNoise" baseFrequency="{round(random.uniform(0.4, 1.2), 2)}"
          numOctaves="2" seed="{random.randint(0, 9999)}" result="noise_{i}" />
        <feDisplacementMap in="SourceGraphic" in2="noise_{i}" scale="{roughness}"
          xChannelSelector="R" yChannelSelector="G" result="rough_{i}" />'''
            source = f"rough_{i}"
        primitives += f'''
        <feGaussianBlur in="{source}" stdDeviation="{blur}" id="feGaussianBlur_{i}" />'''
        defs += f'''  <filter style="color-interpolation-filters:sRGB" id="filter_{i}"
        x="-0.1" y="-0.1" width="1.2" height="1.2">{primitives}
      </filter>
'''
    return defs + '</defs>'


def add_glyph_artefacts(dirs, effects_cfg):
    """dirs.svg_paths -> dirs.svg_effects. Only glyph outlines (id="pathN") are changed."""
    low, high = effects_cfg["glyph_opacity"]

    def style_glyph(match):
        opacity = round(random.uniform(low, high), 2)
        return f'{match.group(0)} style="opacity:{opacity};filter:url(#filter_{random.randint(0, FILTERS_PER_FILE - 1)})"'

    for file in sorted(os.listdir(dirs.svg_paths)):
        if not file.endswith('.svg'):
            continue
        with open(os.path.join(dirs.svg_paths, file), encoding="utf-8") as f:
            svg = f.read()

        defs = glyph_filters(effects_cfg)
        svg, replaced = re.subn(r'<defs\s+id="defs\d+"\s*/>', defs, svg)
        if not replaced:  # no empty <defs/> written by Inkscape: add ours after <svg ...>
            svg = re.sub(r'(<svg\b[^>]*>)', lambda m: m.group(1) + "\n" + defs, svg, count=1)
        svg = re.sub(r'id="path\d+"', style_glyph, svg)

        with open(os.path.join(dirs.svg_effects, file), "w", encoding="utf-8") as f:
            f.write(svg)


def add_background(dirs, backgrounds_dir):
    """dirs.svg_effects -> dirs.svg_background, background from the data-template attribute."""
    backgrounds_dir = resolve(backgrounds_dir)
    for file in sorted(os.listdir(dirs.svg_effects)):
        if not file.endswith('.svg'):
            continue
        with open(os.path.join(dirs.svg_effects, file), encoding="utf-8") as f:
            svg = f.read()

        match = re.search(r'data-template="([^"]+)"', svg)
        background_path = os.path.join(backgrounds_dir, match.group(1)) if match else None
        if background_path and os.path.exists(background_path):
            with Image.open(background_path) as im:
                img_w, img_h = im.size
            mime_type = MIME_TYPES.get(background_path.rsplit('.', 1)[-1].lower(), 'image/png')
            with open(background_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            background_element = (
                f'<image id="background" x="0" y="0" width="{img_w}" height="{img_h}" '
                f'href="data:{mime_type};base64,{encoded}" '
                f'xlink:href="data:{mime_type};base64,{encoded}" '
                f'xmlns:xlink="http://www.w3.org/1999/xlink" />'
            )
            # canvas = background size, background as first element of the layer
            svg = re.sub(r'width="[^"]+"', f'width="{img_w}"', svg, count=1)
            svg = re.sub(r'height="[^"]+"', f'height="{img_h}"', svg, count=1)
            svg = re.sub(r'viewBox="[^"]+"', f'viewBox="0 0 {img_w} {img_h}"', svg, count=1)
            svg = re.sub(r'(<g\s+id="layer1">)', lambda m: m.group(1) + '\n' + background_element, svg)
        elif match:
            print(f"WARNING: background {match.group(1)} not found for {file}, tile stays blank")

        with open(os.path.join(dirs.svg_background, file), 'w', encoding="utf-8") as f:
            f.write(svg)

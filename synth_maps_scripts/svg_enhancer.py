import os, subprocess, re
import base64
import itertools
import random

# Ink on the 3LA scans is dark but not fully opaque: hachures and contour lines show through a little.
MIN_GLYPH_OPACITY = 0.75
MAX_GLYPH_OPACITY = 0.95


def replace_path_id(match):
    opacity = round(random.uniform(MIN_GLYPH_OPACITY, MAX_GLYPH_OPACITY), 2)
    filter_id = random.randint(0, 9)
    path_num = re.search(r'\d+', match.group(0)).group()
    return f'id="path{path_num}" style="opacity:{opacity};filter:url(#filter_{filter_id})"'


from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def add_glyph_artefacts(min_blur_level=0.3, max_blur_level=0.7, min_roughness=0.4, max_roughness=1.2):
    """
    Degrades the glyphs so they look printed and scanned instead of vector-sharp:
    frayed edges (fractal noise displacement, `roughness` in px), blur and varying opacity.
    Displacement and blur move edges by ~1-2 px at most, so the bezier annotations stay valid.
    """
    glyph_path_dir = os.path.join(BASE_DIR, "synth_maps", "svg_maps_with_glyph_paths")
    maps_with_artefacts_dir = os.path.join(BASE_DIR, "synth_maps", "svg_maps_with_artefacts")
    os.makedirs(maps_with_artefacts_dir, exist_ok=True)

    if not os.path.exists(glyph_path_dir):
        print(f"Directory {glyph_path_dir} does not exist!")
        return

    for file in os.listdir(glyph_path_dir):
        if not file.endswith('.svg'):
            continue
        # Build defs block with 10 filters of varying roughness and blur
        all_filters = '<defs id="defs1">\n'
        for filter_strength in range(10):
            blur = round(random.uniform(min_blur_level, max_blur_level), 2)
            roughness = round(random.uniform(min_roughness, max_roughness), 2)
            frequency = round(random.uniform(0.4, 1.2), 2)
            seed = random.randint(0, 9999)
            all_filters += f"""  <filter
        style="color-interpolation-filters:sRGB"
        id="filter_{filter_strength}"
        x="-0.1"
        y="-0.1"
        width="1.2"
        height="1.2">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="{frequency}"
          numOctaves="2"
          seed="{seed}"
          result="noise_{filter_strength}" />
        <feDisplacementMap
          in="SourceGraphic"
          in2="noise_{filter_strength}"
          scale="{roughness}"
          xChannelSelector="R"
          yChannelSelector="G"
          result="rough_{filter_strength}" />
        <feGaussianBlur
          in="rough_{filter_strength}"
          stdDeviation="{blur}"
          id="feGaussianBlur_{filter_strength}" />
      </filter>"""
        all_filters += '</defs>'

        with open(os.path.join(glyph_path_dir, file), "r") as f:
            svg = f.read()

        # Inject filters into defs
        svg = re.sub(r'<defs\s+id="defs\d+"\s*/>', all_filters, svg)

        svg = re.sub(r'id="path\d+"', replace_path_id, svg)

        with open(os.path.join(maps_with_artefacts_dir, file), "w") as f:
            f.write(svg)

        print(f"Processed {file}")


def add_map_background(map_templates_dir=None):
    maps_with_artefacts_dir = os.path.join(BASE_DIR, "synth_maps", "svg_maps_with_artefacts")
    maps_with_background_dir = os.path.join(BASE_DIR, "synth_maps", "svg_maps_w_background")
    os.makedirs(maps_with_background_dir, exist_ok=True)

    if map_templates_dir is None:
        map_templates_dir = os.path.join(BASE_DIR, "map_templates")

    if not os.path.exists(map_templates_dir):
        print(f"Template directory {map_templates_dir} does not exist!")
        return

    template_files = sorted(
        [f for f in os.listdir(map_templates_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.svg'))],
        key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else x
    )
    
    if not template_files:
        print("No template files found!")
        return

    for file in sorted(os.listdir(maps_with_artefacts_dir)):
        if not file.endswith('.svg'):
            continue

        with open(os.path.join(maps_with_artefacts_dir, file), 'r') as f:
            svg = f.read()

        # Check if data-template is stored in svg
        template_file = None
        match = re.search(r'data-template="([^"]+)"', svg)
        if match and match.group(1):
            cand = match.group(1)
            if os.path.exists(os.path.join(map_templates_dir, cand)):
                template_file = cand

        if not template_file:
            file_num_match = re.search(r'\d+', file)
            if file_num_match:
                svg_idx = int(file_num_match.group())
                template_file = template_files[svg_idx % len(template_files)]
            else:
                template_file = template_files[0]

        template_path = os.path.join(map_templates_dir, template_file)
        with Image.open(template_path) as im:
            img_w, img_h = im.size

        # Read and encode the background image as base64
        ext = template_file.split('.')[-1].lower()
        mime_types = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'svg': 'image/svg+xml'}
        mime_type = mime_types.get(ext, 'image/png')

        with open(template_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')

        background_element = (
            f'<image id="background" x="0" y="0" width="{img_w}" height="{img_h}" '
            f'href="data:{mime_type};base64,{encoded}" '
            f'xlink:href="data:{mime_type};base64,{encoded}" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" />'
        )

        # Ensure svg width, height, and viewBox match the template dimensions
        svg = re.sub(r'width="[^"]+"', f'width="{img_w}"', svg, count=1)
        svg = re.sub(r'height="[^"]+"', f'height="{img_h}"', svg, count=1)
        svg = re.sub(r'viewBox="[^"]+"', f'viewBox="0 0 {img_w} {img_h}"', svg, count=1)

        # Insert background image as first element inside <g id="layer1">
        svg = re.sub(
            r'(<g\s+id="layer1">)',
            r'\1' + '\n' + background_element,
            svg
        )

        with open(os.path.join(maps_with_background_dir, file), 'w') as f:
            f.write(svg)

        print(f"Processed {file} with background {template_file} ({img_w}x{img_h})")


if __name__ == "__main__":
    add_glyph_artefacts()
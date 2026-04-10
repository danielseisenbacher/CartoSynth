import os, subprocess, re
import base64
import itertools
import random

def replace_path_id(match):
    opacity = round(random.uniform(0.75, 0.85), 2)
    filter_id = random.randint(0, 9)
    path_num = re.search(r'\d+', match.group(0)).group()
    return f'id="path{path_num}" style="opacity:{opacity};filter:url(#filter_{filter_id})"'


def add_glyph_artefacts(min_blur_level=0.25, max_blur_level=0.75):
    glyph_path_dir = "/workspaces/SynthMap/synth_maps/svg_maps_with_glyph_paths"
    maps_with_artefacts_dir = "/workspaces/SynthMap/synth_maps/svg_maps_with_artefacts"

    for file in os.listdir(glyph_path_dir):
        # Build defs block with 10 filters of varying blur
        all_filters = '<defs id="defs1">\n'
        for filter_strength in range(10):
            blur = round(random.uniform(min_blur_level, max_blur_level), 2)
            all_filters += f"""  <filter
        style="color-interpolation-filters:sRGB"
        id="filter_{filter_strength}"
        x="-0.05"
        y="-0.05"
        width="2"
        height="2">
        <feGaussianBlur
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

        
        


def add_map_background():
    maps_with_artefacts_dir = "/workspaces/SynthMap/synth_maps/svg_maps_with_artefacts"
    maps_with_background_dir = "/workspaces/SynthMap/synth_maps/svg_maps_w_background"
    map_templates_dir = "/workspaces/SynthMap/map_templates"

    template_files = [f for f in os.listdir(map_templates_dir) 
                      if f.endswith('.png') or f.endswith('.jpg') or f.endswith('.svg')]
    
    if not template_files:
        print("No template files found!")
        return

    # itertools.cycle loops back to the start when it runs out
    template_cycle = itertools.cycle(template_files)

    for file in os.listdir(maps_with_artefacts_dir):
        if not file.endswith('.svg'):
            continue

        template_file = next(template_cycle)
        template_path = os.path.join(map_templates_dir, template_file)

        # Read and encode the background image as base64
        ext = template_file.split('.')[-1].lower()
        mime_types = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'svg': 'image/svg+xml'}
        mime_type = mime_types.get(ext, 'image/png')

        with open(template_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')

        background_element = (
            f'<image id="background" x="0" y="0" width="1000" height="1000" '
            f'href="data:{mime_type};base64,{encoded}" '
            f'xlink:href="data:{mime_type};base64,{encoded}" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" />'
        )

        # Read the svg
        with open(os.path.join(maps_with_artefacts_dir, file), 'r') as f:
            svg = f.read()

        # Insert background image as first element inside <g id="layer1">
        svg = re.sub(
            r'(<g\s+id="layer1">)',
            r'\1' + '\n' + background_element,
            svg
        )

        with open(os.path.join(maps_with_background_dir, file), 'w') as f:
            f.write(svg)

        print(f"Processed {file} with background {template_file}")


if __name__ == "__main__":
    add_glyph_artefacts()
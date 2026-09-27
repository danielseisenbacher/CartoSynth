import io
import os
import random
import subprocess

from PIL import Image, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def simulate_scan(png_path, min_blur=0.2, max_blur=0.5, min_jpeg_quality=55, max_jpeg_quality=85):
    """Slight optical blur + JPEG artefacts over the whole tile, like the scanned 3LA sheets."""
    with Image.open(png_path) as im:
        img = im.convert("RGB")
    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(min_blur, max_blur)))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=random.randint(min_jpeg_quality, max_jpeg_quality))
    buffer.seek(0)
    Image.open(buffer).save(png_path)

def svg2png(scan_effect=True):
    svg_source_dir = os.path.join(BASE_DIR, "synth_maps", "svg_maps_w_background")
    png_dir = os.path.join(BASE_DIR, "synth_maps", "png_maps")
    os.makedirs(png_dir, exist_ok=True)

    if not os.path.exists(svg_source_dir):
        print(f"Directory {svg_source_dir} does not exist!")
        return

    for file_name in sorted(os.listdir(svg_source_dir)):
        if not file_name.endswith('.svg'):
            continue
        source_svg = os.path.join(svg_source_dir, file_name)
        png_path = os.path.join(png_dir, f"{file_name.replace('.svg', '')}.png")

        command = (
            "inkscape "
            "--export-type=png "
            "--export-area-page "
            f"--export-filename={png_path} "
            f"{source_svg}"
        )

        # Run the command
        subprocess.run(command, shell=True, check=True)
        if scan_effect:
            simulate_scan(png_path)
        print(f"svg2png processed for {file_name}")


"""Stage 5: render the final SVGs to PNG (Inkscape), optionally with a scan simulation."""
import io
import os
import random
import subprocess

from PIL import Image, ImageFilter


def simulate_scan(png_path, scan_cfg):
    """Slight optical blur + JPEG artefacts over the whole tile, like a scanned map sheet."""
    with Image.open(png_path) as im:
        img = im.convert("RGB")
    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(*scan_cfg["blur"])))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=random.randint(*scan_cfg["jpeg_quality"]))
    buffer.seek(0)
    Image.open(buffer).save(png_path)


def svg2png(dirs, scan_cfg):
    """dirs.svg_background -> dirs.images/<n>.png"""
    files = sorted(f for f in os.listdir(dirs.svg_background) if f.endswith('.svg'))
    for i, file_name in enumerate(files, 1):
        png_path = os.path.join(dirs.images, file_name.replace('.svg', '.png'))
        subprocess.run(
            ["inkscape", "--export-type=png", "--export-area-page", f"--export-filename={png_path}",
             os.path.join(dirs.svg_background, file_name)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if scan_cfg["enabled"]:
            simulate_scan(png_path, scan_cfg)
        if i % 50 == 0 or i == len(files):
            print(f"  rendered {i}/{len(files)}")

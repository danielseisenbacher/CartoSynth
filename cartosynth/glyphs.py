"""
Prepares glyph outlines for custom fonts from cut-out letter images (`./cartosynth.sh glyphs`).

  data/fonts/glyph_scans/<family>/<name>.(png|jpg|tif)   one cut-out letter per file
      -> background removal (only if the image has no transparency yet)
  data/fonts/glyph_images/<family>/<name>.png            black letter on transparent background
      -> vectorisation (vtracer)
  data/fonts/glyphs/<family>/<name>.svg                  input of `./cartosynth.sh fonts`

<name> as in fontforge_build.py: a character (A, a, 0, ä), U+00E4, or a glyph name (zero).
Existing outputs are not overwritten unless --force is given.
"""
import os

import cv2
import numpy as np
import vtracer

from .fonts import FONTS_DIR, GLYPHS_DIR

SCANS_DIR = os.path.join(FONTS_DIR, "glyph_scans")
IMAGES_DIR = os.path.join(FONTS_DIR, "glyph_images")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")


def remove_background(img_bgr):
    """Dark letter on light paper -> black letter with smooth alpha (Otsu threshold)."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    blurred = cv2.GaussianBlur(denoised, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), iterations=1)
    alpha = (cv2.GaussianBlur(binary.astype(np.float32) / 255.0, (3, 3), 0) * 255).astype(np.uint8)
    rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)
    rgba[:, :, 3] = alpha
    return rgba


def to_glyph_image(src, dst):
    img = cv2.imread(src, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError("cannot read image")
    if img.ndim == 3 and img.shape[2] == 4 and img[:, :, 3].min() < 255:
        rgba = img                                   # already cut out
    else:
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        rgba = remove_background(img[:, :, :3])
    cv2.imwrite(dst, rgba)


def vectorize(src_png, dst_svg):
    vtracer.convert_image_to_svg_py(
        src_png, dst_svg,
        colormode='color', hierarchical='stacked', mode='spline',
        filter_speckle=4, color_precision=6, layer_difference=16, corner_threshold=45,
        length_threshold=4.0, max_iterations=15, splice_threshold=45, path_precision=8,
    )


def prepare_glyphs(force=False):
    if not os.path.isdir(SCANS_DIR):
        print(f"No glyph scans in {SCANS_DIR}")
        return
    for family in sorted(os.listdir(SCANS_DIR)):
        scan_dir = os.path.join(SCANS_DIR, family)
        if not os.path.isdir(scan_dir):
            continue
        os.makedirs(os.path.join(IMAGES_DIR, family), exist_ok=True)
        os.makedirs(os.path.join(GLYPHS_DIR, family), exist_ok=True)
        done = skipped = 0
        for file in sorted(os.listdir(scan_dir)):
            if not file.lower().endswith(IMAGE_EXTENSIONS):
                continue
            stem = os.path.splitext(file)[0]
            png = os.path.join(IMAGES_DIR, family, stem + ".png")
            svg = os.path.join(GLYPHS_DIR, family, stem + ".svg")
            if os.path.exists(svg) and not force:
                skipped += 1
                continue
            try:
                to_glyph_image(os.path.join(scan_dir, file), png)
                vectorize(png, svg)
                done += 1
            except Exception as e:
                print(f"  WARNING {family}/{file}: {e}")
        print(f"{family}: {done} glyphs vectorised, {skipped} already existed")

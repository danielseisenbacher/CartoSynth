"""Measures how long a baseline a label needs, by rendering it with Inkscape."""
import os
import subprocess

import svgpathtools

from .svg_templates import get_word_template

REFERENCE_START = 50
REFERENCE_LENGTH = 2000


def text_to_paths(svg_in, svg_out):
    """Inkscape: convert all <text> to glyph outlines (<path>)."""
    subprocess.run(
        ["inkscape", svg_in,
         f"--actions=export-text-to-path;export-plain-svg;export-filename:{svg_out};export-do"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return svg_out


def text_length(text, font_family, font_size, canvas_width, canvas_height, tmp_dir, canvas_buffer=10):
    """
    Width of `text` in px, or False if it is empty or does not fit on the canvas
    (longer than 80% of the usable width / 1.5x the usable height).
    """
    if not text or not text.strip():
        return False

    svg = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="2200" height="500" viewBox="0 0 2200 500" version="1.1"
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <g id="layer1">
    <path id="reference" d="m {REFERENCE_START},250 c 0,0 0,0 {REFERENCE_LENGTH},0" style="fill:none;stroke:#000;stroke-width:0.3"/>
    {get_word_template("reference", text, font_family, font_size)}
  </g>
</svg>'''
    os.makedirs(tmp_dir, exist_ok=True)
    test_file = os.path.join(tmp_dir, "measure.svg")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(svg)
    text_to_paths(test_file, test_file)

    paths, _ = svgpathtools.svg2paths(test_file)
    x_values = set()
    for path in paths:
        x_values |= set(path.bbox()[:2])
    x_values -= {REFERENCE_START, REFERENCE_START + REFERENCE_LENGTH}   # the reference line itself
    if not x_values:
        return False

    length = max(x_values) - min(x_values)
    max_allowed = min(canvas_width - 2 * canvas_buffer, (canvas_height - 2 * canvas_buffer) * 1.5) * 0.8
    if length > max_allowed:
        return False
    return length

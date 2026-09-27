"""
Stage 1: place labels on each tile and write an SVG with <text> on bezier baselines.

Words come from the word list, numbers (e.g. elevations) are generated. Each label gets a
font style that can render it, a size, an ink colour and a baseline that stays inside the
canvas and away from the other labels.
"""
import os
import random
import re
from math import sqrt

import numpy as np
import svgpathtools
from PIL import Image

from . import svg_templates, text_measure
from .config import resolve

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg')


# --- backgrounds -------------------------------------------------------------------------

def list_backgrounds(backgrounds_dir):
    if not backgrounds_dir or not os.path.isdir(backgrounds_dir):
        return []
    files = [f for f in os.listdir(backgrounds_dir) if f.lower().endswith(IMAGE_EXTENSIONS)]
    files.sort(key=lambda x: (int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else -1, x))
    return files


def canvas_for(tile_nr, cfg, backgrounds):
    """(width, height, background file name) of tile `tile_nr`."""
    if backgrounds:
        background = backgrounds[tile_nr % len(backgrounds)]
        with Image.open(os.path.join(resolve(cfg["backgrounds"]["dir"]), background)) as im:
            return im.size[0], im.size[1], background
    width, height = cfg["backgrounds"]["canvas_size"] or (1000, 1000)
    return width, height, ""


# --- labels ------------------------------------------------------------------------------

def choose_style(label, styles):
    """Random font style that can render `label`; adapts the case for single-case styles."""
    has_digit = bool(re.search(r'\d', label))
    has_letter = any(c.isalpha() for c in label)
    fitting = [s for s in styles
               if (s.get("digits", False) or not has_digit) and (s.get("letters", False) or not has_letter)]
    if not fitting:
        fitting = [s for s in styles if s.get("fallback")][-1:]
    style = random.choice(fitting)
    if not style.get("uppercase", True):
        label = label.lower()
    if not style.get("lowercase", True):
        label = label.upper()
    return style, label


def random_number(numbers_cfg):
    """Numeric label, e.g. an elevation: lognormal around `median`, some 1-2 digit values."""
    if random.random() < numbers_cfg["small_share"]:
        return str(random.randint(1, 99))
    value = np.random.lognormal(np.log(numbers_cfg["median"]), numbers_cfg["sigma"])
    return str(int(min(max(value, numbers_cfg["min_value"]), numbers_cfg["max_value"])))


def ink_colour(cfg, is_number):
    ink = cfg["ink"]
    if is_number and ink["number_colours"] and random.random() < ink["number_colour_prob"]:
        return random.choice(ink["number_colours"])
    return random.choice(ink["colours"])


def number_marker(path, font_size, canvas_width, canvas_height):
    """Small point symbol left or right of a number (decoration, not annotated)."""
    radius = max(2.0, font_size * 0.18)
    gap = font_size * 0.45
    direction = path.end - path.start
    unit = direction / abs(direction) if abs(direction) else complex(1, 0)
    anchor = path.start - unit * gap if random.random() < 0.5 else path.end + unit * gap
    x = min(max(anchor.real, radius + 1), canvas_width - radius - 1)
    y = min(max(anchor.imag - font_size * 0.3, radius + 1), canvas_height - radius - 1)
    return {"x": round(x, 1), "y": round(y, 1), "r": round(radius, 1)}


# --- baselines ---------------------------------------------------------------------------

def add_path_buffers(bezier, existing_paths_buffers, canvas_buffer):
    """Circles along the path so later labels keep their distance."""
    for cp in bezier.points(np.linspace(0, 1, 30)):
        for sign in (1, -1):
            existing_paths_buffers.append(
                svgpathtools.path.Arc(
                    start=complex(cp.real, cp.imag - sign * canvas_buffer * 2),
                    radius=complex(canvas_buffer * 2, canvas_buffer * 2),
                    rotation=0,
                    large_arc=False,
                    sweep=True,
                    end=complex(cp.real, cp.imag + sign * canvas_buffer * 2)
                )
            )
    return existing_paths_buffers


def propose_a_path(length, existing_paths_buffers, canvas_width, canvas_height, placement_cfg,
                   straight=False, max_angle_deg=6):
    """
    Baseline of `length` px that stays inside the canvas and does not touch other labels.
    Curved (random cubic bezier, skewed towards horizontal) or, for numbers, straight and
    almost horizontal. Returns (bezier or None, updated buffers).
    """
    canvas_buffer = placement_cfg["canvas_buffer"]
    b, bx, by = canvas_buffer, canvas_width - canvas_buffer, canvas_height - canvas_buffer
    border_buffer = svgpathtools.Path(
        svgpathtools.path.Line(complex(b, b), complex(bx, b)),
        svgpathtools.path.Line(complex(bx, b), complex(bx, by)),
        svgpathtools.path.Line(complex(bx, by), complex(b, by)),
        svgpathtools.path.Line(complex(b, by), complex(b, b))
    )

    for _ in range(placement_cfg["max_attempts"]):
        start = complex(random.randint(b, bx), random.randint(b, by))

        if straight:
            angle = np.radians(random.uniform(-max_angle_deg, max_angle_deg))
            end = start + length * complex(np.cos(angle), np.sin(angle))
            bezier = svgpathtools.path.CubicBezier(start, start + (end - start) / 3, start + 2 * (end - start) / 3, end)
            if border_buffer.intersect(bezier, justonemode=True) or existing_paths_buffers.intersect(bezier, justonemode=True):
                continue
            return bezier, add_path_buffers(bezier, existing_paths_buffers, canvas_buffer)

        # skewed towards horizontal text
        x_length = random.betavariate(3, 1) * length
        y_length = sqrt(length ** 2 - x_length ** 2) * random.choice([1, -1])
        end = start + complex(x_length, y_length)
        chord = svgpathtools.path.Line(start, end)
        if border_buffer.intersect(chord, justonemode=True) or existing_paths_buffers.intersect(chord, justonemode=True):
            continue

        for _ in range(50):
            control1 = start + complex(random.randint(-int(length), int(length)), random.randint(-int(length), int(length)))
            control2 = end + complex(random.randint(-canvas_buffer, canvas_buffer), random.randint(-canvas_buffer, canvas_buffer))
            bezier = svgpathtools.path.CubicBezier(start, control1, control2, end)

            if border_buffer.intersect(bezier, justonemode=True):
                continue

            def safe_curvature(t):
                try:
                    return abs(bezier.curvature(t))
                except (ValueError, ZeroDivisionError):
                    return 0.0

            if max(safe_curvature(t) for t in np.linspace(0, 1, 1000)) > placement_cfg["max_curvature"]:
                continue
            if existing_paths_buffers.intersect(bezier, justonemode=True):
                continue
            return bezier, add_path_buffers(bezier, existing_paths_buffers, canvas_buffer)

    return None, existing_paths_buffers


# --- SVG ---------------------------------------------------------------------------------

def save_svg(path, labels, markers, canvas_width, canvas_height, background, marker_colour):
    body = ""
    for idx, label in enumerate(labels):
        body += svg_templates.get_bezier_template(f"bezier{idx}", svgpathtools.Path(label["bezier"]).d())
        body += svg_templates.get_word_template(f"bezier{idx}", label["text"], label["font"], label["font_size"], label["fill"])
    # every element needs an id (beziers.py reads all ids)
    for idx, marker in enumerate(markers):
        body += svg_templates.get_marker_template(f"marker{idx}", marker["x"], marker["y"], marker["r"], marker_colour)

    svg = svg_templates.get_svg_template(canvas_width, canvas_height, template_name=background)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg.replace("BEZIER_LIST", body))


def create_svgs(cfg, words, dirs):
    """Writes <num_maps> stage-1 SVGs into dirs.svg_text."""
    backgrounds = list_backgrounds(resolve(cfg["backgrounds"]["dir"]))
    if not backgrounds:
        print(f"WARNING: no backgrounds in {cfg['backgrounds']['dir']}, tiles stay blank")
    styles = cfg["fonts"]["styles"]
    numbers_cfg = cfg["numbers"]
    low, high = cfg["labels_per_map"]
    word_idx = 0

    for tile_nr in range(cfg["num_maps"]):
        width, height, background = canvas_for(tile_nr, cfg, backgrounds)
        print(f"[{tile_nr + 1}/{cfg['num_maps']}] tile {tile_nr} ({width}x{height}, background {background or '-'})")

        labels, markers = [], []
        buffers = svgpathtools.Path()
        for _ in range(random.randint(low, high)):
            is_number = random.random() < numbers_cfg["share"]
            if is_number:
                style, text = choose_style(random_number(numbers_cfg), styles)
                font_size = max(8, round(random.randint(*style["size"]) * numbers_cfg["font_scale"]))
            else:
                style, text = choose_style(words[word_idx], styles)
                font_size = random.randint(*style["size"])
                word_idx = (word_idx + 1) % len(words)

            length = text_measure.text_length(text, style["family"], font_size, width, height, dirs.tmp)
            # too long for the tile: shorten words (numbers are dropped)
            while not length and not is_number and len(text) > 2:
                text = text[:-1].strip()
                length = text_measure.text_length(text, style["family"], font_size, width, height, dirs.tmp)
            if not length:
                continue

            bezier, buffers = propose_a_path(length, buffers, width, height, cfg["placement"],
                                             straight=is_number, max_angle_deg=numbers_cfg["max_angle_deg"])
            if bezier is None:
                print(f"    could not place '{text}', skipped")
                continue

            labels.append({"text": text, "bezier": bezier, "font": style["family"],
                           "font_size": font_size, "fill": ink_colour(cfg, is_number)})
            if is_number and random.random() < numbers_cfg["marker_prob"]:
                markers.append(number_marker(bezier, font_size, width, height))
            print(f"    '{text}' [{style['family']}, {font_size}px]")

        save_svg(os.path.join(dirs.svg_text, f"{tile_nr}.svg"), labels, markers, width, height,
                 background, numbers_cfg["marker_colour"])

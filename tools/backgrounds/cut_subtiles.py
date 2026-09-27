#!/usr/bin/env python3
"""
Step 3 of making backgrounds (optional): cut several smaller sub-tiles out of each
text-free tile, e.g. to turn 1024x1024 AI images into varied 300-800 px backgrounds.

Cuts multiple sub-tiles out of every image tile in a directory.

For each source tile (e.g. 1024x1024 map tiles), this generates at least
`--num-crops` rectangular crops whose width and height are each chosen
independently between `--min-size` and `--max-size` pixels, and places
them so that the overlap between any two crops is kept as small as
possible (subject to how many crops you ask for and how big they are).

Usage:
    python tools/backgrounds/cut_subtiles.py --input-dir tiles/ --output-dir subtiles/
    python tools/backgrounds/cut_subtiles.py -i tiles/ -o subtiles/ -n 4 --min-size 300 --max-size 800

Requires: Pillow (pip install Pillow)
"""

import argparse
import itertools
import random
import sys
from pathlib import Path

from PIL import Image

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def rect_overlap_area(a, b):
    """Overlap area (in px^2) between two (x0, y0, x1, y1) rectangles."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ox = max(0, min(ax1, bx1) - max(ax0, bx0))
    oy = max(0, min(ay1, by1) - max(ay0, by0))
    return ox * oy


def random_box(img_w, img_h, min_size, max_size, rng):
    """A random (x0, y0, x1, y1) box with independent random w/h in range."""
    w = rng.randint(min_size, min(max_size, img_w))
    h = rng.randint(min_size, min(max_size, img_h))
    x0 = rng.randint(0, img_w - w)
    y0 = rng.randint(0, img_h - h)
    return (x0, y0, x0 + w, y0 + h)


def place_crops(img_w, img_h, num_crops, min_size, max_size, rng,
                 attempts_per_crop=200):
    """
    Greedily place `num_crops` boxes, minimizing overlap with boxes already
    placed. For each new crop, try many random candidates and keep the one
    with the least total overlap against existing crops.
    """
    placed = []
    for _ in range(num_crops):
        best_box = None
        best_overlap = None
        for _ in range(attempts_per_crop):
            candidate = random_box(img_w, img_h, min_size, max_size, rng)
            total_overlap = sum(rect_overlap_area(candidate, p) for p in placed)
            if best_overlap is None or total_overlap < best_overlap:
                best_overlap = total_overlap
                best_box = candidate
            if best_overlap == 0:
                break  # can't do better than zero overlap
        placed.append(best_box)
    return placed


def process_image(path: Path, output_dir: Path, num_crops, min_size, max_size, rng):
    with Image.open(path) as img:
        img = img.convert(img.mode)
        w, h = img.size

        if w < min_size or h < min_size:
            print(f"  skipping {path.name}: image ({w}x{h}) smaller than min-size {min_size}")
            return

        boxes = place_crops(w, h, num_crops, min_size, max_size, rng)

        stem = path.stem
        ext = path.suffix
        for i, box in enumerate(boxes, start=1):
            crop = img.crop(box)
            out_name = f"{stem}_sub{i}_{box[0]}-{box[1]}_{box[2]-box[0]}x{box[3]-box[1]}{ext}"
            crop.save(output_dir / out_name)
            print(f"  {path.name} -> {out_name}  box={box}  size={box[2]-box[0]}x{box[3]-box[1]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input-dir", required=True, type=Path,
                         help="Directory containing source map tiles")
    parser.add_argument("-o", "--output-dir", required=True, type=Path,
                         help="Directory to write sub-tiles into")
    parser.add_argument("-n", "--num-crops", type=int, default=3,
                         help="Number of sub-tiles to cut per image (minimum 3, default 3)")
    parser.add_argument("--min-size", type=int, default=300,
                         help="Minimum crop width/height in px (default 300)")
    parser.add_argument("--max-size", type=int, default=800,
                         help="Maximum crop width/height in px (default 800)")
    parser.add_argument("--seed", type=int, default=None,
                         help="Random seed, for reproducible crops")
    args = parser.parse_args()

    if args.num_crops < 3:
        parser.error("--num-crops must be at least 3")
    if args.min_size > args.max_size:
        parser.error("--min-size cannot be greater than --max-size")

    rng = random.Random(args.seed)

    if not args.input_dir.is_dir():
        parser.error(f"input dir not found: {args.input_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        p for p in args.input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )

    if not files:
        print(f"No image files found in {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(files)} tile(s). Cutting {args.num_crops} sub-tile(s) each "
          f"(size range {args.min_size}-{args.max_size}px)...")

    for path in files:
        print(f"Processing {path.name}")
        process_image(path, args.output_dir, args.num_crops,
                       args.min_size, args.max_size, rng)

    print("Done.")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Creates simple procedural "old map" backgrounds (paper, contour-like lines, a river) for
trying CartoSynth without own data: examples/backgrounds/example_<n>.png.
Real training data needs real text-free map backgrounds, see README ("Backgrounds").
"""
import argparse
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def make_background(width, height, seed):
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    paper = np.array([228, 216, 182], dtype=float) + np_rng.normal(0, 6, (height, width, 1))
    img = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(img)
    # contour-like closed curves around a few "hills"
    for _ in range(rng.randint(2, 4)):
        cx, cy = rng.uniform(0, width), rng.uniform(0, height)
        for r in range(15, 260, 12):
            pts = []
            for a in np.linspace(0, 2 * np.pi, 90):
                rr = r * (1 + 0.15 * np.sin(3 * a + r / 30))
                pts.append((cx + rr * np.cos(a), cy + 0.7 * rr * np.sin(a)))
            draw.line(pts + [pts[0]], fill=(120, 95, 70), width=1)
    # a river
    x = np.linspace(-20, width + 20, 60)
    y = height * rng.uniform(0.3, 0.7) + 40 * np.sin(x / rng.uniform(60, 120))
    draw.line(list(zip(x, y)), fill=(90, 130, 170), width=4)
    return img.filter(ImageFilter.GaussianBlur(0.6))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-dir", default="examples/backgrounds")
    parser.add_argument("-n", type=int, default=2)
    args = parser.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    for i in range(args.n):
        path = os.path.join(args.out_dir, f"example_{i + 1}.png")
        make_background(640 + 80 * i, 480, seed=i).save(path)
        print(path)

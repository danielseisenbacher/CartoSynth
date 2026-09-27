"""
Draws the annotations onto the rendered tiles (`./cartosynth.sh visualize <config>`):
green = upper bezier (left->right) with its start point, red = lower bezier,
cyan = bbox, text = transcription. Output: <run>/previews/<n>_annotated.png
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw


def bezier_curve(points, n=30):
    p = np.array(points, dtype=float)
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p[0] + 3 * t * ((1 - t) ** 2) * p[1] + 3 * (t ** 2) * (1 - t) * p[2] + (t ** 3) * p[3]


def draw_annotations(image_path, annotations, out_path, scale=2):
    with Image.open(image_path) as im:
        img = im.convert("RGB")
    img = img.resize((img.width * scale, img.height * scale))
    draw = ImageDraw.Draw(img)
    for ann in annotations:
        pts = np.array(ann["bezier_pts"]).reshape(2, 4, 2) * scale
        upper, lower = bezier_curve(pts[0]), bezier_curve(pts[1])
        draw.line([tuple(p) for p in upper], fill=(0, 220, 0), width=2)
        draw.line([tuple(p) for p in lower], fill=(230, 0, 0), width=2)
        x, y = pts[0][0]
        draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(0, 220, 0))
        bx, by, bw, bh = (v * scale for v in ann["bbox"])
        draw.rectangle([bx, by, bx + bw, by + bh], outline=(0, 200, 230))
        lx, ly = pts[1][-1]
        draw.text((lx, ly + 4), ann["transcription"], fill=(0, 0, 255))
    img.save(out_path)


def visualize_run(dirs, annotation_path, limit=10):
    with open(annotation_path, encoding="utf-8") as f:
        coco = json.load(f)
    by_image = {}
    for ann in coco["annotations"]:
        by_image.setdefault(ann["image_id"], []).append(ann)
    os.makedirs(dirs.previews, exist_ok=True)
    written = []
    for img in coco["images"][:limit]:
        out = os.path.join(dirs.previews, os.path.splitext(img["file_name"])[0] + "_annotated.png")
        draw_annotations(os.path.join(dirs.images, img["file_name"]), by_image.get(img["id"], []), out)
        written.append(out)
    print(f"Wrote {len(written)} previews to {dirs.previews}")
    return written

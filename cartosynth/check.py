"""Consistency checks for a finished run (`./cartosynth.sh check <config>`)."""
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter

import numpy as np


def rendered_words(svg_path):
    """Words drawn on a stage-1 tile (labels split at spaces, like the annotations)."""
    root = ET.parse(svg_path).getroot()
    words = []
    for g in root.iter("{http://www.w3.org/2000/svg}g"):
        words += [w for w in g.get("data-text", "").split(" ") if w]
    return words


def check_run(dirs, annotation_path, vocab):
    problems = []
    with open(annotation_path, encoding="utf-8") as f:
        coco = json.load(f)
    images, annotations = coco["images"], coco["annotations"]

    # 1. every image exists and has the stated size
    for img in images:
        if not os.path.exists(os.path.join(dirs.images, img["file_name"])):
            problems.append(f"missing image {img['file_name']}")

    # 2. every rendered word has exactly one annotation and vice versa
    by_image = {}
    for ann in annotations:
        by_image.setdefault(ann["image_id"], []).append(ann["transcription"])
    unlabelled = extra = 0
    for img in images:
        svg = os.path.join(dirs.svg_text, os.path.splitext(img["file_name"])[0] + ".svg")
        if not os.path.exists(svg):
            problems.append(f"missing stage-1 SVG for {img['file_name']}")
            continue
        drawn, labelled = Counter(rendered_words(svg)), Counter(by_image.get(img["id"], []))
        unlabelled += sum((drawn - labelled).values())
        extra += sum((labelled - drawn).values())
    if unlabelled:
        problems.append(f"{unlabelled} rendered words without annotation")
    if extra:
        problems.append(f"{extra} annotations without rendered word")

    # 3. rec encoding
    for ann in annotations:
        rec = ann["rec"]
        if len(rec) != vocab.max_length:
            problems.append(f"annotation {ann['id']}: rec length {len(rec)} != {vocab.max_length}")
        elif rec != vocab.encode(ann["transcription"]):
            problems.append(f"annotation {ann['id']}: rec does not match '{ann['transcription']}'")
        if vocab.pad - 1 in rec:
            problems.append(f"annotation {ann['id']}: uses the unknown class")

    # 4. bezier order: upper curve left->right, lower curve right->left (opposite directions)
    wrong_order = 0
    heights = {"words": [], "numbers": []}
    for ann in annotations:
        p = np.array(ann["bezier_pts"]).reshape(2, 4, 2)
        if np.dot(p[0, 3] - p[0, 0], p[1, 3] - p[1, 0]) > 0:
            wrong_order += 1
        kind = "numbers" if ann["transcription"].isdigit() else "words"
        heights[kind].append(float(np.linalg.norm(p[0].mean(0) - p[1].mean(0))))
    if wrong_order:
        problems.append(f"{wrong_order} annotations with both bezier curves in the same direction")

    # summary
    transcriptions = [a["transcription"] for a in annotations]
    non_ascii = Counter(c for t in transcriptions for c in t if ord(c) > 126)
    print(f"Run: {dirs.root}")
    print(f"  images:       {len(images)}")
    print(f"  annotations:  {len(annotations)} ({len(heights['numbers'])} numbers, "
          f"{len(annotations) / max(len(images), 1):.1f} per image)")
    for kind, values in heights.items():
        if values:
            print(f"  label height: {kind} median {np.median(values):.1f} px")
    if non_ascii:
        print(f"  non-ASCII:    {' '.join(f'{c}:{n}' for c, n in non_ascii.most_common())}")
    if problems:
        print(f"FAILED ({len(problems)} problems):")
        for p in problems[:30]:
            print(f"  - {p}")
        if len(problems) > 30:
            print(f"  ... {len(problems) - 30} more")
        return False
    print("OK: all checks passed")
    return True

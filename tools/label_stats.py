#!/usr/bin/env python3
"""
Label statistics of COCO text annotations (with `bezier_pts` and `transcription`), to calibrate
CartoSynth on real data: share of numbers and short tokens, token counts, label heights and angles.
Prints a ready-to-paste `short_labels` config block.

    python tools/label_stats.py path/to/train_annotations.json
    python tools/label_stats.py output/3la/train_148voc.json      # compare a generated run

Use only training annotations for calibration (not validation/test).
Short tokens = non-numeric labels with at most --max-len characters, plus abbreviations ending
in "." with at most --abbrev-max-len characters (e.g. "Wh.", "Fl.").
"""
import argparse
import json
from collections import Counter

import numpy as np


def geometry(ann):
    p = np.array(ann["bezier_pts"], dtype=float).reshape(2, 4, 2)
    height = float(np.linalg.norm(p[0].mean(0) - p[1].mean(0)))
    direction = p[0, 3] - p[0, 0]
    angle = float(np.degrees(np.arctan2(direction[1], direction[0])))
    return height, angle


def is_short(text, max_len, abbrev_max_len):
    if text.isdigit():
        return False
    return len(text) <= max_len or (text.endswith(".") and len(text) <= abbrev_max_len)


def describe(name, anns, total):
    if not anns:
        print(f"  {name:8s}      0")
        return
    geo = np.array([geometry(a) for a in anns])
    horizontal = np.mean(np.abs(geo[:, 1]) < 10) * 100
    print(f"  {name:8s} {len(anns):6d} ({len(anns) / total * 100:4.1f} %)   median height {np.median(geo[:, 0]):5.1f} px"
          f"   horizontal (±10°) {horizontal:3.0f} %")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("annotations", help="COCO json with bezier_pts and transcription")
    parser.add_argument("--max-len", type=int, default=2, help="max length of short tokens (default 2)")
    parser.add_argument("--abbrev-max-len", type=int, default=3, help="max length of abbreviations ending in '.'")
    args = parser.parse_args()

    with open(args.annotations, encoding="utf-8") as f:
        anns = json.load(f)["annotations"]
    if anns and "transcription" not in anns[0]:
        raise SystemExit("annotations have no 'transcription' field")
    total = len(anns)

    numbers = [a for a in anns if a["transcription"].isdigit()]
    short = [a for a in anns if is_short(a["transcription"], args.max_len, args.abbrev_max_len)]
    single = [a for a in short if len(a["transcription"]) == 1]
    words = [a for a in anns if a not in numbers and a not in short]

    print(f"{args.annotations}: {total} labels")
    describe("numbers", numbers, total)
    describe("short", short, total)
    describe("  1 char", single, total)
    describe("words", words, total)

    counts = Counter(a["transcription"] for a in short)
    word_height = np.median([geometry(a)[0] for a in words]) if words else float("nan")
    single_height = np.median([geometry(a)[0] for a in single]) if single else float("nan")
    longer = [a for a in short if len(a["transcription"]) > 1]
    longer_height = np.median([geometry(a)[0] for a in longer]) if longer else float("nan")

    print("\nConfig block (heights relative to words):")
    print("short_labels:")
    print(f"  share: {len(short) / total:.2f}")
    print("  tokens: {" + ", ".join(f"{json.dumps(t, ensure_ascii=False)}: {n}" for t, n in counts.most_common()) + "}")
    if single:
        print(f"  font_scale_single: {single_height / word_height:.2f}")
    if longer:
        print(f"  font_scale: {longer_height / word_height:.2f}")
    print(f"numbers:\n  share: {len(numbers) / total:.2f}")


if __name__ == "__main__":
    main()

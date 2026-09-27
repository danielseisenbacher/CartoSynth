"""
Generation pipeline, one run = one folder <output_dir>/<run_name>/:

  1. layout      labels on bezier baselines        -> svg/1_text/<n>.svg
  2. beziers     text -> glyph outlines (Inkscape),
                 fit word beziers                   -> svg/2_paths/, previews/<n>.svg
  3. effects     opacity, blur, frayed edges        -> svg/3_effects/
  4. background  background image behind the text  -> svg/4_background/
  5. render      PNG (Inkscape) + scan simulation   -> images/<n>.png
  6. annotations COCO json                          -> <annotation.file_name>
"""
import os
import random
import shutil
import time

import numpy as np
import yaml

from . import beziers, coco, effects, fonts, layout, render
from .check import check_run
from .config import run_dirs
from .vocab import Vocabulary
from .words import load_words


def stage(name):
    print(f"\n=== {name} ({time.strftime('%H:%M:%S')})")


def generate(cfg, overwrite=False):
    dirs = run_dirs(cfg)
    if os.path.exists(dirs.root) and os.listdir(dirs.root):
        if not overwrite:
            raise FileExistsError(f"{dirs.root} already exists. Use another run_name or --overwrite.")
        shutil.rmtree(dirs.root)
    dirs.create()
    with open(os.path.join(dirs.root, "config.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    if cfg["seed"] is not None:
        random.seed(cfg["seed"])
        np.random.seed(cfg["seed"])

    vocab = Vocabulary.from_config(cfg["annotation"])
    words = load_words(cfg["words"], vocab)
    if not fonts.check_coverage(cfg, words):
        raise RuntimeError("Some font styles are not installed, see above (./cartosynth.sh fonts)")

    started = time.time()
    stage(f"1/6 layout: {cfg['num_maps']} tiles")
    layout.create_svgs(cfg, words, dirs)
    stage("2/6 text to paths + bezier fitting")
    bezier_dict = beziers.build_bezier(dirs, previews=cfg["keep_intermediate"])
    stage("3/6 glyph effects")
    effects.add_glyph_artefacts(dirs, cfg["effects"])
    stage("4/6 backgrounds")
    effects.add_background(dirs, cfg["backgrounds"]["dir"])
    stage("5/6 render PNGs")
    render.svg2png(dirs, cfg["effects"]["scan"])
    stage("6/6 annotations")
    annotation_path = os.path.join(dirs.root, cfg["annotation"]["file_name"])
    coco.build_annotations(bezier_dict, dirs, vocab, annotation_path)

    shutil.rmtree(dirs.tmp, ignore_errors=True)
    if not cfg["keep_intermediate"]:
        # svg/1_text stays: `check` compares it with the annotations
        for d in (dirs.svg_paths, dirs.svg_effects, dirs.svg_background):
            shutil.rmtree(d, ignore_errors=True)

    print(f"\nDone in {(time.time() - started) / 60:.1f} min: {annotation_path}\n")
    return check_run(dirs, annotation_path, vocab)

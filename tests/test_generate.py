"""End-to-end: generate two tiles with the default config and check them (needs Inkscape)."""
import json
import shutil

import numpy as np
import pytest

from cartosynth.config import load_config, run_dirs
from cartosynth.pipeline import generate

pytestmark = pytest.mark.skipif(shutil.which("inkscape") is None, reason="needs Inkscape (run ./cartosynth.sh test)")


def test_generate_default_config(tmp_path):
    cfg = load_config(overrides={"num_maps": 2, "seed": 3, "output_dir": str(tmp_path), "run_name": "e2e"})
    assert generate(cfg)

    dirs = run_dirs(cfg)
    with open(f"{dirs.root}/annotations.json", encoding="utf-8") as f:
        coco = json.load(f)
    assert len(coco["images"]) == 2 and coco["annotations"]
    for ann in coco["annotations"]:
        pts = np.array(ann["bezier_pts"]).reshape(2, 4, 2)
        # upper curve and lower curve run in opposite directions (AdelaiDet convention)
        assert np.dot(pts[0, 3] - pts[0, 0], pts[1, 3] - pts[1, 0]) < 0
        assert len(ann["rec"]) == cfg["annotation"]["max_length"]

    with pytest.raises(FileExistsError):
        generate(cfg)

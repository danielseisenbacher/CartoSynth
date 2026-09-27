import random

import numpy as np
import svgpathtools

from cartosynth.config import load_config
from cartosynth.layout import choose_style, number_marker, propose_a_path, random_number
from cartosynth.vocab import VOC148, Vocabulary
from cartosynth.words import load_words

STYLES = [
    {"family": "upper", "size": [10, 20], "letters": True, "digits": False, "uppercase": True, "lowercase": False, "fallback": False},
    {"family": "digits", "size": [10, 20], "letters": False, "digits": True, "fallback": False},
    {"family": "any", "size": [10, 20], "letters": True, "digits": True, "fallback": True},
]


def test_word_filter(tmp_path):
    words_file = tmp_path / "words.txt"
    words_file.write_text("Wien\nX\nČeské Budějovice\nSankt Pölten\n" + "a" * 30 + "\n", encoding="utf-8")
    words = load_words({"file": str(words_file), "min_word_length": 2, "max_word_length": 25, "shuffle": False},
                       Vocabulary(VOC148, case_fallback={"Ö": "ö", "Ü": "ü"}))
    assert words == ["Wien", "Sankt Pölten"]


def test_choose_style_fits_label():
    random.seed(0)
    for _ in range(50):
        style, text = choose_style("1234", STYLES)
        assert style["digits"]
        style, text = choose_style("Wien", STYLES)
        assert style["letters"]
        if style["family"] == "upper":
            assert text == "WIEN"


def test_random_numbers_follow_distribution():
    np.random.seed(0)
    random.seed(0)
    cfg = load_config(overrides={"numbers": {"share": 0.4}})["numbers"]
    values = [int(random_number(cfg)) for _ in range(3000)]
    assert 500 < np.median(values) < 800
    assert 0.1 < np.mean([v >= 1000 for v in values]) < 0.35


def test_straight_paths_stay_on_canvas():
    random.seed(1)
    placement = {"canvas_buffer": 10, "max_attempts": 150, "max_curvature": 0.5}
    buffers = svgpathtools.Path()
    for _ in range(3):
        bezier, buffers = propose_a_path(120, buffers, 500, 400, placement, straight=True, max_angle_deg=6)
        assert bezier is not None
        for p in (bezier.start, bezier.end):
            assert 10 <= p.real <= 490 and 10 <= p.imag <= 390
        angle = np.degrees(np.angle(bezier.end - bezier.start))
        assert abs(angle) <= 6.01
    marker = number_marker(bezier, 20, 500, 400)
    assert 0 < marker["x"] < 500 and 0 < marker["y"] < 400

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


def test_short_label_sampling_follows_weights():
    from cartosynth.layout import random_short_label
    random.seed(0)
    draws = [random_short_label({"tokens": {"W": 3, "Gr": 1}}) for _ in range(4000)]
    assert 0.7 < draws.count("W") / len(draws) < 0.8


def test_keep_case_never_changes_short_tokens():
    random.seed(0)
    lower_only = {"family": "lower", "size": [10, 20], "letters": True, "digits": False,
                  "uppercase": False, "lowercase": True, "fallback": False}
    styles = STYLES + [lower_only]
    for token in ["W", "Gr", "n.", "Wh.", "IM"]:
        for _ in range(50):
            style, text = choose_style(token, styles, keep_case=True)
            assert text == token, (token, style["family"])


def test_label_kind_shares():
    from cartosynth.layout import label_kind
    random.seed(0)
    cfg = load_config(overrides={"numbers": {"share": 0.4},
                                 "short_labels": {"share": 0.12, "tokens": {"W": 1}}})
    kinds = [label_kind(cfg) for _ in range(10000)]
    assert abs(kinds.count("number") / 10000 - 0.40) < 0.02
    assert abs(kinds.count("short") / 10000 - 0.12) < 0.02


def test_short_label_config_is_validated():
    import pytest
    with pytest.raises(ValueError, match="quoted strings"):
        load_config(overrides={"short_labels": {"share": 0.1, "tokens": {False: 1}}})   # YAML: unquoted No
    with pytest.raises(ValueError, match="must not exceed 1"):
        load_config(overrides={"numbers": {"share": 0.9}, "short_labels": {"share": 0.2, "tokens": {"W": 1}},
                               "fonts": {"styles": STYLES}})
    with pytest.raises(ValueError, match="tokens is empty"):
        load_config(overrides={"short_labels": {"share": 0.1}})


def test_unencodable_short_token_is_rejected():
    import pytest
    from cartosynth.words import check_short_tokens
    with pytest.raises(ValueError, match="not encodable"):
        check_short_tokens({"share": 0.1, "tokens": {"Č": 1}}, Vocabulary(VOC148))

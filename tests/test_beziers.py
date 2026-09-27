import numpy as np

from cartosynth.beziers import fit_cubic_bezier, runs_forward


def letter(x, y, w=20, h=30, dx=0.0):
    # oriented letter box: ll/lr on the upper edge, ul/ur on the lower edge (as produced by beziers.py)
    return {"letter": "x", "ll": (x, y), "lr": (x + w + dx, y), "ul": (x + w, y + h), "ur": (x, y + h)}


def check_order(fit):
    for word in fit.values():
        upper, lower = np.array(word["upper_bezier_points"]), np.array(word["lower_bezier_points"])
        assert runs_forward(word["upper_bezier_points"], upper[0], upper[-1])
        assert runs_forward(word["lower_bezier_points"], lower[0], lower[-1])


def test_two_overlapping_letters_do_not_loop():
    # second letter starts left of where the first ends (tight curve): used to produce a loop
    fit = fit_cubic_bezier([[letter(0, 0, dx=15), letter(10, 2)]])
    check_order(fit)
    bbox = list(fit.values())[0]["bbox"]
    assert bbox[2] == 35 and bbox[3] == 32   # bbox covers all corners of both letters (x 0..35, y 0..32)


def test_normal_word_is_fitted():
    fit = fit_cubic_bezier([[letter(i * 25, 0) for i in range(6)]])
    check_order(fit)


def test_short_word_edges_follow_the_baseline():
    # "n." on a horizontal baseline: tall first letter, tiny second letter (y grows downwards)
    baseline = [(0, 30), (10, 30), (20, 30), (30, 30)]
    n = {"letter": "n", "ll": (0, 0), "lr": (15, 0), "ul": (15, 30), "ur": (0, 30), "bezier_ref": baseline}
    dot = {"letter": ".", "ll": (18, 25), "lr": (22, 25), "ul": (22, 30), "ur": (18, 30), "bezier_ref": baseline}
    word = list(fit_cubic_bezier([[n, dot]]).values())[0]
    upper, lower = np.array(word["upper_bezier_points"]), np.array(word["lower_bezier_points"])
    assert np.allclose(upper[:, 1], 0) and np.allclose(lower[:, 1], 30)   # parallel to the baseline
    assert upper[0, 0] == 0 and upper[-1, 0] == 22                         # spans both letters

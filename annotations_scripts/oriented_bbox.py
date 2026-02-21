import numpy as np
from scipy.optimize import minimize_scalar

def oriented_bbox_from_path(input_bezier, input_center_point, path_object, samples_per_segment=20):
    """
    Computes a tight oriented bounding box of a glyph path,
    aligned with the Bézier tangent at the closest point.

    Returns:
        ul, ur, lr, ll (plain Python floats)
    """

    # -----------------------------
    # Bézier setup
    # -----------------------------

    P0, P1, P2, P3 = [np.array(p, dtype=float) for p in input_bezier]
    input_center_point = np.array(input_center_point, dtype=float)

    def bezier(t):
        return (
            (1 - t) ** 3 * P0
            + 3 * (1 - t) ** 2 * t * P1
            + 3 * (1 - t) * t ** 2 * P2
            + t ** 3 * P3
        )

    def bezier_derivative(t):
        return (
            3 * (1 - t) ** 2 * (P1 - P0)
            + 6 * (1 - t) * t * (P2 - P1)
            + 3 * t ** 2 * (P3 - P2)
        )

    def distance_squared(t):
        d = bezier(t) - input_center_point
        return d[0] ** 2 + d[1] ** 2

    # -----------------------------
    # Closest point on Bézier
    # -----------------------------

    res = minimize_scalar(distance_squared, bounds=(0, 1), method="bounded")
    t_closest = res.x
    center = bezier(t_closest)

    # -----------------------------
    # Tangent / normal
    # -----------------------------

    tangent = bezier_derivative(t_closest)
    norm = np.linalg.norm(tangent)
    if norm == 0:
        raise ValueError("Degenerate Bézier tangent")

    t_hat = tangent / norm
    n_hat = np.array([-t_hat[1], t_hat[0]])

    # -----------------------------
    # Sample glyph outline
    # -----------------------------

    points = []

    for segment in path_object:
        for i in range(samples_per_segment):
            t = i / (samples_per_segment - 1)
            p = segment.point(t)
            points.append([p.real, p.imag])

    points = np.array(points, dtype=float)

    # -----------------------------
    # Project into local frame
    # -----------------------------

    local_x = (points - center) @ t_hat
    local_y = (points - center) @ n_hat

    min_x, max_x = local_x.min(), local_x.max()
    min_y, max_y = local_y.min(), local_y.max()

    # -----------------------------
    # Build OBB corners
    # -----------------------------

    ul = center + min_x * t_hat + max_y * n_hat
    ur = center + max_x * t_hat + max_y * n_hat
    lr = center + max_x * t_hat + min_y * n_hat
    ll = center + min_x * t_hat + min_y * n_hat

    return {
        "ul": (float(ul[0]), float(ul[1])),
        "ur": (float(ur[0]), float(ur[1])),
        "lr": (float(lr[0]), float(lr[1])),
        "ll": (float(ll[0]), float(ll[1])),
    }

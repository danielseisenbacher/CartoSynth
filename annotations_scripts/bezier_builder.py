import os
import uuid
from svgpathtools import svg2paths, wsvg, Path, Line, CubicBezier, parse_path
from shapely.geometry import MultiPoint
import subprocess
import xml.etree.ElementTree as ET
import numpy as np
from scipy.special import comb as n_over_k
from scipy.optimize import minimize_scalar


svg_with_glyphs_dir = "/workspaces/SynthMap/synth_maps/svg_maps_with_glyphs"
svg_with_glyph_paths_dir = "/workspaces/SynthMap/synth_maps/svg_maps_with_glyph_paths"
svg_annotated_dir ="/workspaces/SynthMap/annotations/annotation_visualized"

def check_dirs() -> None:
    """
    Checks that all dirs exist.
    """

    for dir in [svg_annotated_dir, svg_with_glyph_paths_dir, svg_with_glyphs_dir]:
        os.makedirs(dir, exist_ok=True)


def glyphs_to_paths(svg_with_glyphs: str) -> str:
    """
    Runs inkscape subprocess to generate paths from text font.
    :param svg_with_glyphs: input file
    :return: svg_maps_with_glyph_paths: path to svg with glyphs as paths
    """
    svg_with_glyph_paths = os.path.join(svg_with_glyph_paths_dir, os.path.basename(svg_with_glyphs))  # result path location

    subprocess.call(
        f'inkscape {svg_with_glyphs} '
        f'--actions="export-text-to-path;'
        f'export-plain-svg;'
        f'export-filename:{svg_with_glyph_paths};'
        f'export-do"',
        shell=True
    )
    return svg_with_glyph_paths


def match_text_to_path_id(svg_with_glyph_paths: str, glyph_to_path_reference:dict) -> list:
    """
    Gets the text from a given svg and creates a relation between letter, word and path_id

    :return: text_relation: text a list of words, letters
    """
    # Parse SVG
    tree = ET.parse(svg_with_glyph_paths)
    root = tree.getroot()

    svg_ns = '{http://www.w3.org/2000/svg}'

    path_reference = {}
    for path_xml in root.iter(f'{svg_ns}path'):

        if not "bezier" in path_xml.get('id'):
            continue

        path = parse_path(path_xml.get('d'))
        segment = path[0]   # First (and only) segment
        bezier_points = [
            (segment.start.real, segment.start.imag),
            (segment.control1.real, segment.control1.imag),
            (segment.control2.real, segment.control2.imag),
            (segment.end.real, segment.end.imag)
        ]
        path_reference[path_xml.get('id')] = bezier_points


    # Build a mapping: path_id -> aria-label of parent group
    text_relation = []
    for g in root.iter(f'{svg_ns}g'):
        label = g.get('aria-label', None)
        if label is None:
            continue

        path_nrs = []
        for count, path_elem in enumerate(g.iter(f'{svg_ns}path')):
            path_id = path_elem.get('id', '<no-id>')
            path_nrs.append(path_id)


        # treat each word separately, to be able to create fitting bbox later
        text_part = []
        count = 0
        for word in label.split(" "):
            for letter in word:
                text_part.append({"path_id": path_nrs[count], "letter": letter, "bezier_ref": glyph_to_path_reference[path_nrs[count]]})
                count += 1
            text_relation.append(text_part)
            text_part = []

    return text_relation


def glyph_bezier_reference(svg_with_glyph_paths: str) -> dict:
    # Parse SVG
    tree = ET.parse(svg_with_glyph_paths)
    root = tree.getroot()
    existing_beziers = {}
    for elem in root:
        for group in elem:
            if "bezier" in group.attrib["id"]:
                bezier_id = group.attrib["id"]
                path_string = group.attrib["d"]

                path = parse_path(path_string)
                segment = path[0]  # First (and only) segment
                bezier_points = [
                    (segment.start.real, segment.start.imag),
                    (segment.control1.real, segment.control1.imag),
                    (segment.control2.real, segment.control2.imag),
                    (segment.end.real, segment.end.imag)
                ]
                existing_beziers[bezier_id] = bezier_points

    glyph_bezier_reference = {}
    for elem in root:
        for group in elem:
            if not "data-bezier-ref" in group.keys():
                continue
            ref_bezier_id = group.attrib["data-bezier-ref"]

            for subgroup in group:
                for path in subgroup:
                    glyph_bezier_reference[path.attrib["id"]] = existing_beziers[ref_bezier_id]

    return glyph_bezier_reference


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


def get_letter_rotated_bbox(svg_with_glyph_paths: str, text_relation: list) -> list:
    """
    Use shapely to get the rotated bounding box for each letter, and save it in the text_relation

    :param svg_with_glyph_paths: path to the svg with glyphs as paths
    :param text_relation: information about words, letters, path_ids
    :return: text_relation, same as before but now with bboxes for each letter
    """

    # Get all glyph paths
    paths, attributes = svg2paths(svg_with_glyph_paths)

    for path, attr in zip(paths, attributes):
        path_id = attr.get("id", "<no-id>")


        if "bezier" in path_id:
            # all bezier paths get ignored, these are created synthetically and do not represent a glyph path
            continue

        for count, word in enumerate(text_relation):

            path_ids = [letter["path_id"] for letter in word]
            if path_id not in path_ids:
                continue

            xmin, xmax, ymin, ymax = [float(x) for x in path.bbox()]        # dont use numpy
            idx_path_id = path_ids.index(path_id)

            text_relation[count][idx_path_id]["bbox"] = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
            text_relation[count][idx_path_id]["bbox_center"] = ((xmin + xmax)/2, (ymin + ymax)/2)

            result_dict = oriented_bbox_from_path(
                input_bezier = text_relation[count][idx_path_id]["bezier_ref"],
                input_center_point = text_relation[count][idx_path_id]["bbox_center"],
                path_object = path
            )

            text_relation[count][idx_path_id]["ul"] = result_dict["ul"]
            text_relation[count][idx_path_id]["ur"] = result_dict["ur"]
            text_relation[count][idx_path_id]["lr"] = result_dict["lr"]
            text_relation[count][idx_path_id]["ll"] = result_dict["ll"]
            text_relation[count][idx_path_id]["letter_bbox"] = [result_dict["ul"], result_dict["ur"], result_dict["lr"], result_dict["ll"]]

    return text_relation




def draw_polygon_outline(paths: list, attributes: list, text_relation_dict: dict):
    """
    Draws the polygon outlines as paths to indicate the limit of words
    :return:
    """
    for word_uuid, value in text_relation_dict.items():
        word = value["letters"]
        line = []
        # Top edge left to right
        for letter in word:
            line.append(letter["ul"])
            line.append(letter["ur"])
        # Bottom edge right to left
        for letter in reversed(word):
            line.append(letter["lr"])
            line.append(letter["ll"])
        # Close
        line.append(word[0]["ul"])

        line_path = Path()
        for i in range(len(line) - 1):
            start = line[i]
            end = line[i + 1]
            line_path.append(Line(
                start=complex(start[0], start[1]),
                end=complex(end[0], end[1])
            ))

        paths.append(line_path)
        attributes.append({
            "id": f"word_bbox_{word_uuid}",
            "stroke": "red",
            "fill": "none",
            "stroke-width": "0.5"
        })

    return paths, attributes


def draw_letter_bbox(paths: list, attributes: list, text_relation_dict: dict):
    for word_uuid, value in text_relation_dict.items():
        word = value["letters"]
        for letter in word:


            corners = [letter["ul"], letter["ur"], letter["lr"], letter["ll"], letter["ul"]]

            bbox_path = Path()
            for i in range(len(corners) - 1):
                start = corners[i]
                end = corners[i + 1]

                bbox_path.append(
                    Line(
                        start=complex(start[0], start[1]),
                        end=complex(end[0], end[1])
                    )
                )
            paths.append(bbox_path)
            attributes.append({
                "id": f"word_bbox_{word_uuid}",
                "stroke": "orange",
                "fill": "none",
                "stroke-width": "0.2"
            })


def fit_cubic_bezier(text_relation: list) -> dict:
    """
    Fit a cubic Bezier curve to a set of points using least squares.

    Args:
        points: numpy array of shape (n, 2) or list of [x, y] coordinates

    Returns:
        control_points: numpy array of shape (4, 2) containing the 4 control points
                       [P0, P1, P2, P3] of the cubic Bezier curve
    """

    # Bernstein basis polynomial
    Mtk = lambda n, t, k: t ** k * (1 - t) ** (n - k) * n_over_k(n, k)

    # Bernstein coefficient matrix for cubic Bezier
    BezierCoeff = lambda ts: [[Mtk(3, t, k) for k in range(4)] for t in ts]

    text_relation_dict = dict()

    for word in text_relation:

        random_word_id = str(uuid.uuid4())
        word_upper_bezier_points = []
        word_lower_bezier_points = []

        for letter in word:
            word_upper_bezier_points.append(letter["ll"])
            word_upper_bezier_points.append(letter["lr"])
            word_lower_bezier_points.append(letter["ul"])
            word_lower_bezier_points.append(letter["ur"])

        if len(word_upper_bezier_points) < 4:
            start = word_upper_bezier_points[0]
            end = word_upper_bezier_points[-1] if len(word_upper_bezier_points) > 1 else start

            # Linear interpolation to create 4 control points
            word_upper_bezier_points = [
                start,
                (start[0] + (end[0] - start[0]) / 3, start[1] + (end[1] - start[1]) / 3),
                (start[0] + 2 * (end[0] - start[0]) / 3, start[1] + 2 * (end[1] - start[1]) / 3),
                end
            ]

        if len(word_lower_bezier_points) < 4:
            start = word_lower_bezier_points[0]
            end = word_lower_bezier_points[-1] if len(word_lower_bezier_points) > 1 else start

            # Linear interpolation to create 4 control points
            word_lower_bezier_points = [
                start,
                (start[0] + (end[0] - start[0]) / 3, start[1] + (end[1] - start[1]) / 3),
                (start[0] + 2 * (end[0] - start[0]) / 3, start[1] + 2 * (end[1] - start[1]) / 3),
                end
            ]

        # build bounding box
        all_points = [*word_upper_bezier_points, *word_lower_bezier_points]
        x_min = min([i[0] for i in all_points])
        y_min = min([i[1] for i in all_points])
        x_max = max([i[0] for i in all_points])
        y_max = max([i[1] for i in all_points])
        delta_x = x_max - x_min
        delta_y = y_max - y_min
        bbox = [round(x_min, 1), round(y_min, 1), round(delta_x, 1), round(delta_y, 1)]

        text_relation_dict[random_word_id] = {
            "upper_bezier_points": word_upper_bezier_points,
            "lower_bezier_points": word_lower_bezier_points,
            "bbox": bbox,
            "letters": word
        }

        for upper_lower_keyword in ["upper_bezier_points", "lower_bezier_points"]:
            points = np.array(text_relation_dict[random_word_id][upper_lower_keyword])
            x = points[:, 0]
            y = points[:, 1]

            # Calculate arc-length parameterization
            dy = y[1:] - y[:-1]
            dx = x[1:] - x[:-1]
            dt = (dx ** 2 + dy ** 2) ** 0.5
            t = dt / dt.sum()
            t = np.hstack(([0], t))
            t = t.cumsum()

            # Stack coordinates
            data = np.column_stack((x, y))

            # Compute pseudoinverse and solve
            Pseudoinverse = np.linalg.pinv(BezierCoeff(t))
            control_points = Pseudoinverse.dot(data)

            # Convert to list of tuples of floats
            text_relation_dict[random_word_id][upper_lower_keyword] = [
                (float(control_points[0, 0]), float(control_points[0, 1])),
                (float(control_points[1, 0]), float(control_points[1, 1])),
                (float(control_points[2, 0]), float(control_points[2, 1])),
                (float(control_points[3, 0]), float(control_points[3, 1]))
            ]

    return text_relation_dict


def draw_upper_and_lower_bezier(paths, attributes, text_relation_dict):
    """
    Draws the upper and lower Bezier curves for each word
    :return:
    """
    for word_uuid, value in text_relation_dict.items():
        upper_control_points = value["upper_bezier_points"]
        lower_control_points = value["lower_bezier_points"]

        # Draw upper Bezier curve
        upper_bezier = CubicBezier(
            start=complex(upper_control_points[0][0], upper_control_points[0][1]),
            control1=complex(upper_control_points[1][0], upper_control_points[1][1]),
            control2=complex(upper_control_points[2][0], upper_control_points[2][1]),
            end=complex(upper_control_points[3][0], upper_control_points[3][1])
        )

        paths.append(Path(upper_bezier))
        attributes.append({
            "id": f"upper_bezier_{word_uuid}",
            "stroke": "blue",
            "fill": "none",
            "stroke-width": "0.5"
        })

        # Draw lower Bezier curve
        lower_bezier = CubicBezier(
            start=complex(lower_control_points[0][0], lower_control_points[0][1]),
            control1=complex(lower_control_points[1][0], lower_control_points[1][1]),
            control2=complex(lower_control_points[2][0], lower_control_points[2][1]),
            end=complex(lower_control_points[3][0], lower_control_points[3][1])
        )

        paths.append(Path(lower_bezier))
        attributes.append({
            "id": f"lower_bezier_{word_uuid}",
            "stroke": "green",
            "fill": "none",
            "stroke-width": "0.5"
        })

    return paths, attributes


def draw_bbox_rectangles(paths: list, attributes: list, text_relation_dict: dict):
    """
    Draws rectangular bounding boxes using the `bbox` key:
    bbox = [x_min, y_min, width, height]
    """
    for word_uuid, value in text_relation_dict.items():
        if "bbox" not in value:
            continue

        x, y, w, h = value["bbox"]

        # Rectangle corners
        ul = (x, y)
        ur = (x + w, y)
        lr = (x + w, y + h)
        ll = (x, y + h)

        rect_path = Path(
            Line(start=complex(*ul), end=complex(*ur)),
            Line(start=complex(*ur), end=complex(*lr)),
            Line(start=complex(*lr), end=complex(*ll)),
            Line(start=complex(*ll), end=complex(*ul)),
        )

        paths.append(rect_path)
        attributes.append({
            "id": f"word_bbox_rect_{word_uuid}",
            "stroke": "blue",
            "fill": "none",
            "stroke-width": "0.5",
        })

    return paths, attributes


def save_svg(svg_with_glyph_paths: str, text_relation_dict: dict, draw_and_save_result=True):
    # Draw bounding box outlines per word
    paths, attributes = svg2paths(svg_with_glyph_paths)

    draw_polygon_outline(paths, attributes, text_relation_dict)

    draw_upper_and_lower_bezier(paths, attributes, text_relation_dict)

    draw_bbox_rectangles(paths, attributes, text_relation_dict)

    draw_letter_bbox(paths, attributes, text_relation_dict)

    # save the annotated file
    svg_annotated_file = os.path.join(svg_annotated_dir, os.path.basename(svg_with_glyph_paths))
    wsvg(paths, attributes=attributes, filename=svg_annotated_file)
    print(f"Saved annotated SVG to {svg_annotated_file}")

    return svg_annotated_file


def build_bezier() -> dict:
    check_dirs()

    if len(os.listdir(svg_with_glyphs_dir)) == 0:
        raise Exception(f"No glyph svg in found: {svg_with_glyphs_dir}")

    bezier_dict = {}

    # annotate each file in svg with glyphs dir
    for file in os.listdir(svg_with_glyphs_dir):
        if not file.endswith(".svg"):
            print(f"Ignoring {file}")

        svg_with_glyph_paths = glyphs_to_paths(os.path.join(svg_with_glyphs_dir, file))

        glyph_to_path_reference = glyph_bezier_reference(svg_with_glyph_paths)

        text_relation = match_text_to_path_id(svg_with_glyph_paths, glyph_to_path_reference)

        text_relation = get_letter_rotated_bbox(svg_with_glyph_paths, text_relation)

        text_relation_dict = fit_cubic_bezier(text_relation)

        save_svg(svg_with_glyph_paths, text_relation_dict, draw_and_save_result=True)

        bezier_dict[file] = text_relation_dict

    return bezier_dict

if __name__ == "__main__":
    bezier_dict = build_bezier()
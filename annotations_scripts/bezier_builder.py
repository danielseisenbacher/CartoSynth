import os
import uuid
from svgpathtools import svg2paths, wsvg, Path, Line, CubicBezier
from shapely.geometry import MultiPoint
import subprocess
import xml.etree.ElementTree as ET
import numpy as np
from scipy.special import comb as n_over_k


svg_with_glyphs_dir = "svg_with_glyphs"
svg_with_glyph_paths_dir ="svg_with_glyph_paths"
svg_annotated_dir ="svg_annotated"


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
    :return: svg_with_glyph_paths: path to svg with glyphs as paths
    """
    svg_with_glyph_paths = os.path.join(svg_with_glyph_paths_dir, os.path.basename(svg_with_glyphs))  # result path location

    subprocess.call(
        f'inkscape {svg_with_glyphs} --actions="export-text-to-path;export-plain-svg;export-filename:{svg_with_glyph_paths};export-do"',
        shell=True
    )
    return svg_with_glyph_paths


def match_text_to_path_id(svg_with_glyph_paths: str) -> list:
    """
    Gets the text from a given svg and creates a relation between letter, word and path_id

    :return: text_relation: text a list of words, letters
    """
    # Parse SVG
    tree = ET.parse(svg_with_glyph_paths)
    root = tree.getroot()

    # Build a mapping: path_id -> aria-label of parent group
    text_relation = []
    for g in root.iter('{http://www.w3.org/2000/svg}g'):
        label = g.get('aria-label', None)

        if label is None:
            continue

        path_nrs = []
        for count, path_elem in enumerate(g.iter('{http://www.w3.org/2000/svg}path')):
            path_id = path_elem.get('id', '<no-id>')
            path_nrs.append(path_id)


        # treat each word separately, to be able to create fitting bbox later
        text_part = []
        count = 0
        for word in label.split(" "):
            for letter in word:
                text_part.append({"path_name": path_nrs[count], "letter": letter})
                count += 1
            text_relation.append(text_part)
            text_part = []

    return text_relation


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

            path_ids = [letter["path_name"] for letter in word]
            if path_id not in path_ids:
                continue

            idx_path_id = path_ids.index(path_id)

            # Sample 50 points along the path
            num_samples = max(50, int(path.length() / 2))
            points = []
            for i in range(num_samples):
                t = i / (num_samples - 1)
                pt = path.point(t)
                points.append((pt.real, pt.imag))

            # minimum_rotated_rectangle gives the oriented bounding box
            mp = MultiPoint(points)
            rotated_rect = mp.minimum_rotated_rectangle
            coords = list(rotated_rect.exterior.coords)[:-1]

            cx = sum(x for x, y in coords) / len(coords)
            cy = sum(y for x, y in coords) / len(coords)

            text_relation[count][idx_path_id]["bbox"] = coords
            text_relation[count][idx_path_id]["center"] = (cx, cy)

    return text_relation


def get_oriented_letter_corners(text_relation: list) -> list:
    """
    Get the ul,ur,ll,lr corners and write them into the text_relation list for each letter, in reading direction.

    :param text_relation: information about words, letters, path_ids, bboxes for each letter
    :return: text_relation: information about words, letters, path_ids, bboxes, ul,ur,ll,lr corners of letters
    """

    # Build oriented ul, ur, ll, lr
    for word_idx, word in enumerate(text_relation):
        if len(word) == 1:
            word[0]["ul"] = word[0]["bbox"][0]
            word[0]["ll"] = word[0]["bbox"][1]
            word[0]["lr"] = word[0]["bbox"][2]
            word[0]["ur"] = word[0]["bbox"][3]
            continue

        for letter_idx, letter in enumerate(word):
            if letter_idx == len(word) - 1:
                start = np.array(text_relation[word_idx][letter_idx - 1]["center"])
                end = np.array(text_relation[word_idx][letter_idx]["center"])
            else:
                start = np.array(text_relation[word_idx][letter_idx]["center"])
                end = np.array(text_relation[word_idx][letter_idx + 1]["center"])

            x_axis = end - start
            x_axis = x_axis / np.linalg.norm(x_axis)
            y_axis = np.array([-x_axis[1], x_axis[0]])

            center = np.array(letter["center"])
            coords = letter["bbox"]

            # Project each corner onto local x and y axes
            projected = []
            for p in coords:
                delta = np.array(p) - center
                local_x = np.dot(delta, x_axis)
                local_y = np.dot(delta, y_axis)
                projected.append((p, local_x, local_y))

            # Classify: pick corner with best match for each role
            ul = max(projected, key=lambda c: -c[1] + c[2])   # most left + most up
            ur = max(projected, key=lambda c:  c[1] + c[2])   # most right + most up
            lr = max(projected, key=lambda c:  c[1] - c[2])   # most right + most down
            ll = max(projected, key=lambda c: -c[1] - c[2])   # most left + most down


            letter["ul"] = ul[0]
            letter["ur"] = ur[0]
            letter["lr"] = lr[0]
            letter["ll"] = ll[0]

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

        text_relation = match_text_to_path_id(svg_with_glyph_paths)

        text_relation = get_letter_rotated_bbox(svg_with_glyph_paths, text_relation)

        text_relation = get_oriented_letter_corners(text_relation)

        text_relation_dict = fit_cubic_bezier(text_relation)

        save_svg(svg_with_glyph_paths, text_relation_dict, draw_and_save_result=True)

        bezier_dict[file] = text_relation_dict

    return bezier_dict

if __name__ == "__main__":
    bezier_dict = build_bezier()

import unicodedata
import random
from math import sqrt
from random import randint, choice
import os
import numpy as np
import svgpathtools
from synth_maps_scripts import (bezier_length_test, svg_templates)
from annotations_scripts import voc148
from collections import Counter
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_random_font(bezier_word, font_config):
    try:
        contains_number = bool(re.search(r'\d', bezier_word))
        contains_letter = bool(re.search('[a-zA-Z]', bezier_word))

        possible_fonts = {x:y for x,y in font_config.items() if y["can_display_numeric"]>=contains_number and y["can_display_letters"]>=contains_letter} 
        if len(possible_fonts) == 0:
            raise Exception

        chosen_font = choice(list(font_config.keys()))

        if not possible_fonts[chosen_font]["uppercase_possible"]:
            bezier_word = bezier_word.lower()

        if not possible_fonts[chosen_font]["lowercase_possible"]:
            bezier_word = bezier_word.upper()
        
        return chosen_font, bezier_word

        
    except Exception:
        fallback_font = [x for x,y in font_config.items() if y["fallback"] is True][-1]
        print(f"Using fallback font [{fallback_font}]for word: {bezier_word}")

        return fallback_font, bezier_word


from PIL import Image

def get_map_template_files(map_templates_dir=None):
    if map_templates_dir is None:
        map_templates_dir = os.path.join(BASE_DIR, "map_templates")
    if not os.path.exists(map_templates_dir):
        return [], map_templates_dir
    files = [f for f in os.listdir(map_templates_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.svg'))]
    files.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else x)
    return files, map_templates_dir


def create_svg(font_config, how_many_svgs=10, min_bezier_on_canvas=20, max_bezier_on_canvas=40, canvas_size=None, map_templates_dir=None):
    training_data = []
    dropped_chars = Counter()
    dropped_rows = 0
    small_training_data = os.path.join(BASE_DIR, "osm", "osm_data", "small_training_data.txt")
    with open(small_training_data, "r") as f:
        for row in f:
            cleaned_row = unicodedata.normalize('NFKC', row.strip())
            len_substrings = [len(substring) for substring in cleaned_row.split(" ")]
            if min(len_substrings) < 2:
                # discard very short words
                continue
            elif max(len_substrings) > 25:
                # discard very long words
                continue

            # discard rows the 148voc dictionary cannot transcribe, so no word is rendered without a label.
            # get_random_font may upper-/lowercase the word, so all variants must be encodable (ß -> SS is fine).
            variants = (cleaned_row, cleaned_row.upper(), cleaned_row.lower())
            if not all(voc148.is_encodable(v) for v in variants):
                dropped_rows += 1
                dropped_chars.update(set().union(*(voc148.unencodable_chars(v) for v in variants)))
                continue

            if cleaned_row != "":
                training_data.append(cleaned_row)

    print(f"Loaded {len(training_data)} words, dropped {dropped_rows} rows not encodable in 148voc: {dict(dropped_chars)}")

    template_files, map_templates_dir = get_map_template_files(map_templates_dir)

    counter = 0
    for svg_nr in range(how_many_svgs):
        # Determine canvas dimensions for this SVG
        template_file = ""
        if canvas_size is not None:
            if isinstance(canvas_size, (tuple, list)):
                canvas_width, canvas_height = canvas_size
            else:
                canvas_width = canvas_height = canvas_size
            if template_files:
                template_file = template_files[svg_nr % len(template_files)]
        elif template_files:
            template_file = template_files[svg_nr % len(template_files)]
            template_path = os.path.join(map_templates_dir, template_file)
            with Image.open(template_path) as im:
                canvas_width, canvas_height = im.size
        else:
            canvas_width, canvas_height = 1000, 1000

        print('='*50)
        print(f'Building svg {svg_nr} [size: {canvas_width}x{canvas_height}, template: {template_file}]..')
        print('-' * 50)
        random_number = randint(min_bezier_on_canvas, max_bezier_on_canvas)

        proposed_paths = svgpathtools.Path()
        proposed_font_config = []
        proposed_paths_buffers = svgpathtools.Path()
        words = []

        for elem in range(random_number):
            bezier_word = training_data[counter]
            random_font, modified_bezier_word = get_random_font(bezier_word, font_config)
            training_data[counter] = modified_bezier_word
            bezier_word = training_data[counter]

            random_font_size = randint(
                font_config[random_font]['font_size_range'][0],
                font_config[random_font]['font_size_range'][-1]
            )

            print(f'Bezier {elem+1}/{random_number}: {bezier_word} [font: {random_font}, font_size: {random_font_size}]')

            bezier_len_required = bezier_length_test.test_word_length(
                bezier_word, random_font, random_font_size, canvas_width, canvas_height
            )

            while not bezier_len_required:
                # sometimes the word is too long for the canvas, in this case we need to reduce the word length
                if len(bezier_word) <= 2:
                    break
                training_data[counter] = bezier_word[:-1].strip()
                bezier_word = training_data[counter]
                bezier_len_required = bezier_length_test.test_word_length(
                    bezier_word, random_font, random_font_size, canvas_width, canvas_height
                )

            if not bezier_len_required:
                counter = (counter + 1) % len(training_data)
                continue

            new_path, proposed_paths_buffers = propose_a_path(
                bezier_len_required,
                existing_paths_buffers=proposed_paths_buffers,
                canvas_width=canvas_width,
                canvas_height=canvas_height
            )

            if new_path is None:
                print(f"↺ Could not place bezier {elem+1} on canvas, skipping...")
                counter = (counter + 1) % len(training_data)
                continue

            proposed_paths.append(new_path)
            proposed_font_config.append({"font": random_font, "font_size": random_font_size})
            words.append(bezier_word)

            counter = (counter + 1) % len(training_data)

        save_to_svg(
            beziers=proposed_paths,
            words=words,
            file_name=f"{svg_nr}.svg",
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            template_name=template_file,
            proposed_font_config=proposed_font_config
        )

        print()
        print('=' * 50)
        print("\n\n")


def propose_a_path(bezier_len_required, existing_paths_buffers, max_curvature=0.5, canvas_width=1000, canvas_height=None, canvas_size=None, canvas_buffer=10):
    if canvas_size is not None:
        if isinstance(canvas_size, (tuple, list)):
            canvas_width, canvas_height = canvas_size
        else:
            canvas_width = canvas_height = canvas_size
    elif canvas_height is None:
        if isinstance(canvas_width, (tuple, list)):
            canvas_width, canvas_height = canvas_width
        else:
            canvas_height = canvas_width

    b = canvas_buffer
    bx = canvas_width - canvas_buffer
    by = canvas_height - canvas_buffer
    border_buffer = svgpathtools.Path(
        svgpathtools.path.Line(complex(b, b), complex(bx, b)),
        svgpathtools.path.Line(complex(bx, b), complex(bx, by)),
        svgpathtools.path.Line(complex(bx, by), complex(b, by)),
        svgpathtools.path.Line(complex(b, by), complex(b, b))
    )

    line_outside_count = 0
    line_touches_other_bezier_count = 0
    total_attempts = 0
    while True:
        total_attempts += 1
        if total_attempts > 150:
            print(f"No valid placement found after {total_attempts} attempts")
            return None, existing_paths_buffers

        starting_point = (
            random.randint(canvas_buffer, canvas_width - canvas_buffer),
            random.randint(canvas_buffer, canvas_height - canvas_buffer)
        )

        # skewed towards horizontal text
        x_length = random.betavariate(3, 1) * bezier_len_required
        y_length = sqrt(bezier_len_required ** 2 - x_length ** 2) * random.choice([1, -1])
        ending_point = (starting_point[0] + x_length, starting_point[1] + y_length)
        starting_point = complex(starting_point[0], starting_point[1])
        ending_point = complex(ending_point[0], ending_point[1])

        new_path = svgpathtools.path.Line(starting_point, ending_point)

        if border_buffer.intersect(new_path, justonemode=True):
            print("↺ line outside of canvas - ", end="")
            line_outside_count += 1
            continue

        if existing_paths_buffers.intersect(new_path, justonemode=True):
            print("↺ line touches other bezier - ", end="")
            line_touches_other_bezier_count += 1
            continue

        # Bezier loop
        bezier_placed = False
        for _ in range(50):
            random_x_offset = random.randint(-int(bezier_len_required), int(bezier_len_required))
            random_y_offset = random.randint(-int(bezier_len_required), int(bezier_len_required))
            control_point_1 = complex(starting_point.real + random_x_offset, starting_point.imag + random_y_offset)

            random_x_offset = random.randint(-canvas_buffer, canvas_buffer)
            random_y_offset = random.randint(-canvas_buffer, canvas_buffer)
            control_point_2 = complex(ending_point.real + random_x_offset, ending_point.imag + random_y_offset)

            new_bezier = svgpathtools.path.CubicBezier(
                start=starting_point,
                control1=control_point_1,
                control2=control_point_2,
                end=ending_point,
            )

            if border_buffer.intersect(new_bezier, justonemode=True):
                print("↺ bezier outside of canvas - ", end="")
                continue

            ts = np.linspace(0, 1, 1000)

            def safe_curvature(t):
                try:
                    return abs(new_bezier.curvature(t))
                except (ValueError, ZeroDivisionError):
                    return 0.0

            curvatures = [safe_curvature(t) for t in ts]

            if max(curvatures) > max_curvature:
                print("↺ curvature of bezier too high - ", end="")
                continue

            if existing_paths_buffers.intersect(new_bezier, justonemode=True):
                print("↺ bezier touches other bezier - ", end="")
                continue

            buffer_center_points = new_bezier.points(np.linspace(0, 1, 30))

            for cp in buffer_center_points:
                existing_paths_buffers.append(
                    svgpathtools.path.Arc(
                        start=complex(cp.real, cp.imag - canvas_buffer * 2),
                        radius=complex(canvas_buffer * 2, canvas_buffer * 2),
                        rotation=0,
                        large_arc=False,
                        sweep=True,
                        end=complex(cp.real, cp.imag + canvas_buffer * 2)
                    )
                )

                existing_paths_buffers.append(
                    svgpathtools.path.Arc(
                        start=complex(cp.real, cp.imag + canvas_buffer * 2),
                        radius=complex(canvas_buffer * 2, canvas_buffer * 2),
                        rotation=0,
                        large_arc=False,
                        sweep=True,
                        end=complex(cp.real, cp.imag - canvas_buffer * 2)
                    )
                )

            print("✓ done")
            return new_bezier, existing_paths_buffers



def save_to_svg(beziers, words, file_name, buffers=None, border=None, special=None, canvas_size=None, canvas_width=1000, canvas_height=None, template_name="", proposed_font_config=None):
    if canvas_size is not None:
        if isinstance(canvas_size, (tuple, list)):
            canvas_width, canvas_height = canvas_size
        else:
            canvas_width = canvas_height = canvas_size
    elif canvas_height is None:
        if isinstance(canvas_width, (tuple, list)):
            canvas_width, canvas_height = canvas_width
        else:
            canvas_height = canvas_width

    svg_template = svg_templates.get_svg_template(canvas_width, canvas_height, template_name=template_name)

    path_str = ''
    path_beziers = [svgpathtools.Path(bezier) for bezier in beziers]
    for idx, (path, word, font_config) in enumerate(zip(path_beziers, words, proposed_font_config)):

        # Add the bezier path to the svg string
        path_str += svg_templates.get_bezier_template(
            bezier_reference_id=f"bezier{idx}",
            geometry_string=path.d()
        )

        # Add the text to the svg string
        path_str += svg_templates.get_word_template(
            bezier_reference_id=f"bezier{idx}",
            bezier_text=word,
            font_family=font_config["font"],
            font_size=font_config["font_size"]
        )

    if buffers:
        path_str += f'<path d="{buffers.d()}" fill="none" stroke="#000000" stroke-width="0.1" />\n'

    if special:
        path_str += f'<path d="{svgpathtools.Path(special).d()}" fill="none" stroke="#aa0000" stroke-width="1.5" />\n'

    if border:
        path_str += f'<path d="{border.d()}" fill="none" stroke="#cc0000" stroke-width="0.5" />\n'

    svg_template = svg_template.replace("BEZIER_LIST", path_str)

    output_dir = os.path.join(BASE_DIR, "synth_maps", "svg_maps_with_glyphs")
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, file_name), "w") as f:
        f.write(svg_template)



def run_synth_map_maker(font_config, how_many_svgs=10, min_bezier_on_canvas=20, max_bezier_on_canvas=40, canvas_size=None, map_templates_dir=None):
    create_svg(
        font_config, 
        how_many_svgs=how_many_svgs, 
        min_bezier_on_canvas=min_bezier_on_canvas, 
        max_bezier_on_canvas=max_bezier_on_canvas,
        canvas_size=canvas_size,
        map_templates_dir=map_templates_dir
    )

import random
from math import sqrt
from random import randint, choice
import os
import numpy as np
import svgpathtools
from synth_maps_scripts import (bezier_length_test, svg_templates)




def create_svg(font_config, how_many_svgs=10, min_bezier_on_canvas=20, max_bezier_on_canvas=40):
    training_data = []
    small_training_data = "/workspaces/SynthMap/osm/osm_data/small_training_data.txt"
    with open(small_training_data, "r") as f:
        for row in f:
            training_data.append(row.strip())


    counter = 0
    for svg_nr in range(how_many_svgs):
        print('='*50)
        print(f'Building svg {svg_nr}..')
        print('-' * 50)
        random_number = randint(min_bezier_on_canvas,max_bezier_on_canvas)

        proposed_paths = svgpathtools.Path()
        proposed_paths_buffers = svgpathtools.Path()
        words = []

        for elem in range(random_number):
            bezier_word = training_data[counter]
            print(f'Bezier {elem+1}/{random_number}: {bezier_word}')

            random_font = choice(list(font_config.keys()))
            random_font_size = randint(
                font_config[random_font]['font_size_range'][0],
                font_config[random_font]['font_size_range'][-1]
            )
            bezier_len_required = bezier_length_test.test_word_length(bezier_word, random_font, random_font_size)

            new_path, proposed_paths_buffers = propose_a_path(
                bezier_len_required,
                existing_paths_buffers=proposed_paths_buffers
            )

            proposed_paths.append(new_path)
            words.append(bezier_word)

            counter += 1
            pass

        save_to_svg(
            beziers=proposed_paths,
            #buffers=proposed_paths_buffers,
            words=words,
            file_name=f"{svg_nr}.svg"
        )

        print()
        print('=' * 50)
        print("\n\n")



def propose_a_path(bezier_len_required, existing_paths_buffers, max_curvature=0.5, canvas_size=500, canvas_buffer=10):
    b = canvas_buffer
    s = canvas_size - canvas_buffer
    border_buffer = svgpathtools.Path(
        svgpathtools.path.Line(complex(b,b), complex(s,b)),
        svgpathtools.path.Line(complex(s,b), complex(s,s)),
        svgpathtools.path.Line(complex(s,s), complex(b,s)),
        svgpathtools.path.Line(complex(b,s), complex(b,b))
    )

    while True:
        starting_point = (
            random.randint(canvas_buffer, canvas_size - canvas_buffer),
            random.randint(canvas_buffer, canvas_size - canvas_buffer)
        )

        # skewed towards horizontal text
        x_length = random.betavariate(3, 1) * bezier_len_required
        y_length = sqrt(bezier_len_required ** 2 - x_length ** 2) * random.choice([1, -1])      # make it go up and down
        ending_point = (starting_point[0] + x_length, starting_point[1] + y_length)
        starting_point = complex(starting_point[0], starting_point[1])
        ending_point = complex(ending_point[0], ending_point[1])

        new_path = svgpathtools.path.Line(starting_point, ending_point)

        if border_buffer.intersect(new_path, justonemode=True):
            print("↺ line outside of canvas - ", end="")
            continue

        # fix: check combined buffer, not list
        if existing_paths_buffers.intersect(new_path, justonemode=True):
            print("↺ line touches other bezier - ", end="")
            continue

        # Bezier loop
        while True:
            random_x_offset = random.randint(-int(bezier_len_required), int(bezier_len_required))
            random_y_offset = random.randint(-int(bezier_len_required), int(bezier_len_required))
            control_point_1 = complex(starting_point.real + random_x_offset, starting_point.imag + random_y_offset)

            random_x_offset = random.randint(-canvas_buffer, canvas_buffer)
            random_y_offset = random.randint(-canvas_buffer, canvas_buffer)
            control_point_2 = complex(ending_point.real + random_x_offset, ending_point.imag  + random_y_offset)

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
            curvatures = [abs(new_bezier.curvature(t)) for t in ts]

            if max(curvatures) > max_curvature:
                print("↺ curvature of bezier too high - ", end="")
                continue

            # fix: use combined_buffer, not list
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



def save_to_svg(beziers, words, file_name, buffers=None, border=None, special=None):
    svg_template = svg_templates.get_svg_template()

    path_str = ''
    path_beziers = [svgpathtools.Path(bezier) for bezier in beziers]
    for idx, (path, word) in enumerate(zip(path_beziers, words)):

        # Add the bezier path to the svg string
        path_str += svg_templates.get_bezier_template(
            bezier_reference_id=f"bezier{idx}",
            geometry_string=path.d()
        )

        # Add the text to the svg string
        path_str += svg_templates.get_word_template(
            bezier_reference_id=f"bezier{idx}",
            bezier_text=word,
            font_family="font6",
            font_size="7"
        )

    if buffers:
        path_str += f'<path d="{buffers.d()}" fill="none" stroke="#000000" stroke-width="0.1" />\n'

    if special:
        path_str += f'<path d="{svgpathtools.Path(special).d()}" fill="none" stroke="#aa0000" stroke-width="1.5" />\n'

    if border:
        path_str += f'<path d="{border.d()}" fill="none" stroke="#cc0000" stroke-width="0.5" />\n'

    svg_template = svg_template.replace("BEZIER_LIST", path_str)

    with open(os.path.join("/workspaces/SynthMap/synth_maps/svg_maps_with_glyphs", file_name), "w") as f:
        f.write(svg_template)



def run_synth_map_maker():
    font_config = {"font6": {"font_size_range": [7]}}
    create_svg(font_config, how_many_svgs=10, min_bezier_on_canvas=20, max_bezier_on_canvas=40)



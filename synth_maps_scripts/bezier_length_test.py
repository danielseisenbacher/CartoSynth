import subprocess
import os
import svgpathtools

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def glyphs_to_paths(svg_with_glyphs: str) -> str:
    """
    Runs inkscape subprocess to generate paths from text font.
    :param svg_with_glyphs: input file
    :return: svg_maps_with_glyph_paths: path to svg with glyphs as paths
    """

    subprocess.call(
        f'inkscape {svg_with_glyphs} '
        f'--actions="export-text-to-path;'
        f'export-plain-svg;'
        f'export-filename:{svg_with_glyphs};'
        f'export-do"',
        shell=True
    )
    return svg_with_glyphs



def test_word_length(bezier_word, random_font, random_font_size, canvas_width=1000, canvas_height=None):
    if not bezier_word or len(bezier_word.strip()) == 0:
        return False

    if canvas_height is None:
        if isinstance(canvas_width, (tuple, list)):
            canvas_width, canvas_height = canvas_width
        else:
            canvas_height = canvas_width

    # Use a generous reference line so measurement never clips or wraps regardless of canvas size
    min_x_of_reference_line = 50
    len_of_reference_line = 2000
    max_x_of_reference_line = min_x_of_reference_line + len_of_reference_line

    straight_line_test = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <svg
                width="2200"
                height="500"
                viewBox="0 0 2200 500"
                version="1.1"
                xmlns="http://www.w3.org/2000/svg"
                xmlns:xlink="http://www.w3.org/1999/xlink">

              <g id="layer1">

                <!-- ================== BEZIERS ================== -->

                <path
                  id="long_test_bezier"
                  d="m {min_x_of_reference_line},250 c 0,0 0,0 {len_of_reference_line},0"
                  style="fill:none;stroke:#000;stroke-width:0.3"/>

                <!-- ================== WORD 1 ================== -->

                <g
                  data-bezier-ref="long_test_bezier"
                  data-text="{bezier_word}">
            
                  <text
                    style="font-size:{random_font_size}px;font-family:{random_font};text-anchor:middle;fill:#000">
                    <textPath
                      xlink:href="#long_test_bezier"
                      startOffset="50%">
                      <tspan>{bezier_word}</tspan>
                    </textPath>
                  </text>
                </g>
              </g>
            </svg>
        '''

    test_dir = os.path.join(BASE_DIR, "synth_maps", "svg_length_testing")
    os.makedirs(test_dir, exist_ok=True)
    len_test_file = os.path.join(test_dir, f"{random_font}.svg")
    with open(len_test_file, 'w') as f:
        f.write(straight_line_test)

    test_path_bezier = glyphs_to_paths(len_test_file)

    paths, attributes = svgpathtools.svg2paths(test_path_bezier)
    x_set = set()
    for path in paths:
        x_set = x_set.union(path.bbox()[:2])

    x_set = x_set - {min_x_of_reference_line, max_x_of_reference_line}
    if not x_set:
        return False

    min_x = min(x_set)
    max_x = max(x_set)
    bezier_length_required = max_x - min_x

    # Max length allowed based on target canvas dimensions
    canvas_buffer = 10
    max_allowed_len = min(canvas_width - 2 * canvas_buffer, (canvas_height - 2 * canvas_buffer) * 1.5) * 0.8

    if bezier_length_required > max_allowed_len:
        print("WORD LENGTH TOO LONG")
        return False

    return bezier_length_required

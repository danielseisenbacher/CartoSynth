import subprocess
import os
import svgpathtools


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



def test_word_length(bezier_word, random_font, random_font_size, canvas_size):
    min_x_of_reference_line = 50
    len_of_reference_line = canvas_size - 2 * min_x_of_reference_line
    max_x_of_reference_line = min_x_of_reference_line + len_of_reference_line

    straight_line_test = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <svg
                width="{canvas_size}"
                height="{canvas_size}"
                viewBox="0 0 {canvas_size} {canvas_size}"
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

    len_test_file = os.path.join("/workspaces/SynthMap/synth_maps/svg_length_testing", f"{random_font}.svg")
    with open(len_test_file, 'w') as f:
        f.write(straight_line_test)

    test_path_bezier = glyphs_to_paths(len_test_file)


    paths, attributes = svgpathtools.svg2paths(test_path_bezier)
    x_set = set()
    for path in paths:
        x_set = x_set.union(path.bbox()[:2])


    x_set = x_set - {min_x_of_reference_line, max_x_of_reference_line}
    min_x = min(x_set)
    max_x = max(x_set)
    bezier_length_required = max_x - min_x

    if bezier_length_required > len_of_reference_line:
        print("WORD LENGTH TOO LONG")
        return False

    return bezier_length_required

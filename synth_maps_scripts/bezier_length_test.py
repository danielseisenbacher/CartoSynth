import subprocess
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
        f'export-filename:path_bezier_{svg_with_glyphs};'
        f'export-do"',
        shell=True
    )
    return f"path_bezier_{svg_with_glyphs}"



def test_word_length(bezier_word, random_font, random_font_size):
    min_x_of_reference_line = 50
    len_of_reference_line = 400
    max_x_of_reference_line = min_x_of_reference_line + len_of_reference_line

    straight_line_test = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <svg
                width="500px"
                height="500px"
                viewBox="0 0 500 500"
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


    with open(f"{random_font}.svg", 'w') as f:
        f.write(straight_line_test)

    test_path_bezier = glyphs_to_paths(f"{random_font}.svg")


    paths, attributes = svgpathtools.svg2paths(test_path_bezier)
    x_set = set()
    for path in paths:
        x_set = x_set.union(path.bbox()[:2])


    x_set = x_set - {min_x_of_reference_line, max_x_of_reference_line}
    min_x = min(x_set)
    max_x = max(x_set)
    bezier_length_required = max_x - min_x

    return bezier_length_required

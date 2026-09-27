"""SVG snippets for the stage-1 files (labels as <text> on bezier baselines)."""
from xml.sax.saxutils import escape, quoteattr


def get_svg_template(canvas_width, canvas_height, template_name=""):
    # data-template: background image, inserted by effects.add_background
    template_attr = f' data-template={quoteattr(template_name)}' if template_name else ''
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg
            width="{canvas_width}"
            height="{canvas_height}"
            viewBox="0 0 {canvas_width} {canvas_height}"{template_attr}
            version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">

          <g id="layer1">

            BEZIER_LIST
          </g>
        </svg>
    '''


def get_bezier_template(bezier_reference_id, geometry_string):
    # invisible baseline the text follows
    return f'''<path
      id="{bezier_reference_id}"
      d="{geometry_string}"
      style="fill:none;stroke:none;stroke-width:0.3"/>'''


def get_word_template(bezier_reference_id, text, font_family, font_size, fill="#000"):
    # data-text: the label as annotated (beziers.py splits it into words at spaces);
    # the family is quoted so names with spaces, digits or '_' are valid CSS
    return f'''
        <g
          data-bezier-ref="{bezier_reference_id}"
          data-text={quoteattr(text)}>
          <text
            style="font-size:{font_size}px;font-family:'{escape(font_family)}';text-anchor:middle;font-variant-ligatures:none;fill:{fill}">
            <textPath
              xlink:href="#{bezier_reference_id}"
              startOffset="50%">
              <tspan>{escape(text)}</tspan>
            </textPath>
          </text>

        </g>
    '''


def get_marker_template(marker_id, x, y, r, colour):
    # small circle with a centre dot, like elevation points on topographic maps
    return f'''
    <circle id="{marker_id}" cx="{x}" cy="{y}" r="{r}" style="fill:none;stroke:{colour};stroke-width:{max(0.8, r * 0.35):.1f}"/>
    <circle id="{marker_id}_dot" cx="{x}" cy="{y}" r="{max(0.6, r * 0.25):.1f}" style="fill:{colour};stroke:none"/>
'''

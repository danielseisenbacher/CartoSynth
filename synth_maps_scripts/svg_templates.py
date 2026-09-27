def get_svg_template(canvas_width=1000, canvas_height=None, template_name=""):
    if canvas_height is None:
        if isinstance(canvas_width, (tuple, list)):
            canvas_width, canvas_height = canvas_width
        else:
            canvas_height = canvas_width

    template_attr = f' data-template="{template_name}"' if template_name else ''
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
    bezier_path_template = '''<path
      id="BEZIER_ID_STRING"
      d="GEOMETRY_STRING"
      style="fill:none;stroke:none;stroke-width:0.3"/>'''

    return (bezier_path_template
            .replace('BEZIER_ID_STRING', bezier_reference_id)
            .replace('GEOMETRY_STRING', geometry_string))



def get_word_template(bezier_reference_id, bezier_text, font_family, font_size, fill="#000"):

    word_template = '''
        <g
          data-bezier-ref="BEZIER_ID_STRING"
          data-text="BEZIER_TEXT_STRING">
          <text
            style="font-size:FONT_SIZEpx;font-family:FONT_FAMILY;text-anchor:middle;font-variant-ligatures:none;fill:FILL_COLOUR">
            <textPath
              xlink:href="#BEZIER_ID_STRING"
              startOffset="50%">
              <tspan>BEZIER_TEXT_STRING</tspan>
            </textPath>
          </text>
    
        </g>
    '''

    return (word_template
            .replace('BEZIER_ID_STRING', bezier_reference_id)
            .replace('FONT_FAMILY', font_family)
            .replace('FONT_SIZE', str(font_size))
            .replace('FILL_COLOUR', fill)
            .replace('BEZIER_TEXT_STRING', bezier_text))


def get_elevation_marker_template(marker_id, x, y, r, colour):
    # small circle with a centre dot, like the elevation points on the 3LA sheets
    return f'''
    <circle id="{marker_id}" cx="{x}" cy="{y}" r="{r}" style="fill:none;stroke:{colour};stroke-width:{max(0.8, r * 0.35):.1f}"/>
    <circle id="{marker_id}_dot" cx="{x}" cy="{y}" r="{max(0.6, r * 0.25):.1f}" style="fill:{colour};stroke:none"/>
'''

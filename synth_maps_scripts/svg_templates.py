def get_svg_template(canvas_size=1000):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg
            width="{canvas_size}"
            height="{canvas_size}"
            viewBox="0 0 {canvas_size} {canvas_size}"
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



def get_word_template(bezier_reference_id, bezier_text, font_family, font_size):

    word_template = '''
        <g
          data-bezier-ref="BEZIER_ID_STRING"
          data-text="BEZIER_TEXT_STRING">
          <text
            style="font-size:FONT_SIZEpx;font-family:FONT_FAMILY;text-anchor:middle;font-variant-ligatures:none;fill:#000">
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
            .replace('BEZIER_TEXT_STRING', bezier_text))
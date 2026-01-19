import fontforge
import os

# Path to the Base Font, the font that will be modified to fit the historic map text font
fonts_dir = os.path.join(os.path.dirname(os.getcwd()), "fonts")
base_font = os.path.join(fonts_dir, "base_font", "BaseFont.ttf")
svg_font_dir = os.path.join(fonts_dir, "svg_fonts")

if not os.path.exists(base_font):
    raise Exception(f"BaseFont.ttf does not exist: {base_font}")


# iterate through different fonts in svg dir to create fonts based on BaseFont.ttf
dirs = [d for d in os.listdir(svg_font_dir) if os.path.isdir(os.path.join(svg_font_dir, d))]

# creat one font for each subdirectory
for d in dirs:
    # get font Base Font using fontforge
    font = fontforge.open(base_font)
    
    # iterate through all letters
    for file in os.listdir(os.path.join(svg_font_dir, d)):
        letter = file.split(".")[0]
        if file.endswith(".svg"):      # only look at svg files 

            svg_path = os.path.join(svg_font_dir, d, file)

            # get the existing glyph instance of the letter
            glyph = font[letter]

            # get the bounding box and existing anchors
            template_bb = glyph.boundingBox()
            existing_anchors = glyph.anchorPoints
            
            left_orig_bearing = glyph.left_side_bearing
            right_orig_bearing = glyph.right_side_bearing

            # delete the glyph
            glyph.clear()

            for anchor in existing_anchors:
                # re-add the anchors
                anchor_class_name,anchor_type,x,y = anchor
                glyph.addAnchorPoint(anchor_class_name,anchor_type,x,y)

            # import the outlines
            glyph.importOutlines(svg_path)
            
            # bounding boxes
            imported_bb = glyph.boundingBox()

            # dimensions
            imported_height = imported_bb[3] - imported_bb[1]
            template_height = template_bb[3] - template_bb[1]
            template_y_min = template_bb[1]

            # centers
            imported_center_x = (imported_bb[0] + imported_bb[2]) / 2
            imported_center_y = (imported_bb[1] + imported_bb[3]) / 2
            template_center_x = (template_bb[0] + template_bb[2]) / 2

            # scale
            scale = template_height / imported_height

            # move imported glyph center to origin
            glyph.transform((
                1, 0,
                0, 1,
                -imported_center_x,
                -imported_center_y
            ))

            # scale around origin
            glyph.transform((
                scale, 0,
                0, scale,
                0, 0
            ))


            glyph.left_side_bearing = int(left_orig_bearing)
            glyph.right_side_bearing = int(right_orig_bearing)


            _,y_min,_,_ = glyph.boundingBox()
            y_diff = template_y_min - y_min
  

            # move glyph back: center horizontally to template, restore vertical position
            glyph.transform((
                1, 0,
                0, 1,
                0, y_diff
            ), ("round",))

            glyph.correctDirection()
    

    # Save the font TrueType Font in the svg Directories
    font_save_dir = os.path.join(svg_font_dir, d, "TrueType_Font")
    os.makedirs(font_save_dir, exist_ok=True)
    font_path = os.path.join(font_save_dir, f"{d}.ttf")
    font.generate(font_path)

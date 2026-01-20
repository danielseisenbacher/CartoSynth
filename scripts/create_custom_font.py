import fontforge
import os
import shutil
import subprocess
import sys


CUSTOM_FONTS_DIR = '/workspaces/SynthMap/fonts'
SYSTEM_FONT_DIR = '/usr/share/fonts/truetype/'
FONT_PATHS = []

def create_custom_font():
    # Path to the Base Font, the font that will be modified to fit the historic map text font
    base_font = os.path.join(CUSTOM_FONTS_DIR, "base_font", "BaseFont.ttf")
    svg_font_dir = os.path.join(CUSTOM_FONTS_DIR, "svg_fonts")

    if not os.path.exists(base_font):
        raise Exception(f"BaseFont.ttf does not exist: {base_font}")


    # iterate through different fonts in svg dir to create fonts based on BaseFont.ttf
    dirs = [d for d in os.listdir(svg_font_dir) if os.path.isdir(os.path.join(svg_font_dir, d))]

    # creat one font for each subdirectory
    for d in dirs:
        # get font Base Font using fontforge
        font = fontforge.open(base_font)
        font.encoding = "UnicodeFull"
        
        # iterate through all letters
        for file in os.listdir(os.path.join(svg_font_dir, d)):
            letter = file.split(".")[0]
            if file.endswith(".svg"):      # only look at svg files 

                svg_path = os.path.join(svg_font_dir, d, file)

                # get the existing glyph instance of the letter
                glyph = font[letter]
                try:
                    glyph.unicode = ord(letter)   # CRITICAL: restore Unicode mapping
                except Exception as e:
                    print(e)
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
        family = d
        style  = "Regular"

        font.familyname = family
        font.fullname   = f"{family} {style}"
        font.fontname   = f"{family}-{style}"   # PostScript name, no spaces

        font.default_base_filename = family

        # Fix style info so fontconfig matches correctly
        font.weight = style
        font.italicangle = 0

        # Fix OS/2 table (THIS IS VERY IMPORTANT)
        font.os2_weight = 400        # Regular
        font.os2_width  = 5
        font.os2_stylemap = 64       # Regular  

        font_save_dir = os.path.join(svg_font_dir, d, "TrueType_Font")
        os.makedirs(font_save_dir, exist_ok=True)
        font_path = os.path.join(font_save_dir, f"{d}.otf")
        font.generate(font_path)
        
        # list all the created font paths
        FONT_PATHS.append(font_path)


def install_custom_font():

    os.makedirs(SYSTEM_FONT_DIR, exist_ok=True)

    installed = 0

    for source_path in FONT_PATHS:

        print(f"Installing font: {source_path}")
        shutil.copy2(source_path, SYSTEM_FONT_DIR)
        installed += 1

    if installed == 0:
        print("No .ttf fonts found.")
        sys.exit(0)

    print(f"Copied {installed} fonts. Rebuilding font cache...")

    # Rebuild font cache
    subprocess.run(["fc-cache", "-f", SYSTEM_FONT_DIR], check=True)

    print("All fonts installed!")


# RUN EVERYTHING
create_custom_font()
install_custom_font()
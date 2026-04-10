import fontforge
import os
import shutil
import subprocess
import sys




def create_custom_font(CUSTOM_FONTS_DIR):
    # Path to the Base Font, the font that will be modified to fit the historic map text font
    base_font = os.path.join(CUSTOM_FONTS_DIR, "base_font", "BaseFont.ttf")
    svg_font_dir = os.path.join(CUSTOM_FONTS_DIR, "svg_fonts")
    FONT_PATHS = []

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
        

        # Configure for new Font
        family = d  # the font family == directory name
        style  = "Regular"
        font.familyname = family
        font.fullname   = f"{family} {style}"
        font.fontname   = f"{family}-{style}"

        # Fix style info so fontconfig matches correctly
        font.weight = "Regular" 
        font.italicangle = 0
        font.os2_weight = 400        
        font.os2_width  = 5
        font.os2_stylemap = 64       
        font.os2_family_class = 0    
        font.sfnt_names = ()  
        
        # Save the Font in the container font dir
        font_save_dir = os.path.join(svg_font_dir, d, "OpenType_Font")
        os.makedirs(font_save_dir, exist_ok=True)
        font_path = os.path.join(font_save_dir, f"{d}.otf")
        font.generate(font_path)
        
        # list all the created font paths
        FONT_PATHS.append(font_path)

    return FONT_PATHS



def install_custom_font(SYSTEM_FONT_DIR, FONT_PATHS):

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
    subprocess.run(["fc-cache", "-f"], check=True)

    print("All fonts installed!")


# RUN EVERYTHING
def run_create_custom_font(CUSTOM_FONTS_DIR='/workspaces/SynthMap/fonts', SYSTEM_FONT_DIR = '/usr/share/fonts/opentype/'):

    FONT_PATHS = create_custom_font(CUSTOM_FONTS_DIR)
    install_custom_font(SYSTEM_FONT_DIR, FONT_PATHS)


# Run via start_fontforge.sh
run_create_custom_font()
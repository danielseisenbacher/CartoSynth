import os

from PIL import Image

tif_font_dir = "tiff_fonts"
png_font_dir = "png_fonts"

for dir in os.listdir(tif_font_dir):
    for file in os.listdir(os.path.join(tif_font_dir, dir)):
        if file.endswith((".tif", ".tiff")):
            # Open the TIFF image
            tif_path = os.path.join(tif_font_dir, dir, file)
            tiff_image = Image.open(tif_path)

            # Save the png image
            tiff_image.save(os.path.join(png_font_dir, dir, file.replace(".tif", ".png").replace(".tiff", ".png")))
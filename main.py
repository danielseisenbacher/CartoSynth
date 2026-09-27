from synth_maps_scripts import synth_map_maker
from osm.osm_scripts import query_osm_data
from annotations_scripts import bezier_builder, annotation_builder, svg2png
from synth_maps_scripts import synth_map_maker, svg_enhancer
import os
import subprocess

# font config
# Set canvas_size = None to automatically use the dimensions of each image in map_templates
canvas_size = None
min_bezier_on_canvas=2
max_bezier_on_canvas=5

min_blur_level = 23
max_blur_level = 27
min_opacity = 64
max_opacity = 74


# create svgs using osm data and put the data onto bezier
font_config = {
    "font1": {"font_size_range": [30, 60], "can_display_numeric": False, "can_display_letters": True, "uppercase_possible": True, "lowercase_possible": False, "fallback": False},
    "font2": {"font_size_range": [30, 60], "can_display_numeric": False, "can_display_letters": True, "uppercase_possible": False, "lowercase_possible": True, "fallback": False},
    "font3": {"font_size_range": [30, 60], "can_display_numeric": False, "can_display_letters": True, "uppercase_possible": True, "lowercase_possible": True, "fallback": False},
    "font4": {"font_size_range": [30, 60], "can_display_numeric": False, "can_display_letters": True, "uppercase_possible": True, "lowercase_possible": False, "fallback": False},
    "font5": {"font_size_range": [30, 60], "can_display_numeric": False, "can_display_letters": True, "uppercase_possible": True, "lowercase_possible": True, "fallback": False},
    "font6": {"font_size_range": [30, 60], "can_display_numeric": False, "can_display_letters": True, "uppercase_possible": True, "lowercase_possible": True, "fallback": True},
    "font7": {"font_size_range": [30, 60], "can_display_numeric": True, "can_display_letters": False, "fallback": False},
    "font8": {"font_size_range": [30, 60], "can_display_numeric": True, "can_display_letters": False, "fallback": False}
}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# check if custom fonts are installed
fontforge_script = os.path.join(BASE_DIR, "font_scripts", "start_fontforge.sh")
result = subprocess.run(["bash", fontforge_script], check=True)

# check if training data exists
osm_save_dir = os.path.join(BASE_DIR, "osm", "osm_data")
osm_path = os.path.join(osm_save_dir, "full_training_data.txt")
if not os.path.exists(osm_path):
    query_osm_data.run_osm_logic("AT", osm_save_dir)
else:
    print("Training data already exists.")


synth_map_maker.run_synth_map_maker(
    font_config, 
    how_many_svgs=2000,
    min_bezier_on_canvas=min_bezier_on_canvas, 
    max_bezier_on_canvas=max_bezier_on_canvas, 
    canvas_size=canvas_size
)


bezier_dict = bezier_builder.build_bezier()


svg_enhancer.add_glyph_artefacts()


svg_enhancer.add_map_background()


svg2png.svg2png()


# convert svgs to pngs
annotation_builder.build_annotations(bezier_dict)



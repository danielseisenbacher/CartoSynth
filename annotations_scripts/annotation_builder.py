from bezier_builder import build_bezier
from svg2png import svg2png
from coco_template import character_map, coco_template, annotations_template, images_template
from PIL import Image
import json
import os
import copy

# get bezier annotation for all images
bezier_dict = build_bezier()

# build annotation dict
count = 0
for image_path, beziers in bezier_dict.items():
    png_path = svg2png(
        "/workspaces/SynthMap/synth_maps/svg_maps_with_glyphs",
        "/workspaces/SynthMap/synth_maps/png_maps",
        image_path
    )
    img = Image.open(png_path)
    width, height = img.size

    # fill template
    image_entry = copy.deepcopy(images_template)
    image_entry["file_name"] = image_path
    image_id = int(os.path.basename(png_path).split(".")[0])
    image_entry["id"] = image_id
    image_entry["width"] = width
    image_entry["height"] = height

    # append image to template
    coco_template["images"].append(image_entry)

    # iterate each word
    for bezier_id, bezier in beziers.items():
        annotation_entry = copy.deepcopy(annotations_template)
        annotation_entry["image_id"] = image_id
        annotation_entry["id"] = count
        annotation_entry["bezier_pts"] = []
        annotation_entry["bezier_pts"].extend([round(coord, 1) for point in bezier["upper_bezier_points"] for coord in point])
        annotation_entry["bezier_pts"].extend([round(coord, 1) for point in bezier["lower_bezier_points"] for coord in point])
        annotation_entry["rec"] = []
        annotation_entry["rec"].extend([character_map[i["letter"]] for i in bezier["letters"]])
        annotation_entry["bbox"] = bezier["bbox"]
        coco_template["annotations"].append(annotation_entry)
        count += 1


# write annotation to json
json.dump(coco_template, open("/workspaces/SynthMap/annotations/annotation.json", "w"))

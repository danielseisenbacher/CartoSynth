try:
    from coco_template import character_map, coco_template, annotations_template, images_template
    from svg2png import svg2png
except:
    from annotations_scripts.coco_template import character_map, coco_template, annotations_template, images_template
    from annotations_scripts.svg2png import svg2png
    
from PIL import Image
import json
import os
import copy



def build_annotations(bezier_dict):
    # build annotation dict
    count = 0
    png_dir = "/workspaces/SynthMap/synth_maps/png_maps"

    for image_path, beziers in bezier_dict.items():
        

        png_path = os.path.join(png_dir, image_path.replace(".svg", ".png"))
        img = Image.open(png_path)
        width, height = img.size

        print(f"Opened {png_path} - size: {width}x{height}")

        # fill template
        image_entry = copy.deepcopy(images_template)
        image_entry["file_name"] = f"{image_path.split(".")[0]}.png"
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
            annotation_entry["bezier_pts"].extend([round(coord, 1) for point in bezier["lower_bezier_points"][::-1] for coord in point]) #clockwise
            annotation_entry["rec"] = []
            
            # PADDING
            MAX_LEN = 50
            NULL_CHAR = 96  # padding token
            rec = [character_map.get(i["letter"], 96) for i in bezier["letters"]]
            rec = rec[:MAX_LEN]
            rec = rec + [NULL_CHAR] * (MAX_LEN - len(rec))
            annotation_entry["rec"] = rec

            annotation_entry["bbox"] = bezier["bbox"]
            coco_template["annotations"].append(annotation_entry)
            count += 1

    # write annotation to json
    json.dump(coco_template, open("/workspaces/SynthMap/annotations/train_96voc.json", "w"))


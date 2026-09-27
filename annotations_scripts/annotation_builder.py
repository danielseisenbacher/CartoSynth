try:
    from coco_template import coco_template, annotations_template, images_template
    from svg2png import svg2png
    import voc148
except:
    from annotations_scripts.coco_template import coco_template, annotations_template, images_template
    from annotations_scripts.svg2png import svg2png
    from annotations_scripts import voc148
    
from PIL import Image
import json
import os
import copy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_annotations(bezier_dict):
    # build annotation dict
    count = 0
    png_dir = os.path.join(BASE_DIR, "synth_maps", "png_maps")
    coco_template["images"] = []
    coco_template["annotations"] = []

    for image_path, beziers in bezier_dict.items():
        png_path = os.path.join(png_dir, image_path.replace(".svg", ".png"))
        if not os.path.exists(png_path):
            print(f"File {png_path} does not exist, skipping...")
            continue
        img = Image.open(png_path)
        width, height = img.size

        print(f"Opened {png_path} - size: {width}x{height}")

        # fill template
        image_entry = copy.deepcopy(images_template)
        image_entry["file_name"] = f"{image_path.split('.')[0]}.png"
        image_id = int(os.path.basename(png_path).split('.')[0])
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
            # 148voc (MapTextPipeline): length 25, padding 148. Raises if a word is not encodable,
            # which cannot happen because synth_map_maker only renders encodable words.
            transcription = "".join(i["letter"] for i in bezier["letters"])
            annotation_entry["transcription"] = transcription
            annotation_entry["rec"] = voc148.encode(transcription)

            annotation_entry["bbox"] = bezier["bbox"]
            coco_template["annotations"].append(annotation_entry)
            count += 1

    # write annotation to json
    annotations_dir = os.path.join(BASE_DIR, "annotations")
    os.makedirs(annotations_dir, exist_ok=True)
    with open(os.path.join(annotations_dir, "train_148voc.json"), "w", encoding="utf-8") as f:
        json.dump(coco_template, f, ensure_ascii=False)


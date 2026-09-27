"""
Writes the annotations in COCO format with AdelaiDet/ABCNet text fields:

  images:      {id, file_name, width, height, ...}
  annotations: {id, image_id, category_id: 1,
                bezier_pts: 16 floats = upper curve left->right (4 points) +
                            lower curve right->left (4 points),
                rec: character indices (see vocab.py), padded to max_length,
                transcription: the word as string,
                bbox: [x, y, w, h]}
"""
import json
import os

from PIL import Image


def build_annotations(bezier_dict, dirs, vocab, output_path):
    images, annotations = [], []

    for svg_name, beziers in bezier_dict.items():
        file_name = svg_name.replace(".svg", ".png")
        png_path = os.path.join(dirs.images, file_name)
        if not os.path.exists(png_path):
            print(f"WARNING: {png_path} does not exist, skipped")
            continue
        with Image.open(png_path) as img:
            width, height = img.size
        image_id = int(os.path.splitext(file_name)[0])
        images.append({"id": image_id, "file_name": file_name, "width": width, "height": height,
                       "license": 0, "coco_url": "", "flickr_url": "", "date_captured": ""})

        for bezier in beziers.values():
            transcription = "".join(letter["letter"] for letter in bezier["letters"])
            annotations.append({
                "id": len(annotations),
                "image_id": image_id,
                "category_id": 1,
                "iscrowd": 0,
                "area": 0,
                "bezier_pts": [round(c, 1) for point in bezier["upper_bezier_points"] for c in point]
                              + [round(c, 1) for point in bezier["lower_bezier_points"][::-1] for c in point],
                # raises for characters outside the dictionary; cannot happen because
                # words.load_words only keeps encodable words
                "rec": vocab.encode(transcription),
                "transcription": transcription,
                "bbox": bezier["bbox"],
            })

    coco = {
        "info": {"description": "CartoSynth synthetic map text"},
        "licenses": [],
        "categories": [{"id": 1, "name": "text", "supercategory": "text"}],
        "images": images,
        "annotations": annotations,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(coco, f, ensure_ascii=False)
    return coco

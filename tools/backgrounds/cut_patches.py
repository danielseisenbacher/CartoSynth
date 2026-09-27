#!/usr/bin/env python3
"""
Step 1 of making backgrounds: cut random patches out of large map scans.

    python tools/backgrounds/cut_patches.py -i scans/ -o patches/ -n 500 --min-size 500 --max-size 1000

The patches still contain text; remove it with remove_text_ai.py (or by hand) before
using them as CartoSynth backgrounds.
"""
import argparse
import random
from pathlib import Path

from PIL import Image

def sample_patches(
    input_dir: str,
    output_dir: str,
    num_patches: int = 5000,
    min_size: int = 400,
    max_size: int = 1000,
    valid_extensions: tuple = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")
):
    """
    Randomly samples rectangular patches of varying widths and heights independently 
    from images in `input_dir` and saves them to `output_dir`.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Gather all image files recursively
    image_paths = [
        p for p in input_path.rglob("*") 
        if p.suffix.lower() in valid_extensions
    ]

    if not image_paths:
        raise ValueError(f"No images found in '{input_dir}' with extensions {valid_extensions}")

    print(f"Found {len(image_paths)} images in {input_dir}")
    print(f"Sampling {num_patches} patches (edge range: {min_size}px - {max_size}px)...")

    # 2. Pre-filter images that are too small for min_size
    valid_images = []
    for img_path in image_paths:
        try:
            with Image.open(img_path) as img:
                w, h = img.size
                if w >= min_size and h >= min_size:
                    valid_images.append(img_path)
                else:
                    print(f"Skipping {img_path.name}: too small ({w}x{h})")
        except Exception as e:
            print(f"Error reading {img_path.name}: {e}")

    if not valid_images:
        raise ValueError("No images meet the minimum size requirement!")

    # 3. Extract patches randomly
    saved_count = 0
    
    while saved_count < num_patches:
        img_path = random.choice(valid_images)

        try:
            with Image.open(img_path) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                    
                w, h = img.size

                # Determine independent width and height bounds based on image size
                max_w_possible = min(w, max_size)
                max_h_possible = min(h, max_size)

                if max_w_possible < min_size or max_h_possible < min_size:
                    continue  # Skip if image dimensions can't support min_size

                # Sample width and height INDEPENDENTLY
                patch_w = random.randint(min_size, max_w_possible)
                patch_h = random.randint(min_size, max_h_possible)

                # Pick random top-left corner coordinates (x, y)
                x = random.randint(0, w - patch_w)
                y = random.randint(0, h - patch_h)

                # Crop bounding box: (left, upper, right, lower)
                crop_box = (x, y, x + patch_w, y + patch_h)
                patch = img.crop(crop_box)

                # Save the patch
                patch_filename = (
                    f"{saved_count + 1:06d}.jpg"
                )
                patch.save(output_path / patch_filename, quality=95)
                
                saved_count += 1

                if saved_count % 500 == 0 or saved_count == num_patches:
                    print(f"Saved {saved_count}/{num_patches} patches...")

        except Exception as e:
            print(f"Error processing {img_path.name}: {e}")

    print(f"\nDone! Extracted {saved_count} patches into '{output_dir}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input-dir", required=True, help="folder with map scans (searched recursively)")
    parser.add_argument("-o", "--output-dir", required=True, help="folder for the patches (<n>.jpg)")
    parser.add_argument("-n", "--num-patches", type=int, default=500)
    parser.add_argument("--min-size", type=int, default=500, help="min patch width/height in px")
    parser.add_argument("--max-size", type=int, default=1000, help="max patch width/height in px")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    random.seed(args.seed)
    sample_patches(args.input_dir, args.output_dir, args.num_patches, args.min_size, args.max_size)

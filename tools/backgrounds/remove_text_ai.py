#!/usr/bin/env python3
"""
Step 2 of making backgrounds: let an image model redraw map patches without any text.

    export OPENAI_API_KEY=...        # never put the key into this file
    pip install openai pillow
    python tools/backgrounds/remove_text_ai.py -i patches/ -o generated/ --limit 50

Each patch is sent to the OpenAI image edit API with the prompt below; the result is a
new, text-free map extent in the same style (not the same place). This costs money per
image: the script prints the estimated cost of every request and the total.
Check the results: remaining text would end up as unlabelled text in the training data.
"""
import argparse
import base64
import os
import sys
from pathlib import Path


PROMPT = """Generate a cartographic map extent that closely mimics the visual style, color palette and aesthetic properties of the reference image, while excluding all text and labels. The geographic region depicted should differ from the reference image, but it must represent a realistic, plausible landscape. Do not include any marginalia or map elements, such as borders, scale bars, north arrows, or titles; output only the clean map image."""

# USD per 1M tokens, for the cost estimate (check the current prices of your model)
TEXT_INPUT_PRICE = 5.00
IMAGE_INPUT_PRICE = 8.00
IMAGE_OUTPUT_PRICE = 30.00


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input-dir", required=True, help="patches with text (*.jpg)")
    parser.add_argument("-o", "--output-dir", required=True, help="text-free results (<name>_generated.png)")
    parser.add_argument("--start", type=int, default=0, help="skip the first N patches")
    parser.add_argument("--limit", type=int, default=None, help="process at most N patches")
    parser.add_argument("--model", default="gpt-image-2.5-sunburst")
    parser.add_argument("--quality", default="medium")
    parser.add_argument("--size", default="1024x1024")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Set the OPENAI_API_KEY environment variable first.")
    from openai import OpenAI  # imported here so --help works without the package
    client = OpenAI()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    input_images = sorted(Path(args.input_dir).glob("*.jpg"))[args.start:]
    if args.limit is not None:
        input_images = input_images[:args.limit]
    print(f"Found {len(input_images)} images.")
    total_cost = 0.0

    for i, image_path in enumerate(input_images, start=1):

        print(f"\n[{i}/{len(input_images)}] Processing {image_path.name}")

        try:
            with open(image_path, "rb") as f:
                image_file = f.read()

            result = client.images.edit(
                model=args.model,
                image=(
                    image_path.name,
                    image_file,
                    "image/jpeg",
                ),
                prompt=PROMPT,
                quality=args.quality,
                size=args.size,
            )

            # --------------------------------------------------
            # Usage / token information
            # --------------------------------------------------

            usage = result.usage

            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens
            total_tokens = usage.total_tokens

            image_input_tokens = usage.input_tokens_details.image_tokens
            text_input_tokens = usage.input_tokens_details.text_tokens

            # --------------------------------------------------
            # Calculate cost
            # --------------------------------------------------

            text_input_cost = (
                text_input_tokens / 1_000_000
            ) * TEXT_INPUT_PRICE

            image_input_cost = (
                image_input_tokens / 1_000_000
            ) * IMAGE_INPUT_PRICE

            image_output_cost = (
                output_tokens / 1_000_000
            ) * IMAGE_OUTPUT_PRICE

            request_cost = (
                text_input_cost
                + image_input_cost
                + image_output_cost
            )

            total_cost += request_cost

            # --------------------------------------------------
            # Print usage
            # --------------------------------------------------

            print(f"    Text input tokens:   {text_input_tokens:,}")
            print(f"    Image input tokens:  {image_input_tokens:,}")
            print(f"    Output tokens:       {output_tokens:,}")
            print(f"    Total tokens:        {total_tokens:,}")

            print(f"    Text input cost:     ${text_input_cost:.6f}")
            print(f"    Image input cost:    ${image_input_cost:.6f}")
            print(f"    Image output cost:   ${image_output_cost:.6f}")
            print(f"    Request cost:        ${request_cost:.6f}")

            # --------------------------------------------------
            # Save image
            # --------------------------------------------------

            image_base64 = result.data[0].b64_json

            output_path = (
                output_dir /
                f"{image_path.stem}_generated.png"
            )

            with open(output_path, "wb") as f:
                f.write(base64.b64decode(image_base64))

            print(f"    Saved -> {output_path}")

        except Exception as e:
            print(f"    ERROR: {e}")
            error_message = str(e)
            if "credit_balance_exhausted" in error_message or "insufficient_quota" in error_message:
                print("\nSTOPPING: API credit balance exhausted.")
                break

    print("\nFinished.")
    print(f"Total estimated cost: ${total_cost:.6f}")
    print(f"Results are in: {output_dir}")


if __name__ == "__main__":
    main()

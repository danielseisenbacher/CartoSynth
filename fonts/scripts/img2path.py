import vtracer
import os


def vectorize_image(input_path, output_path):
    """Convert raster image to SVG using vtracer"""
    vtracer.convert_image_to_svg_py(
        input_path,
        output_path,
        colormode='color',  # 'color' or 'binary'
        hierarchical='stacked',  # 'stacked' or 'cutout'
        mode='spline',  # 'spline', 'polygon', 'none'
        filter_speckle=4,  # Remove small noise (pixels)
        color_precision=6,  # Color matching precision
        layer_difference=16,  # Layer separation threshold
        corner_threshold=45,  # Corner detection angle
        length_threshold=4.0,  # Minimum path length
        max_iterations=15,  # Optimization iterations
        splice_threshold=45,  # Path joining threshold
        path_precision=8  # Coordinate precision
    )


def batch_convert(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    valid_extensions = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')

    for dir in os.listdir(input_folder):
        for filename in os.listdir(os.path.join(input_folder, dir)):
            if filename.lower().endswith(valid_extensions):
                input_path = os.path.join(input_folder, dir, filename)
                output_path = os.path.join(output_folder, dir, f"{os.path.splitext(filename)[0]}.svg")

                try:
                    vectorize_image(input_path, output_path)
                    print(f"✓ Converted {filename}")
                except Exception as e:
                    print(f"✗ Error: {filename}: {e}")


# Usage
input_folder = "fonts/png_fonts"
output_folder = "fonts/svg_fonts"
batch_convert(input_folder, output_folder)
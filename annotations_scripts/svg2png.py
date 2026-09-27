import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def svg2png():
    svg_source_dir = os.path.join(BASE_DIR, "synth_maps", "svg_maps_w_background")
    png_dir = os.path.join(BASE_DIR, "synth_maps", "png_maps")
    os.makedirs(png_dir, exist_ok=True)

    if not os.path.exists(svg_source_dir):
        print(f"Directory {svg_source_dir} does not exist!")
        return

    for file_name in sorted(os.listdir(svg_source_dir)):
        if not file_name.endswith('.svg'):
            continue
        source_svg = os.path.join(svg_source_dir, file_name)
        png_path = os.path.join(png_dir, f"{file_name.replace('.svg', '')}.png")

        command = (
            "inkscape "
            "--export-type=png "
            "--export-area-page "
            f"--export-filename={png_path} "
            f"{source_svg}"
        )

        # Run the command
        subprocess.run(command, shell=True, check=True)
        print(f"svg2png processed for {file_name}")


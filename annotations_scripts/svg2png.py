import os
import subprocess

def svg2png(svg_source_dir, png_dir, svg_filename):
    source_svg = os.path.join(svg_source_dir, svg_filename)
    png_path = os.path.join(png_dir, svg_filename.split(".")[0] + ".png")

    command =   "inkscape "\
                "--export-type=png "\
                "--export-dpi=500 "\
                f"--export-filename={png_path} "\
                f"{source_svg}"

    # Run the command
    subprocess.run(command, shell=True, check=True)

    return png_path
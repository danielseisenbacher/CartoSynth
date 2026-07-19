import os
import subprocess

def svg2png():
    svg_source_dir = "/workspaces/SynthMap/synth_maps/svg_maps_w_background"
    png_dir = "/workspaces/SynthMap/synth_maps/png_maps"
    for file_name in os.listdir(svg_source_dir):
        source_svg = os.path.join(svg_source_dir, file_name)
        png_path = os.path.join(png_dir, f"{file_name.replace(".svg", "")}.png")


        command =   "inkscape "\
                    "--export-type=png "\
                    "--export-width=1000 "\
                    f"--export-filename={png_path} "\
                    f"{source_svg}"

        # "--export-dpi=500 "\
        # Run the command
        subprocess.run(command, shell=True, check=True)
        print(f"svg2png processed for {file_name}")


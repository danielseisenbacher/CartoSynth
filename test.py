import subprocess
input_file = "/workspaces/SynthMap/synth_maps/svg_maps_with_glyphs/3.svg"
output_file = "/workspaces/SynthMap/synth_maps/svg_maps_with_glyph_paths/test_output.svg"


actions = (
    "export-text-to-path;"
    f"export-filename:{output_file};"
    "export-plain-svg;"
    "export-do"
)
subprocess.run(f'inkscape "{input_file}" --actions="{actions}"', shell=True)

from synth_maps_scripts import synth_map_maker
from osm .osm_scripts import query_osm_data
from annotations_scripts import bezier_builder
import os

osm_path = "/workspaces/SynthMap/osm/osm_data/small_training_data.txt"

# check if training data exists
if not os.path.exists(osm_path):
    osm_save_dir = "/workspaces/SynthMap/osm/osm_data"
    query_osm_data.run_osm_logic("AT", osm_save_dir)
else:
    print("Training data already exists.")


bezier_builder.build_bezier()



# create synth map
synth_map_maker.run_synth_map_maker()


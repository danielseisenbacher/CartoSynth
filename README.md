# CartoSynth

Generate synthetic map tiles based on (historic) maps as training data for automated map text detection pipelines

## Output format (148voc, MapTextPipeline)

`main.py` writes `annotations/train_148voc.json` for MapTextPipeline (Rumsey model, `VOC_SIZE: 148`):

- `rec`: 25 indices into the 148-character dictionary (`annotations_scripts/voc148.py`), padded with `148`.
- `transcription`: the rendered word as a string (with umlauts).
- `bezier_pts`: top curve left→right, then bottom curve right→left (AdelaiDet convention).

Only words that the dictionary can fully encode are rendered. `synth_maps_scripts/synth_map_maker.py` drops OSM rows with other characters (e.g. č, š, ž, ý) **before** rendering, so every word in a PNG has a label. Ö/Ü are allowed and encoded as ö/ü (the dictionary has no uppercase Ö/Ü; evaluation is case-insensitive).

The first run (96voc, umlauts transliterated) is kept in `synth_maps_v1_96voc/`.

### Run with docker (no VS Code needed)

```
cd CartoSynth
docker build -f .devcontainer/Dockerfile -t cartosynth .
docker run -d --name cartosynth_run -v "$PWD":/workspace -w /workspace cartosynth \
  bash -c "python -u main.py > synth_run.log 2>&1; chown -R 1000:1000 /workspace"
tail -f synth_run.log
```

Before a new run, move or delete the old `synth_maps/svg_maps_*`, `synth_maps/png_maps` and `annotations/annotation_visualized`. `build_bezier()` processes every SVG in `svg_maps_with_glyphs`.

# CartoSynth

Synthetic map tiles with text annotations for training text spotting models on historical
maps. CartoSynth draws place names and numbers onto text-free map backgrounds, in fonts made
from your map's lettering, and writes exact annotations in the COCO/AdelaiDet format used by
ABCNet, DeepSolo, DNTextSpotter and MapTextPipeline.

![Generated tile and its annotations](docs/example.png)

*`config/3la.yaml` on the bundled example background (an AI-redrawn, text-free tile in the
style of the Austro-Hungarian 3rd Military Survey). Right: upper/lower bezier per word.*

## Quick start

Requires only Docker.

```bash
git clone https://github.com/danielseisenbacher/CartoSynth.git && cd CartoSynth
./cartosynth.sh generate config/default.yaml -n 5   # first run builds the image (~5 min)
./cartosynth.sh visualize output/example            # overlays in output/example/previews/
```

## Your own data

Create `config/<project>.yaml` with the options that differ from
[`config/default.yaml`](config/default.yaml) (all options are documented there;
[`config/3la.yaml`](config/3la.yaml) is a complete example), then
`./cartosynth.sh generate config/<project>.yaml`.

**1. Backgrounds (required).** Text-free images in the style of your maps, e.g. in
`data/backgrounds/<project>/` (`backgrounds.dir`). Any text left in them becomes unlabelled
text in the training data. Ways to get them, scripts in [`tools/backgrounds/`](tools/backgrounds/):
crop text-free areas by hand, retouch/inpaint scans, or let an image model redraw patches
without text:

```bash
python tools/backgrounds/cut_patches.py -i scans/ -o patches/ -n 300
OPENAI_API_KEY=... python tools/backgrounds/remove_text_ai.py -i patches/ -o generated/ --limit 20   # paid, needs `pip install openai`
python tools/backgrounds/cut_subtiles.py -i generated/ -o data/backgrounds/<project>/
```

**2. Words.** A UTF-8 file with one label per line (`words.file`). Included: Austrian place
names from OpenStreetMap (`data/words/austria_small.txt`, `austria_full.txt`). Other
countries: `./cartosynth.sh words CH switzerland`. Numbers (e.g. elevations) are generated,
see `numbers.*`.

**3. Fonts.** Each entry in `fonts.styles` names a font family and what it can draw
(letters, digits, upper/lower case). Either use installed fonts / `.ttf` files in
`data/fonts/files/`, or build fonts from your map's lettering:

1. Cut out one clean example per character into `data/fonts/glyph_scans/<family>/`, named
   `A.png`, `a.png`, `0.png`, `ä.png` (or `U+00E4.png` on case-insensitive file systems).
2. `./cartosynth.sh glyphs` removes the background and vectorises them into `data/fonts/glyphs/<family>/`.
3. `./cartosynth.sh fonts --config config/<project>.yaml` builds `data/fonts/build/<family>.otf`
   (missing characters come from DejaVu Sans; umlauts are composed from your letters) and
   reports characters of your word list a font cannot draw.

**Annotation dictionary.** `annotation.vocabulary` must match your model: `voc96`
(AdelaiDet/ABCNet/DeepSolo), `voc148` (MapTextPipeline) or a file with one character per
line. Words with characters outside it are removed before rendering, so every drawn word is
labelled.

## Output

```
output/<run_name>/
├── images/<n>.png        tiles
├── annotations.json      COCO: bezier_pts, rec, transcription, bbox per word
├── config.yaml           exact config of the run
├── previews/             annotation overlays
└── svg/                  intermediate stages
```

`bezier_pts`: 4 control points of the upper curve (left→right), then 4 of the lower curve
(right→left). `rec`: character indices, padded to `annotation.max_length`.
Every run ends with a check (every drawn word annotated exactly once, correct encoding
and bezier order); run it again with `./cartosynth.sh check output/<run_name>`.

## Commands

| `./cartosynth.sh ...` | |
|---|---|
| `generate <config> [-n N] [--run-name X] [--seed S] [--overwrite]` | generate a dataset |
| `check <run folder>` / `visualize <run folder>` | verify / draw annotations |
| `glyphs`, `fonts [--config C] [--list]` | build custom fonts, check coverage |
| `words <country code> <name>` | place names from OpenStreetMap |
| `test`, `shell`, `build` | tests, shell in the container, rebuild the image |

About 2-4 s per tile. Long runs: `nohup ./cartosynth.sh generate config/3la.yaml > generate.log 2>&1 &`.
Without Docker: install Inkscape ≥ 1.2, FontForge and fontconfig, `pip install -r requirements.txt`,
`python -m cartosynth fonts --install`, then `python -m cartosynth <command>`.
VS Code users can open the repository in the devcontainer.

## Licence

Code, configs, glyph outlines and example images: [MIT](LICENSE). Word lists in `data/words/`:
© OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright). Built fonts
contain glyphs of DejaVu Sans ([licence](https://dejavu-fonts.github.io/License.html)).

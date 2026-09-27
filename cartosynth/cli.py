"""Command line interface: python -m cartosynth <command> ... (or ./cartosynth.sh <command> ...)"""
import argparse
import os
import sys

import yaml

from .config import load_config, resolve, run_dirs


def config_from(path, args=None):
    """A config file, or a run folder (uses the config.yaml saved there)."""
    if os.path.isdir(path):
        saved = os.path.join(path, "config.yaml")
        if not os.path.exists(saved):
            sys.exit(f"{path} has no config.yaml")
        with open(saved, encoding="utf-8") as f:
            return yaml.safe_load(f)
    overrides = {}
    if args is not None:
        if getattr(args, "num_maps", None) is not None:
            overrides["num_maps"] = args.num_maps
        if getattr(args, "run_name", None):
            overrides["run_name"] = args.run_name
        if getattr(args, "seed", None) is not None:
            overrides["seed"] = args.seed
    return load_config(path, overrides)


def cmd_generate(args):
    from .pipeline import generate
    ok = generate(config_from(args.config, args), overwrite=args.overwrite)
    sys.exit(0 if ok else 1)


def cmd_check(args):
    from .check import check_run
    from .vocab import Vocabulary
    cfg = config_from(args.run, args)
    dirs = run_dirs(cfg)
    ok = check_run(dirs, os.path.join(dirs.root, cfg["annotation"]["file_name"]), Vocabulary.from_config(cfg["annotation"]))
    sys.exit(0 if ok else 1)


def cmd_visualize(args):
    from .visualize import visualize_run
    cfg = config_from(args.run, args)
    dirs = run_dirs(cfg)
    visualize_run(dirs, os.path.join(dirs.root, cfg["annotation"]["file_name"]), limit=args.limit)


def cmd_fonts(args):
    from . import fonts
    from .vocab import Vocabulary
    from .words import check_short_tokens, load_words
    if not args.check_only:
        fonts.build_fonts(base_font=args.base_font and resolve(args.base_font), install=args.install)
    cfg = config_from(args.config)
    vocab = Vocabulary.from_config(cfg["annotation"])
    words = load_words(cfg["words"], vocab) + check_short_tokens(cfg["short_labels"], vocab)
    ok = fonts.check_coverage(cfg, words)
    if args.list:
        print("\nInstalled font families:\n  " + "\n  ".join(fonts.available_families()))
    sys.exit(0 if ok else 1)


def cmd_glyphs(args):
    from .glyphs import prepare_glyphs
    prepare_glyphs(force=args.force)


def cmd_words(args):
    from .osm import download_word_lists
    download_word_lists(args.country_code, resolve(args.out_dir), args.name)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cartosynth", description="Synthetic map tiles with text annotations.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("generate", help="generate a dataset")
    p.add_argument("config", help="run config, e.g. config/3la.yaml")
    p.add_argument("-n", "--num-maps", type=int, help="override num_maps")
    p.add_argument("--run-name", help="override run_name (output folder)")
    p.add_argument("--seed", type=int, help="override seed")
    p.add_argument("--overwrite", action="store_true", help="replace an existing run folder")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("check", help="check a finished run (images, annotations, encoding)")
    p.add_argument("run", help="run folder (output/<run_name>) or the config used for it")
    p.add_argument("--run-name", help="with a config: run_name of the run to check")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("visualize", help="draw annotations onto the tiles (-> <run>/previews/)")
    p.add_argument("run", help="run folder (output/<run_name>) or the config used for it")
    p.add_argument("--run-name", help="with a config: run_name of the run")
    p.add_argument("--limit", type=int, default=10, help="number of tiles (default 10)")
    p.set_defaults(func=cmd_visualize)

    p = sub.add_parser("fonts", help="build custom fonts from data/fonts/glyphs and check the configured styles")
    p.add_argument("--config", default="config/default.yaml", help="config whose font styles are checked")
    p.add_argument("--check-only", action="store_true", help="do not build, only check")
    p.add_argument("--base-font", help="font the custom glyphs are put into (default: DejaVu Sans)")
    p.add_argument("--install", action="store_true", help="without Docker: copy fonts to ~/.local/share/fonts")
    p.add_argument("--list", action="store_true", help="list all installed font families")
    p.set_defaults(func=cmd_fonts)

    p = sub.add_parser("glyphs", help="cut-out letter images -> glyph SVGs (data/fonts/glyph_scans -> data/fonts/glyphs)")
    p.add_argument("--force", action="store_true", help="overwrite existing glyph SVGs")
    p.set_defaults(func=cmd_glyphs)

    p = sub.add_parser("words", help="download a word list of place names from OpenStreetMap")
    p.add_argument("country_code", help="ISO 3166-1 code, e.g. AT, CH, CZ")
    p.add_argument("name", help="file prefix, e.g. austria -> data/words/austria_full.txt, austria_small.txt")
    p.add_argument("--out-dir", default="data/words")
    p.set_defaults(func=cmd_words)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

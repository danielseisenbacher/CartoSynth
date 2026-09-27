"""Configuration: config/default.yaml merged with a run config and CLI overrides."""
import copy
import os
from dataclasses import dataclass

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG = os.path.join(REPO_ROOT, "config", "default.yaml")


def deep_merge(base, override):
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def resolve(path):
    """Paths in configs are relative to the repository root."""
    if path is None:
        return None
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def load_config(config_path=None, overrides=None):
    with open(DEFAULT_CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if config_path:
        with open(config_path, encoding="utf-8") as f:
            cfg = deep_merge(cfg, yaml.safe_load(f) or {})
    cfg = deep_merge(cfg, overrides or {})
    validate(cfg)
    return cfg


def validate(cfg):
    errors = []
    if not cfg["fonts"]["styles"]:
        errors.append("fonts.styles is empty")
    if not any(s.get("fallback") for s in cfg["fonts"]["styles"]):
        errors.append("fonts.styles needs one style with `fallback: true`")
    if cfg["numbers"]["share"] > 0 and not any(s.get("digits") for s in cfg["fonts"]["styles"]):
        errors.append("numbers.share > 0 but no font style has `digits: true`")
    short = cfg["short_labels"]
    if short["share"] > 0 and not short["tokens"]:
        errors.append("short_labels.share > 0 but short_labels.tokens is empty")
    if cfg["numbers"]["share"] + short["share"] > 1:
        errors.append("numbers.share + short_labels.share must not exceed 1")
    if any(weight <= 0 for weight in short["tokens"].values()):
        errors.append("short_labels.tokens weights must be positive")
    not_text = [t for t in short["tokens"] if not isinstance(t, str) or not t.strip()]
    if not_text:
        # e.g. unquoted No / On / Off are read by YAML as booleans
        errors.append(f"short_labels.tokens must be quoted strings, got {not_text}")
    low, high = cfg["labels_per_map"]
    if not 0 < low <= high:
        errors.append("labels_per_map must be [min, max] with 0 < min <= max")
    if cfg["words"]["max_word_length"] > cfg["annotation"]["max_length"]:
        errors.append("words.max_word_length must not exceed annotation.max_length")
    if errors:
        raise ValueError("Invalid config:\n  - " + "\n  - ".join(errors))


@dataclass
class RunDirs:
    """Folder layout of one run: <output_dir>/<run_name>/..."""
    root: str

    @property
    def svg_text(self):        # stage 1: labels as <text> on baselines
        return os.path.join(self.root, "svg", "1_text")

    @property
    def svg_paths(self):       # stage 2: glyphs converted to paths (Inkscape)
        return os.path.join(self.root, "svg", "2_paths")

    @property
    def svg_effects(self):     # stage 3: blur, opacity, frayed edges
        return os.path.join(self.root, "svg", "3_effects")

    @property
    def svg_background(self):  # stage 4: background image inserted
        return os.path.join(self.root, "svg", "4_background")

    @property
    def images(self):          # final PNG tiles
        return os.path.join(self.root, "images")

    @property
    def previews(self):        # annotation overlays (SVG) for checking
        return os.path.join(self.root, "previews")

    @property
    def tmp(self):
        return os.path.join(self.root, "tmp")

    def create(self):
        for d in (self.svg_text, self.svg_paths, self.svg_effects, self.svg_background,
                  self.images, self.previews, self.tmp):
            os.makedirs(d, exist_ok=True)


def run_dirs(cfg):
    return RunDirs(os.path.join(resolve(cfg["output_dir"]), cfg["run_name"]))

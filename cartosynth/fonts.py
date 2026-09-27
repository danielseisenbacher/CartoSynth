"""
Fonts: build custom fonts from glyph outlines and check which font styles can render
the labels.

  base font                      the custom glyphs are put into this font; everything
                                 they do not replace (umlauts' dots, ß, punctuation) comes
                                 from it. Default: DejaVu Sans (in the Docker image);
                                 another one: data/fonts/base/BaseFont.ttf or --base-font
  data/fonts/glyphs/<family>/    glyph outlines (SVG), one folder per custom font
  data/fonts/build/              built fonts (<family>.otf)
  data/fonts/files/              ready-made .ttf/.otf fonts you want to use

In the Docker image fontconfig reads data/fonts/build and data/fonts/files directly
(docker/fonts.conf). Without Docker, `--install` copies the fonts to ~/.local/share/fonts.
"""
import os
import shutil
import subprocess

from .config import REPO_ROOT

FONTS_DIR = os.path.join(REPO_ROOT, "data", "fonts")
GLYPHS_DIR = os.path.join(FONTS_DIR, "glyphs")
BUILD_DIR = os.path.join(FONTS_DIR, "build")
FILES_DIR = os.path.join(FONTS_DIR, "files")
CUSTOM_BASE_FONT = os.path.join(FONTS_DIR, "base", "BaseFont.ttf")
DEFAULT_BASE_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def default_base_font():
    return CUSTOM_BASE_FONT if os.path.exists(CUSTOM_BASE_FONT) else DEFAULT_BASE_FONT
FONTFORGE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fontforge_build.py")


def build_fonts(base_font=None, install=False):
    """One font per folder in data/fonts/glyphs; returns the built font files."""
    base_font = base_font or default_base_font()
    if not os.path.isdir(GLYPHS_DIR):
        print(f"No custom glyphs in {GLYPHS_DIR}, nothing to build")
        return []
    if not os.path.exists(base_font):
        raise FileNotFoundError(f"Base font not found: {base_font}")
    print(f"Base font: {base_font}")
    built = []
    for family in sorted(os.listdir(GLYPHS_DIR)):
        glyph_dir = os.path.join(GLYPHS_DIR, family)
        if not os.path.isdir(glyph_dir):
            continue
        out_file = os.path.join(BUILD_DIR, f"{family}.otf")
        result = subprocess.run(["fontforge", "-quiet", "-script", FONTFORGE_SCRIPT, glyph_dir, base_font, out_file],
                                capture_output=True, text=True)
        # FontForge prints its banner and harmless warnings on stderr; show only our lines
        for line in result.stdout.splitlines():
            print("  " + line)
        if result.returncode != 0 or not os.path.exists(out_file):
            raise RuntimeError(f"FontForge failed for {family}:\n{result.stderr[-2000:]}")
        built.append(out_file)
    if install:
        install_fonts(built + list_font_files(FILES_DIR))
    refresh_font_cache()
    return built


def list_font_files(directory):
    if not os.path.isdir(directory):
        return []
    return [os.path.join(directory, f) for f in sorted(os.listdir(directory))
            if f.lower().endswith((".ttf", ".otf"))]


def install_fonts(font_files):
    """Without Docker: copy fonts to the user's font directory."""
    target = os.path.expanduser("~/.local/share/fonts/cartosynth")
    os.makedirs(target, exist_ok=True)
    for f in font_files:
        shutil.copy2(f, target)
    print(f"Installed {len(font_files)} fonts to {target}")


def refresh_font_cache():
    subprocess.run(["fc-cache", "-f"], check=False, capture_output=True)


# --- coverage -----------------------------------------------------------------------------

def font_charset(family):
    """Set of code points of the font with exactly this family name, or None if not installed."""
    result = subprocess.run(["fc-list", "-f", "%{family}\t%{charset}\n", f":family={family}"],
                            capture_output=True, text=True)
    codepoints = None
    for line in result.stdout.splitlines():
        families, _, charset = line.partition("\t")
        if family not in families.split(","):
            continue
        codepoints = codepoints or set()
        for part in charset.split():
            start, _, end = part.partition("-")
            codepoints.update(range(int(start, 16), int(end or start, 16) + 1))
    return codepoints


def needed_characters(style, words, digits_needed):
    """Characters a style will render: words (in its case) and/or digits."""
    chars = set()
    if style.get("letters", False):
        for w in words:
            if not style.get("uppercase", True):
                w = w.lower()
            if not style.get("lowercase", True):
                w = w.upper()
            chars |= set(w)
    if style.get("digits", False) and digits_needed:
        chars |= set("0123456789")
    chars.discard(" ")
    return chars


def check_coverage(cfg, words):
    """Prints, per configured style, whether the font exists and which needed characters it lacks."""
    ok = True
    print("Font styles:")
    for style in cfg["fonts"]["styles"]:
        family = style["family"]
        charset = font_charset(family)
        if charset is None:
            print(f"  {family:20s} NOT FOUND - build it, put the font file into data/fonts/files/, or fix the name")
            ok = False
            continue
        missing = sorted(c for c in needed_characters(style, words, cfg["numbers"]["share"] > 0)
                         if ord(c) not in charset)
        if missing:
            print(f"  {family:20s} ok, but missing {''.join(missing)} (Inkscape substitutes another font)")
        else:
            print(f"  {family:20s} ok")
    return ok


def available_families():
    result = subprocess.run(["fc-list", "-f", "%{family}\n"], capture_output=True, text=True)
    return sorted({f for line in result.stdout.splitlines() for f in line.split(",") if f})

"""
Builds one font from a folder of glyph outlines. Runs inside FontForge's own Python:

    fontforge -script fontforge_build.py <glyph_dir> <base_font> <out_file>

Every <name>.svg in glyph_dir replaces one glyph of the base font; all other characters
keep the base font's shape. <name> is
  - a single character:      A.svg, a.svg, 0.svg, ä.svg
  - a Unicode code point:    U+00E4.svg  (use this on case-insensitive file systems)
  - a PostScript glyph name: zero.svg, adieresis.svg
The imported outline is scaled to the height of the base glyph and placed on its baseline;
side bearings and anchors of the base glyph are kept. The font family name is the folder name.

The base font should cover all characters of your labels. Accented letters whose base letter
was replaced (ä from a, Ö from O, ...) are composed from the new letter + the base font's
accent, scaled like the letter and centred above (or below) it.
"""
import os
import sys
import unicodedata

import fontforge
import psMat

# combining mark -> spacing accent of the base font; True = placed below the letter
ACCENTS = {
    0x300: (0x60, False), 0x301: (0xB4, False), 0x302: (0x2C6, False), 0x303: (0x2DC, False),
    0x304: (0xAF, False), 0x306: (0x2D8, False), 0x307: (0x2D9, False), 0x308: (0xA8, False),
    0x30A: (0x2DA, False), 0x30B: (0x2DD, False), 0x30C: (0x2C7, False),
    0x327: (0xB8, True), 0x328: (0x2DB, True),
}


def glyph_for(font, stem):
    if len(stem) == 1:
        return font[ord(stem)]
    if stem.upper().startswith("U+"):
        return font[int(stem[2:], 16)]
    return font[stem]


def replace_glyph(glyph, svg_path):
    template_bb = glyph.boundingBox()
    anchors = glyph.anchorPoints
    left_bearing, right_bearing = glyph.left_side_bearing, glyph.right_side_bearing

    glyph.clear()
    for anchor_class_name, anchor_type, x, y in anchors:
        glyph.addAnchorPoint(anchor_class_name, anchor_type, x, y)
    glyph.importOutlines(svg_path)

    imported_bb = glyph.boundingBox()
    imported_height = imported_bb[3] - imported_bb[1]
    template_height = template_bb[3] - template_bb[1]
    if imported_height <= 0 or template_height <= 0:
        raise ValueError("empty outline")

    # centre on the origin, scale to the base glyph's height
    glyph.transform((1, 0, 0, 1, -(imported_bb[0] + imported_bb[2]) / 2, -(imported_bb[1] + imported_bb[3]) / 2))
    scale = template_height / imported_height
    glyph.transform((scale, 0, 0, scale, 0, 0))

    glyph.left_side_bearing = int(left_bearing)
    glyph.right_side_bearing = int(right_bearing)

    # restore the vertical position of the base glyph
    _, y_min, _, _ = glyph.boundingBox()
    glyph.transform((1, 0, 0, 1, 0, template_bb[1] - y_min), ("round",))
    glyph.correctDirection()


def compose_accented(font, replaced, original_sizes):
    """
    Accented letters (Latin-1 / Latin Extended-A) whose base letter was replaced: new outline =
    custom letter + accent, accent scaled by the letter's scale factor, centred on the letter.
    """
    composed = []
    gap = font.em * 0.05
    for codepoint in range(0xC0, 0x180):
        decomposition = unicodedata.decomposition(chr(codepoint)).split()
        if len(decomposition) != 2 or decomposition[0].startswith("<"):
            continue
        base_cp, mark_cp = int(decomposition[0], 16), int(decomposition[1], 16)
        if base_cp not in replaced or mark_cp not in ACCENTS or ACCENTS[mark_cp][0] not in font:
            continue
        accent_cp, below = ACCENTS[mark_cp]
        base = font[base_cp]
        bx0, by0, bx1, by1 = base.boundingBox()
        scale = min(max((bx1 - bx0) / max(original_sizes[base_cp], 1), 0.7), 1.6)

        accent = font[accent_cp].foreground
        accent.transform(psMat.scale(scale))
        ax0, ay0, ax1, ay1 = accent.boundingBox()
        dx = (bx0 + bx1) / 2 - (ax0 + ax1) / 2
        dy = (by0 - gap - ay1) if below else (by1 + gap - ay0)
        accent.transform(psMat.translate(dx, dy))

        outline = base.foreground
        outline += accent
        glyph = font.createChar(codepoint, fontforge.nameFromUnicode(codepoint))
        glyph.clear()
        glyph.foreground = outline
        glyph.width = base.width
        composed.append(chr(codepoint))
    return composed


def build_font(glyph_dir, base_font, out_file):
    family = os.path.basename(os.path.normpath(glyph_dir))
    font = fontforge.open(base_font)
    font.encoding = "UnicodeFull"

    replaced, failed, original_sizes = [], [], {}
    for file in sorted(os.listdir(glyph_dir)):
        if not file.lower().endswith(".svg"):
            continue
        stem = os.path.splitext(file)[0]
        try:
            glyph = glyph_for(font, stem)
            x0, _, x1, _ = glyph.boundingBox()
            replace_glyph(glyph, os.path.join(glyph_dir, file))
            replaced.append(glyph.unicode)
            original_sizes[glyph.unicode] = x1 - x0
        except Exception as e:  # missing glyph in the base font, broken SVG, ...
            failed.append(f"{file} ({e})")

    composed = compose_accented(font, set(replaced), original_sizes)

    font.familyname = family
    font.fullname = f"{family} Regular"
    font.fontname = f"{family}-Regular"
    # plain style info so fontconfig matches the family name exactly
    font.weight = "Regular"
    font.italicangle = 0
    font.os2_weight = 400
    font.os2_width = 5
    font.os2_stylemap = 64
    font.os2_family_class = 0
    font.sfnt_names = ()

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    font.generate(out_file)
    print(f"{family}: {len(replaced)} glyphs replaced, {len(composed)} accented letters composed -> {out_file}")
    for f in failed:
        print(f"  WARNING {family}: could not use {f}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: fontforge -script fontforge_build.py <glyph_dir> <base_font> <out_file>")
    build_font(*sys.argv[1:])

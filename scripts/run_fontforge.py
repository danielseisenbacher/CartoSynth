import fontforge

font = fontforge.open("fonts/base_font/BaseFont.ttf")
g = font["A"]
print(g.boundingBox())
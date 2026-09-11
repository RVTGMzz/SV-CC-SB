#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/Cardcha/assets/airship_props/set02_harbor"
OUT.mkdir(parents=True, exist_ok=True)

# Approved Airship palette: dark outline, warm timber, brass, Cardcha purple,
# parchment, and restrained teal technical light.
INK = (42, 24, 38, 255)
INK2 = (63, 35, 46, 255)
WOOD_DARK = (90, 48, 34, 255)
WOOD = (137, 78, 44, 255)
WOOD_LIGHT = (183, 117, 66, 255)
WOOD_HI = (225, 163, 94, 255)
BRASS_DARK = (123, 78, 25, 255)
BRASS = (205, 145, 46, 255)
BRASS_HI = (247, 204, 91, 255)
PURPLE_DARK = (73, 39, 91, 255)
PURPLE = (112, 58, 135, 255)
PURPLE_HI = (164, 92, 177, 255)
PAPER = (231, 216, 166, 255)
PAPER_SHADE = (194, 171, 120, 255)
TEAL_DARK = (22, 79, 82, 255)
TEAL = (49, 153, 146, 255)
TEAL_HI = (110, 221, 198, 255)
SHADOW = (31, 24, 31, 190)

def save(img: Image.Image, name: str) -> None:
    # Native-resolution production art. Never scale a tiny draft up.
    img.quantize(
        colors=128,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE,
    ).save(OUT / name, optimize=True)

def framed_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=INK)
    draw.rectangle((x0+2, y0+2, x1-2, y1-2), fill=BRASS_DARK)
    draw.rectangle((x0+4, y0+4, x1-4, y1-4), fill=WOOD_DARK)
    draw.rectangle((x0+6, y0+6, x1-6, y1-6), fill=WOOD)
    draw.line((x0+7, y0+7, x1-7, y0+7), fill=WOOD_LIGHT, width=2)
    for x, y in ((x0+3, y0+3), (x1-3, y0+3), (x0+3, y1-3), (x1-3, y1-3)):
        draw.rectangle((x-1, y-1, x+1, y+1), fill=BRASS_HI)

# 1) Departures schedule board, 6x4 tiles.
img = Image.new("RGBA", (96, 64), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rectangle((6, 56, 89, 61), fill=SHADOW)
framed_panel(d, (4, 3, 91, 57))
# Purple Cardcha crest/header.
d.rectangle((10, 9, 85, 19), fill=PURPLE_DARK)
d.rectangle((12, 10, 83, 17), fill=PURPLE)
d.line((13, 11, 82, 11), fill=PURPLE_HI, width=1)
# Stylized card/wing emblem.
d.polygon([(47, 11), (51, 14), (47, 17), (43, 14)], fill=BRASS_HI)
d.rectangle((46, 12, 48, 16), fill=PAPER)
# Three readable schedule bands.
rows = [(24, TEAL), (34, BRASS_HI), (44, TEAL_HI)]
for i, (y, lamp) in enumerate(rows):
    d.rectangle((11, y, 83, y+7), fill=INK2)
    d.rectangle((13, y+1, 31, y+5), fill=PAPER_SHADE)
    d.rectangle((34, y+1, 69, y+2), fill=PAPER)
    d.rectangle((34, y+4, 59 - i*3, y+5), fill=WOOD_HI)
    d.rectangle((75, y+1, 80, y+5), fill=TEAL_DARK)
    d.rectangle((76, y+2, 79, y+4), fill=lamp)
# Brass lower lip and small hanging tag.
d.rectangle((9, 53, 86, 56), fill=BRASS_DARK)
d.line((12, 53, 83, 53), fill=BRASS_HI, width=1)
d.rectangle((43, 56, 52, 60), fill=INK)
d.rectangle((45, 56, 50, 59), fill=PAPER_SHADE)
save(img, "departures_schedule_board.png")

# 2) Waiting bench, 6x3 tiles.
img = Image.new("RGBA", (96, 48), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rectangle((7, 42, 89, 46), fill=SHADOW)
# Back frame.
d.rectangle((5, 7, 90, 12), fill=INK)
d.rectangle((7, 8, 88, 10), fill=BRASS_DARK)
for x in (9, 31, 53, 75, 87):
    d.rectangle((x, 11, x+3, 28), fill=INK)
    d.rectangle((x+1, 12, x+2, 27), fill=WOOD_LIGHT)
# Purple padded back and seat.
for x0, x1 in ((13, 31), (34, 52), (55, 73), (76, 86)):
    d.rectangle((x0, 13, x1, 25), fill=PURPLE_DARK)
    d.rectangle((x0+2, 14, x1-1, 23), fill=PURPLE)
    d.line((x0+3, 15, x1-2, 15), fill=PURPLE_HI, width=1)
d.rectangle((7, 27, 89, 36), fill=INK)
d.rectangle((9, 28, 87, 34), fill=PURPLE_DARK)
d.rectangle((11, 29, 85, 32), fill=PURPLE)
d.line((12, 29, 84, 29), fill=PURPLE_HI, width=1)
# Wood/brass base and legs.
d.rectangle((6, 35, 90, 39), fill=WOOD_DARK)
d.rectangle((8, 35, 88, 36), fill=WOOD_HI)
for x in (10, 27, 68, 85):
    d.rectangle((x, 38, x+4, 44), fill=INK)
    d.rectangle((x+1, 38, x+3, 42), fill=BRASS)
    d.rectangle((x+1, 43, x+4, 44), fill=BRASS_HI)
save(img, "waiting_bench.png")

# 3) Luggage cart, 4x4 tiles.
img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.ellipse((5, 57, 59, 63), fill=SHADOW)
# Tall brass cart frame.
d.rectangle((9, 7, 13, 54), fill=INK)
d.rectangle((10, 8, 12, 52), fill=BRASS)
d.rectangle((50, 7, 54, 54), fill=INK)
d.rectangle((51, 8, 53, 52), fill=BRASS)
d.rectangle((11, 6, 52, 10), fill=INK)
d.rectangle((13, 7, 50, 8), fill=BRASS_HI)
# Handle curls.
d.arc((5, 4, 18, 18), 160, 300, fill=BRASS_HI, width=2)
d.arc((46, 4, 59, 18), 240, 20, fill=BRASS_HI, width=2)
# Back luggage.
d.rectangle((16, 20, 45, 44), fill=INK)
d.rectangle((18, 21, 43, 42), fill=WOOD_DARK)
d.rectangle((20, 23, 41, 40), fill=WOOD)
d.rectangle((27, 18, 34, 23), fill=INK)
d.rectangle((28, 19, 33, 22), fill=BRASS)
d.rectangle((19, 29, 42, 32), fill=BRASS_DARK)
d.rectangle((29, 29, 31, 32), fill=BRASS_HI)
# Purple travel bag in front.
d.rectangle((12, 34, 35, 51), fill=INK)
d.rectangle((14, 35, 33, 49), fill=PURPLE_DARK)
d.rectangle((16, 36, 31, 47), fill=PURPLE)
d.line((17, 37, 30, 37), fill=PURPLE_HI, width=1)
d.rectangle((20, 31, 27, 35), fill=INK)
d.rectangle((21, 32, 26, 34), fill=BRASS)
# Teal tag.
d.rectangle((36, 34, 47, 45), fill=TEAL_DARK)
d.rectangle((38, 36, 45, 42), fill=TEAL)
d.rectangle((40, 37, 43, 39), fill=TEAL_HI)
# Cart base and wheels.
d.rectangle((7, 51, 56, 56), fill=INK)
d.rectangle((9, 52, 54, 54), fill=WOOD_LIGHT)
d.rectangle((12, 55, 50, 57), fill=BRASS_DARK)
for x in (13, 45):
    d.ellipse((x, 54, x+8, 62), fill=INK)
    d.ellipse((x+2, 56, x+6, 60), fill=BRASS)
    d.point((x+4, 58), fill=BRASS_HI)
save(img, "luggage_cart.png")

manifest = {
    "version": "0691-set02-harbor",
    "staticPhysicalOwner": "TMX map layers",
    "runtimeOverlays": [],
    "design": "native-resolution layered Stardew-style harbor furnishings",
    "props": {
        "departures_schedule_board": [96, 64],
        "waiting_bench": [96, 48],
        "luggage_cart": [64, 64],
    },
}
(OUT / "set02_harbor_manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)
print("0691 Set02 Harbor furnishings materialized:", OUT)

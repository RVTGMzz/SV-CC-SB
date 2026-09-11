#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/Cardcha/assets"
SOURCE = ASSETS / "airship_props/density_0693"
PAIRS = {
    "sky_dock_density_0693.png": "airship_0693_sky_dock_density.png",
    "airship_deck_density_0693.png": "airship_0693_deck_density.png",
}
for src_name,dst_name in PAIRS.items():
    src=SOURCE/src_name
    dst=ASSETS/dst_name
    im=Image.open(src).convert("RGBA")
    im.save(dst,optimize=True,compress_level=9)
print("0693 flat RGBA TMX density textures materialized")

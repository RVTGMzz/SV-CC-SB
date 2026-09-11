#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import struct
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.60"
BRANCH = "cardcha-alpha28-0693-airship-interior-density-rebuild"


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"0693 validation FAIL: {msg}")


def png_info(path: Path) -> tuple[int,int,int]:
    raw = path.read_bytes()
    require(raw[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} not PNG")
    w,h = struct.unpack(">II", raw[16:24])
    return w,h,raw[25]


def vals(root: ET.Element, layer_name: str) -> list[int]:
    layer = next((x for x in root.findall("layer") if x.attrib.get("name") == layer_name), None)
    require(layer is not None, f"missing layer {layer_name}")
    data = layer.find("data")
    require(data is not None and data.attrib.get("encoding") == "csv", f"{layer_name} not CSV")
    out = [int(x.strip()) for x in (data.text or "").split(",") if x.strip()]
    require(len(out) == int(root.attrib["width"]) * int(root.attrib["height"]), f"{layer_name} wrong tile count")
    return out

for rel in ["manifest.json","Cardcha.csproj","Directory.Build.targets"]:
    require(VERSION in (SRC/rel).read_text(encoding="utf-8"), f"{rel} version")

asset_root = SRC / "assets/airship_props/density_0693"
for name,size in [("sky_dock_density_0693.png",(480,288)),("airship_deck_density_0693.png",(384,224))]:
    w,h,color_type = png_info(asset_root/name)
    require((w,h)==size, f"{name} size {(w,h)} != {size}")
    require(color_type == 6, f"{name} must be true RGBA PNG color type 6, got {color_type}")

# Sky Dock composition + protected spine.
dock = ET.parse(SRC/"assets/sky_dock_interior.tmx").getroot()
require((int(dock.attrib["width"]),int(dock.attrib["height"]))==(30,18),"dock dimensions")
dock_sets={x.attrib.get("name"):x for x in dock.findall("tileset")}
require("CardchaSkyDockDensity0693" in dock_sets,"dock density tileset missing")
require(dock_sets["CardchaSkyDockDensity0693"].find("image").attrib.get("source")=="airship_props/density_0693/sky_dock_density_0693.png","dock density source")
dock_back=vals(dock,"BackDecor"); dock_build=vals(dock,"Buildings")
require(sum(5800 <= v <= 6339 for v in dock_back) >= 65,"dock density coverage too sparse")
require(not any(5000 <= v <= 5024 for v in dock_back),"rejected old route-board cluster still active")
require(not any(5300 <= v <= 5308 for v in dock_back),"old crate cluster still active")
require(not any(5500 <= v <= 5799 for v in dock_back),"old sparse Set02 GIDs still active")
require(any(5100 <= v <= 5141 for v in dock_back),"authored boarding gate missing")
require(any(5200 <= v <= 5205 for v in dock_back),"dock signal lamp missing")
for y in range(7,18):
    for x in range(14,17):
        require(dock_build[y*30+x] != 5400, f"dock center spine blocked at {x},{y}")
for x,y in [(7,7),(23,8),(5,11),(15,16),(15,14)]:
    require(dock_build[y*30+x] != 5400, f"dock interaction/arrival tile blocked at {x},{y}")

# Deck composition + hero props + upgrade sockets.
deck = ET.parse(SRC/"assets/airship_deck.tmx").getroot()
require((int(deck.attrib["width"]),int(deck.attrib["height"]))==(24,14),"deck dimensions")
deck_sets={x.attrib.get("name"):x for x in deck.findall("tileset")}
require("CardchaAirshipDeckDensity0693" in deck_sets,"deck density tileset missing")
require(deck_sets["CardchaAirshipDeckDensity0693"].find("image").attrib.get("source")=="airship_props/density_0693/airship_deck_density_0693.png","deck density source")
deck_back=vals(deck,"BackDecor"); deck_build=vals(deck,"Buildings")
require(sum(5800 <= v <= 6135 for v in deck_back) >= 50,"deck density coverage too sparse")
require(any(5000 <= v <= 5049 for v in deck_back),"Observation Window missing")
require(any(5100 <= v <= 5134 for v in deck_back),"Navigation Console missing")
require(sum(5200 <= v <= 5205 for v in deck_back) >= 2,"deck signal lamps missing")
for x,y in [(4,8),(19,8),(7,11),(16,11),(12,12),(12,6)]:
    require(deck_build[y*24+x] != 5400, f"deck gameplay anchor blocked at {x},{y}")

renderer=(SRC/"Services/AirshipInteriorStardewRenderer.cs").read_text(encoding="utf-8")
require("DrawDeckStardewDecor(batch);" not in renderer,"physical deck runtime decor was re-enabled")
require("DrawDockStardewDecor(batch);" not in renderer,"physical dock runtime decor was re-enabled")
require("Draw0690WindowOverlay(batch);" in renderer and "Draw0690ConsoleOverlay(batch);" in renderer,"0690 hero motion overlay lost")

audit=json.loads((ROOT/"render_depth_audit.json").read_text(encoding="utf-8"))
require(audit.get("branch")==BRANCH,"render_depth_audit branch")
text=json.dumps(audit)
require("0693 Airship dense physical interior scene->TMX; runtime remains VFX-only" in text,"0693 depth migration marker")

latest=(ROOT/"handoff/LATEST_CARDCHA_HANDOFF.md").read_text(encoding="utf-8")
handoff=(ROOT/"handoff/ALPHA28_0693_AIRSHIP_INTERIOR_DENSITY_REBUILD.md").read_text(encoding="utf-8")
require(BRANCH in latest and VERSION in latest,"latest handoff current")
require("In-game visual acceptance remains PENDING" in handoff,"handoff acceptance state")

print("0693 Airship interior density validation PASS")

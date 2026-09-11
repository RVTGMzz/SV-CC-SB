#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.59"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.60"
BRANCH = "cardcha-alpha28-0693-airship-interior-density-rebuild"
PARENT_BRANCH = "cardcha-alpha28-0692-airship-rgba-gate-restore"
PARENT_HEAD = "18eef43802d9261b287fab06258daa78526940a5"

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = SRC / rel
    if p.exists():
        write(p, read(p).replace(OLD_VERSION, NEW_VERSION))

def csv_values(layer: ET.Element) -> list[int]:
    data = layer.find("data")
    if data is None or data.attrib.get("encoding") != "csv":
        raise RuntimeError(f"layer {layer.attrib.get('name')} is not CSV")
    toks = [x.strip() for x in (data.text or "").split(",")]
    if not toks or any(x == "" for x in toks):
        raise RuntimeError(f"empty CSV token in layer {layer.attrib.get('name')}")
    return [int(x) for x in toks]

def set_csv(layer: ET.Element, vals: list[int]) -> None:
    data = layer.find("data"); assert data is not None
    data.text = "\n" + ",".join(str(x) for x in vals) + "\n"

def get_layer(root: ET.Element, name: str) -> ET.Element:
    for layer in root.findall("layer"):
        if layer.attrib.get("name") == name:
            return layer
    raise RuntimeError(f"missing layer {name}")

def remove_tileset(root: ET.Element, name: str) -> None:
    for ts in list(root.findall("tileset")):
        if ts.attrib.get("name") == name:
            root.remove(ts)

def add_tileset(root: ET.Element, firstgid: int, name: str, source: str, width: int, height: int) -> None:
    remove_tileset(root, name)
    ts = ET.Element("tileset", {
        "firstgid": str(firstgid), "name": name, "tilewidth": "16", "tileheight": "16",
        "tilecount": str((width // 16) * (height // 16)), "columns": str(width // 16),
    })
    ET.SubElement(ts, "image", {"source": source, "width": str(width), "height": str(height)})
    children = list(root)
    layer_index = next((i for i,c in enumerate(children) if c.tag == "layer"), len(children))
    root.insert(layer_index, ts)

def blit_asset(root: ET.Element, layer_name: str, firstgid: int, asset: Path, x: int, y: int) -> None:
    im = Image.open(asset).convert("RGBA")
    if im.width % 16 or im.height % 16:
        raise RuntimeError(f"{asset.name} must align to 16px TMX grid")
    cols, rows = im.width // 16, im.height // 16
    mw, mh = int(root.attrib["width"]), int(root.attrib["height"])
    layer = get_layer(root, layer_name); vals = csv_values(layer)
    for ty in range(rows):
        for tx in range(cols):
            tile = im.crop((tx*16,ty*16,tx*16+16,ty*16+16))
            if tile.getchannel("A").getbbox() is None:
                continue
            mx,my=x+tx,y+ty
            if not (0 <= mx < mw and 0 <= my < mh):
                raise RuntimeError(f"{asset.name} outside map at {mx},{my}")
            vals[my*mw+mx] = firstgid + ty*cols + tx
    set_csv(layer, vals)

def clear_ranges(root: ET.Element, layer_name: str, ranges: list[tuple[int,int]]) -> None:
    layer=get_layer(root,layer_name); vals=csv_values(layer)
    for i,v in enumerate(vals):
        if any(lo <= v <= hi for lo,hi in ranges): vals[i]=0
    set_csv(layer,vals)

def clear_gid(root: ET.Element, layer_name: str, gid: int) -> None:
    layer=get_layer(root,layer_name); vals=csv_values(layer)
    vals=[0 if v == gid else v for v in vals]
    set_csv(layer,vals)

def add_blockers(root: ET.Element, blocker_gid: int, cells: list[tuple[int,int]]) -> None:
    mw,mh=int(root.attrib["width"]),int(root.attrib["height"])
    layer=get_layer(root,"Buildings"); vals=csv_values(layer)
    for x,y in cells:
        if not (0 <= x < mw and 0 <= y < mh): raise RuntimeError(f"blocker outside map {x},{y}")
        idx=y*mw+x
        if vals[idx] == 0: vals[idx]=blocker_gid
    set_csv(layer,vals)

def set_property(root: ET.Element, name: str, value: str) -> None:
    props=root.find("properties")
    if props is None:
        props=ET.Element("properties"); root.insert(0,props)
    for p in props.findall("property"):
        if p.attrib.get("name") == name:
            p.set("value",value); return
    ET.SubElement(props,"property",{"name":name,"value":value})

DENSITY = SRC / "assets/airship_props/density_0693"

# SKY DOCK: replace sparse prototype grouping with one authored dense scene layer,
# then restore the hero gate + signal lamp on top. Central x=14..16 stays visually open.
dock_path = SRC / "assets/sky_dock_interior.tmx"
dock = ET.parse(dock_path); r=dock.getroot()
add_tileset(r,5800,"CardchaSkyDockDensity0693","airship_props/density_0693/sky_dock_density_0693.png",480,288)
clear_ranges(r,"BackDecor",[(5000,5024),(5300,5308),(5500,5799),(5800,6339)])
blit_asset(r,"BackDecor",5800,DENSITY/"sky_dock_density_0693.png",0,0)
blit_asset(r,"BackDecor",5100,SRC/"assets/airship_0692_boarding_gate_arch.png",20,3)
blit_asset(r,"BackDecor",5200,SRC/"assets/airship_0692_signal_lamp.png",17,4)
clear_gid(r,"Buildings",5400)
dock_blockers=[]
dock_blockers += [(20,y) for y in range(5,9)] + [(26,y) for y in range(5,9)]
dock_blockers += [(x,y) for y in range(9,12) for x in range(2,11)]
dock_blockers += [(x,y) for y in (15,16) for x in range(1,8)]
dock_blockers += [(x,y) for y in (14,15,16) for x in range(24,29)]
add_blockers(r,5400,dock_blockers)
set_property(r,"CardchaInteriorDensity","0693|dense-harbor-scene|service-left|boarding-right|center-spine-open")
ET.indent(dock,space=" "); dock.write(dock_path,encoding="UTF-8",xml_declaration=True)

# AIRSHIP DECK: the observation window + navigation console stay the two hero props.
# Density furniture lives at wall/corner edges and leaves all four upgrade sockets + lower exit usable.
deck_path = SRC / "assets/airship_deck.tmx"
deck = ET.parse(deck_path); r=deck.getroot()
add_tileset(r,5800,"CardchaAirshipDeckDensity0693","airship_props/density_0693/airship_deck_density_0693.png",384,224)
clear_ranges(r,"BackDecor",[(5800,6135)])
blit_asset(r,"BackDecor",5800,DENSITY/"airship_deck_density_0693.png",0,0)
blit_asset(r,"BackDecor",5000,SRC/"assets/airship_0692_observation_window.png",7,1)
blit_asset(r,"BackDecor",5100,SRC/"assets/airship_0692_navigation_console.png",9,5)
blit_asset(r,"BackDecor",5200,SRC/"assets/airship_0692_signal_lamp.png",4,4)
blit_asset(r,"BackDecor",5200,SRC/"assets/airship_0692_signal_lamp.png",18,4)
clear_gid(r,"Buildings",5400)
deck_blockers=[]
deck_blockers += [(x,y) for y in (8,9) for x in range(9,16)]
deck_blockers += [(x,y) for y in (6,7) for x in range(1,6)]
deck_blockers += [(x,y) for y in (5,6) for x in range(19,23)]
deck_blockers += [(x,y) for y in (11,12) for x in range(1,4)]
deck_blockers += [(x,y) for y in (11,12) for x in range(20,23)]
add_blockers(r,5400,deck_blockers)
set_property(r,"CardchaInteriorDensity","0693|lived-in-deck|books|telescope|tea|gramophone|rug|hero-props-preserved")
ET.indent(deck,space=" "); deck.write(deck_path,encoding="UTF-8",xml_declaration=True)

audit_path = ROOT / "render_depth_audit.json"
audit = json.loads(read(audit_path)); audit["branch"] = BRANCH
done = audit.setdefault("completedDepthMigrations",[])
marker = "0693 Airship dense physical interior scene->TMX; runtime remains VFX-only"
if marker not in done: done.append(marker)
write(audit_path,json.dumps(audit,indent=2)+"\n")

handoff = ROOT / "handoff/ALPHA28_0693_AIRSHIP_INTERIOR_DENSITY_REBUILD.md"
handoff.write_text(f'''# Alpha 28 0693 — Airship Interior Density Rebuild

## Source of truth
- Branch: `{BRANCH}`
- Parent: `{PARENT_BRANCH}` @ `{PARENT_HEAD}`
- Build: `{NEW_VERSION}`

## Trigger
Ron tested the Airship rooms and reported that the approved concept felt rich, but the actual rooms still read as almost empty. The issue was structural: old runtime decor was removed for rendering-depth safety, while only a small subset of replacements had been migrated into TMX.

## 0693 change
This pass restores room-level composition as map-native art instead of turning the old runtime physical renderer back on.

### Sky Dock
- dense departures/service board cluster;
- substantial harbor desk / route service area;
- waiting nook with seating, lamp, plants and side table;
- luggage/boarding cluster;
- existing 0692 authored boarding gate retained;
- center x=14..16 arrival/exit spine remains open.

### Airship Deck
- existing Observation Window and Navigation Console remain hero props;
- bookshelf/work library on left wall;
- telescope observation corner on right wall;
- tea cart and gramophone corner props;
- central Cardcha rug and extra plants/clock detail;
- all four upgrade sockets and lower doorway remain reachable.

## Rendering contract
- New physical density art is generated directly at full map-native resolution: Dock 480x288 and Deck 384x224.
- No tiny source sprite is enlarged to fake detail.
- Physical art is owned by TMX `BackDecor` + native collision.
- `DrawDeckStardewDecor()` / `DrawDockStardewDecor()` remain unused; they are not re-enabled.
- Existing 0690 window/console moving pixels remain VFX-only.
- Existing 0692 exterior gate farmer-depth fix is frozen.

## Acceptance
CI/compile/package validation is required. In-game visual acceptance remains PENDING until Ron tests the 0693 TEST package.
''',encoding="utf-8")

latest = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"
latest.write_text(f'''# Latest Cardcha Handoff

Current source-of-truth branch: `{BRANCH}`

Current build: `{NEW_VERSION}`

Current handoff: `handoff/ALPHA28_0693_AIRSHIP_INTERIOR_DENSITY_REBUILD.md`

Parent source-of-truth: `{PARENT_BRANCH}` @ `{PARENT_HEAD}`

Status: Airship room-density rebuild materialized by 0693 workflow; in-game visual acceptance remains PENDING until Ron tests.
''',encoding="utf-8")

print("0693 Airship interior density rebuild materialized")

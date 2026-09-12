#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
BLUEPRINT = ROOT / "handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.61"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.62"
BRANCH = "cardcha-alpha28-0696-airship-concept-faithful-visible-integration"
TILE = 16

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

def csv_values(layer: ET.Element) -> list[int]:
    data = layer.find("data")
    if data is None or data.attrib.get("encoding") != "csv":
        raise RuntimeError(f"layer {layer.attrib.get('name')} is not CSV")
    tokens = [x.strip() for x in (data.text or "").split(",") if x.strip()]
    vals = [int(x) for x in tokens]
    expected = int(layer.attrib["width"]) * int(layer.attrib["height"])
    if len(vals) != expected:
        raise RuntimeError(f"layer {layer.attrib.get('name')} has {len(vals)} cells, expected {expected}")
    return vals

def set_csv(layer: ET.Element, vals: list[int]) -> None:
    data = layer.find("data")
    if data is None:
        data = ET.SubElement(layer, "data", {"encoding": "csv"})
    data.text = "\n" + ",".join(str(v) for v in vals) + "\n"

def get_layer(root: ET.Element, name: str) -> ET.Element | None:
    return next((layer for layer in root.findall("layer") if layer.attrib.get("name") == name), None)

def ensure_layer(root: ET.Element, name: str, after: str) -> ET.Element:
    existing = get_layer(root, name)
    if existing is not None:
        return existing
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    ids = [int(x.attrib.get("id", "0")) for x in root.findall("layer")]
    layer_id = max(ids or [0]) + 1
    layer = ET.Element("layer", {"id": str(layer_id), "name": name, "width": str(w), "height": str(h)})
    data = ET.SubElement(layer, "data", {"encoding": "csv"})
    data.text = "\n" + ",".join("0" for _ in range(w * h)) + "\n"
    children = list(root)
    anchor_index = next((i for i, child in enumerate(children) if child.tag == "layer" and child.attrib.get("name") == after), None)
    if anchor_index is None:
        root.append(layer)
    else:
        root.insert(anchor_index + 1, layer)
    root.set("nextlayerid", str(max(int(root.attrib.get("nextlayerid", "1")), layer_id + 1)))
    return layer

def remove_layer(root: ET.Element, name: str) -> None:
    layer = get_layer(root, name)
    if layer is not None:
        root.remove(layer)

def set_property(root: ET.Element, name: str, value: str) -> None:
    props = root.find("properties")
    if props is None:
        props = ET.Element("properties")
        root.insert(0, props)
    for prop in props.findall("property"):
        if prop.attrib.get("name") == name:
            prop.set("value", value)
            return
    ET.SubElement(props, "property", {"name": name, "value": value})

def remove_tileset(root: ET.Element, name: str) -> None:
    for ts in list(root.findall("tileset")):
        if ts.attrib.get("name") == name:
            root.remove(ts)

def ensure_tileset(root: ET.Element, firstgid: int, name: str, source: str, width: int, height: int, blocker: bool = False) -> None:
    ts = next((x for x in root.findall("tileset") if x.attrib.get("name") == name), None)
    if ts is None:
        ts = ET.Element("tileset")
        children = list(root)
        layer_index = next((i for i, child in enumerate(children) if child.tag == "layer"), len(children))
        root.insert(layer_index, ts)
    ts.attrib.clear()
    ts.attrib.update({
        "firstgid": str(firstgid),
        "name": name,
        "tilewidth": str(TILE),
        "tileheight": str(TILE),
        "tilecount": str((width // TILE) * (height // TILE)),
        "columns": str(width // TILE),
    })
    for child in list(ts):
        ts.remove(child)
    ET.SubElement(ts, "image", {"source": source, "width": str(width), "height": str(height)})
    if blocker:
        tile = ET.SubElement(ts, "tile", {"id": "0"})
        props = ET.SubElement(tile, "properties")
        ET.SubElement(props, "property", {"name": "Passable", "value": "F"})

def clear_gid_range(root: ET.Element, lo: int, hi: int) -> None:
    for layer in root.findall("layer"):
        vals = csv_values(layer)
        changed = False
        for i, value in enumerate(vals):
            if lo <= value <= hi:
                vals[i] = 0
                changed = True
        if changed:
            set_csv(layer, vals)

def alpha_occupied(path: Path) -> set[tuple[int, int]]:
    im = Image.open(path).convert("RGBA")
    if im.width % TILE or im.height % TILE:
        raise RuntimeError(f"{path} must be 16px-grid aligned")
    alpha = im.getchannel("A")
    out = set()
    for ty in range(im.height // TILE):
        for tx in range(im.width // TILE):
            if alpha.crop((tx*TILE, ty*TILE, (tx+1)*TILE, (ty+1)*TILE)).getbbox() is not None:
                out.add((tx, ty))
    return out

def place_prop(root: ET.Element, prop: dict) -> None:
    asset = ROOT / prop["asset"]
    im = Image.open(asset).convert("RGBA")
    cols, rows = im.width // TILE, im.height // TILE
    expected = prop["footprint_tiles"]
    if [cols, rows] != expected:
        raise RuntimeError(f"{prop['id']} footprint drift: file={cols}x{rows}, blueprint={expected}")
    occupied = alpha_occupied(asset)
    ax, ay = prop["anchor"]
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    assigned_rows = {}
    for visual_slice in prop["visual_slices"]:
        layer_name = visual_slice["layer"]
        y0, y1 = visual_slice["rows"]
        layer = get_layer(root, layer_name)
        if layer is None:
            raise RuntimeError(f"{prop['id']} missing target layer {layer_name}")
        vals = csv_values(layer)
        for ty in range(y0, y1 + 1):
            if ty in assigned_rows:
                raise RuntimeError(f"{prop['id']} source row {ty} assigned twice")
            assigned_rows[ty] = layer_name
            for tx in range(cols):
                if (tx, ty) not in occupied:
                    continue
                mx, my = ax + tx, ay + ty
                if not (0 <= mx < w and 0 <= my < h):
                    raise RuntimeError(f"{prop['id']} outside map at {mx},{my}")
                vals[my*w + mx] = prop["firstgid"] + ty*cols + tx
        set_csv(layer, vals)
    missing_rows = sorted(set(range(rows)) - set(assigned_rows))
    if missing_rows:
        raise RuntimeError(f"{prop['id']} visual rows not assigned: {missing_rows}")

def expand_rects(rects: list[list[int]]) -> set[tuple[int, int]]:
    out = set()
    for x, y, w, h in rects:
        for yy in range(y, y+h):
            for xx in range(x, x+w):
                out.add((xx, yy))
    return out

def restore_collision(root: ET.Element, props: list[dict], blocker_gid: int = 5400) -> None:
    buildings = get_layer(root, "Buildings")
    if buildings is None:
        raise RuntimeError("Buildings layer missing")
    vals = csv_values(buildings)
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    vals = [0 if v == blocker_gid else v for v in vals]
    cells = set()
    for prop in props:
        cells |= expand_rects(prop.get("collision_rects", []))
    for x, y in sorted(cells):
        if not (0 <= x < w and 0 <= y < h):
            raise RuntimeError(f"collision outside map: {x},{y}")
        idx = y*w + x
        if vals[idx] != 0:
            continue
        vals[idx] = blocker_gid
    set_csv(buildings, vals)

def configure_room(room_name: str, room: dict) -> None:
    map_path = ROOT / room["map"]
    tree = ET.parse(map_path)
    root = tree.getroot()
    if [int(root.attrib["width"]), int(root.attrib["height"])] != room["dimensions_tiles"]:
        raise RuntimeError(f"{room_name} map dimensions drifted")

    remove_layer(root, "BackDecor")
    ensure_layer(root, "Back2", "Back")
    ensure_layer(root, "Buildings2", "Buildings")
    ensure_layer(root, "Front2", "Front")

    density_name = "CardchaAirshipDeckDensity0693" if room_name == "deck" else "CardchaSkyDockDensity0693"
    remove_tileset(root, density_name)
    clear_gid_range(root, 5800, 6999)

    unique_props = {}
    for prop in room["props"]:
        unique_props.setdefault(prop["tileset_name"], prop)
    for prop in unique_props.values():
        asset = ROOT / prop["asset"]
        im = Image.open(asset)
        source = str(Path(prop["asset"]).relative_to("src/Cardcha/assets")).replace("\\", "/")
        ensure_tileset(root, prop["firstgid"], prop["tileset_name"], source, im.width, im.height)

    ensure_tileset(root, 5400, "CardchaCollision0690", "airship_props/set01_redux/collision_blocker.png", 16, 16, blocker=True)

    seen = set()
    for prop in room["props"]:
        key = (prop["firstgid"], prop["footprint_tiles"][0] * prop["footprint_tiles"][1])
        if key in seen:
            continue
        seen.add(key)
        clear_gid_range(root, key[0], key[0] + key[1] - 1)
    clear_gid_range(root, 5400, 5400)

    for prop in room["props"]:
        place_prop(root, prop)
    restore_collision(root, room["props"])

    set_property(root, "CardchaAirshipVersion", NEW_VERSION)
    set_property(root, "CardchaTextureContract", "0696A|exact-separated-sprites|supported-suffix-layers|base-Buildings-collision")
    set_property(root, "CardchaInteriorDensity", "0696A|repo-recovered-approved-props|external-source-pack-pending")
    set_property(root, "CardchaVisualAcceptance", "PENDING-RON-IN-GAME")
    set_property(root, "CardchaBackDecorPolicy", "deprecated-removed|do-not-use-for-production-physical-art")
    set_property(root, "CardchaSourceBlueprint", "handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json")

    ET.indent(tree, space=" ")
    tree.write(map_path, encoding="UTF-8", xml_declaration=True)

def update_versions() -> None:
    for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
        path = SRC / rel
        if path.exists():
            text = read(path).replace(OLD_VERSION, NEW_VERSION)
            text = text.replace("0695 REGION I ENVIRONMENT PROP INTEGRATION TEST", "0696A AIRSHIP VISIBLE ARCHITECTURE RECOVERY TEST")
            write(path, text)

def update_service_markers() -> None:
    path = SRC / "Services/AirshipFoundationService.cs"
    text = read(path)
    text, n1 = re.subn(r'InteriorDecorVersion \+ "-069\d+-bridge"', 'InteriorDecorVersion + "-0696-bridge"', text)
    text, n2 = re.subn(r'InteriorDecorVersion \+ "-069\d+-dock"', 'InteriorDecorVersion + "-0696-dock"', text)
    if n1 < 1 or n2 < 1:
        raise RuntimeError(f"could not update Airship decor markers: bridge={n1}, dock={n2}")
    text = text.replace("// 0690: physical bridge furnishings are authored into airship_deck.tmx.", "// 0696A: exact approved bridge props are authored into runtime-supported TMX layers.")
    text = text.replace("// 0691: physical dock furnishings, including Set02 Harbor, are authored into sky_dock_interior.tmx.", "// 0696A: exact approved dock props are authored into runtime-supported TMX layers.")
    write(path, text)

def update_render_audit() -> None:
    path = ROOT / "render_depth_audit.json"
    data = json.loads(read(path))
    data["branch"] = BRANCH
    done = data.setdefault("completedDepthMigrations", [])
    marker = "0696A Airship approved Set01+Set02 physical art->supported TMX suffix layers; collision->base Buildings; BackDecor retired"
    if marker not in done:
        done.append(marker)
    write(path, json.dumps(data, indent=2) + "\n")

def update_handoff() -> None:
    handoff = ROOT / "handoff/ALPHA28_0696A_AIRSHIP_VISIBLE_ARCHITECTURE_RECOVERY.md"
    handoff.write_text(f'''# Alpha 28 / 0696A — Airship Visible Architecture Recovery

## Status
- Branch: `{BRANCH}`
- Build: `{NEW_VERSION}`
- Technical scope: repo-recovered approved Set01 + Set02 physical art only
- Visual acceptance: **PENDING-RON-IN-GAME**
- Full 0696 composition: **WIP / external source pack still pending**

## What 0696A fixes
- removes production dependence on custom `BackDecor`;
- removes the rejected 0693 full-room density atlas from active map placement;
- points production tilesets back to the exact separated approved source PNGs already present in repo;
- restores complete native-size footprints at their approved historical anchors;
- uses `Buildings2` for nonblocking physical art behind actors;
- uses `Front2` only for upper depth/occlusion slices;
- keeps gameplay collision on base `Buildings` through the transparent collision primitive;
- preserves the boarding-gate center opening and Sky Dock x=14..16 travel spine;
- keeps Observation Window / Navigation Console runtime overlays VFX-only.

## Source gap
The previous session recorded `concept(1).rar` (6 PNGs) and `sprite(1).rar` (22 PNGs), but those exact external source packs are not recoverable from the repo. 0696A does not invent replacements. Missing approved library/telescope/rug/service-detail zones remain explicitly pending in `handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json`.

## Acceptance rule
This build can prove the rendering architecture and exact recovered prop footprints. It **cannot** be called the final 0696 visual pass until Ron tests it in game and the missing approved source pack is restored for the remaining composition.
''', encoding="utf-8")

    latest = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"
    latest.write_text(f'''# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
Continue on:
`{BRANCH}`

Current recovery handoff:
`handoff/ALPHA28_0696A_AIRSHIP_VISIBLE_ARCHITECTURE_RECOVERY.md`

Authoritative blueprint:
`handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json`

Authoritative repo-source inventory:
`handoff/AIRSHIP_SOURCE_PACK_0696.json`

## Status
- 0696A runtime-visible architecture recovery: materialized/validated by its workflow
- 0696 full Airship composition: **WIP**
- visual acceptance: **PENDING-RON-IN-GAME**
- external source gap: `concept(1).rar` 6 PNGs + `sprite(1).rar` 22 PNGs are not recoverable from repo

## Non-negotiable continuation rule
Do not redraw, shrink, or silently substitute the missing approved source sprites. Continue source-first when the exact source pack becomes available. Technical PASS never changes visual acceptance without Ron's in-game confirmation.

0695 remains the last pre-0696 production baseline:
`cardcha-alpha28-0695-region1-prop-integration`
''', encoding="utf-8")

def main() -> None:
    bp = json.loads(BLUEPRINT.read_text(encoding="utf-8"))
    update_versions()
    for room_name, room in bp["rooms"].items():
        configure_room(room_name, room)
    update_service_markers()
    update_render_audit()
    update_handoff()
    print(f"0696A Airship visible architecture recovery materialized: {NEW_VERSION}")

if __name__ == "__main__":
    main()

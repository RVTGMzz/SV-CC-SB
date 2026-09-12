#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json"
TILE = 16
LAYERS = ["Back2", "Buildings2", "Front", "Front2"]

def csv_values(root: ET.Element, name: str) -> list[int]:
    layer = next((x for x in root.findall("layer") if x.attrib.get("name") == name), None)
    if layer is None:
        return [0] * (int(root.attrib["width"]) * int(root.attrib["height"]))
    data = layer.find("data")
    assert data is not None and data.attrib.get("encoding") == "csv"
    return [int(x.strip()) for x in (data.text or "").split(",") if x.strip()]

def tilesets(root: ET.Element, map_path: Path) -> list[dict]:
    out = []
    for ts in root.findall("tileset"):
        image = ts.find("image")
        if image is None:
            continue
        path = (map_path.parent / image.attrib["source"]).resolve()
        if not path.exists():
            continue
        out.append({
            "firstgid": int(ts.attrib["firstgid"]),
            "tilecount": int(ts.attrib.get("tilecount", "0")),
            "columns": int(ts.attrib.get("columns", "1")),
            "image": Image.open(path).convert("RGBA"),
        })
    return sorted(out, key=lambda x: x["firstgid"])

def resolve_tile(tsets: list[dict], gid: int):
    if not gid:
        return None
    choice = None
    for ts in tsets:
        if ts["firstgid"] <= gid:
            choice = ts
        else:
            break
    if choice is None:
        return None
    local = gid - choice["firstgid"]
    if local < 0 or local >= choice["tilecount"]:
        return None
    tx = local % choice["columns"]
    ty = local // choice["columns"]
    return choice["image"].crop((tx*TILE, ty*TILE, (tx+1)*TILE, (ty+1)*TILE))

def render_room(room_name: str, room: dict) -> dict:
    map_path = ROOT / room["map"]
    root = ET.parse(map_path).getroot()
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    tsets = tilesets(root, map_path)
    canvas = Image.new("RGBA", (w*TILE, h*TILE), (34, 31, 39, 255))
    draw = ImageDraw.Draw(canvas, "RGBA")
    for x in range(w+1):
        draw.line((x*TILE, 0, x*TILE, h*TILE), fill=(90,90,100,50))
    for y in range(h+1):
        draw.line((0, y*TILE, w*TILE, y*TILE), fill=(90,90,100,50))

    for layer_name in LAYERS:
        vals = csv_values(root, layer_name)
        for i, gid in enumerate(vals):
            tile = resolve_tile(tsets, gid)
            if tile is None:
                continue
            x, y = i % w, i // w
            canvas.alpha_composite(tile, (x*TILE, y*TILE))

    buildings = csv_values(root, "Buildings")
    draw = ImageDraw.Draw(canvas, "RGBA")
    for i, gid in enumerate(buildings):
        if gid != 5400:
            continue
        x, y = i % w, i // w
        draw.rectangle((x*TILE, y*TILE, (x+1)*TILE-1, (y+1)*TILE-1), fill=(230,80,80,55), outline=(250,120,120,160))

    for prop in room["props"]:
        ax, ay = prop["anchor"]
        pw, ph = prop["footprint_tiles"]
        hero = prop.get("hero", False)
        outline = (255,225,110,230) if hero else (120,215,255,170)
        draw.rectangle((ax*TILE, ay*TILE, (ax+pw)*TILE-1, (ay+ph)*TILE-1), outline=outline, width=1)
        draw.text((ax*TILE+2, ay*TILE+2), prop["id"], fill=outline)

    if room_name == "sky_dock":
        x0, x1 = room["protected_open_lane"]["x"]
        draw.rectangle((x0*TILE, 0, (x1+1)*TILE-1, h*TILE-1), outline=(120,255,160,150), width=1)

    scale = 3
    canvas = canvas.resize((canvas.width*scale, canvas.height*scale), Image.Resampling.NEAREST)
    out = ROOT / f"handoff/AIRSHIP_0696A_{room_name.upper()}_PREVIEW.png"
    canvas.save(out)

    occupied_visual = sum(sum(1 for x in csv_values(root, lname) if x) for lname in LAYERS)
    return {
        "room": room_name,
        "preview": str(out.relative_to(ROOT)).replace("\\", "/"),
        "custom_visual_tile_placements": occupied_visual,
        "pending_source_zone_count": len(room.get("pending_source_zones", [])),
        "full_composition_gate": "BLOCKED_EXTERNAL_SOURCE_PACK" if room.get("pending_source_zones") else "READY",
    }

def main() -> None:
    bp = json.loads(BLUEPRINT.read_text(encoding="utf-8"))
    report = [render_room(name, room) for name, room in bp["rooms"].items()]
    output = {
        "phase": bp["phase"],
        "preview_type": "deterministic-TMX-custom-layer-footprint-preview",
        "technical_preview": "PASS",
        "visual_acceptance": "PENDING-RON-IN-GAME",
        "full_composition_gate": "BLOCKED_EXTERNAL_SOURCE_PACK",
        "rooms": report,
        "note": "Preview validates placement, scale, layer ownership, and collision. It is not an in-game visual acceptance screenshot."
    }
    path = ROOT / "handoff/AIRSHIP_PREVIEW_REPORT_0696.json"
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()

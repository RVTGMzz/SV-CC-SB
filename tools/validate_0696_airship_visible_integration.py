#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json"
SOURCE_PACK = ROOT / "handoff/AIRSHIP_SOURCE_PACK_0696.json"
TILE = 16
ALLOWED_VISUAL = {"Back2", "Buildings2", "Front", "Front2"}
FORBIDDEN_PHYSICAL = {"BackDecor"}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def csv_values(root: ET.Element, name: str) -> list[int]:
    layer = next((x for x in root.findall("layer") if x.attrib.get("name") == name), None)
    if layer is None:
        raise AssertionError(f"missing layer {name}")
    data = layer.find("data")
    assert data is not None and data.attrib.get("encoding") == "csv", name
    vals = [int(x.strip()) for x in (data.text or "").split(",") if x.strip()]
    expected = int(root.attrib["width"]) * int(root.attrib["height"])
    assert len(vals) == expected, (name, len(vals), expected)
    return vals

def occupied_cells(path: Path) -> set[tuple[int, int]]:
    im = Image.open(path).convert("RGBA")
    alpha = im.getchannel("A")
    cols, rows = im.width // TILE, im.height // TILE
    out = set()
    for ty in range(rows):
        for tx in range(cols):
            if alpha.crop((tx*TILE, ty*TILE, (tx+1)*TILE, (ty+1)*TILE)).getbbox() is not None:
                out.add((tx, ty))
    return out

def expand_rects(rects: list[list[int]]) -> set[tuple[int, int]]:
    out = set()
    for x, y, w, h in rects:
        out |= {(xx, yy) for yy in range(y, y+h) for xx in range(x, x+w)}
    return out

def validate_source_pack(bp: dict) -> None:
    src = json.loads(SOURCE_PACK.read_text(encoding="utf-8"))
    assert src["visual_acceptance"] == "PENDING-RON-IN-GAME"
    assert src["repo_recovered_assets_complete"] is True
    by_path = {x["path"]: x for x in src["assets"]}
    for room in bp["rooms"].values():
        for prop in room["props"]:
            rec = by_path[prop["asset"]]
            assert rec["status"] == "exact", prop["id"]
            assert sha256(ROOT / prop["asset"]) == rec["sha256"], prop["id"]
            assert rec["tile_footprint"] == prop["footprint_tiles"], prop["id"]

def validate_room(room_name: str, room: dict) -> dict:
    path = ROOT / room["map"]
    root = ET.parse(path).getroot()
    assert [int(root.attrib["width"]), int(root.attrib["height"])] == room["dimensions_tiles"]
    layer_names = [x.attrib.get("name") for x in root.findall("layer")]
    assert not (FORBIDDEN_PHYSICAL & set(layer_names)), f"{room_name}: BackDecor still exists"
    for required in ("Back", "Back2", "Buildings", "Buildings2", "Front", "Front2"):
        assert required in layer_names, f"{room_name}: missing {required}"

    ts_by_name = {x.attrib.get("name"): x for x in root.findall("tileset")}
    assert not any("Density0693" in (x.attrib.get("name") or "") for x in root.findall("tileset")), room_name

    w = int(root.attrib["width"])
    visual_layer_vals = {name: csv_values(root, name) for name in ALLOWED_VISUAL if name in layer_names}
    buildings = csv_values(root, "Buildings")

    expected_collision = set()
    results = []
    for prop in room["props"]:
        ts = ts_by_name.get(prop["tileset_name"])
        assert ts is not None, (room_name, prop["id"], "tileset")
        assert int(ts.attrib["firstgid"]) == prop["firstgid"]
        image = ts.find("image")
        assert image is not None
        expected_source = str(Path(prop["asset"]).relative_to("src/Cardcha/assets")).replace("\\", "/")
        assert image.attrib["source"] == expected_source, (prop["id"], image.attrib["source"], expected_source)

        assigned = {}
        for sl in prop["visual_slices"]:
            assert sl["layer"] in ALLOWED_VISUAL, (prop["id"], sl["layer"])
            for ty in range(sl["rows"][0], sl["rows"][1] + 1):
                assert ty not in assigned, (prop["id"], "duplicate-row", ty)
                assigned[ty] = sl["layer"]
        assert set(assigned) == set(range(prop["footprint_tiles"][1])), (prop["id"], assigned)

        occupied = occupied_cells(ROOT / prop["asset"])
        ax, ay = prop["anchor"]
        represented = 0
        for tx, ty in occupied:
            layer_name = assigned[ty]
            vals = visual_layer_vals[layer_name]
            mx, my = ax + tx, ay + ty
            expected_gid = prop["firstgid"] + ty * prop["footprint_tiles"][0] + tx
            actual = vals[my*w + mx]
            assert actual == expected_gid, (room_name, prop["id"], layer_name, (mx,my), actual, expected_gid)
            represented += 1

        expected_collision |= expand_rects(prop.get("collision_rects", []))
        results.append({"id": prop["id"], "occupied_cells": len(occupied), "represented_cells": represented})

    # A tileset can have multiple approved instances, such as the two Deck signal lamps.
    # Validate every production GID against the union of all blueprint-authorized positions.
    expected_positions: dict[int, set[tuple[str, int, int]]] = {}
    known_gids: set[int] = set()
    for prop in room["props"]:
        occupied = occupied_cells(ROOT / prop["asset"])
        assigned = {}
        for sl in prop["visual_slices"]:
            for ty in range(sl["rows"][0], sl["rows"][1] + 1):
                assigned[ty] = sl["layer"]
        ax, ay = prop["anchor"]
        cols = prop["footprint_tiles"][0]
        for tx, ty in occupied:
            gid = prop["firstgid"] + ty * cols + tx
            known_gids.add(gid)
            expected_positions.setdefault(gid, set()).add((assigned[ty], ax + tx, ay + ty))

    for lname, vals in visual_layer_vals.items():
        for i, value in enumerate(vals):
            if value not in known_gids:
                continue
            x, y = i % w, i // w
            assert (lname, x, y) in expected_positions[value], (
                room_name, "unexpected-prop-placement", value, lname, x, y,
                sorted(expected_positions[value])
            )

    actual_collision = {(i % w, i // w) for i, value in enumerate(buildings) if value == 5400}
    missing_collision = {cell for cell in expected_collision if buildings[cell[1]*w + cell[0]] == 0}
    assert not missing_collision, (room_name, "missing-collision", sorted(missing_collision))
    unexpected_5400 = actual_collision - expected_collision
    assert not unexpected_5400, (room_name, "unexpected-0696-blocker", sorted(unexpected_5400))

    if room_name == "sky_dock":
        lane = room["protected_open_lane"]["x"]
        for y in range(int(root.attrib["height"])):
            for x in range(lane[0], lane[1] + 1):
                assert buildings[y*w+x] != 5400, ("sky_dock", "spine-blocked", x, y)
        gate = next(x for x in room["props"] if x["id"] == "boarding_gate")
        opening = gate["walk_through_opening"]
        for y in range(opening["y"][0], opening["y"][1] + 1):
            for x in range(opening["x"][0], opening["x"][1] + 1):
                assert buildings[y*w+x] != 5400, ("sky_dock", "gate-opening-blocked", x, y)

    props = {p.attrib.get("name"): p.attrib.get("value") for ps in root.findall("properties") for p in ps.findall("property")}
    assert props.get("CardchaVisualAcceptance") == "PENDING-RON-IN-GAME"
    assert props.get("CardchaBackDecorPolicy", "").startswith("deprecated-removed")
    return {"room": room_name, "props": results, "collision_cells": len(expected_collision), "layers": layer_names}

def main() -> None:
    bp = json.loads(BLUEPRINT.read_text(encoding="utf-8"))
    assert bp["visual_acceptance"] == "PENDING-RON-IN-GAME"
    validate_source_pack(bp)
    report = [validate_room(name, room) for name, room in bp["rooms"].items()]
    out = {
        "phase": bp["phase"],
        "technical_validation": "PASS",
        "visual_acceptance": "PENDING-RON-IN-GAME",
        "external_source_pack_complete": False,
        "rooms": report,
    }
    path = ROOT / "handoff/AIRSHIP_VISIBLE_INTEGRATION_VALIDATION_0696.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"

OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.57"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.58"
BRANCH = "cardcha-alpha28-0691-airship-prop-set02-harbor-furnishings"
PARENT_BRANCH = "cardcha-alpha28-0690-airship-interior-visual-rebuild"
PARENT_HEAD = "ceec814e76e3f79d1d34259a532e354a2c731362"

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = SRC / rel
    if not p.exists():
        continue
    s = read(p).replace(OLD_VERSION, NEW_VERSION)
    if rel == "ModEntry.cs":
        s = s.replace(
            "0690 AIRSHIP INTERIOR VISUAL REBUILD TEST",
            "0691 AIRSHIP PROP SET02 HARBOR FURNISHINGS TEST",
        )
    write(p, s)

def csv_values(layer: ET.Element) -> list[int]:
    data = layer.find("data")
    if data is None or data.attrib.get("encoding") != "csv":
        raise RuntimeError(f"layer {layer.attrib.get('name')} is not CSV")
    toks = [x.strip() for x in (data.text or "").split(",")]
    if not toks or any(x == "" for x in toks):
        raise RuntimeError(f"empty CSV token in layer {layer.attrib.get('name')}")
    return [int(x) for x in toks]

def set_csv(layer: ET.Element, vals: list[int]) -> None:
    data = layer.find("data")
    assert data is not None
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

def add_tileset(
    root: ET.Element,
    firstgid: int,
    name: str,
    source: str,
    width: int,
    height: int,
) -> None:
    remove_tileset(root, name)
    ts = ET.Element(
        "tileset",
        {
            "firstgid": str(firstgid),
            "name": name,
            "tilewidth": "16",
            "tileheight": "16",
            "tilecount": str((width // 16) * (height // 16)),
            "columns": str(width // 16),
        },
    )
    ET.SubElement(
        ts,
        "image",
        {"source": source, "width": str(width), "height": str(height)},
    )
    children = list(root)
    layer_index = next(
        (i for i, child in enumerate(children) if child.tag == "layer"),
        len(children),
    )
    root.insert(layer_index, ts)

def blit_asset(
    root: ET.Element,
    layer_name: str,
    firstgid: int,
    asset: Path,
    x: int,
    y: int,
) -> None:
    from PIL import Image

    im = Image.open(asset).convert("RGBA")
    if im.width % 16 != 0 or im.height % 16 != 0:
        raise RuntimeError(f"{asset.name} is not aligned to the 16px TMX grid")
    cols, rows = im.width // 16, im.height // 16
    map_w, map_h = int(root.attrib["width"]), int(root.attrib["height"])
    layer = get_layer(root, layer_name)
    vals = csv_values(layer)
    if len(vals) != map_w * map_h:
        raise RuntimeError(
            f"{layer_name} expected {map_w * map_h} tiles, got {len(vals)}"
        )

    for ty in range(rows):
        for tx in range(cols):
            tile = im.crop((tx * 16, ty * 16, tx * 16 + 16, ty * 16 + 16))
            if tile.getchannel("A").getbbox() is None:
                continue
            mx, my = x + tx, y + ty
            if not (0 <= mx < map_w and 0 <= my < map_h):
                raise RuntimeError(f"{asset.name} placement outside map at {mx},{my}")
            vals[my * map_w + mx] = firstgid + ty * cols + tx
    set_csv(layer, vals)

def add_blockers(
    root: ET.Element,
    blocker_gid: int,
    cells: list[tuple[int, int]],
) -> None:
    map_w, map_h = int(root.attrib["width"]), int(root.attrib["height"])
    layer = get_layer(root, "Buildings")
    vals = csv_values(layer)
    for x, y in cells:
        if not (0 <= x < map_w and 0 <= y < map_h):
            raise RuntimeError(f"blocker outside map {x},{y}")
        idx = y * map_w + x
        if vals[idx] == 0:
            vals[idx] = blocker_gid
    set_csv(layer, vals)

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

ASSET = SRC / "assets/airship_props/set02_harbor"
dock_path = SRC / "assets/sky_dock_interior.tmx"
dock = ET.parse(dock_path)
root = dock.getroot()

# 0691 Set 02 is intentionally dock-focused. It adds visual function without
# touching the 0690 observation/navigation hero props on Airship Deck.
add_tileset(
    root,
    5500,
    "CardchaDeparturesBoard0691",
    "airship_props/set02_harbor/departures_schedule_board.png",
    96,
    64,
)
add_tileset(
    root,
    5600,
    "CardchaWaitingBench0691",
    "airship_props/set02_harbor/waiting_bench.png",
    96,
    48,
)
add_tileset(
    root,
    5700,
    "CardchaLuggageCart0691",
    "airship_props/set02_harbor/luggage_cart.png",
    64,
    64,
)

# Composition:
# left/service side = information + waiting,
# right/boarding side = luggage,
# x=14..16 central arrival/exit spine remains untouched.
blit_asset(
    root,
    "BackDecor",
    5500,
    ASSET / "departures_schedule_board.png",
    8,
    3,
)
blit_asset(
    root,
    "BackDecor",
    5600,
    ASSET / "waiting_bench.png",
    3,
    10,
)
blit_asset(
    root,
    "BackDecor",
    5700,
    ASSET / "luggage_cart.png",
    21,
    10,
)

set02_blockers: list[tuple[int, int]] = []
set02_blockers += [(x, 6) for x in range(8, 14)]
set02_blockers += [(x, y) for y in (11, 12) for x in range(3, 9)]
set02_blockers += [(x, y) for y in (12, 13) for x in range(21, 25)]
add_blockers(root, 5400, set02_blockers)

set_property(
    root,
    "CardchaHarborFurnishings",
    "0691|departures-board|waiting-bench|luggage-cart|center-spine-protected",
)
ET.indent(dock, space=" ")
dock.write(dock_path, encoding="UTF-8", xml_declaration=True)

# Force one clean vanilla-furniture cleanup pass when loading the 0691 dock.
# Deck remains on its 0690 marker because 0691 does not change Deck physical art.
service_path = SRC / "Services/AirshipFoundationService.cs"
service = read(service)
dock_fn = re.compile(
    r"(private void EnsureSkyDockVanillaFurniture\(GameLocation dock\)\s*\{.*?"
    r"private static void ClearInteriorDecor)",
    re.S,
)
match = dock_fn.search(service)
if not match:
    raise RuntimeError("could not locate EnsureSkyDockVanillaFurniture")
block = match.group(1)
block = block.replace("-0690-dock", "-0691-dock")
block = block.replace(
    "// 0690: physical dock furnishings are authored into sky_dock_interior.tmx.",
    "// 0691: physical dock furnishings, including Set02 Harbor, are authored into sky_dock_interior.tmx.",
)
service = service[: match.start(1)] + block + service[match.end(1) :]
write(service_path, service)

audit_path = ROOT / "render_depth_audit.json"
audit = json.loads(read(audit_path))
audit["branch"] = BRANCH
done = audit.setdefault("completedDepthMigrations", [])
marker = "0691 Airship Set02 harbor furnishings->TMX; no new runtime physical rendering"
if marker not in done:
    done.append(marker)
write(audit_path, json.dumps(audit, indent=2) + "\n")

handoff_path = ROOT / "handoff/ALPHA28_0691_AIRSHIP_PROP_SET02_HARBOR_FURNISHINGS.md"
handoff_path.write_text(
    f"""# Alpha 28 0691 — Airship Prop Set 02 / Harbor Furnishings Integration

## Source of truth
- Current implementation branch: `{BRANCH}`
- Parent source-of-truth: `{PARENT_BRANCH}` @ `{PARENT_HEAD}`
- Build: `{NEW_VERSION}`
- 0690 in-game visual acceptance remains pending.

## Purpose
Extend the approved 0690 Airship language with a restrained, map-native Sky Dock furnishing pass. The goal is stronger harbor/station identity without cluttering the central route or reintroducing vanilla furniture.

## 0691 Set 02 — integrated
- Departures Schedule Board: 96x64, left/service information zone.
- Waiting Bench: 96x48, lower-left waiting zone.
- Luggage Cart: 64x64, lower-right boarding/luggage zone.

Asset library:
`src/Cardcha/assets/airship_props/set02_harbor/`

All three props are authored at native production resolution. No tiny draft is upscaled.

## Rendering contract
- All Set 02 physical art is owned by `sky_dock_interior.tmx`.
- 0691 adds no new runtime visual overlay and no new physical `RenderedWorld` drawing.
- Existing 0690 Observation Window / Navigation Console overlay behavior is frozen.
- Airship Deck physical map is frozen for this pass.
- Boss and Region content inherited from 0690 is frozen by CI.

## Composition
- Departures information reinforces the left/service side.
- Waiting bench creates a readable passenger nook without entering the center lane.
- Luggage cart reinforces the right/boarding side.
- Center x=14..16 arrival/exit spine remains free of Set 02 art.
- Existing route interaction, boarding bay and lower exit anchors remain reachable.

## Acceptance state
Repository validation, compile and package status must be taken from the completed 0691 GitHub Actions run.
In-game visual acceptance is pending Ron's later test. Do not claim visual acceptance until Ron reports it.

## Continuation
After CI success, record the materialized source head, workflow run, artifact ID, verified inner TEST ZIP SHA256, and keep the real TEST ZIP as the handoff package.
""",
    encoding="utf-8",
)

latest_path = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"
latest_path.write_text(
    f"""# Latest Cardcha Handoff

Current source-of-truth branch: `{BRANCH}`

Current build: `{NEW_VERSION}`

Current handoff: `handoff/ALPHA28_0691_AIRSHIP_PROP_SET02_HARBOR_FURNISHINGS.md`

Parent source-of-truth: `{PARENT_BRANCH}` @ `{PARENT_HEAD}`

Status: Airship Set 02 Harbor furnishings integrated as map-native Sky Dock art; CI/package status is finalized by the 0691 workflow. In-game visual acceptance remains pending.
""",
    encoding="utf-8",
)

print("0691 Harbor furnishings integration materialized")

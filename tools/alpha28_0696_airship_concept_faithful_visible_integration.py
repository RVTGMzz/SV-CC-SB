#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.61"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.62"
BRANCH = "cardcha-alpha28-0696-airship-concept-faithful-visible-integration"
PARENT = "cardcha-alpha28-0695-region1-prop-integration"
PARENT_HEAD = "d5ea0df497f6c9041045f043411fea678601a98b"

CONCEPT_HASHES = {
    "airship_0693_deck_density.png": "4eede9193c5c7c7ed3ed17f049e2d6012bf8429e32eedc150718bf312b519b27",
    "airship_0693_sky_dock_density.png": "c327c6e68fec2e9d1148b3aa2417c67fbf85b062cdfdc207d8045c6ed3ec52a3",
}
MAPS = [
    SRC / "assets/airship_deck.tmx",
    SRC / "assets/sky_dock_interior.tmx",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def layer(root: ET.Element, name: str) -> ET.Element:
    item = next((x for x in root.findall("layer") if x.attrib.get("name") == name), None)
    if item is None:
        raise RuntimeError(f"missing layer {name}")
    return item


def vals(item: ET.Element) -> list[int]:
    data = item.find("data")
    if data is None or data.attrib.get("encoding") != "csv":
        raise RuntimeError(f"{item.attrib.get('name')} is not CSV")
    toks = [x.strip() for x in (data.text or "").split(",")]
    if not toks or any(not x for x in toks):
        raise RuntimeError(f"{item.attrib.get('name')} has empty CSV token")
    return [int(x) for x in toks]


def set_vals(item: ET.Element, data_vals: list[int]) -> None:
    data = item.find("data")
    assert data is not None
    data.text = "\n" + ",".join(str(x) for x in data_vals) + "\n"


def set_property(root: ET.Element, name: str, value: str) -> None:
    props = root.find("properties")
    if props is None:
        props = ET.Element("properties")
        root.insert(0, props)
    for p in props.findall("property"):
        if p.attrib.get("name") == name:
            p.set("value", value)
            return
    ET.SubElement(props, "property", {"name": name, "value": value})


def set_passable_true(ts: ET.Element) -> None:
    tilecount = int(ts.attrib.get("tilecount", "0"))
    existing = {int(t.attrib["id"]): t for t in ts.findall("tile")}
    for tile_id in range(tilecount):
        tile = existing.get(tile_id)
        if tile is None:
            tile = ET.SubElement(ts, "tile", {"id": str(tile_id)})
        props = tile.find("properties")
        if props is None:
            props = ET.SubElement(tile, "properties")
        prop = next((p for p in props.findall("property") if p.attrib.get("name") == "Passable"), None)
        if prop is None:
            ET.SubElement(props, "property", {"name": "Passable", "value": "T"})
        else:
            prop.set("value", "T")


def assert_concept_hashes() -> None:
    for filename, expected in CONCEPT_HASHES.items():
        path = SRC / "assets" / filename
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"approved concept asset drifted: {filename}: {actual} != {expected}")


def migrate_map(path: Path) -> dict[str, int]:
    tree = ET.parse(path)
    root = tree.getroot()
    back = vals(layer(root, "Back"))
    decor_layer = layer(root, "BackDecor")
    decor = vals(decor_layer)
    buildings_layer = layer(root, "Buildings")
    buildings = vals(buildings_layer)
    front_layer = layer(root, "Front")
    front = vals(front_layer)

    if not (len(back) == len(decor) == len(buildings) == len(front)):
        raise RuntimeError(f"{path.name}: layer size mismatch")

    moved_buildings = 0
    moved_front = 0
    collision_before = [i for i, v in enumerate(buildings) if v == 5400]
    concept_before = Counter(v for v in decor if v != 0)

    for i, gid in enumerate(decor):
        if gid == 0:
            continue
        if buildings[i] == 0:
            buildings[i] = gid
            moved_buildings += 1
        elif front[i] == 0:
            front[i] = gid
            moved_front += 1
        else:
            raise RuntimeError(f"{path.name}: cannot migrate visible art at cell {i}; Buildings and Front both occupied")

    set_vals(buildings_layer, buildings)
    set_vals(front_layer, front)
    root.remove(decor_layer)

    # All art-only Airship tilesets are explicitly passable. Physical collision stays owned by
    # the dedicated 5400 blocker tiles and inherited structural Buildings cells.
    for ts in root.findall("tileset"):
        firstgid = int(ts.attrib.get("firstgid", "0"))
        name = ts.attrib.get("name", "")
        if firstgid == 5400 or name == "CardchaCollision0690":
            continue
        if firstgid >= 5000:
            set_passable_true(ts)

    collision_after = [i for i, v in enumerate(buildings) if v == 5400]
    if collision_before != collision_after:
        raise RuntimeError(f"{path.name}: dedicated collision blocker topology changed")

    migrated = Counter()
    for i, original_gid in enumerate(decor):
        if original_gid:
            visible_gid = buildings[i] if buildings[i] == original_gid else front[i]
            if visible_gid != original_gid:
                raise RuntimeError(f"{path.name}: concept tile lost at cell {i}")
            migrated[original_gid] += 1
    if migrated != concept_before:
        raise RuntimeError(f"{path.name}: concept tile multiset changed during migration")

    set_property(root, "CardchaTextureContract", "0696|approved-concept-hash-locked|standard-visible-map-layers-only")
    set_property(root, "CardchaInteriorDensity", "0696|concept-faithful|Buildings+Front|no-BackDecor|collision-blockers-preserved")
    set_property(root, "CardchaVisualAcceptance", "PENDING-RON-IN-GAME")

    ET.indent(tree, space=" ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    return {
        "conceptTiles": sum(concept_before.values()),
        "movedToBuildings": moved_buildings,
        "movedToFront": moved_front,
        "collisionBlockers": len(collision_after),
    }


assert_concept_hashes()

for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = SRC / rel
    if p.exists():
        text = read(p)
        if OLD_VERSION in text:
            write(p, text.replace(OLD_VERSION, NEW_VERSION))

stats = {p.name: migrate_map(p) for p in MAPS}

audit_path = ROOT / "render_depth_audit.json"
audit = json.loads(read(audit_path))
audit["branch"] = BRANCH
completed = audit.setdefault("completedDepthMigrations", [])
marker = "0696 Airship approved concept art BackDecor->standard Buildings/Front map layers; exact concept hashes locked"
if marker not in completed:
    completed.append(marker)
write(audit_path, json.dumps(audit, indent=2) + "\n")

handoff = ROOT / "handoff/ALPHA28_0696_AIRSHIP_CONCEPT_FAITHFUL_VISIBLE_INTEGRATION.md"
handoff.write_text(f'''# Alpha 28 0696 - Airship Concept-Faithful Visible Integration

## Source of truth
- Branch: `{BRANCH}`
- Parent: `{PARENT}` @ `{PARENT_HEAD}`
- Build: `{NEW_VERSION}`

## Trigger
Ron tested the real package and both Airship rooms were still visually empty despite the 0693 density concept being present in the archive.

## Root cause confirmed
The two approved concept PNGs were already packaged byte-for-byte, but 0693 placed the physical scene into a custom TMX layer named `BackDecor`. The repository validators only checked asset/GID presence, so they could pass while the real Stardew render path did not visibly draw that physical layer.

0696 treats in-game visibility as a first-class contract instead of equating file presence with successful integration.

## Exact concept lock
- Deck SHA256: `{CONCEPT_HASHES['airship_0693_deck_density.png']}`
- Sky Dock SHA256: `{CONCEPT_HASHES['airship_0693_sky_dock_density.png']}`

These are the exact approved concept assets Ron supplied. 0696 refuses to materialize if either image drifts.

## Integration repair
- Removes `BackDecor` from both Airship TMX maps.
- Migrates every non-empty concept/hero-prop tile to Stardew-standard visible layers only.
- Uses `Buildings` when the cell was free.
- Uses `Front` only when the inherited `Buildings` cell was already occupied, so visual art is not silently dropped.
- Marks art-only custom tilesets `Passable=T`.
- Keeps dedicated GID 5400 blocker cells untouched as the physical collision source.
- Keeps `Back`, room dimensions, Airship mechanics, upgrade sockets, route logic, and runtime VFX frozen.

## Materialized migration stats
```json
{json.dumps(stats, indent=2)}
```

## Acceptance
Repository validation / compile / package must pass in CI.

**In-game visual acceptance: PENDING.** Ron must verify both rooms in the real game before this is accepted.
''', encoding="utf-8")

latest = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"
latest.write_text(f'''# Latest Cardcha Handoff

Current source-of-truth branch: `{BRANCH}`

Current build: `{NEW_VERSION}`

Current handoff: `handoff/ALPHA28_0696_AIRSHIP_CONCEPT_FAITHFUL_VISIBLE_INTEGRATION.md`

Parent source-of-truth: `{PARENT}` @ `{PARENT_HEAD}`

Status: **0696 Airship concept-faithful visible-layer repair materialized; CI/package verification pending in generated handoff. In-game visual acceptance remains PENDING.**

Critical rule: the approved 0693 Deck/Sky Dock concept PNG hashes are locked. Physical Airship concept art must use standard visible TMX layers; do not reintroduce the custom `BackDecor` ownership path.
''', encoding="utf-8")

print("0696 Airship concept-faithful visible integration materialized")
print(json.dumps(stats, indent=2))

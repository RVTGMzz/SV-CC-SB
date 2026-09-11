#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import random
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
ROOM_DIR = SRC / "assets/region1_rooms"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.60"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.61"
BRANCH = "cardcha-alpha28-0695-region1-prop-integration"
PARENT_BRANCH = "cardcha-alpha28-0694-region1-environment-prop-concept"
PARENT_HEAD = "5f8fdafa4dfd7db964728cbe6378da1c82b102ea"
TILESET_NAME = "CardchaRegion1Environment0695"
TILESET_SOURCE = "region1_environment_props_0695.png"
FIRST_GID = 6000
LAST_GID = 6127

ROOMS = [
    ("room_1_verdant_clearing.tmx", "verdant-clearing", 0),
    ("room_2_moss_creek.tmx", "moss-creek", 1),
    ("room_3_old_ruins.tmx", "old-ruins", 2),
    ("room_4_briar_thicket.tmx", "briar-thicket", 3),
    ("room_5_hollow_grove.tmx", "hollow-grove", 4),
    ("room_6_card_shrine.tmx", "card-shrine", 5),
]

GROUND = {
    0: [(3,3),(5,3),(23,3),(25,4),(3,7),(5,9),(22,7),(24,9),(4,12),(6,14),(21,12),(24,14),(7,8),(20,10),(7,15),(21,15),(9,13),(19,13),(3,16),(24,16)],
    1: [(2,4),(4,5),(5,7),(3,9),(5,11),(4,13),(6,15),(22,4),(24,5),(23,7),(25,9),(23,11),(24,13),(21,15),(7,9),(20,8),(7,12),(20,12),(8,15),(19,15),(10,8),(18,11)],
    2: [(3,3),(5,4),(23,3),(25,5),(3,8),(5,10),(22,8),(24,10),(4,13),(6,15),(21,13),(24,15),(7,7),(20,7),(7,14),(20,14),(9,9),(19,11),(3,16),(23,16)],
    3: [(2,4),(4,4),(5,6),(3,8),(5,10),(3,12),(5,14),(22,4),(24,5),(23,7),(25,9),(23,11),(25,13),(22,15),(7,8),(20,8),(7,11),(20,12),(7,15),(20,15),(9,13),(19,10)],
    4: [(3,4),(5,5),(4,8),(6,10),(3,12),(5,15),(22,4),(24,6),(23,9),(25,11),(22,13),(24,15),(7,7),(20,8),(7,13),(20,14),(9,9),(19,11),(8,15),(21,16)],
    5: [(3,4),(5,5),(23,4),(25,5),(3,8),(5,11),(22,8),(24,11),(4,14),(6,16),(21,14),(24,16),(7,8),(20,8),(7,13),(20,13),(9,15),(19,15),(10,11),(18,11)],
}

SOLID_ROWS = {0:[2],1:[2],2:[4],3:[6],4:[2,6],5:[7,4]}
FRONT_ROWS = {0:[3],1:[3],2:[5],3:[6],4:[3,6],5:[7,5]}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def layer(root: ET.Element, name: str) -> ET.Element:
    found = next((x for x in root.findall("layer") if x.attrib.get("name") == name), None)
    if found is None:
        raise RuntimeError(f"missing layer {name}")
    return found


def values(root: ET.Element, name: str) -> list[int]:
    item = layer(root, name)
    data = item.find("data")
    if data is None or data.attrib.get("encoding") != "csv":
        raise RuntimeError(f"layer {name} is not CSV")
    toks = [x.strip() for x in (data.text or "").split(",")]
    if not toks or any(x == "" for x in toks):
        raise RuntimeError(f"empty CSV token in {name}")
    out = [int(x) for x in toks]
    expected = int(root.attrib["width"]) * int(root.attrib["height"])
    if len(out) != expected:
        raise RuntimeError(f"{name} tile count {len(out)} != {expected}")
    return out


def set_values(root: ET.Element, name: str, vals: list[int]) -> None:
    data = layer(root, name).find("data")
    assert data is not None
    data.text = "\n" + ",".join(str(x) for x in vals) + "\n"


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


def add_tileset(root: ET.Element) -> None:
    remove_tileset(root, TILESET_NAME)
    ts = ET.Element("tileset", {
        "firstgid": str(FIRST_GID), "name": TILESET_NAME,
        "tilewidth": "16", "tileheight": "16", "tilecount": "128", "columns": "16",
    })
    ET.SubElement(ts, "image", {"source": TILESET_SOURCE, "width": "256", "height": "128"})
    children = list(root)
    first_layer = next((i for i, c in enumerate(children) if c.tag == "layer"), len(children))
    root.insert(first_layer, ts)


def ensure_back_decor(root: ET.Element) -> ET.Element:
    existing = next((x for x in root.findall("layer") if x.attrib.get("name") == "BackDecor"), None)
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    if existing is not None:
        vals = values(root, "BackDecor")
        vals = [0 if FIRST_GID <= v <= LAST_GID else v for v in vals]
        set_values(root, "BackDecor", vals)
        return existing
    used_ids = [int(x.attrib.get("id", "0")) for x in root.findall("layer")]
    new_id = max(used_ids or [0]) + 1
    item = ET.Element("layer", {"id": str(new_id), "name": "BackDecor", "width": str(w), "height": str(h)})
    data = ET.SubElement(item, "data", {"encoding": "csv"})
    data.text = "\n" + ",".join("0" for _ in range(w * h)) + "\n"
    children = list(root)
    back_index = next(i for i, c in enumerate(children) if c.tag == "layer" and c.attrib.get("name") == "Back")
    root.insert(back_index + 1, item)
    root.set("nextlayerid", str(max(new_id + 1, int(root.attrib.get("nextlayerid", "1")))))
    return item


def protected_tall(x: int, y: int) -> bool:
    # Tall/solid custom art stays out of every protected 0694 interaction breathing-space band.
    if 6 <= x <= 22 and 1 <= y <= 6: return True
    if 8 <= x <= 20 and 7 <= y <= 14: return True
    if 10 <= x <= 18 and 15 <= y <= 19: return True
    return False


def anchor_cell(x: int, y: int) -> bool:
    return (x, y) in {(14,17),(14,18),(9,2),(14,2),(19,2),(7,5),(14,5),(21,5),(14,10)}


def gid(row: int, col: int) -> int:
    return FIRST_GID + row * 16 + (col % 16)


def place_ground(root: ET.Element, room_index: int) -> int:
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    vals = values(root, "BackDecor")
    count = 0
    for i, (x, y) in enumerate(GROUND[room_index]):
        if not (0 <= x < w and 0 <= y < h) or anchor_cell(x, y): continue
        row = 0 if (i + room_index) % 3 else 1
        if room_index == 3 and i % 4 == 0: row = 1
        vals[y*w+x] = gid(row, (i * 5 + room_index * 3) % 16)
        count += 1
    set_values(root, "BackDecor", vals)
    return count


def replace_existing_solids(root: ET.Element, room_index: int) -> tuple[list[tuple[int,int]], int]:
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    vals = values(root, "Buildings")
    candidates: list[tuple[int,int]] = []
    for y in range(3, min(h-2, 17)):
        for x in range(0, w):
            if vals[y*w+x] == 0 or protected_tall(x,y) or anchor_cell(x,y):
                continue
            # Prefer the inherited outer collision rim. This adds visual identity without adding obstacles.
            if x <= 1 or x >= w - 2:
                candidates.append((x,y))
    rng = random.Random(695100 + room_index)
    rng.shuffle(candidates)
    target = [8, 9, 11, 12, 10, 9][room_index]
    chosen = sorted(candidates[:min(target, len(candidates))], key=lambda p: (p[1], p[0]))
    rows = SOLID_ROWS[room_index]
    for i, (x,y) in enumerate(chosen):
        row = rows[i % len(rows)]
        vals[y*w+x] = gid(row, (room_index*3 + i*5) % 16)
    set_values(root, "Buildings", vals)
    return chosen, len(chosen)


def place_front_tops(root: ET.Element, room_index: int, solid_cells: list[tuple[int,int]]) -> int:
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    vals = values(root, "Front")
    vals = [0 if FIRST_GID <= v <= LAST_GID else v for v in vals]
    rows = FRONT_ROWS[room_index]
    count = 0
    for i, (x, y) in enumerate(solid_cells):
        if count >= [3,3,4,4,4,4][room_index]: break
        fy = y - 1
        if fy < 1 or protected_tall(x,fy) or anchor_cell(x,fy): continue
        idx = fy*w+x
        if vals[idx] != 0: continue
        row = rows[count % len(rows)]
        vals[idx] = gid(row, 8 + ((room_index*2 + count*3) % 8) if row == 3 else (room_index*4 + count*3) % 16)
        count += 1
    set_values(root, "Front", vals)
    return count


for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = SRC / rel
    if p.exists():
        text = read(p)
        if OLD_VERSION in text: write(p, text.replace(OLD_VERSION, NEW_VERSION))

airship_path = SRC / "Services/AirshipFoundationService.cs"
airship = read(airship_path)
legacy_call = "            Region1StardewDecorRenderer.Draw(e.SpriteBatch, location, activeRoomIndex);\n"
if legacy_call in airship:
    airship = airship.replace(legacy_call, "", 1)
elif "Region1StardewDecorRenderer.Draw(" in airship:
    raise RuntimeError("0695 could not remove Region1StardewDecorRenderer with the expected single-line contract")
write(airship_path, airship)

legacy_renderer = SRC / "Services/Region1StardewDecorRenderer.cs"
if legacy_renderer.exists(): legacy_renderer.unlink()
legacy_atlas = SRC / "assets/region1_environment_decor.png"
if legacy_atlas.exists(): legacy_atlas.unlink()

room_stats = {}
for filename, slug, room_index in ROOMS:
    path = ROOM_DIR / filename
    tree = ET.parse(path)
    root = tree.getroot()
    if (int(root.attrib.get("width", "0")), int(root.attrib.get("height", "0"))) != (28,20):
        raise RuntimeError(f"{filename}: expected 28x20 room")
    before_mask = [v != 0 for v in values(root, "Buildings")]
    add_tileset(root)
    ensure_back_decor(root)
    ground_count = place_ground(root, room_index)
    chosen, solid_count = replace_existing_solids(root, room_index)
    front_count = place_front_tops(root, room_index, chosen)
    after_mask = [v != 0 for v in values(root, "Buildings")]
    if before_mask != after_mask: raise RuntimeError(f"{filename}: collision topology changed")
    set_property(root, "CardchaRegionVersion", NEW_VERSION)
    set_property(root, "CardchaAssetPolicy", "cardcha-owned-map|vanilla-terrain+cardcha-owned-region1-props|no-third-party-assets")
    set_property(root, "CardchaRegionEnvironment", f"0695|{slug}|map-native-props|BackDecor+Buildings+Front|anchors-frozen")
    set_property(root, "CardchaTextureContract", "0695|flat-rgba-region1-environment|png-color-type-6")
    ET.indent(tree, space=" ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    room_stats[slug] = {"ground": ground_count, "solidReplacements": solid_count, "front": front_count}

concept_path = ROOT / "handoff/REGION1_ENVIRONMENT_PROP_CONCEPT_0694.json"
concept = json.loads(read(concept_path))
concept["status"] = "approved-and-integrated-by-0695"
concept["approvedBy"] = "Ron"
concept["productionBranch"] = BRANCH
concept["productionBuild"] = NEW_VERSION
write(concept_path, json.dumps(concept, indent=2) + "\n")

audit_path = ROOT / "render_depth_audit.json"
audit = json.loads(read(audit_path))
audit["branch"] = BRANCH
debt = audit.setdefault("confirmedUnsafePhysicalPostWorld", [])
audit["confirmedUnsafePhysicalPostWorld"] = [x for x in debt if x != "Region1StardewDecorRenderer.Draw"]
done = audit.setdefault("completedDepthMigrations", [])
marker = "0695 Region I Hunt Run physical environment decor->TMX BackDecor/Buildings/Front; legacy RenderedWorld renderer removed"
if marker not in done: done.append(marker)
write(audit_path, json.dumps(audit, indent=2) + "\n")

depth_validator = ROOT / "tools/validate_render_depth_contract.py"
dv = read(depth_validator)
dv = dv.replace('    "Region1StardewDecorRenderer.Draw",\n', '')
warning = '''if "Region1StardewDecorRenderer.Draw(e.SpriteBatch, location, activeRoomIndex);" in airship:\n    print("RENDER DEPTH AUDIT WARNING: Region I post-world decor debt remains in legacy source but must be runtime-suppressed/migrated before visual acceptance.")\n'''
dv = dv.replace(warning, '')
write(depth_validator, dv)

handoff = ROOT / "handoff/ALPHA28_0695_REGION1_ENVIRONMENT_PROP_PRODUCTION_INTEGRATION.md"
handoff.write_text(f'''# Alpha 28 0695 - Region I Environment Prop Production Integration\n\n## Source of truth\n- Branch: `{BRANCH}`\n- Parent concept: `{PARENT_BRANCH}` @ `{PARENT_HEAD}`\n- Build: `{NEW_VERSION}`\n\n## Approved direction\nRon approved the 0694 Region I environment concept for production integration. 0695 implements that approved Stardew-forest language without changing Hunt Run gameplay topology.\n\n## Production changes\n- Added one Cardcha-owned native 16px RGBA prop tilesheet: `region1_environment_props_0695.png` (256x128, 128 tiles).\n- Added seven approved prop families: moss/root, log/stump, forage/mushroom, field-stone ruins, trail signs, briar/hollow growth, and Card Shrine relics.\n- Integrated the sheet into all six `region1_rooms/*.tmx` maps as `CardchaRegion1Environment0695` at firstgid 6000.\n- Added map-native `BackDecor` ground-detail compositions with a different authored signature per room.\n- Replaced only already-solid `Buildings` cells with visual prop bases; the zero/non-zero collision mask is unchanged.\n- Added selective `Front` upper silhouettes only outside protected gameplay bands.\n- Removed the runtime call to `Region1StardewDecorRenderer.Draw`.\n- Removed the now-unused legacy `Region1StardewDecorRenderer.cs` and `region1_environment_decor.png`.\n\n## Gameplay freeze\nThe following anchors remain source-of-truth and unchanged: arrival near `(14,17)`, retreat `(14,18)`, route choices `(9,2)` / `(19,2)`, boss `(14,2)`, boons `(7,5)` / `(14,5)` / `(21,5)`, and rare/lost-cache center `(14,10)`.\n\n0695 changes environment presentation only. Encounters, rewards, run length, route logic, fares, boss rules and Region I main hub remain frozen.\n\n## Rendering-depth contract\n- Physical Hunt Run environment art is now TMX-owned (`BackDecor`, `Buildings`, selective `Front`).\n- `Display.RenderedWorld` no longer paints the six-room physical environment prop atlas.\n- Runtime Hunt Run route/boon/boss markers remain because those are interaction/VFX overlays, not permanent physical furniture.\n- `AirshipFoundationService.DrawRegion1Details` remains separately audited legacy debt for the main Region I map and is not falsely marked migrated by 0695.\n\n## Materialized room stats\n```json\n{json.dumps(room_stats, indent=2)}\n```\n\n## Acceptance\nRepository validation / compile / package must pass in CI.\n\n**In-game visual acceptance: PENDING.** CI success is not visual acceptance. Ron must inspect the real TEST package before this Region I visual pass is called accepted.\n\nAirship 0693 visual acceptance also remains PENDING unless Ron separately reports acceptance.\n''', encoding="utf-8")

latest = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"
latest.write_text(f'''# Latest Cardcha Handoff\n\nCurrent source-of-truth branch: `{BRANCH}`\n\nCurrent build: `{NEW_VERSION}`\n\nCurrent handoff: `handoff/ALPHA28_0695_REGION1_ENVIRONMENT_PROP_PRODUCTION_INTEGRATION.md`\n\nParent concept: `{PARENT_BRANCH}` @ `{PARENT_HEAD}`\n\nStatus: **0695 production integration materialized; CI / package verification pending in this generated handoff. In-game visual acceptance remains PENDING.**\n\n0695 migrates the six Region I Hunt Run room environment props from the legacy physical `RenderedWorld` renderer into map-native TMX `BackDecor` / `Buildings` / selective `Front` layers while freezing gameplay anchors and collision topology.\n''', encoding="utf-8")

print("0695 Region I environment prop production integration materialized")
print(json.dumps(room_stats, indent=2))

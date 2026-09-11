#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import struct
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
ROOM_DIR = SRC / "assets/region1_rooms"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.61"
BRANCH = "cardcha-alpha28-0695-region1-prop-integration"
PARENT_REMOTE = "origin/cardcha-alpha28-0694-region1-environment-prop-concept"
FIRST_GID, LAST_GID = 6000, 6127
ROOMS = [
    "room_1_verdant_clearing.tmx", "room_2_moss_creek.tmx", "room_3_old_ruins.tmx",
    "room_4_briar_thicket.tmx", "room_5_hollow_grove.tmx", "room_6_card_shrine.tmx",
]
ANCHORS = {(14,17),(14,18),(9,2),(14,2),(19,2),(7,5),(14,5),(21,5),(14,10)}


def req(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit("0695 validation FAIL: " + message)


def png_info(path: Path) -> tuple[int,int,int]:
    raw = path.read_bytes()
    req(raw[:8] == b"\x89PNG\r\n\x1a\n", path.name + " not PNG")
    req(raw[12:16] == b"IHDR", path.name + " missing IHDR")
    w,h = struct.unpack(">II", raw[16:24])
    return w,h,raw[25]


def layer_values(root: ET.Element, name: str) -> list[int]:
    item = next((x for x in root.findall("layer") if x.attrib.get("name") == name), None)
    req(item is not None, f"missing layer {name}")
    data = item.find("data")
    req(data is not None and data.attrib.get("encoding") == "csv", f"{name} not CSV")
    toks = [x.strip() for x in (data.text or "").split(",")]
    req(bool(toks) and all(toks), f"{name} has empty CSV token")
    vals = [int(x) for x in toks]
    req(len(vals) == int(root.attrib["width"])*int(root.attrib["height"]), f"{name} tile count")
    return vals


def parent_text(path: str) -> str:
    cp = subprocess.run(["git","show",f"{PARENT_REMOTE}:{path}"], cwd=ROOT, text=True, capture_output=True)
    req(cp.returncode == 0, f"cannot read parent {path}: {cp.stderr.strip()}")
    return cp.stdout


def custom(v: int) -> bool:
    return FIRST_GID <= v <= LAST_GID


def protected_tall(x:int,y:int) -> bool:
    return ((6 <= x <= 22 and 1 <= y <= 6)
            or (8 <= x <= 20 and 7 <= y <= 14)
            or (10 <= x <= 18 and 15 <= y <= 19))


for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets"]:
    req(VERSION in (SRC/rel).read_text(encoding="utf-8"), rel + " version")

sheet = ROOM_DIR / "region1_environment_props_0695.png"
w,h,ct = png_info(sheet)
req((w,h) == (256,128), "prop sheet must be 256x128")
req(ct == 6, "prop sheet must be true RGBA PNG color type 6")
manifest = json.loads((ROOM_DIR/"region1_environment_props_0695_manifest.json").read_text(encoding="utf-8"))
req(manifest.get("staticPhysicalOwner") == "TMX map layers", "asset manifest physical owner")
req(manifest.get("runtimeOverlays") == [], "asset manifest runtime overlays must be empty")
req(set(manifest.get("families",{})) == {"P01","P02","P03","P04","P05","P06","P07"}, "seven 0694-approved prop families")
req(manifest.get("thirdPartyAssets") is False, "third-party asset policy")
req(not (SRC/"assets/region1_environment_decor.png").exists(), "legacy 0669 Region I decor atlas still exists")
req(not (SRC/"Services/Region1StardewDecorRenderer.cs").exists(), "legacy Region1StardewDecorRenderer.cs still exists")

airship_path = "src/Cardcha/Services/AirshipFoundationService.cs"
airship = (SRC/"Services/AirshipFoundationService.cs").read_text(encoding="utf-8")
req("Region1StardewDecorRenderer" not in airship, "legacy room physical renderer reference remains")
req("this.DrawRegion1HuntRun2Overlay(e.SpriteBatch, location);" in airship, "Hunt Run interaction/VFX overlay was lost")
parent_airship = parent_text(airship_path)
expected_airship = parent_airship.replace("            Region1StardewDecorRenderer.Draw(e.SpriteBatch, location, activeRoomIndex);\n", "", 1)
req(expected_airship != parent_airship, "parent renderer line not found for exact source freeze")
req(airship == expected_airship, "AirshipFoundationService changed beyond removal of legacy Region I physical renderer call")

signatures = []
for room in ROOMS:
    current_path = ROOM_DIR / room
    root = ET.parse(current_path).getroot()
    parent = ET.fromstring(parent_text("src/Cardcha/assets/region1_rooms/" + room))
    req((int(root.attrib["width"]), int(root.attrib["height"])) == (28,20), room + " dimensions")
    ts = next((x for x in root.findall("tileset") if x.attrib.get("name") == "CardchaRegion1Environment0695"), None)
    req(ts is not None and int(ts.attrib.get("firstgid","0")) == FIRST_GID, room + " 0695 tileset")
    image = ts.find("image")
    req(image is not None and image.attrib.get("source") == "region1_environment_props_0695.png", room + " flat prop texture source")

    back = layer_values(root,"Back")
    parent_back = layer_values(parent,"Back")
    req(back == parent_back, room + " base terrain Back layer changed")

    current_build = layer_values(root,"Buildings")
    parent_build = layer_values(parent,"Buildings")
    req([x != 0 for x in current_build] == [x != 0 for x in parent_build], room + " collision zero/nonzero topology changed")
    req(sum(custom(v) for v in current_build) >= 3, room + " has too little map-native solid identity art")

    decor = layer_values(root,"BackDecor")
    req(sum(custom(v) for v in decor) >= 18, room + " has too little BackDecor density")
    front = layer_values(root,"Front")
    req(sum(custom(v) for v in front) >= 2, room + " lacks selective Front silhouettes")

    width = 28
    for y in range(20):
        for x in range(28):
            idx = y*width+x
            if custom(current_build[idx]) or custom(front[idx]):
                req(not protected_tall(x,y), f"{room} tall custom prop entered protected band at {x},{y}")
            if (x,y) in ANCHORS:
                req(not custom(current_build[idx]), f"{room} anchor custom Buildings at {x},{y}")
                req(not custom(front[idx]), f"{room} anchor custom Front at {x},{y}")

    props = {p.attrib.get("name"):p.attrib.get("value") for ps in root.findall("properties") for p in ps.findall("property")}
    req(props.get("CardchaRegionVersion") == VERSION, room + " region version")
    req(props.get("CardchaTextureContract") == "0695|flat-rgba-region1-environment|png-color-type-6", room + " texture contract")
    req("anchors-frozen" in props.get("CardchaRegionEnvironment",""), room + " anchor contract")
    req("no-third-party-assets" in props.get("CardchaAssetPolicy",""), room + " asset policy")
    signatures.append(tuple(i for i,v in enumerate(decor) if custom(v)))

req(len(set(signatures)) == 6, "the six rooms regressed to a repeated placement stamp")

audit = json.loads((ROOT/"render_depth_audit.json").read_text(encoding="utf-8"))
req(audit.get("branch") == BRANCH, "render audit branch")
req("Region1StardewDecorRenderer.Draw" not in audit.get("confirmedUnsafePhysicalPostWorld",[]), "migrated renderer still marked as active debt")
req("AirshipFoundationService.DrawRegion1Details" in audit.get("confirmedUnsafePhysicalPostWorld",[]), "main Region I map debt was falsely cleared")
marker = "0695 Region I Hunt Run physical environment decor->TMX BackDecor/Buildings/Front; legacy RenderedWorld renderer removed"
req(marker in audit.get("completedDepthMigrations",[]), "0695 depth migration marker")

depth = (ROOT/"tools/validate_render_depth_contract.py").read_text(encoding="utf-8")
req('    "Region1StardewDecorRenderer.Draw",' not in depth, "render-depth validator still requires migrated debt")
req("Region1StardewDecorRenderer.Draw(e.SpriteBatch" not in depth, "render-depth validator still warns on migrated path")

concept = json.loads((ROOT/"handoff/REGION1_ENVIRONMENT_PROP_CONCEPT_0694.json").read_text(encoding="utf-8"))
req(concept.get("status") == "approved-and-integrated-by-0695", "0694 approval status")
req(concept.get("productionBranch") == BRANCH, "0694 production branch link")
latest = (ROOT/"handoff/LATEST_CARDCHA_HANDOFF.md").read_text(encoding="utf-8")
handoff = (ROOT/"handoff/ALPHA28_0695_REGION1_ENVIRONMENT_PROP_PRODUCTION_INTEGRATION.md").read_text(encoding="utf-8")
req(BRANCH in latest and VERSION in latest, "latest handoff pointer")
req("In-game visual acceptance: PENDING" in handoff, "0695 visual acceptance must remain pending")
req("Airship 0693 visual acceptance also remains PENDING" in handoff, "0693 Airship acceptance truth lost")

print("0695 Region I environment prop production integration validation PASS")

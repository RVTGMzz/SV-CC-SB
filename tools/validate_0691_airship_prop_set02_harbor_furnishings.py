#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.58"
BRANCH = "cardcha-alpha28-0691-airship-prop-set02-harbor-furnishings"

def need(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("0691 validation FAIL: " + msg)

def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

manifest = json.loads(text(SRC / "manifest.json"))
need(manifest.get("Version") == VERSION, "manifest version")
need(VERSION in text(SRC / "Cardcha.csproj"), "csproj version")
need(VERSION in text(SRC / "Directory.Build.targets"), "Directory.Build.targets version")

asset = SRC / "assets/airship_props/set02_harbor"
expected = {
    "departures_schedule_board.png": (96, 64),
    "waiting_bench.png": (96, 48),
    "luggage_cart.png": (64, 64),
}
for name, size in expected.items():
    path = asset / name
    need(path.exists() and path.stat().st_size > 100, f"missing asset {name}")
    im = Image.open(path).convert("RGBA")
    need(im.size == size, f"{name} size {im.size} != {size}")
    need(im.getchannel("A").getbbox() is not None, f"{name} is empty")

asset_manifest = json.loads(text(asset / "set02_harbor_manifest.json"))
need(asset_manifest.get("version") == "0691-set02-harbor", "asset manifest version")
need(asset_manifest.get("runtimeOverlays") == [], "Set02 must not add runtime overlays")
need(
    asset_manifest.get("staticPhysicalOwner") == "TMX map layers",
    "Set02 physical owner must be TMX",
)

def map_audit(path: Path, wh: tuple[int, int]) -> tuple[ET.Element, dict[str, list[int]], dict[str, int]]:
    root = ET.parse(path).getroot()
    need(
        (int(root.attrib["width"]), int(root.attrib["height"])) == wh,
        f"{path.name} dimensions",
    )
    tilesets = {
        ts.attrib.get("name", ""): int(ts.attrib["firstgid"])
        for ts in root.findall("tileset")
    }
    layers: dict[str, list[int]] = {}
    for layer in root.findall("layer"):
        data = layer.find("data")
        if data is None or data.attrib.get("encoding") != "csv":
            continue
        toks = [x.strip() for x in (data.text or "").split(",")]
        need(toks and all(toks), f"{path.name}/{layer.attrib.get('name')} empty CSV token")
        vals = [int(x) for x in toks]
        need(
            len(vals) == wh[0] * wh[1],
            f"{path.name}/{layer.attrib.get('name')} tile count",
        )
        layers[layer.attrib["name"]] = vals
    return root, layers, tilesets

dock_root, dock, tilesets = map_audit(
    SRC / "assets/sky_dock_interior.tmx",
    (30, 18),
)
required = {
    "CardchaRouteNoticeBoard0690": 5000,
    "CardchaBoardingGate0690": 5100,
    "CardchaSignalLamp0690": 5200,
    "CardchaCargoCrate0690": 5300,
    "CardchaCollision0690": 5400,
    "CardchaDeparturesBoard0691": 5500,
    "CardchaWaitingBench0691": 5600,
    "CardchaLuggageCart0691": 5700,
}
for name, gid in required.items():
    need(tilesets.get(name) == gid, f"sky dock tileset {name}")

back = dock["BackDecor"]
need(any(5500 <= v < 5524 for v in back), "departures board not placed")
need(any(5600 <= v < 5618 for v in back), "waiting bench not placed")
need(any(5700 <= v < 5716 for v in back), "luggage cart not placed")
need(any(5000 <= v < 5025 for v in back), "0690 route board regressed")
need(any(5100 <= v < 5142 for v in back), "0690 boarding gate regressed")
need(any(5300 <= v < 5309 for v in back), "0690 cargo crate regressed")

w = 30
for y in range(3, 17):
    for x in range(14, 17):
        v = back[y * w + x]
        need(not (5500 <= v < 5800), f"Set02 entered center spine at {x},{y}")

for x, y in [(7, 7), (23, 8), (15, 16), (15, 14)]:
    need(dock["Buildings"][y * w + x] != 5400, f"critical tile blocked {x},{y}")

for x, y in (
    [(x, 6) for x in range(8, 14)]
    + [(x, y) for y in (11, 12) for x in range(3, 9)]
    + [(x, y) for y in (12, 13) for x in range(21, 25)]
):
    need(dock["Buildings"][y * w + x] == 5400, f"Set02 blocker missing {x},{y}")

props = dock_root.find("properties")
prop_map = {
    p.attrib.get("name"): p.attrib.get("value")
    for p in ([] if props is None else props.findall("property"))
}
need(
    prop_map.get("CardchaHarborFurnishings")
    == "0691|departures-board|waiting-bench|luggage-cart|center-spine-protected",
    "0691 map property",
)

deck_root, deck, deck_tilesets = map_audit(
    SRC / "assets/airship_deck.tmx",
    (24, 14),
)
for name, gid in {
    "CardchaObservationWindow0690": 5000,
    "CardchaNavigationConsole0690": 5100,
    "CardchaSignalLamp0690": 5200,
    "CardchaCollision0690": 5400,
}.items():
    need(deck_tilesets.get(name) == gid, f"deck inherited tileset {name}")
need(any(5000 <= v < 5050 for v in deck["BackDecor"]), "deck observation window regressed")
need(any(5100 <= v < 5135 for v in deck["BackDecor"]), "deck navigation console regressed")

service = text(SRC / "Services/AirshipFoundationService.cs")
bridge = re.search(
    r"private void EnsureDeckVanillaFurniture\(GameLocation deck\)(.*?)"
    r"private void EnsureSkyDockVanillaFurniture",
    service,
    re.S,
)
dock_fn = re.search(
    r"private void EnsureSkyDockVanillaFurniture\(GameLocation dock\)(.*?)"
    r"private static void ClearInteriorDecor",
    service,
    re.S,
)
need(bridge is not None and "TryAddInteriorFurniture" not in bridge.group(1), "bridge vanilla clutter active")
need(dock_fn is not None and "TryAddInteriorFurniture" not in dock_fn.group(1), "dock vanilla clutter active")
need("-0690-bridge" in bridge.group(1), "deck marker should remain 0690")
need("-0691-dock" in dock_fn.group(1), "dock marker should advance to 0691")

renderer = text(SRC / "Services/AirshipInteriorStardewRenderer.cs")
for token in [
    "Draw0690WindowOverlay(batch)",
    "Draw0690ConsoleOverlay(batch)",
    "observation_window_overlay_1.png",
    "navigation_console_overlay_4.png",
]:
    need(token in renderer, f"0690 renderer inheritance missing {token}")
need("set02_harbor" not in renderer, "Set02 must not be runtime-rendered")

audit = json.loads(text(ROOT / "render_depth_audit.json"))
need(audit.get("branch") == BRANCH, "render audit branch")
need(
    "0691 Airship Set02 harbor furnishings->TMX; no new runtime physical rendering"
    in audit.get("completedDepthMigrations", []),
    "0691 migration marker",
)
need(
    audit["renderedWorldSubscribers"]["Airship"]["physicalAllowed"] is False,
    "Airship physicalAllowed must remain false",
)

handoff = ROOT / "handoff/ALPHA28_0691_AIRSHIP_PROP_SET02_HARBOR_FURNISHINGS.md"
need(handoff.exists(), "0691 handoff missing")
need(BRANCH in text(ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"), "latest handoff branch")
need(VERSION in text(handoff), "handoff build version")
print("0691 validation PASS")

#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image
import json
import struct
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
ASSETS = SRC / "assets"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.59"
BRANCH = "cardcha-alpha28-0692-airship-rgba-gate-restore"


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("0692 validation FAIL: " + msg)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def png_color_type(path: Path) -> int:
    raw = path.read_bytes()
    need(raw[:8] == b"\x89PNG\r\n\x1a\n", f"not PNG: {path}")
    need(raw[12:16] == b"IHDR", f"missing IHDR: {path}")
    return raw[25]


manifest = json.loads(text(SRC / "manifest.json"))
need(manifest.get("Version") == VERSION, "manifest version")
need(VERSION in text(SRC / "Cardcha.csproj"), "csproj version")
need(VERSION in text(SRC / "Directory.Build.targets"), "Directory.Build.targets version")

flat = {
    "route": "airship_0692_route_notice_board.png",
    "gate": "airship_0692_boarding_gate_arch.png",
    "signal": "airship_0692_signal_lamp.png",
    "cargo": "airship_0692_cargo_parcel_crate.png",
    "window": "airship_0692_observation_window.png",
    "console": "airship_0692_navigation_console.png",
    "collision": "airship_0692_collision_blocker.png",
    "departures": "airship_0692_departures_schedule_board.png",
    "bench": "airship_0692_waiting_bench.png",
    "luggage": "airship_0692_luggage_cart.png",
}

expected_sizes = {
    "route": (80, 80),
    "gate": (112, 96),
    "signal": (32, 48),
    "cargo": (48, 48),
    "window": (160, 80),
    "console": (112, 80),
    "collision": (16, 16),
    "departures": (96, 64),
    "bench": (96, 48),
    "luggage": (64, 64),
}

for key, name in flat.items():
    p = ASSETS / name
    need(p.exists() and p.stat().st_size > 50, f"missing flat RGBA texture {name}")
    with Image.open(p) as im:
        need(im.mode == "RGBA", f"{name} Pillow mode {im.mode}, expected RGBA")
        need(im.size == expected_sizes[key], f"{name} size {im.size} != {expected_sizes[key]}")
    need(png_color_type(p) == 6, f"{name} PNG color type {png_color_type(p)} != 6 RGBA")

# Source-library textures and runtime VFX overlays must also no longer be indexed.
set01 = ASSETS / "airship_props/set01_redux"
set02 = ASSETS / "airship_props/set02_harbor"
for name in [
    "route_notice_board.png", "boarding_gate_arch.png", "signal_lamp.png",
    "cargo_parcel_crate.png", "observation_window_base.png",
    "navigation_console_base.png", "collision_blocker.png",
] + [f"observation_window_overlay_{i}.png" for i in range(1, 5)] \
  + [f"navigation_console_overlay_{i}.png" for i in range(1, 5)]:
    p = set01 / name
    need(p.exists(), f"missing Set01 {name}")
    need(png_color_type(p) == 6, f"Set01 {name} is not true RGBA")
for name in ["departures_schedule_board.png", "waiting_bench.png", "luggage_cart.png"]:
    p = set02 / name
    need(p.exists(), f"missing Set02 {name}")
    need(png_color_type(p) == 6, f"Set02 {name} is not true RGBA")
need(png_color_type(ASSETS / "airship_gate_auth.png") == 6, "outdoor authored gate is not RGBA")


def map_audit(path: Path, wh: tuple[int, int]):
    root = ET.parse(path).getroot()
    need((int(root.attrib["width"]), int(root.attrib["height"])) == wh, f"{path.name} dimensions")
    layers: dict[str, list[int]] = {}
    for layer in root.findall("layer"):
        data = layer.find("data")
        if data is None or data.attrib.get("encoding") != "csv":
            continue
        toks = [x.strip() for x in (data.text or "").split(",")]
        need(toks and all(toks), f"{path.name}/{layer.attrib.get('name')} empty CSV token")
        vals = [int(x) for x in toks]
        need(len(vals) == wh[0] * wh[1], f"{path.name}/{layer.attrib.get('name')} tile count")
        layers[layer.attrib["name"]] = vals
    tilesets = {}
    for ts in root.findall("tileset"):
        image = ts.find("image")
        tilesets[ts.attrib.get("name", "")] = (
            int(ts.attrib["firstgid"]),
            None if image is None else image.attrib.get("source"),
        )
    props = root.find("properties")
    prop_map = {
        p.attrib.get("name"): p.attrib.get("value")
        for p in ([] if props is None else props.findall("property"))
    }
    return root, layers, tilesets, prop_map


def assert_asset_footprint(
    vals: list[int], map_w: int, gid: int, image_path: Path, x: int, y: int, label: str
) -> None:
    im = Image.open(image_path).convert("RGBA")
    cols, rows = im.width // 16, im.height // 16
    for ty in range(rows):
        for tx in range(cols):
            tile = im.crop((tx * 16, ty * 16, tx * 16 + 16, ty * 16 + 16))
            nonempty = tile.getchannel("A").getbbox() is not None
            actual = vals[(y + ty) * map_w + (x + tx)]
            if nonempty:
                expected = gid + ty * cols + tx
                need(actual == expected, f"{label} footprint {x+tx},{y+ty}: {actual} != {expected}")


dock_root, dock, dock_ts, dock_props = map_audit(ASSETS / "sky_dock_interior.tmx", (30, 18))
expected_dock_ts = {
    "CardchaRouteNoticeBoard0690": (5000, flat["route"]),
    "CardchaBoardingGate0690": (5100, flat["gate"]),
    "CardchaSignalLamp0690": (5200, flat["signal"]),
    "CardchaCargoCrate0690": (5300, flat["cargo"]),
    "CardchaCollision0690": (5400, flat["collision"]),
    "CardchaDeparturesBoard0691": (5500, flat["departures"]),
    "CardchaWaitingBench0691": (5600, flat["bench"]),
    "CardchaLuggageCart0691": (5700, flat["luggage"]),
}
for name, expected in expected_dock_ts.items():
    need(dock_ts.get(name) == expected, f"dock tileset {name}: {dock_ts.get(name)} != {expected}")
need(dock_props.get("CardchaTextureContract") == "0692|flat-rgba-tmx-textures|png-color-type-6", "dock texture contract")

back = dock["BackDecor"]
assert_asset_footprint(back, 30, 5000, ASSETS / flat["route"], 2, 3, "route board")
assert_asset_footprint(back, 30, 5100, ASSETS / flat["gate"], 20, 3, "boarding gate")
assert_asset_footprint(back, 30, 5200, ASSETS / flat["signal"], 17, 4, "dock signal")
assert_asset_footprint(back, 30, 5300, ASSETS / flat["cargo"], 26, 10, "cargo")
assert_asset_footprint(back, 30, 5500, ASSETS / flat["departures"], 8, 3, "departures")
assert_asset_footprint(back, 30, 5600, ASSETS / flat["bench"], 3, 10, "waiting bench")
assert_asset_footprint(back, 30, 5700, ASSETS / flat["luggage"], 21, 10, "luggage cart")

for y in range(3, 17):
    for x in range(14, 17):
        v = back[y * 30 + x]
        need(not (5500 <= v < 5800), f"Set02 entered center spine at {x},{y}")

_, deck, deck_ts, deck_props = map_audit(ASSETS / "airship_deck.tmx", (24, 14))
expected_deck_ts = {
    "CardchaObservationWindow0690": (5000, flat["window"]),
    "CardchaNavigationConsole0690": (5100, flat["console"]),
    "CardchaSignalLamp0690": (5200, flat["signal"]),
    "CardchaCollision0690": (5400, flat["collision"]),
}
for name, expected in expected_deck_ts.items():
    need(deck_ts.get(name) == expected, f"deck tileset {name}: {deck_ts.get(name)} != {expected}")
need(deck_props.get("CardchaTextureContract") == "0692|flat-rgba-tmx-textures|png-color-type-6", "deck texture contract")
back_deck = deck["BackDecor"]
assert_asset_footprint(back_deck, 24, 5000, ASSETS / flat["window"], 7, 1, "observation window")
assert_asset_footprint(back_deck, 24, 5100, ASSETS / flat["console"], 9, 5, "navigation console")
assert_asset_footprint(back_deck, 24, 5200, ASSETS / flat["signal"], 4, 4, "deck signal left")
assert_asset_footprint(back_deck, 24, 5200, ASSETS / flat["signal"], 18, 4, "deck signal right")

# Exterior gate contract: the farmer-depth path MUST bypass the Harmony-blocked
# legacy wrapper, while the wrapper remains available for the suppression patch.
service = text(SRC / "Services/AirshipFoundationService.cs")
need("internal void DrawForestGateAtFarmerDepth(SpriteBatch batch)" in service, "farmer-depth gate method missing")
farmer_start = service.index("internal void DrawForestGateAtFarmerDepth(SpriteBatch batch)")
farmer_end = service.index("private static Point ResolveForestGateLandingTile", farmer_start)
farmer_block = service[farmer_start:farmer_end]
need("DrawSkyDockCore(batch, this.ResolveSkyDockTile())" in farmer_block, "farmer-depth path does not call DrawSkyDockCore")
need("this.DrawSkyDock(batch, this.ResolveSkyDockTile())" not in farmer_block, "farmer-depth path still calls blocked legacy DrawSkyDock")
need("private void DrawSkyDockCore(SpriteBatch batch, Point tile)" in service, "DrawSkyDockCore missing")
legacy_start = service.index("private void DrawSkyDock(SpriteBatch batch, Point tile)")
legacy_end = service.index("private void DrawSkyDockCore(SpriteBatch batch, Point tile)", legacy_start)
legacy_block = service[legacy_start:legacy_end]
need("this.DrawSkyDockCore(batch, tile);" in legacy_block, "legacy wrapper does not delegate to core")

patch = text(SRC / "Patches/AirshipGateDepthPatch.cs")
need('"DrawSkyDock"' in patch, "depth patch no longer suppresses legacy wrapper")
need('"DrawSkyDockCore"' not in patch, "depth patch must never suppress DrawSkyDockCore")
need("BeforeFarmerDraw" in patch and "AfterFarmerDraw" in patch, "farmer depth injection missing")

audit = json.loads(text(ROOT / "render_depth_audit.json"))
need(audit.get("branch") == BRANCH, "render audit branch")
need(audit["renderedWorldSubscribers"]["Airship"]["physicalAllowed"] is False, "Airship physicalAllowed must remain false")
for marker in [
    "0692 Airship TMX physical textures->flat true RGBA PNG color type 6",
    "0692 exterior gate farmer-depth path->unpatched DrawSkyDockCore; legacy DrawSkyDock remains suppressed",
]:
    need(marker in audit.get("completedDepthMigrations", []), f"missing audit marker: {marker}")

handoff = ROOT / "handoff/ALPHA28_0692_AIRSHIP_RGBA_GATE_RESTORE.md"
need(handoff.exists(), "0692 handoff missing")
need(BRANCH in text(ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"), "latest handoff branch")
print("0692 validation PASS")

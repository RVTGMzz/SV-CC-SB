#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
DECK = SRC / "assets" / "airship_deck.tmx"
DOCK = SRC / "assets" / "sky_dock_interior.tmx"
PATCH = SRC / "Patches" / "AirshipGateDepthPatch.cs"
AMBIENT = SRC / "Services" / "AirshipAmbientAnimationService.cs"
FOUNDATION = SRC / "Services" / "AirshipFoundationService.cs"
CONSOLE = SRC / "assets" / "airship_props" / "set01_redux" / "navigation_console_body_d3g.png"
REPORT = ROOT / "handoff" / "AIRSHIP_0696D3G_ASSET_SEPARATION_NATURAL_COLLISION_DAYLIGHT_VALIDATION.json"

DECK_W, DECK_H = 24, 14
DOCK_W, DOCK_H = 30, 18


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_map(path: Path, width: int, height: int):
    root = ET.parse(path).getroot()
    props = {
        p.attrib.get("name", ""): p.attrib.get("value", "")
        for p in root.findall("./properties/property")
    }
    layers: dict[str, list[int]] = {}
    for layer in root.findall("layer"):
        name = layer.attrib.get("name", "")
        data = layer.find("data")
        if data is None or data.text is None:
            continue
        values = [int(v.strip()) for v in data.text.replace("\n", "").split(",") if v.strip()]
        if len(values) != width * height:
            raise AssertionError(f"{path.name}:{name} expected {width*height} cells, got {len(values)}")
        layers[name] = values
    return root, props, layers


def cell(layer: list[int], width: int, x: int, y: int) -> int:
    return layer[y * width + x]


def count_range(layer: list[int], lo: int, hi: int) -> int:
    return sum(1 for v in layer if lo <= v <= hi)


def prop_rgb(value: str) -> tuple[int, int, int]:
    parts = [int(x) for x in value.split()]
    if len(parts) != 3:
        raise ValueError(value)
    return parts[0], parts[1], parts[2]


def main() -> None:
    deck_root, deck_props, deck_layers = parse_map(DECK, DECK_W, DECK_H)
    _, dock_props, dock_layers = parse_map(DOCK, DOCK_W, DOCK_H)
    patch = read(PATCH)
    ambient = read(AMBIENT)
    foundation = read(FOUNDATION)

    deck_buildings = deck_layers["Buildings"]
    deck_buildings2 = deck_layers["Buildings2"]
    deck_back2 = deck_layers["Back2"]
    deck_front2 = deck_layers["Front2"]
    dock_buildings = dock_layers["Buildings"]

    console_tileset = next(
        (t for t in deck_root.findall("tileset") if t.attrib.get("firstgid") == "5100"),
        None,
    )
    console_image = console_tileset.find("image") if console_tileset is not None else None
    console_source = console_image.attrib.get("source", "") if console_image is not None else ""

    with Image.open(CONSOLE) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        alpha_values = list(alpha.getdata())
        transparent = sum(1 for a in alpha_values if a < 255)
        fully_transparent = sum(1 for a in alpha_values if a == 0)
        visible = sum(1 for a in alpha_values if a > 0)
        total = max(1, len(alpha_values))
        console_meta = {
            "size": list(rgba.size),
            "mode": rgba.mode,
            "transparentOrPartialPixels": transparent,
            "fullyTransparentPixels": fully_transparent,
            "visiblePixels": visible,
            "transparentRatio": round(transparent / total, 6),
        }

    daylight = prop_rgb(deck_props.get("AmbientLight", "999 999 999"))
    night = prop_rgb(deck_props.get("AmbientNightLight", "0 0 0"))

    gate_posts = all(
        cell(deck_buildings, DECK_W, x, y) == 5400
        for y in range(4, 7)
        for x in (2, 3, 5, 6)
    )
    gate_center_open = all(
        cell(deck_buildings, DECK_W, 4, y) != 5400
        for y in range(4, 7)
    )

    station_collision = all(
        cell(deck_buildings, DECK_W, x, y) == 5400
        for y, xs in (
            (8, range(3, 6)),
            (8, range(18, 21)),
            (11, range(6, 9)),
            (11, range(15, 18)),
        )
        for x in xs
    )

    console_base_collision = all(
        cell(deck_buildings, DECK_W, x, y) == 5400
        for y in (8, 9)
        for x in range(9, 16)
    ) and all(
        cell(deck_buildings, DECK_W, x, 10) != 5400
        for x in range(9, 16)
    )

    dock_gate_posts = all(
        cell(dock_buildings, DOCK_W, x, y) == 5400
        for y in range(5, 9)
        for x in (20, 26)
    )
    dock_gate_center_open = all(
        cell(dock_buildings, DOCK_W, 23, y) != 5400
        for y in range(5, 10)
    )
    dock_route_base = all(
        cell(dock_buildings, DOCK_W, x, y) == 5400
        for y in (6, 7)
        for x in range(2, 7)
    )
    dock_bench_base = all(
        cell(dock_buildings, DOCK_W, x, y) == 5400
        for y in (11, 12)
        for x in range(3, 9)
    )
    dock_cargo_base = all(
        cell(dock_buildings, DOCK_W, x, y) == 5400
        for y in (11, 12)
        for x in range(26, 29)
    )

    station_tokens = [
        "new Point(4, 8)",
        "new Point(19, 8)",
        "new Point(7, 11)",
        "new Point(16, 11)",
    ]

    checks = {
        "consoleAssetExists": CONSOLE.is_file(),
        "consoleAssetSize112x80": console_meta["size"] == [112, 80],
        "consoleAssetHasRealAlpha": (
            console_meta["visiblePixels"] > 0
            and console_meta["fullyTransparentPixels"] > 0
            and console_meta["transparentRatio"] >= 0.05
        ),
        "consoleTilesetUsesD3GTransparentAsset": (
            console_source == "airship_props/set01_redux/navigation_console_body_d3g.png"
            and "navigation_console_base.png" not in DECK.read_text(encoding="utf-8")
        ),
        "consoleFullyGroundedOnBuildings2": (
            count_range(deck_buildings2, 5100, 5134) == 35
            and count_range(deck_front2, 5100, 5134) == 0
            and count_range(deck_back2, 5100, 5134) == 0
        ),
        "observationWindowOwnedByBack2": (
            count_range(deck_back2, 5000, 5049) == 50
            and count_range(deck_buildings2, 5000, 5049) == 0
            and count_range(deck_front2, 5000, 5049) == 0
        ),
        "travelGateLampIntersectionRemoved": all(
            not (5200 <= cell(deck_buildings2, DECK_W, x, y) <= 5205)
            for y in range(4, 7)
            for x in (4, 5)
        ),
        "nativeDaylightPropertiesPresent": (
            deck_props.get("AmbientLight") == "70 70 70"
            and deck_props.get("AmbientNightLight") == "145 135 115"
            and sum(daylight) < sum(night)
        ),
        "deckTravelGateSegmentedCollision": gate_posts and gate_center_open,
        "deckConsoleSolidBaseOnly": console_base_collision,
        "fourUpgradeStationCollisionBases": station_collision,
        "skyDockNativeCollisionDeclared": (
            "native-5400" in dock_props.get("CardchaD3GCollision", "")
            and "no-position-rewind" in dock_props.get("CardchaD3GCollision", "")
        ),
        "skyDockGatePostsBlockedCenterOpen": dock_gate_posts and dock_gate_center_open,
        "skyDockLargePropBasesNative": dock_route_base and dock_bench_base and dock_cargo_base,
        "forcedPlayerPositionArchitectureRemoved": all(
            token not in patch
            for token in (
                "player.Position =",
                "LastSafePlayerPosition",
                "EnforceD3FPhysicalFootprints",
                "EnforceD3GPhysicalFootprints",
                "BuildD3FBlockedRects",
                "BuildD3GBlockedRects",
                "PrepareD3FDeckMap",
                "PrepareD3GDeckMap",
            )
        ),
        "forestGateUsesCollisionQueryNotTeleport": all(
            token in patch
            for token in (
                'typeof(GameLocation),',
                '"isCollidingPosition"',
                "AfterCollisionCheck",
                "BuildForestGateSolidSegments",
                "ResolveSkyDockTile",
            )
        ),
        "runtimeConsoleOwnsAnimationOnly": (
            "state.RadarGlow" in ambient
            and "state.RadarSweep" in ambient
            and "state.RadarPings" in ambient
            and "config.Frame.Path" not in ambient
            and "state.RadarBackground" not in ambient
        ),
        "legacyFullDeckReplayStillRejected": (
            "DeckMarkersMethod.Invoke" not in patch
            and "private static bool SuppressLegacyDeckMarkers()" in patch
            and "=> false;" in patch
        ),
        "fourUpgradeStationsPreserved": all(token in patch for token in station_tokens)
            and 'const string label = "UPGRADE";' in patch,
        "travelAffordancePreserved": (
            'DrawD3GBoardingPad(batch, tile, "TRAVEL");' in patch
            and 'DrawD3GBoardingPad(b, new Point(23, 8), "BOARD AIRSHIP");' in patch
        ),
        "travelGameplayHandlerStillAuthoritative": (
            "ResolveDeckTravelGateTile" in foundation
            and "ActionTouchesStation(action, travelGate)" in foundation
            and "HandleRegion1DepartureRequest();" in foundation
        ),
    }

    report = {
        "phase": "0696D3-G",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "mode": "static-source-asset-tmx-contract",
        "authority": "Ron 2026-09-18 D3-F runtime feedback supersedes D3-F runtime assumptions",
        "assetEvidence": console_meta,
        "lightingEvidence": {
            "dayAmbientLight": list(daylight),
            "nightAmbientLight": list(night),
            "note": "Stardew ambient values are subtractive; lower daytime values mean a brighter room.",
        },
        "checks": checks,
        "runtimeAcceptance": "PENDING-RON-IN-GAME",
        "runtimeNote": "Static/asset/TMX validation is not Runtime PASS. Ron must test the D3-G TEST package in Stardew Valley.",
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

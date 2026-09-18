#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
ROOM1 = SRC / "assets" / "sky_dock_interior.tmx"
ROOM2 = SRC / "assets" / "airship_deck.tmx"
PATCH = SRC / "Patches" / "AirshipGateDepthPatch.cs"
FOUNDATION = SRC / "Services" / "AirshipFoundationService.cs"
AMBIENT = SRC / "Services" / "AirshipAmbientAnimationService.cs"
RENDERER = SRC / "Services" / "AirshipInteriorStardewRenderer.cs"
MANIFEST = SRC / "manifest.json"
CSPROJ = SRC / "Cardcha.csproj"
TARGETS = SRC / "Directory.Build.targets"
I18N_EN = SRC / "i18n" / "default.json"
I18N_VI = SRC / "i18n" / "vi.json"

RUNNER = SRC / "assets" / "airship_props" / "set01_redux" / "airship_runner_d3h.png"
CONSOLE_BASE = SRC / "assets" / "airship_props" / "set01_redux" / "navigation_console_base.png"
CONSOLE_D3H = SRC / "assets" / "airship_props" / "set01_redux" / "navigation_console_body_d3h.png"
CONSOLE_D3G = SRC / "assets" / "airship_props" / "set01_redux" / "navigation_console_body_d3g.png"
HARBOR = SRC / "assets" / "airship_props" / "set02_harbor"

REPORT = ROOT / "handoff" / "AIRSHIP_0696D3H_DENSITY_RUNNER_INTERACTION_POLISH_VALIDATION.json"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.72"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_map(path: Path):
    root = ET.parse(path).getroot()
    width = int(root.attrib["width"])
    height = int(root.attrib["height"])
    props = {
        p.attrib.get("name", ""): p.attrib.get("value", "")
        for p in root.findall("./properties/property")
    }
    layers: dict[str, list[int]] = {}
    for layer in root.findall("layer"):
        data = layer.find("data")
        if data is None or data.text is None:
            continue
        vals = [int(v.strip()) for v in data.text.replace("\n", "").split(",") if v.strip()]
        if len(vals) != width * height:
            raise AssertionError(f"{path.name}:{layer.attrib.get('name')} cell count {len(vals)} != {width*height}")
        layers[layer.attrib["name"]] = vals
    tilesets = {}
    for ts in root.findall("tileset"):
        img = ts.find("image")
        tilesets[int(ts.attrib["firstgid"])] = {
            "name": ts.attrib.get("name", ""),
            "source": img.attrib.get("source", "") if img is not None else "",
        }
    return root, width, height, props, layers, tilesets


def cell(layer: list[int], width: int, x: int, y: int) -> int:
    return layer[y * width + x]


def all_eq(layer, width, points, value):
    return all(cell(layer, width, x, y) == value for x, y in points)


def bbox_size(path: Path):
    with Image.open(path) as im:
        box = im.convert("RGBA").getbbox()
        if box is None:
            return (0, 0), list(im.size)
        return (box[2] - box[0], box[3] - box[1]), list(im.size)


def ratio_close(a: int, b: int, target=2/3, tol=0.08):
    return b > 0 and abs((a / b) - target) <= tol


def main():
    _, w1, h1, p1, l1, ts1 = parse_map(ROOM1)
    _, w2, h2, p2, l2, ts2 = parse_map(ROOM2)
    foundation = FOUNDATION.read_text(encoding="utf-8")
    patch = PATCH.read_text(encoding="utf-8")
    ambient = AMBIENT.read_text(encoding="utf-8")
    renderer = RENDERER.read_text(encoding="utf-8")
    en = json.loads(I18N_EN.read_text(encoding="utf-8"))
    vi = json.loads(I18N_VI.read_text(encoding="utf-8"))

    # Pixel-art asset evidence.
    with Image.open(RUNNER) as im:
        rgba = im.convert("RGBA")
        colors = rgba.getcolors(maxcolors=10000) or []
        runner_alpha = sorted(set(a for *_, a in rgba.getdata()))
        runner_info = {
            "size": list(rgba.size),
            "uniqueColors": len(colors),
            "alphaValues": runner_alpha,
        }

    with Image.open(CONSOLE_D3H) as im:
        rgba = im.convert("RGBA")
        alphas = sorted(set(a for *_, a in rgba.getdata()))
        transparent = sum(1 for *_, a in rgba.getdata() if a == 0)
        visible = sum(1 for *_, a in rgba.getdata() if a == 255)
        console_info = {
            "size": list(rgba.size),
            "alphaValues": alphas,
            "transparentPixels": transparent,
            "opaquePixels": visible,
            "sha256": sha(CONSOLE_D3H),
            "sourceSha256": sha(CONSOLE_BASE),
            "oldD3GSha256": sha(CONSOLE_D3G),
        }

    scaled = {}
    for new_name, old_name in (
        ("waiting_bench_d3h.png", "waiting_bench.png"),
        ("lost_found_board_d3h.png", "departures_schedule_board.png"),
        ("luggage_cart_d3h.png", "luggage_cart.png"),
    ):
        new_path, old_path = HARBOR / new_name, HARBOR / old_name
        new_bbox, new_canvas = bbox_size(new_path)
        old_bbox, old_canvas = bbox_size(old_path)
        scaled[new_name] = {
            "newBBox": list(new_bbox), "oldBBox": list(old_bbox),
            "canvas": new_canvas,
            "nearestScaleApprox2over3": (
                new_canvas == old_canvas
                and ratio_close(new_bbox[0], old_bbox[0])
                and ratio_close(new_bbox[1], old_bbox[1])
            ),
        }

    b1, b12, f12 = l1["Buildings"], l1["Buildings2"], l1["Front2"]
    back12 = l1["Back2"]
    b2, b22, f22, back22 = l2["Buildings"], l2["Buildings2"], l2["Front2"], l2["Back2"]

    room1_front_lanes = {
        "notice": all(cell(b1, w1, x, 8) != 5400 for x in range(2, 7)),
        "lostFound": all(cell(b1, w1, x, 7) != 5400 for x in range(8, 14)),
        "bench": all(cell(b1, w1, x, 12) != 5400 for x in range(3, 9)),
        "luggage": all(cell(b1, w1, x, 13) != 5400 for x in range(14, 18)),
        "cargo": all(cell(b1, w1, x, 12) != 5400 for x in range(20, 23)),
    }

    checks = {
        "versionManifest72": VERSION in MANIFEST.read_text(encoding="utf-8"),
        "versionCsproj72": VERSION in CSPROJ.read_text(encoding="utf-8"),
        "versionTargets72": VERSION in TARGETS.read_text(encoding="utf-8"),

        # Room 1 density + lighting.
        "room1ExactlyTwoThirdsOldArea": (w1, h1) == (24, 15) and (w1*h1*3 == 30*18*2),
        "room1DoorwayCentered": cell(b1, w1, 11, 14) == 0 and cell(b1, w1, 12, 14) == 0,
        "room1DaylightRecovered": p1.get("AmbientLight") == "25 25 25" and p1.get("AmbientNightLight") == "105 95 85",
        "room1D3HScaledAssetsWired": (
            ts1[5500]["source"].endswith("lost_found_board_d3h.png")
            and ts1[5600]["source"].endswith("waiting_bench_d3h.png")
            and ts1[5700]["source"].endswith("luggage_cart_d3h.png")
        ),
        "room1ScaledPropsAreApproxTwoThirdsNearestCanvas": all(x["nearestScaleApprox2over3"] for x in scaled.values()),
        "room1RunnerIsMapNative": (
            ts1[5800]["source"].endswith("airship_runner_d3h.png")
            and cell(back12, w1, 17, 8) == 5803
            and cell(back12, w1, 12, 13) == 5802
        ),
        "runnerPixelArtSmallPalette": (
            runner_info["size"] == [192, 16]
            and runner_info["uniqueColors"] <= 16
            and len(runner_info["alphaValues"]) <= 4
        ),

        # Room1 natural collision + front interaction rows.
        "noticeBoardBodyBlocked": all_eq(b1, w1, [(x,y) for y in (6,7) for x in range(2,7)], 5400),
        "lostFoundBodyBlocked": all_eq(b1, w1, [(x,6) for x in range(8,14)], 5400),
        "waitingBenchBaseBlocked": all_eq(b1, w1, [(x,11) for x in range(3,9)], 5400),
        "luggageBaseBlocked": all_eq(b1, w1, [(x,12) for x in range(14,18)], 5400),
        "cargoBaseBlocked": all_eq(b1, w1, [(x,11) for x in range(20,23)], 5400),
        "room1FrontInteractionRowsOpen": all(room1_front_lanes.values()),
        "room1GatePostsBlockedCenterOpen": (
            all_eq(b1,w1,[(14,y) for y in range(5,9)]+[(20,y) for y in range(5,9)],5400)
            and cell(b1,w1,17,8) != 5400
        ),
        "room1LampBlocked": cell(b1,w1,21,6) == 5400 and cell(b1,w1,22,6) == 5400,
        "room1HeadClipPropsNotFront2": (
            not any(5600 <= v <= 5617 for v in f12)
            and not any(5700 <= v <= 5715 for v in f12)
            and not any(5300 <= v <= 5308 for v in f12)
        ),

        # Interaction authority: bench is no longer Lost & Found.
        "lostFoundMovedOffBench": (
            "return new Point(Math.Clamp(10, 2, width - 3), Math.Clamp(6, 3, height - 3));" in foundation
            and "ResolveSkyDockWaitingBenchTile" in foundation
            and "ResolveSkyDockLuggageCartTile" in foundation
        ),
        "room1PropInfoLocalized": all(k in en and k in vi for k in (
            "airship.skydock.waiting_bench.info",
            "airship.skydock.luggage_cart.info",
            "airship.skydock.cargo.info",
        )),

        # Console #7: full detail restored, transparent outer canvas retained.
        "consoleD3HUsesOriginalFullDetailBytes": (
            console_info["sha256"] == console_info["sourceSha256"]
            and console_info["sha256"] != console_info["oldD3GSha256"]
        ),
        "consoleD3HHardAlphaTransparent": (
            console_info["size"] == [112,80]
            and console_info["alphaValues"] == [0,255]
            and console_info["transparentPixels"] > 1000
            and console_info["opaquePixels"] > 5000
        ),
        "deckUsesD3HConsoleBody": ts2[5100]["source"].endswith("navigation_console_body_d3h.png"),
        "consoleNeverReturnsToFront2": not any(5100 <= v <= 5134 for v in f22),

        # Room2 runner / travel / upgrades / lamp.
        "deckRunnerMapNative": (
            ts2[5800]["source"].endswith("airship_runner_d3h.png")
            and cell(back22,w2,4,5) == 5803
            and cell(back22,w2,12,12) == 5802
        ),
        "travelGateOneAndHalfScale": "const int width = 366;" in patch,
        "navigationUpgradeTwoX": "i == 1 ? 192 : 96" in patch,
        "fourUpgradeSocketsPreserved": all(token in patch for token in (
            "new Point(4, 8)", "new Point(19, 8)", "new Point(7, 11)", "new Point(16, 11)"
        )),
        "fourUpgradeBasesBlocked": all_eq(b2,w2,
            [(x,8) for x in range(3,6)] +
            [(x,8) for x in range(18,21)] +
            [(x,11) for x in range(6,9)] +
            [(x,11) for x in range(15,18)], 5400),
        "upgradeGlowPassPresent": "D3-H station glow" in patch,
        "deckLampMovedAndBlocked": (
            cell(b22,w2,21,4) == 5200 and cell(b22,w2,22,4) == 5201
            and cell(b2,w2,21,6) == 5400 and cell(b2,w2,22,6) == 5400
        ),

        # Window #11 wall attachment / depth.
        "observationWindowExactWallFootprint": "ObservationWindowPresentationScale = 4.0f" in ambient,
        "observationWindowBodyBackOwned": (
            sum(1 for v in back22 if 5000 <= v <= 5049) == 50
            and sum(1 for v in b22 if 5000 <= v <= 5049) == 0
            and sum(1 for v in f22 if 5000 <= v <= 5049) == 0
        ),

        # Never regress to ghost/body position correction.
        "noForcedFarmerPositionCorrection": all(t not in patch for t in (
            "player.Position =", "LastSafePlayerPosition", "EnforceD3FPhysicalFootprints",
            "EnforceD3GPhysicalFootprints", "BuildD3FBlockedRects", "BuildD3GBlockedRects"
        )),
        "room1BoardingPadResolvesNewBay": (
            'ResolvePoint("ResolveSkyDockInteriorBayTile", location, new Point(17, 8))' in patch
            and '"BOARD AIRSHIP"' in patch
        ),
        "room1FunctionalLightPoolsPresent": "0696D3-H: map AmbientLight owns general daylight" in renderer,
    }

    report = {
        "phase": "0696D3-H",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "version": VERSION,
        "authority": "Ron post-D3-G 12-image runtime feedback + Stardew-style rug constraint",
        "room1": {
            "size": [w1,h1],
            "oldSize": [30,18],
            "areaRatio": (w1*h1)/(30*18),
            "frontLanes": room1_front_lanes,
            "scaledAssets": scaled,
        },
        "runner": runner_info,
        "console": console_info,
        "checks": checks,
        "runtimeAcceptance": "PENDING-RON-IN-GAME",
        "runtimeNote": "Static validation cannot prove final visual scale, readability, collision feel, or Runtime PASS. Ron must test the D3-H TEST package.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

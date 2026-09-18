#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.73"

DECK = SRC / "assets" / "airship_deck.tmx"
DOCK = SRC / "assets" / "sky_dock_interior.tmx"
PATCH = SRC / "Patches" / "AirshipGateDepthPatch.cs"
FOUNDATION = SRC / "Services" / "AirshipFoundationService.cs"
AMBIENT = SRC / "Services" / "AirshipAmbientAnimationService.cs"
RENDERER = SRC / "Services" / "AirshipInteriorStardewRenderer.cs"
RESONANCE = SRC / "Services" / "ChaChaSkillMaterialService.cs"
CONSOLE = SRC / "assets" / "airship_props" / "set01_redux" / "navigation_console_body_d3i.png"
AMBIENT_MANIFEST = SRC / "assets" / "airship_props" / "set01_redux" / "airship_ambient_manifest.json"
REPORT = ROOT / "handoff" / "AIRSHIP_0696D3I_RUNTIME_CORRECTION_VALIDATION.json"


def parse_map(path: Path):
    root = ET.parse(path).getroot()
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    props = {p.attrib.get("name",""): p.attrib.get("value","") for p in root.findall("./properties/property")}
    layers = {}
    for layer in root.findall("layer"):
        data = layer.find("data")
        if data is None or data.text is None:
            continue
        vals = [int(v.strip()) for v in data.text.replace("\n","").split(",") if v.strip()]
        if len(vals) != w*h:
            raise AssertionError(f"{path.name}:{layer.attrib.get('name')} count {len(vals)} != {w*h}")
        layers[layer.attrib["name"]] = vals
    tilesets = {}
    for ts in root.findall("tileset"):
        img = ts.find("image")
        tilesets[int(ts.attrib["firstgid"])] = {
            "name": ts.attrib.get("name",""),
            "source": img.attrib.get("source","") if img is not None else "",
        }
    return w,h,props,layers,tilesets


def cell(layer, w, x, y):
    return layer[y*w+x]


def is_beige_candidate(r,g,b,a):
    return a > 0 and r >= 205 and g >= 155 and b >= 95 and (r-b) >= 60 and (g-b) >= 35


def main():
    w2,h2,p2,l2,t2 = parse_map(DECK)
    w1,h1,p1,l1,t1 = parse_map(DOCK)
    patch = PATCH.read_text(encoding="utf-8")
    foundation = FOUNDATION.read_text(encoding="utf-8")
    ambient = AMBIENT.read_text(encoding="utf-8")
    renderer = RENDERER.read_text(encoding="utf-8")
    resonance = RESONANCE.read_text(encoding="utf-8")
    ambient_manifest = json.loads(AMBIENT_MANIFEST.read_text(encoding="utf-8"))

    if not CONSOLE.exists():
        raise SystemExit("D3-I console asset was not materialized before validation")

    with Image.open(CONSOLE) as im:
        rgba = im.convert("RGBA")
        pixels = list(rgba.getdata())
        alpha_values = sorted(set(a for *_,a in pixels))
        transparent = sum(a == 0 for *_,a in pixels)
        opaque = sum(a == 255 for *_,a in pixels)
        beige_opaque = sum(is_beige_candidate(r,g,b,a) for r,g,b,a in pixels)

    all_deck_tiles = [v for layer in l2.values() for v in layer]

    checks = {
        "versionManifest73": VERSION in (SRC/"manifest.json").read_text(encoding="utf-8"),
        "versionCsproj73": VERSION in (SRC/"Cardcha.csproj").read_text(encoding="utf-8"),
        "versionTargets73": VERSION in (SRC/"Directory.Build.targets").read_text(encoding="utf-8"),
        "versionDeck73": p2.get("CardchaAirshipVersion") == VERSION,
        "versionDock73": p1.get("CardchaAirshipVersion") == VERSION,
        "ambientManifest73": ambient_manifest.get("version") == VERSION,

        "consoleD3ISourceWired": t2[5100]["source"].endswith("navigation_console_body_d3i.png"),
        "consoleD3IHardAlpha": rgba.size == (112,80) and alpha_values == [0,255],
        "consoleD3IMatteRemoved": transparent >= 3000 and beige_opaque <= 250,
        "consoleD3IDetailPreserved": opaque >= 5000,
        "consoleSweepReduced": (
            "ConsoleSweepPresentationScale = 0.58f" in ambient
            and "ConsoleFxPresentationScale = 0.72f" in ambient
            and "ScaleAroundCenter(viewport, ConsoleSweepPresentationScale)" in ambient
        ),

        "windowShellRemovedFromTMX": not any(5000 <= v <= 5049 for v in all_deck_tiles),
        "windowFramePreFarmerRuntime": (
            "Window frame leaves TMX entirely" in ambient
            and "Texture2D? frame = GetTexture(config.Frame.Path);" in ambient
            and "0.8848f" in ambient
        ),
        "windowStillExactScale": "ObservationWindowPresentationScale = 4.0f" in ambient,

        "allUpgradeStationsBackTo96": (
            "const int presentationSize = 96;" in patch
            and "i == 1 ? 192 : 96" not in patch
            and "const int fallbackWidth = 68;" in patch
        ),
        "resonanceMachineActuallyTwoX": (
            "ChaCha Resonance machine Ron asked to enlarge" in resonance
            and "168, 36" in resonance
            and "132, 40" in resonance
            and "* 96f" in resonance
            and "1.44f" in resonance
        ),
        "fourUpgradeSocketsPreserved": all(x in patch for x in (
            "new Point(4, 8)", "new Point(19, 8)", "new Point(7, 11)", "new Point(16, 11)"
        )),

        "lampMovedAwayFromResonance": (
            cell(l2["Buildings2"],w2,18,4) == 5200
            and cell(l2["Buildings2"],w2,19,4) == 5201
            and not any(5200 <= cell(l2["Buildings2"],w2,x,y) <= 5205 for y in range(4,7) for x in (21,22))
        ),
        "lampCollisionMoved": (
            cell(l2["Buildings"],w2,18,6) == 5400
            and cell(l2["Buildings"],w2,19,6) == 5400
            and cell(l2["Buildings"],w2,21,6) != 5400
            and cell(l2["Buildings"],w2,22,6) != 5400
        ),

        "boardingPadInsideGate": (
            cell(l1["Back2"],w1,17,7) == 5803
            and cell(l1["Back2"],w1,17,8) == 5800
            and 'new Point(17, 7)' in patch
            and "Math.Clamp(7, 3, height - 5)" in foundation
            and "17f * 64f + 32f, 7f * 64f + 34f" in renderer
        ),
        "boardAirshipStillPresent": '"BOARD AIRSHIP"' in patch,
        "travelStillPresent": '"TRAVEL"' in patch and "const int width = 366;" in patch,

        "noForcedFarmerPositionCorrection": all(token not in patch for token in (
            "player.Position =", "LastSafePlayerPosition", "EnforceD3FPhysicalFootprints",
            "EnforceD3GPhysicalFootprints", "BuildD3FBlockedRects", "BuildD3GBlockedRects"
        )),
    }

    report = {
        "phase":"0696D3-I",
        "status":"PASS" if all(checks.values()) else "FAIL",
        "version":VERSION,
        "authority":"Ron post-D3-H runtime feedback: console matte/gauge, Window head occlusion, wrong 2x target, BOARD AIRSHIP pad outside gate",
        "console":{
            "size":list(rgba.size),
            "alphaValues":alpha_values,
            "transparentPixels":transparent,
            "opaquePixels":opaque,
            "beigeOpaquePixels":beige_opaque,
        },
        "checks":checks,
        "runtimeAcceptance":"PENDING-RON-IN-GAME",
        "runtimeNote":"Static validation cannot prove visual acceptance. Ron must test the exact D3-I package."
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if report["status"] != "PASS":
        raise SystemExit(2)

if __name__ == "__main__":
    main()

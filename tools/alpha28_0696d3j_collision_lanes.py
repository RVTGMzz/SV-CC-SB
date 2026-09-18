#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.74"

DOCK = SRC / "assets" / "sky_dock_interior.tmx"
DECK = SRC / "assets" / "airship_deck.tmx"
PATCH = SRC / "Patches" / "AirshipGateDepthPatch.cs"
FOUNDATION = SRC / "Services" / "AirshipFoundationService.cs"
RESONANCE = SRC / "Services" / "ChaChaSkillMaterialService.cs"
I18N_EN = SRC / "i18n" / "default.json"
I18N_VI = SRC / "i18n" / "vi.json"
AMBIENT = SRC / "assets" / "airship_props" / "set01_redux" / "airship_ambient_manifest.json"
REPORT = ROOT / "handoff" / "AIRSHIP_0696D3J_COLLISION_LANES_VALIDATION.json"


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
            raise AssertionError(f"{path.name}:{layer.attrib.get('name')} {len(vals)} != {w*h}")
        layers[layer.attrib["name"]] = vals
    return w,h,props,layers


def cell(layer, w, x, y):
    return layer[y*w+x]


def all_value(layer, w, points, value):
    return all(cell(layer,w,x,y)==value for x,y in points)


def all_not_value(layer, w, points, value):
    return all(cell(layer,w,x,y)!=value for x,y in points)


def rect_points(x0,y0,w,h):
    return [(x,y) for y in range(y0,y0+h) for x in range(x0,x0+w)]


def runner_points(layer, w, h):
    out=[]
    for y in range(h):
        for x in range(w):
            v=cell(layer,w,x,y)
            if 5800 <= v <= 5811:
                out.append((x,y))
    return out


def main():
    w1,h1,p1,l1 = parse_map(DOCK)
    w2,h2,p2,l2 = parse_map(DECK)
    patch = PATCH.read_text(encoding="utf-8")
    foundation = FOUNDATION.read_text(encoding="utf-8")
    resonance = RESONANCE.read_text(encoding="utf-8")
    en = json.loads(I18N_EN.read_text(encoding="utf-8"))
    vi = json.loads(I18N_VI.read_text(encoding="utf-8"))
    ambient = json.loads(AMBIENT.read_text(encoding="utf-8"))

    b1,b12,back12 = l1["Buildings"],l1["Buildings2"],l1["Back2"]
    b2,back22 = l2["Buildings"],l2["Back2"]

    room1_runner = runner_points(back12,w1,h1)
    room2_runner = runner_points(back22,w2,h2)

    checks = {
        "versionManifest74": VERSION in (SRC/"manifest.json").read_text(encoding="utf-8"),
        "versionCsproj74": VERSION in (SRC/"Cardcha.csproj").read_text(encoding="utf-8"),
        "versionTargets74": VERSION in (SRC/"Directory.Build.targets").read_text(encoding="utf-8"),
        "versionDock74": p1.get("CardchaAirshipVersion")==VERSION,
        "versionDeck74": p2.get("CardchaAirshipVersion")==VERSION,
        "versionAmbient74": ambient.get("version")==VERSION,

        "room1Still24x15": (w1,h1)==(24,15),
        "room1LightingRecovered": p1.get("AmbientLight")=="230 225 215" and p1.get("AmbientNightLight")=="160 150 140",

        # Room 1 visual reflow keeps runner free.
        "waitingBenchShiftedLeft": all(
            cell(b12,w1,2+x,9+y)==5600+y*6+x for y in range(3) for x in range(6)
        ),
        "luggageShiftedOffRunner": all(
            cell(b12,w1,8+x,9+y)==5700+y*4+x for y in range(4) for x in range(4)
        ),

        # Room 1 full-body collision.
        "noticeFullBodyBlocked": all_value(b1,w1,rect_points(2,5,5,3),5400),
        "lostFoundFullBodyBlocked": all_value(b1,w1,rect_points(8,5,6,2),5400),
        "benchFullBodyBlocked": all_value(b1,w1,rect_points(2,9,6,3),5400),
        "luggageFullBodyBlocked": all_value(b1,w1,rect_points(8,9,4,4),5400),
        "cargoFullBodyBlocked": all_value(b1,w1,rect_points(20,9,3,3),5400),
        "boardingSidesBlocked": (
            all_value(b1,w1,rect_points(14,5,3,4),5400)
            and all_value(b1,w1,rect_points(18,5,3,4),5400)
        ),
        "boardingCenterThroatOpen": all_not_value(b1,w1,[(17,y) for y in range(5,9)],5400),
        "room1LampBlocked": all_value(b1,w1,rect_points(21,5,2,2),5400),

        # Exact front interaction lanes.
        "noticeFrontLaneOpen": all_not_value(b1,w1,[(x,8) for x in range(2,7)],5400),
        "lostFoundFrontLaneOpen": all_not_value(b1,w1,[(x,7) for x in range(8,14)],5400),
        "benchFrontLaneOpen": all_not_value(b1,w1,[(x,12) for x in range(2,8)],5400),
        "luggageFrontLaneOpen": all_not_value(b1,w1,[(x,13) for x in range(8,12)],5400),
        "cargoFrontLaneOpen": all_not_value(b1,w1,[(x,12) for x in range(20,23)],5400),
        "room1RunnerNeverBlocked": all_not_value(b1,w1,room1_runner,5400),
        "boardAirshipStillInsideGate": cell(back12,w1,17,7)==5803 and cell(b1,w1,17,7)!=5400,

        # Deck collision lanes.
        "travelGateSidesBlocked": (
            all_value(b2,w2,rect_points(2,4,2,3),5400)
            and all_value(b2,w2,rect_points(5,4,2,3),5400)
        ),
        "travelCenterOpen": all_not_value(b2,w2,[(4,5),(4,6),(4,7)],5400),
        "consoleFullBodyBlocked": all_value(b2,w2,rect_points(9,5,7,5),5400),
        "consoleFrontLaneOpen": all_not_value(b2,w2,[(x,10) for x in range(9,16)],5400),
        "fourUpgradeBasesBlocked": (
            all_value(b2,w2,rect_points(3,8,3,1),5400)
            and all_value(b2,w2,rect_points(18,8,3,1),5400)
            and all_value(b2,w2,rect_points(6,11,3,1),5400)
            and all_value(b2,w2,rect_points(15,11,3,1),5400)
        ),
        "lampBlocked": all_value(b2,w2,rect_points(18,6,2,1),5400),
        "resonanceBodyBlocked": all_value(b2,w2,rect_points(20,5,3,2),5400),
        "resonanceFrontLaneOpen": all_not_value(b2,w2,[(x,7) for x in range(20,23)],5400),
        "room2RunnerNeverBlocked": all_not_value(b2,w2,room2_runner,5400),
        "travelRunnerEndsOnPad": cell(back22,w2,4,5)==5803,

        # Runtime collision query mirrors TMX instead of moving Farmer.
        "collisionQueryMirrorsDock": "BuildD3JSkyDockSolidSegments" in patch and "TileRect(2, 5, 5, 3)" in patch and "TileRect(8, 9, 4, 4)" in patch,
        "collisionQueryMirrorsDeck": "BuildD3JDeckSolidSegments" in patch and "TileRect(9, 5, 7, 5)" in patch and "TileRect(20, 5, 3, 2)" in patch,
        "noForcedPositionCorrection": all(t not in patch for t in (
            "player.Position =", "LastSafePlayerPosition", "EnforceD3FPhysicalFootprints",
            "EnforceD3GPhysicalFootprints", "BuildD3FBlockedRects", "BuildD3GBlockedRects"
        )),

        # Interaction targets follow the new lanes/reflow.
        "insideGateBayFallback": 'ResolveSkyDockInteriorBayTile", new Point(17, 7)' in patch,
        "luggageResolverMoved": "Math.Clamp(9, 2, width - 3), Math.Clamp(12, 4, height - 2)" in foundation,
        "resonanceInteractionFrontLane": "StationInteractionTile = new(21, 7)" in resonance,
        "room1InfoLocalized": all(k in en and k in vi for k in (
            "airship.skydock.waiting_bench.info",
            "airship.skydock.luggage_cart.info",
            "airship.skydock.cargo.info",
        )),
    }

    report={
        "phase":"0696D3-J",
        "status":"PASS" if all(checks.values()) else "FAIL",
        "version":VERSION,
        "authority":"Ron's original 12-point room feedback reasserted after D3-I: collision/blocking was not sufficiently materialized.",
        "room1":{
            "size":[w1,h1],
            "ambientDay":p1.get("AmbientLight"),
            "ambientNight":p1.get("AmbientNightLight"),
            "runnerTiles":room1_runner,
        },
        "room2":{
            "size":[w2,h2],
            "runnerTiles":room2_runner,
        },
        "checks":checks,
        "runtimeAcceptance":"PENDING-RON-IN-GAME",
        "runtimeNote":"D3-J proves collision contracts statically and by native collision-query wiring. Ron must still confirm actual movement in game."
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if report["status"]!="PASS":
        raise SystemExit(2)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.75"

PATCH = SRC / "Patches" / "AirshipGateDepthPatch.cs"
MODENTRY = SRC / "ModEntry.cs"
DOCK = SRC / "assets" / "sky_dock_interior.tmx"
DECK = SRC / "assets" / "airship_deck.tmx"
AMBIENT = SRC / "assets" / "airship_props" / "set01_redux" / "airship_ambient_manifest.json"
REPORT = ROOT / "handoff" / "AIRSHIP_0696D3K_COLLISION_HOOK_VALIDATION.json"


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


def cell(a,w,x,y):
    return a[y*w+x]


def rect(x0,y0,w,h):
    return [(x,y) for y in range(y0,y0+h) for x in range(x0,x0+w)]


def all_value(a,w,points,value):
    return all(cell(a,w,x,y)==value for x,y in points)


def all_not(a,w,points,value):
    return all(cell(a,w,x,y)!=value for x,y in points)


def main():
    patch = PATCH.read_text(encoding="utf-8")
    modentry = MODENTRY.read_text(encoding="utf-8")
    manifest = json.loads((SRC/"manifest.json").read_text(encoding="utf-8"))
    ambient = json.loads(AMBIENT.read_text(encoding="utf-8"))
    w1,h1,p1,l1 = parse_map(DOCK)
    w2,h2,p2,l2 = parse_map(DECK)
    b1,b2 = l1["Buildings"],l2["Buildings"]

    checks = {
        "manifestVersion75": manifest.get("Version") == VERSION,
        "csprojVersion75": VERSION in (SRC/"Cardcha.csproj").read_text(encoding="utf-8"),
        "targetsVersion75": VERSION in (SRC/"Directory.Build.targets").read_text(encoding="utf-8"),
        "dockVersion75": p1.get("CardchaAirshipVersion") == VERSION,
        "deckVersion75": p2.get("CardchaAirshipVersion") == VERSION,
        "ambientVersion75": ambient.get("version") == VERSION,

        "dynamicCollisionResolver": (
            "AccessTools.GetDeclaredMethods(typeof(GameLocation))" in patch
            and 'candidate.Name.Equals("isCollidingPosition", StringComparison.Ordinal)' in patch
            and "candidate.ReturnType != typeof(bool)" in patch
            and "parameters[0].ParameterType != typeof(Rectangle)" in patch
            and "collisionHookCount++" in patch
        ),
        "noLegacyExactNineParamSignature": (
            "typeof(xTile.Dimensions.Rectangle)" not in patch
            and 'AccessTools.Method(\n            typeof(GameLocation),\n            "isCollidingPosition"' not in patch
        ),
        "genericHarmonyPostfix": (
            "MethodBase __originalMethod" in patch
            and "object[] __args" in patch
            and "ParameterInfo[] parameters = __originalMethod.GetParameters();" in patch
            and 'parameter.Name?.Equals("isFarmer", StringComparison.OrdinalIgnoreCase)' in patch
            and "typeof(Character).IsAssignableFrom(parameter.ParameterType)" in patch
        ),
        "collisionHookSuccessLog": "installed collision hooks on {collisionHookCount}" in patch,
        "noForcedFarmerPosition": all(t not in patch for t in (
            "player.Position =", "LastSafePlayerPosition", "EnforceD3FPhysicalFootprints",
            "EnforceD3GPhysicalFootprints"
        )),

        "startupBannerUsesManifestVersion": (
            '$"Cardcha! {this.ModManifest.Version} 0696D3-K COLLISION HOOK RUNTIME FIX TEST"' in modentry
            and "0.3.0-alpha.28.0.4.14.4.5.12.69 0686 HOLLOW CURATOR ARCHIVE RULE ADAPTATION TEST" not in modentry
        ),

        # Preserve D3-J collision footprint contract.
        "room1NoticeBlocked": all_value(b1,w1,rect(2,5,5,3),5400),
        "room1LostFoundBlocked": all_value(b1,w1,rect(8,5,6,2),5400),
        "room1BenchBlocked": all_value(b1,w1,rect(2,9,6,3),5400),
        "room1LuggageBlocked": all_value(b1,w1,rect(8,9,4,4),5400),
        "room1CargoBlocked": all_value(b1,w1,rect(20,9,3,3),5400),
        "room1BoardingCenterOpen": all_not(b1,w1,[(17,y) for y in range(5,9)],5400),

        "deckTravelSidesBlocked": (
            all_value(b2,w2,rect(2,4,2,3),5400)
            and all_value(b2,w2,rect(5,4,2,3),5400)
        ),
        "deckConsoleBlocked": all_value(b2,w2,rect(9,5,7,5),5400),
        "deckFourUpgradeBasesBlocked": (
            all_value(b2,w2,rect(3,8,3,1),5400)
            and all_value(b2,w2,rect(18,8,3,1),5400)
            and all_value(b2,w2,rect(6,11,3,1),5400)
            and all_value(b2,w2,rect(15,11,3,1),5400)
        ),
        "deckLampBlocked": all_value(b2,w2,rect(18,6,2,1),5400),
        "deckResonanceBlocked": all_value(b2,w2,rect(20,5,3,2),5400),

        "runtimeSegmentsRenamedD3K": (
            "BuildD3KSkyDockSolidSegments" in patch
            and "BuildD3KDeckSolidSegments" in patch
            and "BuildD3JSkyDockSolidSegments" not in patch
            and "BuildD3JDeckSolidSegments" not in patch
        ),
    }

    report = {
        "phase":"0696D3-K",
        "status":"PASS" if all(checks.values()) else "FAIL",
        "version":VERSION,
        "authority":"Ron runtime SMAPI log: GameLocation.isCollidingPosition resolver failed and startup banner still reported .69/0686.",
        "checks":checks,
        "runtimeAcceptance":"PENDING-RON-IN-GAME",
        "runtimeExpectedLogs":[
            "0696D3-K installed collision hooks on <N> GameLocation.isCollidingPosition overload(s).",
            f"Cardcha! {VERSION} 0696D3-K COLLISION HOOK RUNTIME FIX TEST",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(2)

if __name__ == "__main__":
    main()

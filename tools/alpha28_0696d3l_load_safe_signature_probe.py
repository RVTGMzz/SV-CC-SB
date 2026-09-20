#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"src"/"Cardcha"
VERSION="0.3.0-alpha.28.0.4.14.4.5.12.76"
PATCH=SRC/"Patches"/"AirshipGateDepthPatch.cs"
MODENTRY=SRC/"ModEntry.cs"
DOCK=SRC/"assets"/"sky_dock_interior.tmx"
DECK=SRC/"assets"/"airship_deck.tmx"
AMBIENT=SRC/"assets"/"airship_props"/"set01_redux"/"airship_ambient_manifest.json"
REPORT=ROOT/"handoff"/"AIRSHIP_0696D3L_LOAD_SAFE_SIGNATURE_VALIDATION.json"

def parse_map(path):
    root=ET.parse(path).getroot()
    w,h=int(root.attrib["width"]),int(root.attrib["height"])
    props={p.attrib.get("name",""):p.attrib.get("value","") for p in root.findall("./properties/property")}
    layers={}
    for layer in root.findall("layer"):
        data=layer.find("data")
        if data is None or data.text is None: continue
        vals=[int(v.strip()) for v in data.text.replace("\n","").split(",") if v.strip()]
        assert len(vals)==w*h,(path.name,layer.attrib.get("name"),len(vals),w*h)
        layers[layer.attrib["name"]]=vals
    return w,h,props,layers

def rect(x0,y0,w,h): return [(x,y) for y in range(y0,y0+h) for x in range(x0,x0+w)]
def cell(a,w,x,y): return a[y*w+x]
def allv(a,w,pts,v): return all(cell(a,w,x,y)==v for x,y in pts)
def alln(a,w,pts,v): return all(cell(a,w,x,y)!=v for x,y in pts)

def main():
    patch=PATCH.read_text(encoding="utf-8")
    modentry=MODENTRY.read_text(encoding="utf-8")
    manifest=json.loads((SRC/"manifest.json").read_text(encoding="utf-8"))
    ambient=json.loads(AMBIENT.read_text(encoding="utf-8"))
    w1,h1,p1,l1=parse_map(DOCK); w2,h2,p2,l2=parse_map(DECK)
    b1,b2=l1["Buildings"],l2["Buildings"]
    checks={
      "manifestVersion76":manifest.get("Version")==VERSION,
      "csprojVersion76":VERSION in (SRC/"Cardcha.csproj").read_text(encoding="utf-8"),
      "targetsVersion76":VERSION in (SRC/"Directory.Build.targets").read_text(encoding="utf-8"),
      "dockVersion76":p1.get("CardchaAirshipVersion")==VERSION,
      "deckVersion76":p2.get("CardchaAirshipVersion")==VERSION,
      "ambientVersion76":ambient.get("version")==VERSION,
      "signatureProbePresent":all(x in patch for x in (
          "collisionCandidateCount",
          "0696D3-L collision signature probe",
          "parameter.ParameterType.FullName",
          "parameter.Name"
      )),
      "hotPathHarmonyPostfixDisabled":(
          "nameof(AfterCollisionCheck)" not in patch
          and "harmony.Patch(\n                candidate" not in patch
          and "runtime collision Harmony postfix is intentionally disabled" in patch
      ),
      "legacyGenericPostfixOnlyDormant":(
          "MethodBase __originalMethod" in patch and "object[] __args" in patch
      ),
      "noForcedFarmerPosition":all(t not in patch for t in (
          "player.Position =","LastSafePlayerPosition","EnforceD3FPhysicalFootprints","EnforceD3GPhysicalFootprints"
      )),
      "startupBannerD3L":'$"Cardcha! {this.ModManifest.Version} 0696D3-L LOAD-SAFE SIGNATURE PROBE TEST"' in modentry,
      "room1NoticeBlocked":allv(b1,w1,rect(2,5,5,3),5400),
      "room1LostFoundBlocked":allv(b1,w1,rect(8,5,6,2),5400),
      "room1BenchBlocked":allv(b1,w1,rect(2,9,6,3),5400),
      "room1LuggageBlocked":allv(b1,w1,rect(8,9,4,4),5400),
      "room1CargoBlocked":allv(b1,w1,rect(20,9,3,3),5400),
      "room1BoardingCenterOpen":alln(b1,w1,[(17,y) for y in range(5,9)],5400),
      "deckTravelSidesBlocked":allv(b2,w2,rect(2,4,2,3),5400) and allv(b2,w2,rect(5,4,2,3),5400),
      "deckTravelCenterOpen":alln(b2,w2,[(4,y) for y in range(4,7)],5400),
      "deckConsoleBlocked":allv(b2,w2,rect(9,5,7,5),5400),
      "deckFourUpgradeBasesBlocked":(
          allv(b2,w2,rect(3,8,3,1),5400) and allv(b2,w2,rect(18,8,3,1),5400)
          and allv(b2,w2,rect(6,11,3,1),5400) and allv(b2,w2,rect(15,11,3,1),5400)
      ),
      "deckLampBlocked":allv(b2,w2,rect(18,6,2,1),5400),
      "deckResonanceBlocked":allv(b2,w2,rect(20,5,3,2),5400),
    }
    report={
      "phase":"0696D3-L","status":"PASS" if all(checks.values()) else "FAIL","version":VERSION,
      "authority":"Ron runtime: D3-K .75 installed 3 collision hooks but save load never reached playable world; log ended without a Cardcha exception during post-load initialization.",
      "checks":checks,"runtimeAcceptance":"PENDING-RON-IN-GAME",
      "runtimeExpectedLogs":[
        "0696D3-L collision signature probe [1]: ...",
        "0696D3-L load-safe mode: observed <N> compatible GameLocation.isCollidingPosition overload(s); runtime collision Harmony postfix is intentionally disabled.",
        f"Cardcha! {VERSION} 0696D3-L LOAD-SAFE SIGNATURE PROBE TEST",
      ],
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if report["status"]!="PASS": raise SystemExit(2)

if __name__=="__main__": main()

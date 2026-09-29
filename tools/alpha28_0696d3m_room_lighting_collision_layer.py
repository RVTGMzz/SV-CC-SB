#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"src"/"Cardcha"
VERSION="0.3.0-alpha.28.0.4.14.4.5.12.77"
DECK=SRC/"assets"/"airship_deck.tmx"
DOCK=SRC/"assets"/"sky_dock_interior.tmx"
AMBIENT=SRC/"assets"/"airship_props"/"set01_redux"/"airship_ambient_manifest.json"
PATCH=SRC/"Patches"/"AirshipGateDepthPatch.cs"
SERVICE=SRC/"Services"/"AirshipFoundationService.cs"
ANIM=SRC/"Services"/"AirshipAmbientAnimationService.cs"
MODENTRY=SRC/"ModEntry.cs"
REPORT=ROOT/"handoff"/"AIRSHIP_0696D3M_ROOM_FIX_VALIDATION.json"

def parse_map(path: Path):
    root=ET.parse(path).getroot()
    w,h=int(root.attrib["width"]),int(root.attrib["height"])
    props={p.attrib.get("name",""):p.attrib.get("value","") for p in root.findall("./properties/property")}
    layers={}
    for layer in root.findall("layer"):
        d=layer.find("data")
        if d is None or d.text is None:
            continue
        vals=[int(v.strip()) for v in d.text.replace("\n","").split(",") if v.strip()]
        assert len(vals)==w*h,(path.name,layer.attrib.get("name"),len(vals),w*h)
        layers[layer.attrib["name"]]=vals
    return w,h,props,layers

def cell(a,w,x,y): return a[y*w+x]
def rect(x0,y0,w,h): return [(x,y) for y in range(y0,y0+h) for x in range(x0,x0+w)]
def allv(a,w,pts,v): return all(cell(a,w,x,y)==v for x,y in pts)
def alln(a,w,pts,v): return all(cell(a,w,x,y)!=v for x,y in pts)

def main():
    w1,h1,p1,l1=parse_map(DOCK)
    w2,h2,p2,l2=parse_map(DECK)
    b2=l2["Buildings"]
    service=SERVICE.read_text(encoding="utf-8")
    anim=ANIM.read_text(encoding="utf-8")
    patch=PATCH.read_text(encoding="utf-8")
    modentry=MODENTRY.read_text(encoding="utf-8")
    manifest=json.loads((SRC/"manifest.json").read_text(encoding="utf-8"))
    ambient=json.loads(AMBIENT.read_text(encoding="utf-8"))

    checks={
      "manifestVersion77":manifest.get("Version")==VERSION,
      "csprojVersion77":VERSION in (SRC/"Cardcha.csproj").read_text(encoding="utf-8"),
      "targetsVersion77":VERSION in (SRC/"Directory.Build.targets").read_text(encoding="utf-8"),
      "dockVersion77":p1.get("CardchaAirshipVersion")==VERSION,
      "deckVersion77":p2.get("CardchaAirshipVersion")==VERSION,
      "ambientVersion77":ambient.get("version")==VERSION,

      "room1AuthoredDayReadable":p1.get("AmbientLight")=="255 250 240",
      "room1AuthoredNightReadable":p1.get("AmbientNightLight")=="225 215 200",
      "room1RuntimeAmbientGuard":all(t in service for t in (
          "D3MRoom1AmbientLight = new(255, 250, 240)",
          "this.ApplyD3MInteriorLighting();",
          "this.ApplyD3MInteriorLighting(e.NewLocation);",
          "Game1.ambientLight = D3MRoom1AmbientLight;",
          "Game1.ambientLight = this.D3MPreviousAmbientLight;",
      )),

      "windowBackgroundDepth":all(t in anim for t in (
          "WindowBackdropDepth = 0.0200f",
          "WindowAirshipDepth = 0.0205f",
          "WindowFrameDepth = 0.0210f",
      )),
      "consoleBackgroundDepth":all(t in anim for t in (
          "ConsoleGlowDepth = 0.0500f",
          "ConsoleSweepDepth = 0.0505f",
          "ConsolePingsDepth = 0.0510f",
      )),
      "legacyHighWindowDepthGone":all(t not in anim for t in ("0.8840f","0.8845f","0.8848f")),
      "legacyHighConsoleDepthGone":all(t not in anim for t in ("0.8850f","0.8852f","0.8854f")),

      "windowSillSolid":allv(b2,w2,[(x,5) for x in range(7,17)],5400),
      "engineUpgradeFullBody":allv(b2,w2,rect(3,7,3,2),5400),
      "navigationUpgradeFullBody":allv(b2,w2,rect(18,7,3,2),5400),
      "hullUpgradeFullBody":allv(b2,w2,rect(6,10,3,2),5400),
      "reactorUpgradeFullBody":allv(b2,w2,rect(15,10,3,2),5400),

      "engineFrontLaneOpen":alln(b2,w2,[(x,9) for x in range(3,6)],5400),
      "navigationFrontLaneOpen":alln(b2,w2,[(x,9) for x in range(18,21)],5400),
      "hullFrontLaneOpen":alln(b2,w2,[(x,12) for x in range(6,9)],5400),
      "reactorFrontLaneOpen":alln(b2,w2,[(x,12) for x in range(15,18)],5400),
      "resonanceInteractionStillReachable":alln(b2,w2,[(21,7),(22,7)],5400),

      "travelCenterStillOpen":alln(b2,w2,[(4,5),(4,6)],5400),
      "boardAirshipCenterStillOpen":alln(l1["Buildings"],w1,[(17,y) for y in range(5,9)],5400),

      "noCollisionHarmonyInstall":(
          "nameof(AfterCollisionCheck)" not in patch
          and "runtime collision Harmony postfix is intentionally disabled" in patch
      ),
      "noForcedFarmerPosition":all(t not in patch for t in (
          "player.Position =","LastSafePlayerPosition","EnforceD3FPhysicalFootprints","EnforceD3GPhysicalFootprints"
      )),
      "startupBannerD3M":'$"Cardcha! {this.ModManifest.Version} 0696D3-M ROOM LIGHTING COLLISION LAYER FIX TEST"' in modentry,
    }

    report={
      "phase":"0696D3-M",
      "status":"PASS" if all(checks.values()) else "FAIL",
      "version":VERSION,
      "authority":"Ron 2026-09-29 screenshots: Room 1 near-black; Room 2 Farmer can stand inside UPGRADE; Room 2 wall/runtime layers overlap incorrectly.",
      "checks":checks,
      "runtimeAcceptance":"PENDING-RON-IN-GAME",
      "runtimeFocus":[
        "Room 1 readable at current time without near-black wash",
        "Farmer cannot stand inside any of four UPGRADE machines",
        "Window and console transient layers stay behind Farmer",
        "Window lower sill cannot be entered",
        "TRAVEL/BOARD AIRSHIP/interactions remain usable",
      ],
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if report["status"]!="PASS":
        raise SystemExit(2)

if __name__=="__main__": main()

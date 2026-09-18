#!/usr/bin/env python3
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import argparse
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

from PIL import Image

VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.74"
ROOT = "Cardcha/"
DOCK = ROOT + "assets/sky_dock_interior.tmx"
DECK = ROOT + "assets/airship_deck.tmx"
CONSOLE = ROOT + "assets/airship_props/set01_redux/navigation_console_body_d3i.png"

def parse_map(data: bytes):
    root = ET.fromstring(data.decode("utf-8"))
    w,h = int(root.attrib["width"]), int(root.attrib["height"])
    props = {p.attrib.get("name",""):p.attrib.get("value","") for p in root.findall("./properties/property")}
    layers={}
    for layer in root.findall("layer"):
        d=layer.find("data")
        if d is None or d.text is None:
            continue
        vals=[int(v.strip()) for v in d.text.replace("\n","").split(",") if v.strip()]
        layers[layer.attrib["name"]]=vals
    return w,h,props,layers

def cell(a,w,x,y):
    return a[y*w+x]

def all_value(a,w,points,value):
    return all(cell(a,w,x,y)==value for x,y in points)

def all_not(a,w,points,value):
    return all(cell(a,w,x,y)!=value for x,y in points)

def rect(x0,y0,w,h):
    return [(x,y) for y in range(y0,y0+h) for x in range(x0,x0+w)]

def runner_points(layer,w,h):
    return [(x,y) for y in range(h) for x in range(w) if 5800<=cell(layer,w,x,y)<=5811]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("package",type=Path)
    ap.add_argument("--report",type=Path)
    args=ap.parse_args()

    package_sha=hashlib.sha256(args.package.read_bytes()).hexdigest()
    with zipfile.ZipFile(args.package) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        manifest=json.loads(z.read(ROOT+"manifest.json"))
        dll=z.read(ROOT+"Cardcha.dll")
        w1,h1,p1,l1=parse_map(z.read(DOCK))
        w2,h2,p2,l2=parse_map(z.read(DECK))
        b1,back1=l1["Buildings"],l1["Back2"]
        b2,back2=l2["Buildings"],l2["Back2"]

        with Image.open(BytesIO(z.read(CONSOLE))) as im:
            console=im.convert("RGBA")
            alpha=sorted(set(a for *_,a in console.getdata()))

        r1=runner_points(back1,w1,h1)
        r2=runner_points(back2,w2,h2)

        checks={
            "manifestVersion74":manifest.get("Version")==VERSION,
            "releaseDllPresent":dll[:2]==b"MZ" and len(dll)>50000,
            "singleProductionRoot":bool(names) and all(n.startswith(ROOT) for n in names),
            "noDeveloperClutter":not any(
                n.lower().endswith((".cs",".csproj",".targets",".pdb",".py",".ps1"))
                or any(seg in n.lower() for seg in ("/bin/","/obj/","/tools/","/handoff/","/.git/"))
                for n in names
            ),
            "room1Version74":p1.get("CardchaAirshipVersion")==VERSION,
            "room2Version74":p2.get("CardchaAirshipVersion")==VERSION,
            "room1BrightLighting":p1.get("AmbientLight")=="230 225 215" and p1.get("AmbientNightLight")=="160 150 140",
            "room1NoticeBlocked":all_value(b1,w1,rect(2,5,5,3),5400),
            "room1LostFoundBlocked":all_value(b1,w1,rect(8,5,6,2),5400),
            "room1BenchBlocked":all_value(b1,w1,rect(2,9,6,3),5400),
            "room1LuggageBlocked":all_value(b1,w1,rect(8,9,4,4),5400),
            "room1CargoBlocked":all_value(b1,w1,rect(20,9,3,3),5400),
            "room1BoardingSidesBlocked":all_value(b1,w1,rect(14,5,3,4),5400) and all_value(b1,w1,rect(18,5,3,4),5400),
            "room1BoardingCenterOpen":all_not(b1,w1,[(17,y) for y in range(5,9)],5400),
            "room1RunnerClear":all_not(b1,w1,r1,5400),
            "room1BoardPadInsideGate":cell(back1,w1,17,7)==5803,

            "deckTravelSidesBlocked":all_value(b2,w2,rect(2,4,2,3),5400) and all_value(b2,w2,rect(5,4,2,3),5400),
            "deckTravelCenterOpen":all_not(b2,w2,[(4,5),(4,6),(4,7)],5400),
            "deckConsoleFullBodyBlocked":all_value(b2,w2,rect(9,5,7,5),5400),
            "deckConsoleFrontLaneOpen":all_not(b2,w2,[(x,10) for x in range(9,16)],5400),
            "deckFourUpgradeBasesBlocked":(
                all_value(b2,w2,rect(3,8,3,1),5400)
                and all_value(b2,w2,rect(18,8,3,1),5400)
                and all_value(b2,w2,rect(6,11,3,1),5400)
                and all_value(b2,w2,rect(15,11,3,1),5400)
            ),
            "deckLampBlocked":all_value(b2,w2,rect(18,6,2,1),5400),
            "deckResonanceBlocked":all_value(b2,w2,rect(20,5,3,2),5400),
            "deckResonanceFrontLaneOpen":all_not(b2,w2,[(20,7),(21,7),(22,7)],5400),
            "deckRunnerClear":all_not(b2,w2,r2,5400),
            "travelPadStillPresent":cell(back2,w2,4,5)==5803,

            "consoleGeneratedAssetPackaged":CONSOLE in names and console.size==(112,80) and alpha==[0,255],
            "i18nPresent":ROOT+"i18n/default.json" in names and ROOT+"i18n/vi.json" in names,
        }

    report={
        "phase":"0696D3-J-package-audit",
        "status":"PASS" if all(checks.values()) else "FAIL",
        "version":VERSION,
        "package":args.package.name,
        "packageSha256":package_sha,
        "checks":checks,
        "details":{
            "fileCount":len(names),
            "dllBytes":len(dll),
            "room1RunnerTiles":r1,
            "room2RunnerTiles":r2,
        },
        "runtimeAcceptance":"PENDING-RON-IN-GAME",
        "runtimeNote":"Package audit proves the collision maps are shipped. Ron still needs to confirm actual movement/collision in game."
    }
    out=json.dumps(report,indent=2)+"\n"
    print(out,end="")
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(out,encoding="utf-8")
    if report["status"]!="PASS":
        raise SystemExit(2)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.75"
ROOT = "Cardcha/"
DOCK = ROOT + "assets/sky_dock_interior.tmx"
DECK = ROOT + "assets/airship_deck.tmx"

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
        if len(vals) != w*h:
            raise AssertionError(f"{layer.attrib.get('name')} count {len(vals)} != {w*h}")
        layers[layer.attrib["name"]]=vals
    return w,h,props,layers

def cell(a,w,x,y):
    return a[y*w+x]

def all_value(a,w,pts,value):
    return all(cell(a,w,x,y)==value for x,y in pts)

def rect(x0,y0,w,h):
    return [(x,y) for y in range(y0,y0+h) for x in range(x0,x0+w)]

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
        b1,b2=l1["Buildings"],l2["Buildings"]

        checks={
            "manifestVersion75":manifest.get("Version")==VERSION,
            "releaseDllPresent":dll[:2]==b"MZ" and len(dll)>50000,
            "singleProductionRoot":bool(names) and all(n.startswith(ROOT) for n in names),
            "noDeveloperClutter":not any(
                n.lower().endswith((".cs",".csproj",".targets",".pdb",".py",".ps1"))
                or any(seg in n.lower() for seg in ("/bin/","/obj/","/tools/","/handoff/","/.git/"))
                for n in names
            ),
            "room1Version75":p1.get("CardchaAirshipVersion")==VERSION,
            "room2Version75":p2.get("CardchaAirshipVersion")==VERSION,
            "room1CoreCollisionPreserved":(
                all_value(b1,w1,rect(2,5,5,3),5400)
                and all_value(b1,w1,rect(8,5,6,2),5400)
                and all_value(b1,w1,rect(2,9,6,3),5400)
                and all_value(b1,w1,rect(8,9,4,4),5400)
                and all_value(b1,w1,rect(20,9,3,3),5400)
            ),
            "deckCoreCollisionPreserved":(
                all_value(b2,w2,rect(9,5,7,5),5400)
                and all_value(b2,w2,rect(3,8,3,1),5400)
                and all_value(b2,w2,rect(18,8,3,1),5400)
                and all_value(b2,w2,rect(6,11,3,1),5400)
                and all_value(b2,w2,rect(15,11,3,1),5400)
                and all_value(b2,w2,rect(20,5,3,2),5400)
            ),
            "i18nPresent":ROOT+"i18n/default.json" in names and ROOT+"i18n/vi.json" in names,
        }

    report={
        "phase":"0696D3-K-package-audit",
        "status":"PASS" if all(checks.values()) else "FAIL",
        "version":VERSION,
        "package":args.package.name,
        "packageSha256":package_sha,
        "checks":checks,
        "details":{
            "fileCount":len(names),
            "dllBytes":len(dll),
            "room1Size":[w1,h1],
            "room2Size":[w2,h2],
        },
        "runtimeAcceptance":"PENDING-RON-IN-GAME",
        "expectedRuntimeEvidence":[
            "collision hook install count must be > 0",
            "startup banner must report .75 / 0696D3-K",
        ],
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

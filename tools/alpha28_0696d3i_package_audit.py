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

VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.73"
ROOT = "Cardcha/"
DECK = ROOT + "assets/airship_deck.tmx"
DOCK = ROOT + "assets/sky_dock_interior.tmx"
CONSOLE = ROOT + "assets/airship_props/set01_redux/navigation_console_body_d3i.png"

def parse_map(data: bytes):
    root = ET.fromstring(data.decode("utf-8"))
    w,h = int(root.attrib["width"]), int(root.attrib["height"])
    props = {p.attrib.get("name",""):p.attrib.get("value","") for p in root.findall("./properties/property")}
    ts = {}
    for t in root.findall("tileset"):
        img=t.find("image")
        ts[int(t.attrib["firstgid"])] = img.attrib.get("source","") if img is not None else ""
    layers={}
    for layer in root.findall("layer"):
        d=layer.find("data")
        if d is None or d.text is None: continue
        vals=[int(v.strip()) for v in d.text.replace("\n","").split(",") if v.strip()]
        layers[layer.attrib["name"]]=vals
    return w,h,props,ts,layers

def cell(a,w,x,y): return a[y*w+x]

def is_beige(r,g,b,a):
    return a>0 and r>=205 and g>=155 and b>=95 and (r-b)>=60 and (g-b)>=35

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
        w2,h2,p2,t2,l2=parse_map(z.read(DECK))
        w1,h1,p1,t1,l1=parse_map(z.read(DOCK))

        with Image.open(BytesIO(z.read(CONSOLE))) as im:
            console=im.convert("RGBA")
            pixels=list(console.getdata())
            alpha=sorted(set(a for *_,a in pixels))
            transparent=sum(a==0 for *_,a in pixels)
            opaque=sum(a==255 for *_,a in pixels)
            beige=sum(is_beige(r,g,b,a) for r,g,b,a in pixels)

        all_deck=[v for layer in l2.values() for v in layer]
        checks={
            "manifestVersion73": manifest.get("Version")==VERSION,
            "releaseDllPresent": dll[:2]==b"MZ" and len(dll)>50000,
            "singleProductionRoot": bool(names) and all(n.startswith(ROOT) for n in names),
            "noDeveloperClutter": not any(
                n.lower().endswith((".cs",".csproj",".targets",".pdb",".py",".ps1"))
                or any(seg in n.lower() for seg in ("/bin/","/obj/","/tools/","/handoff/","/.git/"))
                for n in names
            ),
            "consoleD3IPackaged": CONSOLE in names and t2.get(5100,"").endswith("navigation_console_body_d3i.png"),
            "consoleHardAlpha": console.size==(112,80) and alpha==[0,255],
            "consoleMatteRemoved": transparent>=3000 and beige<=250 and opaque>=5000,
            "windowShellAbsentFromMap": not any(5000<=v<=5049 for v in all_deck),
            "lampMoved": cell(l2["Buildings2"],w2,18,4)==5200 and cell(l2["Buildings2"],w2,19,4)==5201,
            "lampCollisionMoved": cell(l2["Buildings"],w2,18,6)==5400 and cell(l2["Buildings"],w2,19,6)==5400,
            "boardingPadInsideGate": cell(l1["Back2"],w1,17,7)==5803 and cell(l1["Back2"],w1,17,8)==5800,
            "i18nPresent": ROOT+"i18n/default.json" in names and ROOT+"i18n/vi.json" in names,
        }

    report={
        "phase":"0696D3-I-package-audit",
        "status":"PASS" if all(checks.values()) else "FAIL",
        "version":VERSION,
        "package":args.package.name,
        "packageSha256":package_sha,
        "checks":checks,
        "details":{
            "fileCount":len(names),
            "dllBytes":len(dll),
            "consoleTransparentPixels":transparent,
            "consoleOpaquePixels":opaque,
            "consoleBeigeOpaquePixels":beige,
            "room1Size":[w1,h1],
            "room2Size":[w2,h2],
        },
        "runtimeAcceptance":"PENDING-RON-IN-GAME",
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

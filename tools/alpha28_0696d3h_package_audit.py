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

VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.72"
ROOT = "Cardcha/"
ROOM1 = ROOT + "assets/sky_dock_interior.tmx"
ROOM2 = ROOT + "assets/airship_deck.tmx"
RUNNER = ROOT + "assets/airship_props/set01_redux/airship_runner_d3h.png"
CONSOLE = ROOT + "assets/airship_props/set01_redux/navigation_console_body_d3h.png"
CONSOLE_BASE = ROOT + "assets/airship_props/set01_redux/navigation_console_base.png"


def parse_map(data: bytes):
    root = ET.fromstring(data.decode("utf-8"))
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
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
        w1,h1,p1,t1,l1=parse_map(z.read(ROOM1))
        w2,h2,p2,t2,l2=parse_map(z.read(ROOM2))

        with Image.open(BytesIO(z.read(RUNNER))) as im:
            runner=im.convert("RGBA")
            runner_colors=runner.getcolors(maxcolors=10000) or []
            runner_alpha=sorted(set(a for *_,a in runner.getdata()))

        with Image.open(BytesIO(z.read(CONSOLE))) as im:
            console=im.convert("RGBA")
            console_alpha=sorted(set(a for *_,a in console.getdata()))
            console_trans=sum(1 for *_,a in console.getdata() if a==0)
            console_opaque=sum(1 for *_,a in console.getdata() if a==255)

        b1=l1["Buildings"]; b2=l2["Buildings"]; b22=l2["Buildings2"]; back22=l2["Back2"]; f22=l2["Front2"]
        checks={
            "manifestVersion72": manifest.get("Version")==VERSION,
            "releaseDllPresent": dll[:2]==b"MZ" and len(dll)>50000,
            "singleProductionRoot": bool(names) and all(n.startswith(ROOT) for n in names),
            "noDeveloperClutter": not any(
                n.lower().endswith((".cs",".csproj",".targets",".pdb"))
                or any(seg in n.lower() for seg in ("/bin/","/obj/","/tools/","/handoff/","/.git/"))
                for n in names
            ),
            "room1Resized24x15": (w1,h1)==(24,15),
            "room1D3HLightingPackaged": p1.get("AmbientLight")=="25 25 25" and p1.get("AmbientNightLight")=="105 95 85",
            "d3hScaledHarborAssetsPackaged": all(ROOT+"assets/airship_props/set02_harbor/"+n in names for n in (
                "waiting_bench_d3h.png","lost_found_board_d3h.png","luggage_cart_d3h.png"
            )),
            "runnerPackagedPixelAtlas": (
                RUNNER in names and runner.size==(192,16)
                and len(runner_colors)<=16 and len(runner_alpha)<=4
                and t1.get(5800,"").endswith("airship_runner_d3h.png")
                and t2.get(5800,"").endswith("airship_runner_d3h.png")
            ),
            "room1BoardingPadOnRunner": cell(l1["Back2"],w1,17,8)==5803,
            "room2TravelPadOnRunner": cell(l2["Back2"],w2,4,5)==5803,
            "consoleFullDetailBytesPreserved": z.read(CONSOLE)==z.read(CONSOLE_BASE),
            "consoleHardAlpha": console.size==(112,80) and console_alpha==[0,255] and console_trans>1000 and console_opaque>5000,
            "deckUsesD3HConsole": t2.get(5100,"").endswith("navigation_console_body_d3h.png"),
            "consoleNotFront2": not any(5100<=v<=5134 for v in f22),
            "windowBackOwned": sum(1 for v in back22 if 5000<=v<=5049)==50 and not any(5000<=v<=5049 for v in b22),
            "deckLampMovedBlocked": cell(b22,w2,21,4)==5200 and cell(b2,w2,21,6)==5400 and cell(b2,w2,22,6)==5400,
            "fourUpgradeBasesBlocked": all(
                cell(b2,w2,x,y)==5400 for y,xs in (
                    (8,range(3,6)),(8,range(18,21)),(11,range(6,9)),(11,range(15,18))
                ) for x in xs
            ),
            "i18nPresent": ROOT+"i18n/default.json" in names and ROOT+"i18n/vi.json" in names,
        }

    report={
        "phase":"0696D3-H-package-audit",
        "status":"PASS" if all(checks.values()) else "FAIL",
        "version":VERSION,
        "package":args.package.name,
        "packageSha256":package_sha,
        "checks":checks,
        "details":{
            "fileCount":len(names),
            "dllBytes":len(dll),
            "room1Size":[w1,h1],
            "runnerUniqueColors":len(runner_colors),
            "runnerAlphaValues":runner_alpha,
            "consoleTransparentPixels":console_trans,
            "consoleOpaquePixels":console_opaque,
        },
        "runtimeAcceptance":"PENDING-RON-IN-GAME",
        "runtimeNote":"Package audit proves distributable D3-H files/contracts only. Ron runtime test is still required."
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

#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, zipfile, xml.etree.ElementTree as ET

VERSION="0.3.0-alpha.28.0.4.14.4.5.12.77"
ROOT="Cardcha/"

def parse(data: bytes):
    r=ET.fromstring(data.decode("utf-8"))
    w,h=int(r.attrib["width"]),int(r.attrib["height"])
    props={p.attrib.get("name",""):p.attrib.get("value","") for p in r.findall("./properties/property")}
    layers={}
    for layer in r.findall("layer"):
        d=layer.find("data")
        if d is None or d.text is None: continue
        vals=[int(v.strip()) for v in d.text.replace("\n","").split(",") if v.strip()]
        assert len(vals)==w*h
        layers[layer.attrib["name"]]=vals
    return w,h,props,layers

def cell(a,w,x,y): return a[y*w+x]
def rect(x0,y0,w,h): return [(x,y) for y in range(y0,y0+h) for x in range(x0,x0+w)]
def allv(a,w,pts,v): return all(cell(a,w,x,y)==v for x,y in pts)
def alln(a,w,pts,v): return all(cell(a,w,x,y)!=v for x,y in pts)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("package",type=Path)
    ap.add_argument("--report",type=Path)
    a=ap.parse_args()

    digest=hashlib.sha256(a.package.read_bytes()).hexdigest()
    with zipfile.ZipFile(a.package) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        manifest=json.loads(z.read(ROOT+"manifest.json"))
        dll=z.read(ROOT+"Cardcha.dll")
        w1,h1,p1,l1=parse(z.read(ROOT+"assets/sky_dock_interior.tmx"))
        w2,h2,p2,l2=parse(z.read(ROOT+"assets/airship_deck.tmx"))
        b2=l2["Buildings"]
        ambient=json.loads(z.read(ROOT+"assets/airship_props/set01_redux/airship_ambient_manifest.json"))

        checks={
          "manifestVersion77":manifest.get("Version")==VERSION,
          "ambientVersion77":ambient.get("version")==VERSION,
          "releaseDllPresent":dll[:2]==b"MZ" and len(dll)>50000,
          "singleProductionRoot":bool(names) and all(n.startswith(ROOT) for n in names),
          "noDeveloperClutter":not any(
              n.lower().endswith((".cs",".csproj",".targets",".pdb",".py",".ps1"))
              or any(s in n.lower() for s in ("/bin/","/obj/","/tools/","/handoff/","/.git/"))
              for n in names
          ),
          "room1Version77":p1.get("CardchaAirshipVersion")==VERSION,
          "room2Version77":p2.get("CardchaAirshipVersion")==VERSION,
          "room1DayAmbient":p1.get("AmbientLight")=="255 250 240",
          "room1NightAmbient":p1.get("AmbientNightLight")=="225 215 200",
          "windowSillSolid":allv(b2,w2,[(x,5) for x in range(7,17)],5400),
          "upgradeFullBodies":(
              allv(b2,w2,rect(3,7,3,2),5400)
              and allv(b2,w2,rect(18,7,3,2),5400)
              and allv(b2,w2,rect(6,10,3,2),5400)
              and allv(b2,w2,rect(15,10,3,2),5400)
          ),
          "upgradeFrontLanes":(
              alln(b2,w2,[(x,9) for x in range(3,6)],5400)
              and alln(b2,w2,[(x,9) for x in range(18,21)],5400)
              and alln(b2,w2,[(x,12) for x in range(6,9)],5400)
              and alln(b2,w2,[(x,12) for x in range(15,18)],5400)
          ),
          "i18nPresent":ROOT+"i18n/default.json" in names and ROOT+"i18n/vi.json" in names,
        }

    report={
      "phase":"0696D3-M-package-audit",
      "status":"PASS" if all(checks.values()) else "FAIL",
      "version":VERSION,
      "package":a.package.name,
      "packageSha256":digest,
      "checks":checks,
      "runtimeAcceptance":"PENDING-RON-IN-GAME",
    }
    out=json.dumps(report,indent=2)+"\n"
    print(out,end="")
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(out,encoding="utf-8")
    if report["status"]!="PASS":
        raise SystemExit(2)

if __name__=="__main__": main()

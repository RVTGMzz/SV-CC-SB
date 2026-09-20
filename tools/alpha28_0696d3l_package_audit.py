#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, zipfile, xml.etree.ElementTree as ET

VERSION="0.3.0-alpha.28.0.4.14.4.5.12.76"; ROOT="Cardcha/"
def parse(data):
    r=ET.fromstring(data.decode("utf-8")); w,h=int(r.attrib["width"]),int(r.attrib["height"])
    p={x.attrib.get("name",""):x.attrib.get("value","") for x in r.findall("./properties/property")}
    L={}
    for layer in r.findall("layer"):
        d=layer.find("data")
        if d is None or d.text is None: continue
        vals=[int(v.strip()) for v in d.text.replace("\n","").split(",") if v.strip()]
        assert len(vals)==w*h
        L[layer.attrib["name"]]=vals
    return w,h,p,L
def rect(x0,y0,w,h): return [(x,y) for y in range(y0,y0+h) for x in range(x0,x0+w)]
def ok(a,w,pts,v): return all(a[y*w+x]==v for x,y in pts)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("package",type=Path); ap.add_argument("--report",type=Path); a=ap.parse_args()
    sha=hashlib.sha256(a.package.read_bytes()).hexdigest()
    with zipfile.ZipFile(a.package) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        m=json.loads(z.read(ROOT+"manifest.json")); dll=z.read(ROOT+"Cardcha.dll")
        w1,h1,p1,l1=parse(z.read(ROOT+"assets/sky_dock_interior.tmx"))
        w2,h2,p2,l2=parse(z.read(ROOT+"assets/airship_deck.tmx"))
        b1,b2=l1["Buildings"],l2["Buildings"]
        checks={
          "manifestVersion76":m.get("Version")==VERSION,
          "releaseDllPresent":dll[:2]==b"MZ" and len(dll)>50000,
          "singleProductionRoot":bool(names) and all(n.startswith(ROOT) for n in names),
          "noDeveloperClutter":not any(n.lower().endswith((".cs",".csproj",".targets",".pdb",".py",".ps1")) or any(s in n.lower() for s in ("/bin/","/obj/","/tools/","/handoff/","/.git/")) for n in names),
          "room1Version76":p1.get("CardchaAirshipVersion")==VERSION,
          "room2Version76":p2.get("CardchaAirshipVersion")==VERSION,
          "room1CollisionPreserved":ok(b1,w1,rect(2,5,5,3),5400) and ok(b1,w1,rect(8,5,6,2),5400) and ok(b1,w1,rect(2,9,6,3),5400) and ok(b1,w1,rect(8,9,4,4),5400) and ok(b1,w1,rect(20,9,3,3),5400),
          "deckCollisionPreserved":ok(b2,w2,rect(9,5,7,5),5400) and ok(b2,w2,rect(3,8,3,1),5400) and ok(b2,w2,rect(18,8,3,1),5400) and ok(b2,w2,rect(6,11,3,1),5400) and ok(b2,w2,rect(15,11,3,1),5400) and ok(b2,w2,rect(20,5,3,2),5400),
          "i18nPresent":ROOT+"i18n/default.json" in names and ROOT+"i18n/vi.json" in names,
        }
    report={"phase":"0696D3-L-package-audit","status":"PASS" if all(checks.values()) else "FAIL","version":VERSION,"package":a.package.name,"packageSha256":sha,"checks":checks,"runtimeAcceptance":"PENDING-RON-IN-GAME"}
    out=json.dumps(report,indent=2)+"\n"; print(out,end="")
    if a.report: a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(out,encoding="utf-8")
    if report["status"]!="PASS": raise SystemExit(2)
if __name__=="__main__": main()

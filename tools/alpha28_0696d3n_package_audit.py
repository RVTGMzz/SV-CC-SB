#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, zipfile, xml.etree.ElementTree as ET

V="0.3.0-alpha.28.0.4.14.4.5.12.78"
ROOT="Cardcha/"

def props(data):
    r=ET.fromstring(data.decode("utf-8"))
    return {p.attrib.get("name",""):p.attrib.get("value","") for p in r.findall("./properties/property")}

ap=argparse.ArgumentParser()
ap.add_argument("package",type=Path)
ap.add_argument("--report",type=Path)
a=ap.parse_args()

sha=hashlib.sha256(a.package.read_bytes()).hexdigest()
with zipfile.ZipFile(a.package) as z:
    names=[n for n in z.namelist() if not n.endswith("/")]
    manifest=json.loads(z.read(ROOT+"manifest.json"))
    ambient=json.loads(z.read(ROOT+"assets/airship_props/set01_redux/airship_ambient_manifest.json"))
    dock=props(z.read(ROOT+"assets/sky_dock_interior.tmx"))
    deck=props(z.read(ROOT+"assets/airship_deck.tmx"))
    dll=z.read(ROOT+"Cardcha.dll")
    checks={
      "manifest78":manifest.get("Version")==V,
      "ambient78":ambient.get("version")==V,
      "dock78":dock.get("CardchaAirshipVersion")==V,
      "deck78":deck.get("CardchaAirshipVersion")==V,
      "d3nCabinLightProperty":dock.get("CardchaD3NCabinLights")=="8-runtime-stardew-light-sources|night-safe|room1-only|cleanup-on-exit",
      "dllPresent":dll[:2]==b"MZ" and len(dll)>50000,
      "singleRoot":bool(names) and all(n.startswith(ROOT) for n in names),
      "noDevClutter":not any(n.lower().endswith((".cs",".csproj",".targets",".pdb",".py",".ps1")) or "/tools/" in n.lower() or "/handoff/" in n.lower() for n in names),
      "i18n":ROOT+"i18n/default.json" in names and ROOT+"i18n/vi.json" in names,
    }

report={
 "phase":"0696D3-N-package-audit",
 "version":V,
 "status":"PASS" if all(checks.values()) else "FAIL",
 "package":a.package.name,
 "packageSha256":sha,
 "checks":checks,
 "runtimeAcceptance":"PENDING-RON-IN-GAME",
}
s=json.dumps(report,indent=2)+"\n"
print(s,end="")
if a.report:
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(s,encoding="utf-8")
if report["status"]!="PASS": raise SystemExit(2)

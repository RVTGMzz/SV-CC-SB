#!/usr/bin/env python3
from pathlib import Path
import json, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"src"/"Cardcha"
V="0.3.0-alpha.28.0.4.14.4.5.12.78"

svc=(SRC/"Services"/"AirshipFoundationService.cs").read_text(encoding="utf-8")
anim=(SRC/"Services"/"AirshipAmbientAnimationService.cs").read_text(encoding="utf-8")
mod=(SRC/"ModEntry.cs").read_text(encoding="utf-8")
ambient=json.loads((SRC/"assets"/"airship_props"/"set01_redux"/"airship_ambient_manifest.json").read_text(encoding="utf-8"))

def parse_map(path):
    root=ET.parse(path).getroot()
    w,h=int(root.attrib["width"]),int(root.attrib["height"])
    props={p.attrib.get("name",""):p.attrib.get("value","") for p in root.findall("./properties/property")}
    layers={}
    for layer in root.findall("layer"):
        data=layer.find("data")
        if data is None or data.text is None:
            continue
        vals=[int(v.strip()) for v in data.text.replace("\n","").split(",") if v.strip()]
        if len(vals)!=w*h:
            raise SystemExit(f"{path.name}:{layer.attrib.get('name')} invalid tile count {len(vals)} != {w*h}")
        layers[layer.attrib["name"]]=vals
    return w,h,props,layers

def cell(a,w,x,y): return a[y*w+x]
def all5400(a,w,pts): return all(cell(a,w,x,y)==5400 for x,y in pts)
def rect(x0,y0,ww,hh): return [(x,y) for y in range(y0,y0+hh) for x in range(x0,x0+ww)]

w1,h1,p1,l1=parse_map(SRC/"assets"/"sky_dock_interior.tmx")
w2,h2,p2,l2=parse_map(SRC/"assets"/"airship_deck.tmx")
b2=l2["Buildings"]

ids=[
"RouteBoard","LostFound","WaitingBench","Luggage",
"BoardingLeft","BoardingRight","BoardingCenter","Exit"
]

checks={
"manifest78":json.loads((SRC/"manifest.json").read_text(encoding="utf-8")).get("Version")==V,
"csproj78":V in (SRC/"Cardcha.csproj").read_text(encoding="utf-8"),
"targets78":V in (SRC/"Directory.Build.targets").read_text(encoding="utf-8"),
"dock78":p1.get("CardchaAirshipVersion")==V,
"deck78":p2.get("CardchaAirshipVersion")==V,
"ambient78":ambient.get("version")==V,
"startupD3N":"0696D3-N CABIN LIGHT SOURCES NIGHT FIX TEST" in mod,

"d3nProperty":p1.get("CardchaD3NCabinLights")=="8-runtime-stardew-light-sources|night-safe|room1-only|cleanup-on-exit",
"eightNamedLights":all(f'Ronvotri.Cardcha/D3N/{x}' in svc for x in ids),
"fixtureCountEight":svc.count('("Ronvotri.Cardcha/D3N/')==8,
"usesCurrentLightSources":"Game1.currentLightSources.ContainsKey(id)" in svc and "Game1.currentLightSources.Add(" in svc,
"usesStardewLightSource":"new LightSource(" in svc and "LightSource.LightContext.MapLight" in svc,
"constructorRoomScope":"0L,\n                    SkyDockInteriorLocationName" in svc,
"cleanup":"Game1.currentLightSources.Remove(id);" in svc and svc.count("this.RemoveD3NRoom1Lights();")>=2,
"tickEnsure":"this.ApplyD3NInteriorLighting();" in svc and "this.EnsureD3NRoom1Lights();" in svc,
"warpEnsure":"this.ApplyD3NInteriorLighting(e.NewLocation);" in svc,
"ambientFallbackPreserved":"D3MRoom1AmbientLight = new(255, 250, 240)" in svc,
"boardingCenterWideLight":'new Point(17, 8), 4.2f' in svc,

# D3-M collision/depth authority must survive D3-N.
"windowSillStillSolid":all5400(b2,w2,[(x,5) for x in range(7,17)]),
"engineStillFullBody":all5400(b2,w2,rect(3,7,3,2)),
"navigationStillFullBody":all5400(b2,w2,rect(18,7,3,2)),
"hullStillFullBody":all5400(b2,w2,rect(6,10,3,2)),
"reactorStillFullBody":all5400(b2,w2,rect(15,10,3,2)),
"windowDepthStillBackground":all(x in anim for x in (
    "WindowBackdropDepth = 0.0200f",
    "WindowAirshipDepth = 0.0205f",
    "WindowFrameDepth = 0.0210f",
)),
"consoleDepthStillBackground":all(x in anim for x in (
    "ConsoleGlowDepth = 0.0500f",
    "ConsoleSweepDepth = 0.0505f",
    "ConsolePingsDepth = 0.0510f",
)),
"noFarmerPositionPin":"player.Position =" not in svc,
}

status="PASS" if all(checks.values()) else "FAIL"
report={
 "phase":"0696D3-N",
 "version":V,
 "status":status,
 "authority":"Ron runtime screenshot at 20:00: Room 1 nearly black despite D3-M ambient guard.",
 "checks":checks,
 "runtimeAcceptance":"PENDING-RON-IN-GAME",
 "runtimeFocus":[
   "20:00 Room 1 has visible Stardew light pools and is readable",
   "fixture lighting disappears when leaving Room 1",
   "D3-M Room 2 collision/depth fixes remain intact",
 ]
}
out=ROOT/"handoff"/"AIRSHIP_0696D3N_NIGHT_LIGHT_VALIDATION.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
if status!="PASS":
    raise SystemExit(2)

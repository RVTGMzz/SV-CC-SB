#!/usr/bin/env python3
from pathlib import Path
import json, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"src"/"Cardcha"
V="0.3.0-alpha.28.0.4.14.4.5.12.78"
svc=(SRC/"Services"/"AirshipFoundationService.cs").read_text(encoding="utf-8")
mod=(SRC/"ModEntry.cs").read_text(encoding="utf-8")
dock=ET.parse(SRC/"assets"/"sky_dock_interior.tmx").getroot()
props={p.attrib.get("name",""):p.attrib.get("value","") for p in dock.findall("./properties/property")}
ambient=json.loads((SRC/"assets"/"airship_props"/"set01_redux"/"airship_ambient_manifest.json").read_text(encoding="utf-8"))

ids=[
"RouteBoard","LostFound","WaitingBench","Luggage",
"BoardingLeft","BoardingRight","BoardingCenter","Exit"
]
checks={
"manifest78": json.loads((SRC/"manifest.json").read_text(encoding="utf-8")).get("Version")==V,
"csproj78": V in (SRC/"Cardcha.csproj").read_text(encoding="utf-8"),
"targets78": V in (SRC/"Directory.Build.targets").read_text(encoding="utf-8"),
"dock78": props.get("CardchaAirshipVersion")==V,
"ambient78": ambient.get("version")==V,
"startupD3N": "0696D3-N CABIN LIGHT SOURCES NIGHT FIX TEST" in mod,
"d3nProperty": props.get("CardchaD3NCabinLights")=="8-runtime-stardew-light-sources|night-safe|room1-only|cleanup-on-exit",
"eightNamedLights": all(f'Ronvotri.Cardcha/D3N/{x}' in svc for x in ids),
"fixtureCountEight": svc.count('("Ronvotri.Cardcha/D3N/')==8,
"usesCurrentLightSources": "Game1.currentLightSources.ContainsKey(id)" in svc and "Game1.currentLightSources.Add(" in svc,
"usesStardewLightSource": "new LightSource(" in svc and "LightSource.LightContext.MapLight" in svc,
"roomScoped": "SkyDockInteriorLocationName" in svc and "onlyLocation" not in svc, # constructor positional location is expected
"cleanup": "Game1.currentLightSources.Remove(id);" in svc and "this.RemoveD3NRoom1Lights();" in svc,
"tickEnsure": "this.ApplyD3NInteriorLighting();" in svc and "this.EnsureD3NRoom1Lights();" in svc,
"warpEnsure": "this.ApplyD3NInteriorLighting(e.NewLocation);" in svc,
"ambientFallbackPreserved": "D3MRoom1AmbientLight = new(255, 250, 240)" in svc,
"noFarmerPositionPin": "player.Position =" not in svc,
}
# roomScoped above is just a source guard; require the constructor to receive the room name.
checks["constructorRoomScope"]="0L,\n                    SkyDockInteriorLocationName" in svc

status="PASS" if all(checks.values()) else "FAIL"
report={"phase":"0696D3-N","version":V,"status":status,"checks":checks,"runtimeAcceptance":"PENDING-RON-IN-GAME"}
out=ROOT/"handoff"/"AIRSHIP_0696D3N_NIGHT_LIGHT_VALIDATION.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
if status!="PASS": raise SystemExit(2)

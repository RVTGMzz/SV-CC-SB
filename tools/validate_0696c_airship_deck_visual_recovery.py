#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
CARDCHA=ROOT/"src/Cardcha"
PROP=CARDCHA/"assets/airship_props/set01_redux"
MANIFEST=PROP/"airship_ambient_manifest.json"
MAP=CARDCHA/"assets/airship_deck.tmx"
SHELL_GID=7200
SEASONS=["default","spring","summer","fall","winter"]
TIMES=["morning","noon","evening","night"]
WEATHERS=["clear","rain","storm","snow"]
VERSION="0.3.0-alpha.28.0.4.14.4.5.12.64"


def csv_layer(root: ET.Element,name: str) -> list[int]:
    l=next((x for x in root.findall("layer") if x.attrib.get("name")==name),None)
    assert l is not None,name
    d=l.find("data"); assert d is not None and d.attrib.get("encoding")=="csv",name
    vals=[int(x.strip()) for x in (d.text or "").split(",") if x.strip()]
    assert len(vals)==int(root.attrib["width"])*int(root.attrib["height"]),(name,len(vals))
    return vals


def opaque_black_count(path: Path) -> int:
    im=Image.open(path).convert("RGBA")
    return sum(1 for r,g,b,a in im.getdata() if a>240 and r<8 and g<8 and b<8)


def main() -> None:
    m=json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert m["schemaVersion"]==2
    assert m["version"]==VERSION
    assert m["visualAcceptance"]=="PENDING-RON-IN-GAME"
    ow=m["observationWindow"]
    matrix=ow["sceneMatrix"]
    states=matrix["states"]
    assert set(SEASONS)<=set(states)
    paths=[]
    for season in SEASONS:
        for tod in TIMES:
            assert tod in states[season],(season,tod)
            for weather in WEATHERS:
                p=states[season][tod].get(weather)
                assert p,(season,tod,weather)
                full=CARDCHA/p
                assert full.exists(),p
                assert Image.open(full).size==(128,42),(p,Image.open(full).size)
                paths.append(p)
    assert len(paths)==80 and len(set(paths))==80
    assert ow["legacyFallback"]["enabled"] is False
    assert ow["legacyFallback"]["paths"]==[]

    frame=CARDCHA/ow["frame"]["path"]
    mask=CARDCHA/ow["mask"]["path"]
    assert Image.open(frame).size==(160,80)
    assert Image.open(mask).size==(160,80)
    frame_rgba=Image.open(frame).convert("RGBA")
    transparent=sum(1 for a in frame_rgba.getchannel("A").getdata() if a==0)
    assert transparent>2000,transparent

    # The three rejected legacy frames genuinely contain opaque black wipes. Production must not use them.
    legacy_black={}
    for i in (2,3,4):
        p=PROP/f"observation_window_overlay_{i}.png"
        legacy_black[str(i)]=opaque_black_count(p)
        assert legacy_black[str(i)]>1000,(i,legacy_black[str(i)])
    service=(CARDCHA/"Services/AirshipAmbientAnimationService.cs").read_text(encoding="utf-8")
    window_block=service.split("private static bool DrawObservationWindow",1)[1].split("private static bool DrawNavigationConsole",1)[0]
    assert "DrawLegacyFullOverlay" not in window_block
    assert "if (!state.AmbientAssetsReady)\n            return false;" in window_block

    resolver=(CARDCHA/"Services/AirshipAmbientResolver.cs").read_text(encoding="utf-8")
    assert "ResolveScenePath" in resolver
    assert "TryResolveScene" in resolver

    # Moving FX contracts.
    for name,size in {
        "window_runtime/window_fx_clouds_strip.png":(128*6,42),
        "window_runtime/window_fx_rain_strip.png":(128*6,42),
        "window_runtime/window_fx_snow_strip.png":(128*6,42),
        "window_runtime/window_fx_lightning_flash_01.png":(160,80),
        "window_runtime/window_fx_lightning_flash_02.png":(160,80),
        "console_runtime/radar_bg.png":(48,32),
        "console_runtime/radar_sweep_strip.png":(48*8,32),
        "console_runtime/radar_pings_strip.png":(48*4,32),
        "console_runtime/radar_glow_strip.png":(48*4,32),
        "console_runtime/navigation_console_frame.png":(112,80),
    }.items():
        p=PROP/name
        assert p.exists(),name
        assert Image.open(p).size==size,(name,Image.open(p).size,size)

    renderer=(CARDCHA/"Services/AirshipInteriorStardewRenderer.cs").read_text(encoding="utf-8")
    assert renderer.count("DrawUpgradeStations(batch, save, phase);")==1
    foundation=(CARDCHA/"Services/AirshipFoundationService.cs").read_text(encoding="utf-8")
    assert "private bool TryRecoverDeckBoundary()" in foundation
    assert "if (this.TryRecoverDeckBoundary())" in foundation
    assert "tileY >= 13 && tileX is 11 or 12" in foundation

    root=ET.parse(MAP).getroot(); w=int(root.attrib["width"]); h=int(root.attrib["height"])
    assert (w,h)==(24,14)
    ts=next((x for x in root.findall("tileset") if x.attrib.get("name")=="CardchaAirshipDeckRoomShell0696C"),None)
    assert ts is not None
    assert int(ts.attrib["firstgid"])==SHELL_GID
    image=ts.find("image"); assert image is not None and image.attrib["source"]=="airship_props/room_shell/airship_deck_border_0696c.png"
    shell=CARDCHA/"assets"/image.attrib["source"]
    assert shell.exists() and Image.open(shell).size==(160,16)
    alpha=Image.open(shell).convert("RGBA").getchannel("A")
    for i in range(10):
        assert alpha.crop((i*16,0,(i+1)*16,16)).getbbox() is not None,i

    b2=csv_layer(root,"Buildings2"); f2=csv_layer(root,"Front2"); buildings=csv_layer(root,"Buildings")
    assert b2[0]==SHELL_GID+6 and b2[23]==SHELL_GID+7
    assert all(b2[x]==SHELL_GID+3 for x in range(1,23))
    assert all(b2[y*w]==SHELL_GID for y in range(1,13))
    assert all(b2[y*w+23]==SHELL_GID+1 for y in range(1,13))
    assert f2[13*w+10]==SHELL_GID+8 and f2[13*w+13]==SHELL_GID+9
    assert f2[13*w+11]==0 and f2[13*w+12]==0
    assert buildings[13*w+11]==0 and buildings[13*w+12]==0
    assert all(buildings[13*w+x] != 0 for x in list(range(0,11))+list(range(13,24)))

    props={p.attrib.get("name"):p.attrib.get("value") for ps in root.findall("properties") for p in ps.findall("property")}
    assert props.get("CardchaAirshipVersion")==VERSION
    assert props.get("CardchaRoomShellContract")=="0696C|visible-shell|doorway-x11-12|runtime-void-guard"
    assert props.get("CardchaAmbientContract")=="0696C|season-time-weather-matrix"
    assert props.get("CardchaVisualAcceptance")=="PENDING-RON-IN-GAME"

    package_manifest=json.loads((CARDCHA/"manifest.json").read_text(encoding="utf-8"))
    assert package_manifest["Version"]==VERSION

    report={
        "phase":"0696C-airship-deck-visual-recovery",
        "technicalValidation":"PASS",
        "visualAcceptance":"PENDING-RON-IN-GAME",
        "windowSceneCount":len(paths),
        "environmentDimensions":{"seasons":5,"timeBuckets":4,"weatherStates":4},
        "legacyRejectedWindowBlackPixels":legacy_black,
        "upgradeStationsRestored":4,
        "visibleRoomShell":True,
        "bottomDoorway":{"x":[11,12],"y":13,"voidGuard":True},
    }
    out=ROOT/"handoff/AIRSHIP_0696C_VISUAL_RECOVERY_VALIDATION.json"
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()

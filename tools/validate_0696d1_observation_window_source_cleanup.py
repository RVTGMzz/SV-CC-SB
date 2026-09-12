#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"
PROP_ROOT = CARDCHA / "assets/airship_props/set01_redux"
BASE = PROP_ROOT / "observation_window_base.png"
FRAME = PROP_ROOT / "window_runtime/observation_window_frame.png"
MASK = PROP_ROOT / "window_runtime/observation_window_view_mask.png"
MANIFEST = PROP_ROOT / "airship_ambient_manifest.json"
REPORT = ROOT / "handoff/AIRSHIP_0696D1_WINDOW_SOURCE_CLEANUP_VALIDATION.json"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.65"
MATTE_SEEDS = [(244,214,168),(244,210,156),(238,204,156)]
MATTE_DISTANCE = 24


def rgb_sha(im: Image.Image) -> str:
    return hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()


def is_matte(px: tuple[int,int,int,int]) -> bool:
    r,g,b,a = px
    if a == 0:
        return True
    t2 = MATTE_DISTANCE * MATTE_DISTANCE
    return min((r-sr)**2+(g-sg)**2+(b-sb)**2 for sr,sg,sb in MATTE_SEEDS) <= t2


def border_connected_opaque_matte(im: Image.Image) -> int:
    im = im.convert("RGBA")
    w,h = im.size
    q=deque(); seen=set()
    def offer(x:int,y:int):
        p=(x,y)
        if p in seen or not is_matte(im.getpixel(p)):
            return
        seen.add(p); q.append(p)
    for x in range(w): offer(x,0); offer(x,h-1)
    for y in range(h): offer(0,y); offer(w-1,y)
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<w and 0<=ny<h: offer(nx,ny)
    return sum(1 for p in seen if im.getpixel(p)[3] > 0)


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["phase"] == "0696D1-observation-window-source-cleanup"
    assert report["version"] == NEW_VERSION
    assert report["scopeLock"] == {
        "windowSourceChanged": True,
        "consoleSourceChanged": False,
        "environmentMatrixRebuilt": False,
        "roomShellChanged": False,
        "collisionChanged": False,
    }
    cleanup=report["cleanup"]
    assert cleanup["opaqueMattePixelsMadeTransparent"] >= 2000, cleanup
    assert cleanup["transparentPixelsAfter"] > cleanup["transparentPixelsBefore"] + 2000, cleanup
    assert cleanup["rgbShaBefore"] == cleanup["rgbShaAfter"], cleanup

    base=Image.open(BASE).convert("RGBA")
    frame=Image.open(FRAME).convert("RGBA")
    mask=Image.open(MASK).convert("RGBA")
    assert base.size == (160,80)
    assert frame.size == (160,80)
    assert mask.size == (160,80)
    assert rgb_sha(base) == cleanup["rgbShaAfter"]
    assert border_connected_opaque_matte(base) == 0, "base still has border-connected opaque matte"
    assert border_connected_opaque_matte(frame) == 0, "runtime frame still has border-connected opaque matte"

    mask_alpha=mask.getchannel("A")
    frame_alpha=frame.getchannel("A")
    aperture=0
    leakage=0
    for y in range(80):
        for x in range(160):
            if mask_alpha.getpixel((x,y)) > 0:
                aperture += 1
                if frame_alpha.getpixel((x,y)) > 0:
                    leakage += 1
    assert aperture > 2000, aperture
    assert leakage == 0, leakage

    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["version"] == NEW_VERSION
    assert manifest["workstream"] == "0696D1-observation-window-source-cleanup"
    ow=manifest["observationWindow"]
    assert ow["productionStatus"] == "SOURCE_CLEANED_D1_MATRIX_REBUILD_PENDING_D2"
    assert ow["sourceCleanup"]["rgbArtworkPreserved"] is True

    # D1 must not collapse or silently rewrite the environment matrix.
    states=ow["sceneMatrix"]["states"]
    count=sum(len(weather) for season in states.values() for weather in season.values())
    assert count == 80, count

    package_manifest=json.loads((CARDCHA/"manifest.json").read_text(encoding="utf-8"))
    assert package_manifest["Version"] == NEW_VERSION

    report["technicalValidation"] = "PASS"
    report["validator"] = {
        "baseBorderConnectedOpaqueMattePixels": 0,
        "frameBorderConnectedOpaqueMattePixels": 0,
        "aperturePixels": aperture,
        "apertureLeakagePixels": leakage,
        "environmentSceneCountPreserved": count,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

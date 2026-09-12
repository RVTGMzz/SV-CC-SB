#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import io
import json
import subprocess
from PIL import Image
from alpha28_0696d1r_window_bounded_cleanup import (
    BASELINE_COMMIT, EXPECTED_SIZE, BASE, OVERLAYS, FRAME,
    clean_base, sanitize_overlay, alpha_components, bbox,
)

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"
PROP = CARDCHA / "assets/airship_props/set01_redux"
REPORT = ROOT / "handoff/AIRSHIP_0696D1R_WINDOW_BOUNDED_VALIDATION.json"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.67"


def baseline(path: Path) -> Image.Image:
    rel = path.relative_to(ROOT).as_posix()
    raw = subprocess.check_output(["git","show",f"{BASELINE_COMMIT}:{rel}"], cwd=ROOT)
    return Image.open(io.BytesIO(raw)).convert("RGBA")


def validate_base() -> dict:
    src = baseline(BASE)
    expected, stats = clean_base(src)
    actual = Image.open(BASE).convert("RGBA")
    frame = Image.open(FRAME).convert("RGBA")
    assert actual.size == frame.size == EXPECTED_SIZE
    assert actual.tobytes() == expected.tobytes(), "materialized base differs from deterministic bounded cleanup"
    assert frame.tobytes() == actual.tobytes(), "rejected hollow-frame behavior returned"

    comps = alpha_components(actual)
    assert comps
    detached_edge=[]
    for pts in comps[1:]:
        if any(x in (0,actual.width-1) or y in (0,actual.height-1) for x,y in pts):
            detached_edge.append({"pixels":len(pts),"bbox":bbox(pts)})
    assert not detached_edge, detached_edge
    assert stats["detachedEdgePixelsRemoved"] > 0, stats
    assert stats["remainingDetachedEdgeComponents"] == 0
    return stats


def validate_overlays() -> list[dict]:
    results=[]
    for i,path in enumerate(OVERLAYS,1):
        src=baseline(path)
        expected,stats=sanitize_overlay(src,i)
        actual=Image.open(path).convert("RGBA")
        assert actual.size == EXPECTED_SIZE
        assert actual.tobytes() == expected.tobytes(), (i,"overlay differs from bounded pure-black repair")
        assert stats["remainingOpaquePureBlack"] == 0
        results.append(stats)
    assert results[0]["opaquePureBlackRemoved"] == 0
    assert all(x["opaquePureBlackRemoved"] > 1000 for x in results[1:])
    return results


def main() -> None:
    base_stats=validate_base(); overlay_stats=validate_overlays()
    package=json.loads((CARDCHA/"manifest.json").read_text(encoding="utf-8"))
    ambient=json.loads((PROP/"airship_ambient_manifest.json").read_text(encoding="utf-8"))
    assert package["Version"] == VERSION
    assert ambient["version"] == VERSION
    assert ambient["observationWindow"]["productionStatus"] == "D1R_FINAL_BOUNDED_CLEAN_4_OVERLAYS_ACTIVE_D2_PENDING"

    service=(CARDCHA/"Services/AirshipAmbientAnimationService.cs").read_text(encoding="utf-8")
    assert "D1RWindowOverlayPaths" in service and "D1RWindowFrameDurationMs" in service
    window_block=service.split("private static bool DrawObservationWindow",1)[1].split("private static bool DrawNavigationConsole",1)[0]
    assert "DrawLegacyFullOverlay" in window_block
    assert "state.BackdropPath" not in window_block
    assert "config.Frame.Path" not in window_block

    out={
        "phase":"0696D1R-window-bounded-cleanup-final",
        "technicalValidation":"PASS",
        "visualAcceptance":"PENDING-RON-VISUAL",
        "version":VERSION,
        "base":base_stats,
        "overlays":overlay_stats,
        "contracts":{
            "independentOverlayFiles":4,
            "dimensionsEach":[160,80],
            "remainingDetachedEdgeComponents":0,
            "crop":False,"shift":False,"stripPacking":False,"hollowAperture":False,
            "runtimeUsesFourApprovedOverlays":True,
        }
    }
    REPORT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2))

if __name__=="__main__": main()

#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import io
import json
import subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"
PROP = CARDCHA / "assets/airship_props/set01_redux"
WINDOW = PROP / "window_runtime"
BASE = PROP / "observation_window_base.png"
OVERLAYS = [PROP / f"observation_window_overlay_{i}.png" for i in range(1,5)]
FRAME = WINDOW / "observation_window_frame.png"
REPORT = ROOT / "handoff/AIRSHIP_0696D1R_WINDOW_BOUNDED_VALIDATION.json"
BASELINE_COMMIT = "0b13de1ac30dfa019061d3626c478c5460dab89f"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.66"
MATTE_RGB = {(244,214,168),(244,210,156),(238,204,156)}
EXPECTED = (160,80)


def baseline_image(rel: str) -> Image.Image:
    raw = subprocess.check_output(["git","show",f"{BASELINE_COMMIT}:{rel}"], cwd=ROOT)
    return Image.open(io.BytesIO(raw)).convert("RGBA")


def rgba_sha(im: Image.Image) -> str:
    return hashlib.sha256(im.convert("RGBA").tobytes()).hexdigest()


def validate_base() -> dict:
    rel = BASE.relative_to(ROOT).as_posix()
    before = baseline_image(rel)
    after = Image.open(BASE).convert("RGBA")
    assert before.size == after.size == EXPECTED

    changed = 0
    illegal = []
    exact_matte_remaining_on_changed_source = 0
    for y in range(EXPECTED[1]):
        for x in range(EXPECTED[0]):
            b = before.getpixel((x,y))
            a = after.getpixel((x,y))
            if b == a:
                continue
            changed += 1
            if not (b[:3] in MATTE_RGB and b[3] > 0 and a[:3] == b[:3] and a[3] == 0):
                illegal.append((x,y,b,a))
    assert not illegal, f"D1R changed non-matte Window art: {illegal[:8]}"
    assert changed > 0, "D1R did not clean any Window matte pixels"

    # Every non-matte source pixel, including edge wood/lantern/plant pixels, must survive exactly.
    for y in range(EXPECTED[1]):
        for x in range(EXPECTED[0]):
            b = before.getpixel((x,y))
            a = after.getpixel((x,y))
            if b[:3] not in MATTE_RGB:
                assert a == b, ("non-matte-drift",x,y,b,a)

    # The rejected D1 hollowing must not return: runtime frame must equal the full cleaned base.
    frame = Image.open(FRAME).convert("RGBA")
    assert frame.size == EXPECTED
    assert frame.tobytes() == after.tobytes(), "runtime Window frame is not a full clean copy of base"

    return {
        "changedExactMattePixels": changed,
        "rgbaShaBaseline": rgba_sha(before),
        "rgbaShaFixed": rgba_sha(after),
        "frameEqualsCleanBase": True,
    }


def validate_overlays() -> list[dict]:
    out = []
    for i, path in enumerate(OVERLAYS,1):
        rel = path.relative_to(ROOT).as_posix()
        before = baseline_image(rel)
        after = Image.open(path).convert("RGBA")
        assert before.size == after.size == EXPECTED, (i,before.size,after.size)
        removed = 0
        for y in range(EXPECTED[1]):
            for x in range(EXPECTED[0]):
                b = before.getpixel((x,y))
                a = after.getpixel((x,y))
                if b[:3] == (0,0,0) and b[3] > 0:
                    assert a == (0,0,0,0), (i,"black-mask-not-cleared",x,y,b,a)
                    removed += 1
                else:
                    assert a == b, (i,"nonblack-drift",x,y,b,a)
        remaining_opaque_black = sum(
            1 for r,g,b,a in after.getdata() if a > 0 and (r,g,b) == (0,0,0)
        )
        assert remaining_opaque_black == 0, (i,remaining_opaque_black)
        out.append({
            "frame": i,
            "size": list(after.size),
            "pureBlackMaskPixelsRemoved": removed,
            "remainingOpaquePureBlack": remaining_opaque_black,
            "rgbaShaBaseline": rgba_sha(before),
            "rgbaShaFixed": rgba_sha(after),
        })
    # Frame 1 historically contains no black wipe; frames 2..4 must have repairs.
    assert out[0]["pureBlackMaskPixelsRemoved"] == 0
    assert all(x["pureBlackMaskPixelsRemoved"] > 1000 for x in out[1:]), out
    return out


def main() -> None:
    base = validate_base()
    overlays = validate_overlays()

    manifest = json.loads((CARDCHA/"manifest.json").read_text(encoding="utf-8"))
    assert manifest["Version"] == VERSION
    ambient = json.loads((PROP/"airship_ambient_manifest.json").read_text(encoding="utf-8"))
    assert ambient["version"] == VERSION
    assert ambient["observationWindow"]["productionStatus"] == "D1R_BOUNDED_SOURCE_CLEAN_4_OVERLAYS_ACTIVE_D2_PENDING"

    service = (CARDCHA/"Services/AirshipAmbientAnimationService.cs").read_text(encoding="utf-8")
    assert "D1RWindowOverlayPaths" in service
    assert "D1RWindowFrameDurationMs" in service
    window_block = service.split("private static bool DrawObservationWindow",1)[1].split("private static bool DrawNavigationConsole",1)[0]
    assert "state.BackdropPath" not in window_block
    assert "config.Frame.Path" not in window_block
    assert "DrawLegacyFullOverlay" in window_block

    result = {
        "phase": "0696D1R-window-bounded-cleanup",
        "technicalValidation": "PASS",
        "visualAcceptance": "PENDING-RON-VISUAL",
        "version": VERSION,
        "base": base,
        "overlays": overlays,
        "contracts": {
            "independentFiles": 4,
            "dimensionsEach": [160,80],
            "crop": False,
            "shift": False,
            "stripPacking": False,
            "hollowAperture": False,
            "runtimeUsesFourApprovedOverlays": True,
        },
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

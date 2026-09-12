#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"
PROP = CARDCHA / "assets/airship_props/set01_redux"
WINDOW = PROP / "window_runtime"
BASE = PROP / "observation_window_base.png"
FRAME = WINDOW / "observation_window_frame.png"
AIRSHIP = WINDOW / "observation_window_airship.png"
AMBIENT = PROP / "airship_ambient_manifest.json"
REPORT = ROOT / "handoff/AIRSHIP_0696D1S_AIRSHIP_MOTION_REPAIR_VALIDATION.json"
PREVIEW = ROOT / "handoff/AIRSHIP_0696D1S_AIRSHIP_MOTION_PREVIEW.png"
SERVICE = CARDCHA / "Services/AirshipAmbientAnimationService.cs"
MANIFEST = CARDCHA / "manifest.json"

EXPECTED_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.68"
PATCH_SOURCE = (71, 33, 86, 42)
PATCH_TARGET = (89, 33, 104, 42)
EXPECTED_POSITIONS = [[62, 33], [71, 33], [80, 33], [89, 33]]


def main() -> None:
    base = Image.open(BASE).convert("RGBA")
    frame = Image.open(FRAME).convert("RGBA")
    airship = Image.open(AIRSHIP).convert("RGBA")
    preview = Image.open(PREVIEW).convert("RGBA")

    assert base.size == (160, 80), base.size
    assert frame.size == base.size, frame.size
    assert base.tobytes() == frame.tobytes(), "runtime frame drifted from cleaned map-native Window source"

    # D1S extracted sprite is intentionally tiny native pixel art, never an upscaled raster.
    assert 10 <= airship.width <= 20, airship.size
    assert 7 <= airship.height <= 14, airship.size
    opaque = sum(1 for a in airship.getchannel("A").getdata() if a > 0)
    assert opaque >= 70, opaque

    # The static source location must now be exactly the selected nearby clean-sky patch.
    assert base.crop(PATCH_SOURCE).tobytes() == base.crop(PATCH_TARGET).tobytes(), \
        "static airship source location was not removed with the locked clean patch"

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["version"] == EXPECTED_VERSION
    assert report["contracts"]["legacyOverlayCycling"] is False
    assert report["contracts"]["windowColumnsAnimated"] is False
    assert report["contracts"]["onlyAirshipMoves"] is True
    assert report["positions"] == EXPECTED_POSITIONS
    assert report["airship"]["spriteAlphaPixels"] == opaque

    ambient = json.loads(AMBIENT.read_text(encoding="utf-8"))
    ow = ambient["observationWindow"]
    assert ambient["version"] == EXPECTED_VERSION
    assert ow["productionStatus"] == "D1S_REAL_AIRSHIP_SPRITE_MOTION_D2_PENDING"
    motion = ow["airshipMotion"]
    assert motion["legacyOverlayCycling"] is False
    assert motion["positionsPx"] == EXPECTED_POSITIONS
    assert motion["runtimeSprite"].endswith("observation_window_airship.png")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["Version"] == EXPECTED_VERSION

    service = SERVICE.read_text(encoding="utf-8")
    assert "D1SAirshipPath" in service
    assert "observation_window_airship.png" in service
    assert "D1SAirshipPositions" in service
    assert "observation_window_overlay_2.png" not in service
    assert "D1RWindowOverlayPaths" not in service
    assert "only the real airship sprite" in service.lower()

    # Four side-by-side preview states must exist for visual inspection.
    assert preview.width > 160 * 4 and preview.height > 80 * 4

    print("0696D1S airship motion validator PASS")
    print(f"sprite={airship.size} opaque={opaque} positions={EXPECTED_POSITIONS}")
    print("legacy overlay column animation: DISABLED")


if __name__ == "__main__":
    main()

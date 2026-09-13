#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "src/Cardcha/Services/AirshipAmbientAnimationService.cs"

FORBIDDEN = (
    "observation_window_overlay_2.png",
    "observation_window_overlay_3.png",
    "observation_window_overlay_4.png",
)


def main() -> None:
    text = SERVICE.read_text(encoding="utf-8")
    leaked = [name for name in FORBIDDEN if name in text]
    if leaked:
        raise RuntimeError("0696D2 legacy environment overlay reuse detected: " + ", ".join(leaked))
    if "D1SAirshipPath" not in text or "observation_window_airship.png" not in text:
        raise RuntimeError("0696D2 independent .68 airship runtime path missing")
    if "Resolver.ResolveWindow(clockMs)" not in text:
        raise RuntimeError("0696D2 Window resolver wiring missing")
    print("0696D2 no-legacy-overlay guard PASS; independent .68 airship preserved")


if __name__ == "__main__":
    main()

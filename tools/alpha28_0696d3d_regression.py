#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.70"
REPORT = ROOT / "handoff/AIRSHIP_0696D3D_REGRESSION_VALIDATION.json"

D2_EXPECTED = {
    "morning": "93f6d4fcd403838d5758be012448c44978e65a8a4cb8bb33d4b24e4fb00802c0",
    "noon": "38cf1e47d73b7374c21932ca6fbd957a3f55d833385698d0b415721ebaddb29f",
    "evening": "2b3fb1ec4e4dd8d0bb7b2a3cf511ce7f8757e8dbbbb9ba54493f791df6aa0b5f",
    "night": "5d9ec8cbb2f13221d0463e474209d5a7bb3fbc4d1eb05bee28a15483b4c1173b",
}
D1S_SHA = "58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce"
RADAR_SHA = "5cbe64fc2f8c9a9f8b34dd6b6c90fd8ad56038248413a6f60df599c797bf0e62"
SHELL_SHA = "f2e0ef5128ecb9b1083588a419b9b1c57fcf2b9034326b59e4b8483d4713eddd"

WINDOW_ROOT = ROOT / "src/Cardcha/assets/airship_props/set01_redux/window_runtime"
RADAR = ROOT / "src/Cardcha/assets/airship_props/set01_redux/navigation_console_base.png"
SHELL = ROOT / "src/Cardcha/assets/airship_props/room_shell/airship_deck_border_0696c.png"
DECK = ROOT / "src/Cardcha/assets/airship_deck.tmx"
DOCK = ROOT / "src/Cardcha/assets/sky_dock_interior.tmx"
FOUNDATION = ROOT / "src/Cardcha/Services/AirshipFoundationService.cs"
AMBIENT = ROOT / "src/Cardcha/Services/AirshipAmbientAnimationService.cs"
RENDERER = ROOT / "src/Cardcha/Services/AirshipInteriorStardewRenderer.cs"
MANIFEST = ROOT / "src/Cardcha/manifest.json"
CSPROJ = ROOT / "src/Cardcha/Cardcha.csproj"
TARGETS = ROOT / "src/Cardcha/Directory.Build.targets"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_png(path: Path, size: tuple[int, int], exact_sha: str) -> dict:
    actual = sha(path)
    with Image.open(path) as image:
        image.load()
        contract = image.format == "PNG" and image.size == size and image.mode == "RGBA"
        return {
            "path": str(path.relative_to(ROOT)),
            "sha256": actual,
            "expectedSha256": exact_sha,
            "shaExact": actual == exact_sha,
            "format": image.format,
            "size": list(image.size),
            "mode": image.mode,
            "pngContract": contract,
        }


def all_checks_true(report: dict) -> bool:
    return report.get("status") == "PASS" and all(report.get("checks", {}).values())


def run_current_validators() -> dict:
    tools = ROOT / "tools"
    with tempfile.TemporaryDirectory(prefix="cardcha-0696d3d-") as td:
        temp = Path(td)

        d3a = load_module(tools / "alpha28_0696d3a_gameplay_room_integration.py", "cardcha_d3a_recheck")
        d3a.REPORT = temp / "d3a.json"
        a = d3a.validate()

        d3b = load_module(tools / "alpha28_0696d3b_prop_integration.py", "cardcha_d3b_recheck")
        d3b.REPORT = temp / "d3b.json"
        b = d3b.validate()

        d3c = load_module(tools / "alpha28_0696d3c_room_shell_and_entrances.py", "cardcha_d3c_recheck")
        d3c.REPORT = temp / "d3c.json"
        d3c.EXPECTED_SHELL_SHA = SHELL_SHA
        c = d3c.validate()

    return {
        "D3A": {"status": a.get("status"), "checks": a.get("checks", {}), "pass": all_checks_true(a)},
        "D3B": {"status": b.get("status"), "checks": b.get("checks", {}), "pass": all_checks_true(b)},
        "D3C": {"status": c.get("status"), "checks": c.get("checks", {}), "pass": all_checks_true(c)},
    }


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    csproj = CSPROJ.read_text(encoding="utf-8")
    targets = TARGETS.read_text(encoding="utf-8")
    deck = DECK.read_text(encoding="utf-8")
    dock = DOCK.read_text(encoding="utf-8")
    foundation = FOUNDATION.read_text(encoding="utf-8")
    ambient = AMBIENT.read_text(encoding="utf-8")
    renderer = RENDERER.read_text(encoding="utf-8")

    d2 = {
        state: check_png(WINDOW_ROOT / f"window_scene_default_{state}_clear.png", (160, 80), wanted)
        for state, wanted in D2_EXPECTED.items()
    }
    d1s = check_png(WINDOW_ROOT / "observation_window_airship.png", (15, 9), D1S_SHA)
    radar = check_png(RADAR, (112, 80), RADAR_SHA)
    shell = check_png(SHELL, (160, 16), SHELL_SHA)
    validators = run_current_validators()

    checks = {
        "versionManifest70": manifest.get("Version") == VERSION,
        "versionCsproj70": f"<Version>{VERSION}</Version>" in csproj,
        "versionTargets70": VERSION in targets,
        "d2FourStateCanonicalBytes": all(v["shaExact"] and v["pngContract"] for v in d2.values()),
        "d1SIndependentAirshipFrozen": d1s["shaExact"] and d1s["pngContract"],
        "radarApprovedBackingFrozen": radar["shaExact"] and radar["pngContract"],
        "radarDeckContractCorrected": 'CardchaD3BIntegration" value="radar-reference-backing-preserved|radar-footprint|machine-scale-normalization"' in deck,
        "room2ShellContractPresent": "CardchaRoomShellContract" in deck,
        "room1ShellAssetFrozen": shell["shaExact"] and shell["pngContract"],
        "room1ShellContractPresent": "CardchaRoomShellContract" in dock,
        "dedicatedTravelGateSourcePresent": "ResolveDeckTravelGateTile" in foundation and "ActionTouchesStation(action, travelGate)" in foundation,
        "helmDepartureRemoved": "if (action == helm)" not in foundation,
        "travelGateRendered": "DrawTravelGate0696D3A(batch, phase);" in renderer,
        "allFourUpgradeSystemsPresent": all(token in renderer for token in ["AirshipEngineLevel", "AirshipNavigationLevel", "AirshipHullLevel", "AirshipReactorLevel"]),
        "entranceGateD3CScale": "2.88f * pulse" in foundation and "ForestGateUseDistance = 256f" in foundation,
        "observationWindowD3CScale": "ObservationWindowPresentationScale = 4.25f" in ambient and "ResolveObservationWindowPresentation" in ambient,
        "d3AValidatorCurrentPass": validators["D3A"]["pass"],
        "d3BValidatorCurrentPass": validators["D3B"]["pass"],
        "d3CValidatorCurrentPass": validators["D3C"]["pass"],
    }

    report = {
        "phase": "0696D3-D",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "version": VERSION,
        "mode": "read-only-static-regression",
        "checks": checks,
        "validators": validators,
        "assets": {
            "d2WindowMatrix": d2,
            "d1SAirship": d1s,
            "radar": radar,
            "roomShell": shell,
        },
        "runtimeAcceptance": "PENDING-RON-IN-GAME",
        "runtimeNote": "CI proves source/assets/contracts/build/package only; it does not claim in-game Runtime PASS.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

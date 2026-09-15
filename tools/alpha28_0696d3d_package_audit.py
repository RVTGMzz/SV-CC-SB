#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import io
import json
import zipfile

from PIL import Image

VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.70"
D2_EXPECTED = {
    "morning": "93f6d4fcd403838d5758be012448c44978e65a8a4cb8bb33d4b24e4fb00802c0",
    "noon": "38cf1e47d73b7374c21932ca6fbd957a3f55d833385698d0b415721ebaddb29f",
    "evening": "2b3fb1ec4e4dd8d0bb7b2a3cf511ce7f8757e8dbbbb9ba54493f791df6aa0b5f",
    "night": "5d9ec8cbb2f13221d0463e474209d5a7bb3fbc4d1eb05bee28a15483b4c1173b",
}
D1S_SHA = "58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce"
RADAR_SHA = "5cbe64fc2f8c9a9f8b34dd6b6c90fd8ad56038248413a6f60df599c797bf0e62"
SHELL_SHA = "f2e0ef5128ecb9b1083588a419b9b1c57fcf2b9034326b59e4b8483d4713eddd"
ROOT = "Cardcha/assets/airship_props/set01_redux/"


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def png_check(raw: bytes, size: tuple[int, int]) -> bool:
    with Image.open(io.BytesIO(raw)) as image:
        image.load()
        return image.format == "PNG" and image.size == size and image.mode == "RGBA"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    package_sha = hashlib.sha256(args.package.read_bytes()).hexdigest()
    checks: dict[str, bool] = {}
    details: dict[str, object] = {}

    with zipfile.ZipFile(args.package) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        manifest = json.loads(z.read("Cardcha/manifest.json"))
        dll = z.read("Cardcha/Cardcha.dll")

        checks["manifestVersion70"] = manifest.get("Version") == VERSION
        checks["releaseDllPresent"] = dll[:2] == b"MZ" and len(dll) > 50000
        checks["singleProductionRoot"] = all(n.startswith("Cardcha/") for n in names)
        forbidden = (".cs", ".csproj", ".targets", ".pdb")
        forbidden_segments = ("/bin/", "/obj/", "/tools/", "/handoff/", "/.git/")
        checks["noDeveloperClutter"] = not any(
            n.lower().endswith(forbidden) or any(seg in n.lower() for seg in forbidden_segments)
            for n in names
        )
        checks["i18nPresent"] = any(n.startswith("Cardcha/i18n/") for n in names)
        checks["assetsPresent"] = any(n.startswith("Cardcha/assets/") for n in names)

        window_results = {}
        for state, wanted in D2_EXPECTED.items():
            path = ROOT + f"window_runtime/window_scene_default_{state}_clear.png"
            raw = z.read(path)
            actual = sha_bytes(raw)
            contract = png_check(raw, (160, 80))
            window_results[state] = {"sha256": actual, "expectedSha256": wanted, "pngContract": contract}
        checks["d2FourStateCanonicalBytes"] = all(
            item["sha256"] == item["expectedSha256"] and item["pngContract"]
            for item in window_results.values()
        )
        details["d2WindowMatrix"] = window_results

        d1s = z.read(ROOT + "window_runtime/observation_window_airship.png")
        checks["d1SIndependentAirshipFrozen"] = sha_bytes(d1s) == D1S_SHA and png_check(d1s, (15, 9))

        radar = z.read(ROOT + "navigation_console_base.png")
        checks["approvedRadarBackingFrozen"] = sha_bytes(radar) == RADAR_SHA and png_check(radar, (112, 80))

        shell = z.read("Cardcha/assets/airship_props/room_shell/airship_deck_border_0696c.png")
        checks["roomShellFrozen"] = sha_bytes(shell) == SHELL_SHA and png_check(shell, (160, 16))

        deck = z.read("Cardcha/assets/airship_deck.tmx").decode("utf-8")
        dock = z.read("Cardcha/assets/sky_dock_interior.tmx").decode("utf-8")
        checks["deckRadarContractCorrected"] = (
            'CardchaD3BIntegration" value="radar-reference-backing-preserved|radar-footprint|machine-scale-normalization"' in deck
        )
        checks["deckGameplayContractPresent"] = "CardchaD3AIntegration" in deck
        checks["room2ShellContractPresent"] = "CardchaRoomShellContract" in deck
        checks["room1ShellContractPresent"] = "CardchaRoomShellContract" in dock

        ambient = json.loads(z.read(ROOT + "airship_ambient_manifest.json"))
        window = ambient["observationWindow"]
        checks["noLegacyEnvironmentOverlayReuse"] = window["d2ClearMatrix"]["legacyEnvironmentOverlayReuse"] is False
        checks["independentD1SAirshipLayer"] = window["d2ClearMatrix"]["airshipLayer"] == "independent-.68-runtime-sprite"

        details.update({
            "fileCount": len(names),
            "dllBytes": len(dll),
            "d1SAirshipSha256": sha_bytes(d1s),
            "radarSha256": sha_bytes(radar),
            "roomShellSha256": sha_bytes(shell),
        })

    report = {
        "phase": "0696D3-D-package-audit",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "package": args.package.name,
        "packageSha256": package_sha,
        "version": VERSION,
        "checks": checks,
        "details": details,
        "runtimeAcceptance": "PENDING-RON-IN-GAME",
    }
    text = json.dumps(report, indent=2) + "\n"
    print(text, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    if report["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import zipfile

VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.70"


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
        checks["singleProductionRoot"] = bool(names) and all(n.startswith("Cardcha/") for n in names)

        forbidden_suffixes = (".cs", ".csproj", ".targets", ".pdb")
        forbidden_segments = ("/bin/", "/obj/", "/tools/", "/handoff/", "/.git/")
        checks["noDeveloperClutter"] = not any(
            n.lower().endswith(forbidden_suffixes)
            or any(seg in n.lower() for seg in forbidden_segments)
            for n in names
        )
        checks["i18nPresent"] = any(n.startswith("Cardcha/i18n/") for n in names)
        checks["assetsPresent"] = any(n.startswith("Cardcha/assets/") for n in names)
        checks["deckMapPresent"] = "Cardcha/assets/airship_deck.tmx" in names
        checks["skyDockInteriorMapPresent"] = "Cardcha/assets/sky_dock_interior.tmx" in names
        checks["ambientManifestPresent"] = (
            "Cardcha/assets/airship_props/set01_redux/airship_ambient_manifest.json" in names
        )
        checks["radarAnimationAssetsPresent"] = all(
            path in names
            for path in (
                "Cardcha/assets/airship_props/set01_redux/console_runtime/radar_glow_strip.png",
                "Cardcha/assets/airship_props/set01_redux/console_runtime/radar_sweep_strip.png",
                "Cardcha/assets/airship_props/set01_redux/console_runtime/radar_pings_strip.png",
            )
        )

        details.update({
            "fileCount": len(names),
            "dllBytes": len(dll),
            "manifestVersion": manifest.get("Version"),
        })

    report = {
        "phase": "0696D3-E-package-audit",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "package": args.package.name,
        "packageSha256": package_sha,
        "version": VERSION,
        "checks": checks,
        "details": details,
        "runtimeAcceptance": "PENDING-RON-IN-GAME",
        "runtimeNote": "Package audit proves distributable structure only. Runtime interaction/depth acceptance remains an in-game retest.",
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

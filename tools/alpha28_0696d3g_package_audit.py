#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from io import BytesIO
import argparse
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

from PIL import Image

VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.71"
CONSOLE_PATH = "Cardcha/assets/airship_props/set01_redux/navigation_console_body_d3g.png"


def parse_layer(root: ET.Element, name: str, width: int, height: int) -> list[int]:
    layer = next((x for x in root.findall("layer") if x.attrib.get("name") == name), None)
    if layer is None:
        raise ValueError(f"missing layer {name}")
    data = layer.find("data")
    if data is None or data.text is None:
        raise ValueError(f"missing CSV data for {name}")
    values = [int(v.strip()) for v in data.text.replace("\n", "").split(",") if v.strip()]
    if len(values) != width * height:
        raise ValueError(f"{name}: expected {width*height} cells, got {len(values)}")
    return values


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

        checks["manifestVersion71"] = manifest.get("Version") == VERSION
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
        checks["upgradeAtlasPresent"] = "Cardcha/assets/airship_upgrade_visuals.png" in names
        checks["travelGateArtPresent"] = (
            "Cardcha/assets/airship_props/set01_redux/boarding_gate_arch.png" in names
        )
        checks["d3gTransparentConsoleAssetPresent"] = CONSOLE_PATH in names

        console_bytes = z.read(CONSOLE_PATH)
        with Image.open(BytesIO(console_bytes)) as image:
            rgba = image.convert("RGBA")
            alpha = list(rgba.getchannel("A").getdata())
            transparent = sum(1 for a in alpha if a < 255)
            fully_transparent = sum(1 for a in alpha if a == 0)
            visible = sum(1 for a in alpha if a > 0)
            checks["d3gConsoleAssetHasRealAlpha"] = (
                rgba.size == (112, 80)
                and visible > 0
                and fully_transparent > 0
                and transparent / max(1, len(alpha)) >= 0.05
            )
            details["consoleAsset"] = {
                "size": list(rgba.size),
                "transparentOrPartialPixels": transparent,
                "fullyTransparentPixels": fully_transparent,
                "visiblePixels": visible,
            }

        deck_text = z.read("Cardcha/assets/airship_deck.tmx").decode("utf-8")
        deck_root = ET.fromstring(deck_text)
        props = {
            p.attrib.get("name", ""): p.attrib.get("value", "")
            for p in deck_root.findall("./properties/property")
        }
        tileset = next(
            (t for t in deck_root.findall("tileset") if t.attrib.get("firstgid") == "5100"),
            None,
        )
        image = tileset.find("image") if tileset is not None else None
        source = image.attrib.get("source", "") if image is not None else ""

        buildings2 = parse_layer(deck_root, "Buildings2", 24, 14)
        front2 = parse_layer(deck_root, "Front2", 24, 14)
        back2 = parse_layer(deck_root, "Back2", 24, 14)

        checks["packagedDeckUsesD3GConsoleAsset"] = (
            source == "airship_props/set01_redux/navigation_console_body_d3g.png"
            and "navigation_console_base.png" not in deck_text
        )
        checks["packagedConsoleNotForegroundBlanket"] = (
            sum(1 for v in buildings2 if 5100 <= v <= 5134) == 35
            and sum(1 for v in front2 if 5100 <= v <= 5134) == 0
        )
        checks["packagedWindowIsBackgroundArchitecture"] = (
            sum(1 for v in back2 if 5000 <= v <= 5049) == 50
            and sum(1 for v in buildings2 if 5000 <= v <= 5049) == 0
        )
        checks["packagedDaylightContractPresent"] = (
            props.get("AmbientLight") == "70 70 70"
            and props.get("AmbientNightLight") == "145 135 115"
        )

        checks["transparentConsoleRuntimeAssetsPresent"] = all(
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
            "consoleTilesetSource": source,
            "dayAmbientLight": props.get("AmbientLight"),
            "nightAmbientLight": props.get("AmbientNightLight"),
        })

    report = {
        "phase": "0696D3-G-package-audit",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "package": args.package.name,
        "packageSha256": package_sha,
        "version": VERSION,
        "checks": checks,
        "details": details,
        "runtimeAcceptance": "PENDING-RON-IN-GAME",
        "runtimeNote": "Package audit proves distributable structure and packaged D3-G asset/TMX contracts only. Runtime acceptance requires Ron's in-game retest.",
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

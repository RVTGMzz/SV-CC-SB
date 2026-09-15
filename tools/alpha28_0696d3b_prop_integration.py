#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import math
import re

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
NAV = ROOT / "src/Cardcha/assets/airship_props/set01_redux/navigation_console_base.png"
RENDERER = ROOT / "src/Cardcha/Services/AirshipInteriorStardewRenderer.cs"
DECK = ROOT / "src/Cardcha/assets/airship_deck.tmx"
REPORT = ROOT / "handoff/AIRSHIP_0696D3B_PROP_INTEGRATION_VALIDATION.json"

# 0696D3-D correction: the supplied radar art, including its yellow/beige backing,
# is the approved reference. D3-B must preserve these bytes rather than flood-fill
# the backing to transparency.
EXPECTED_NAV_SOURCE_SHA = "5cbe64fc2f8c9a9f8b34dd6b6c90fd8ad56038248413a6f60df599c797bf0e62"
BACKGROUND_RGB = (245, 215, 169)
BACKGROUND_DISTANCE = 30.0
NAV_SIZE = (112, 80)
COLLISION_GID = 5400
RADAR_COLLISION = [(x, 9) for x in range(9, 16)] + [(x, 8) for x in range(10, 15)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one baseline match, found {count}")
    return text.replace(old, new, 1)


def is_background_candidate(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    if a == 0 or r <= 180 or g <= 150 or b <= 100:
        return False
    dr = r - BACKGROUND_RGB[0]
    dg = g - BACKGROUND_RGB[1]
    db = b - BACKGROUND_RGB[2]
    return math.sqrt(dr * dr + dg * dg + db * db) <= BACKGROUND_DISTANCE


def preserve_navigation_console() -> dict:
    """Validate the approved radar reference without modifying any image bytes."""
    current_sha = sha(NAV)
    if current_sha != EXPECTED_NAV_SOURCE_SHA:
        raise RuntimeError(
            "navigation console no longer matches the approved D3-D reference: "
            f"expected {EXPECTED_NAV_SOURCE_SHA}, got {current_sha}"
        )

    with Image.open(NAV) as image:
        image.load()
        if image.format != "PNG" or image.size != NAV_SIZE or image.mode != "RGBA":
            raise RuntimeError(
                f"navigation console contract changed: {image.format} {image.size} {image.mode}"
            )

    return {
        "referenceBackingPreserved": True,
        "beforeSha256": current_sha,
        "afterSha256": current_sha,
        "modifiedPixels": 0,
    }


def patch_renderer_scale() -> None:
    text = RENDERER.read_text(encoding="utf-8")
    old = """            DrawRect(batch, new Rectangle((int)center.X - 54, (int)center.Y + 9, 108, 18), new Color(49, 34, 31) * 0.92f);\n            DrawRect(batch, new Rectangle((int)center.X - 46, (int)center.Y + 7, 92, 7), new Color(177, 118, 57) * 0.78f);\n            DrawRect(batch, new Rectangle((int)center.X - 54, (int)center.Y - 55, 108, 72), accent * (0.055f + pulse * 0.035f));\n            DrawRect(batch, new Rectangle((int)center.X - 38, (int)center.Y - 42, 76, 52), accent * (0.065f + pulse * 0.045f));\n            Rectangle dst = new((int)center.X - 52, (int)center.Y - 70, 104, 104);\n"""
    new = """            // 0696D3-B: keep the D3-A grounded footprint but pull visual mass closer to native Stardew scale.\n            DrawRect(batch, new Rectangle((int)center.X - 48, (int)center.Y + 9, 96, 16), new Color(49, 34, 31) * 0.92f);\n            DrawRect(batch, new Rectangle((int)center.X - 41, (int)center.Y + 7, 82, 6), new Color(177, 118, 57) * 0.78f);\n            DrawRect(batch, new Rectangle((int)center.X - 48, (int)center.Y - 49, 96, 64), accent * (0.050f + pulse * 0.032f));\n            DrawRect(batch, new Rectangle((int)center.X - 34, (int)center.Y - 38, 68, 47), accent * (0.060f + pulse * 0.040f));\n            Rectangle dst = new((int)center.X - 48, (int)center.Y - 64, 96, 96);\n"""
    text = replace_once(text, old, new, "upgrade machine visual scale")
    RENDERER.write_text(text, encoding="utf-8")


def patch_radar_collision() -> None:
    text = DECK.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(<layer id="3" name="Buildings" width="24" height="14">.*?<data encoding="csv">)(.*?)(</data>.*?</layer>)',
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError("Buildings layer not found")
    values = [int(x.strip()) for x in match.group(2).replace("\n", "").split(",") if x.strip()]
    if len(values) != 24 * 14:
        raise RuntimeError(f"unexpected Buildings tile count {len(values)}")
    for x, y in RADAR_COLLISION:
        values[y * 24 + x] = COLLISION_GID
    rows = [",".join(str(v) for v in values[y * 24:(y + 1) * 24]) for y in range(14)]
    data = "\n" + ",\n".join(rows) + "\n"
    text = text[:match.start()] + match.group(1) + data + match.group(3) + text[match.end():]

    old_marker = (
        '  <property name="CardchaD3BIntegration" '
        'value="radar-background-cleanup|radar-footprint|machine-scale-normalization" />'
    )
    new_marker = (
        '  <property name="CardchaD3BIntegration" '
        'value="radar-reference-backing-preserved|radar-footprint|machine-scale-normalization" />'
    )
    if old_marker in text:
        text = text.replace(old_marker, new_marker, 1)
    elif "CardchaD3BIntegration" not in text:
        text = text.replace(
            '  <property name="CardchaD3AIntegration" value="upgrade-footprints|dedicated-travel-gate|gameplay-first" />\n',
            '  <property name="CardchaD3AIntegration" value="upgrade-footprints|dedicated-travel-gate|gameplay-first" />\n'
            + new_marker
            + "\n",
            1,
        )
    DECK.write_text(text, encoding="utf-8")


def validate(preservation: dict | None = None) -> dict:
    renderer = RENDERER.read_text(encoding="utf-8")
    deck = DECK.read_text(encoding="utf-8")
    current_sha = sha(NAV)

    with Image.open(NAV) as image:
        image.load()
        edge_candidates = 0
        for x in range(image.width):
            edge_candidates += int(is_background_candidate(image.getpixel((x, 0))))
            edge_candidates += int(is_background_candidate(image.getpixel((x, image.height - 1))))
        for y in range(image.height):
            edge_candidates += int(is_background_candidate(image.getpixel((0, y))))
            edge_candidates += int(is_background_candidate(image.getpixel((image.width - 1, y))))
        transparent = sum(1 for p in image.getdata() if p[3] == 0)
        image_contract = image.format == "PNG" and image.size == NAV_SIZE and image.mode == "RGBA"

    pattern = re.compile(
        r'<layer id="3" name="Buildings" width="24" height="14">.*?<data encoding="csv">(.*?)</data>',
        re.S,
    )
    match = pattern.search(deck)
    radar_collision_ok = False
    if match:
        values = [int(x.strip()) for x in match.group(1).replace("\n", "").split(",") if x.strip()]
        radar_collision_ok = (
            len(values) == 24 * 14
            and all(values[y * 24 + x] == COLLISION_GID for x, y in RADAR_COLLISION)
        )

    checks = {
        "navigationConsolePngContract": image_contract,
        "navigationConsoleReferenceBackingPreserved": current_sha == EXPECTED_NAV_SOURCE_SHA,
        "approvedYellowBeigeBackingPresent": edge_candidates > 0,
        "upgradeMachinesNormalizedTo96px": (
            "Rectangle dst = new((int)center.X - 48, (int)center.Y - 64, 96, 96);" in renderer
        ),
        "d3ATravelGatePreserved": "DrawTravelGate0696D3A(batch, phase);" in renderer,
        "radarCollisionFootprint": radar_collision_ok,
        "deckD3BPropertyCorrected": "radar-reference-backing-preserved" in deck,
    }
    report = {
        "phase": "0696D3-B / 0696D3-D corrected contract",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "navigationConsole": {
            "path": str(NAV.relative_to(ROOT)),
            "approvedReferenceSha256": EXPECTED_NAV_SOURCE_SHA,
            "currentSha256": current_sha,
            "backgroundSeedRgb": list(BACKGROUND_RGB),
            "backgroundDistance": BACKGROUND_DISTANCE,
            "edgeBackgroundCandidatesPresent": edge_candidates,
            "transparentPixels": transparent,
            "preservation": preservation,
        },
        "radarCollisionTiles": [list(p) for p in RADAR_COLLISION],
        "upgradeMachineVisualSize": [96, 96],
        "checks": checks,
        "scopeDeferred": ["room1-border", "entrance-arch-x2", "window-size-adjustment"],
        "correction": (
            "0696D3-D freezes the approved yellow/beige radar backing. "
            "The previous edge flood-fill cleanup is retired and must not run again."
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["status"] != "PASS":
        raise SystemExit(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if not args.apply and not args.validate:
        parser.error("choose --apply and/or --validate")

    preservation = None
    if args.apply:
        preservation = preserve_navigation_console()
        patch_renderer_scale()
        patch_radar_collision()
    if args.validate:
        print(json.dumps(validate(preservation), indent=2))


if __name__ == "__main__":
    main()

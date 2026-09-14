#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
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


def clean_navigation_console() -> dict:
    before_sha = sha(NAV)
    if before_sha != EXPECTED_NAV_SOURCE_SHA:
        with Image.open(NAV) as existing:
            existing.load()
            if existing.size == NAV_SIZE and existing.mode == "RGBA":
                rgba = existing.copy()
                edge_bg = 0
                for x in range(rgba.width):
                    edge_bg += int(is_background_candidate(rgba.getpixel((x, 0))))
                    edge_bg += int(is_background_candidate(rgba.getpixel((x, rgba.height - 1))))
                for y in range(rgba.height):
                    edge_bg += int(is_background_candidate(rgba.getpixel((0, y))))
                    edge_bg += int(is_background_candidate(rgba.getpixel((rgba.width - 1, y))))
                if edge_bg == 0:
                    return {
                        "sourceAlreadyCleaned": True,
                        "beforeSha256": before_sha,
                        "afterSha256": before_sha,
                        "removedPixels": 0,
                    }
        raise RuntimeError(f"navigation console source SHA changed unexpectedly: {before_sha}")

    with Image.open(NAV) as image:
        image.load()
        if image.format != "PNG" or image.size != NAV_SIZE or image.mode != "RGBA":
            raise RuntimeError(f"navigation console contract changed: {image.format} {image.size} {image.mode}")
        out = image.copy()

    width, height = out.size
    queue: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    for x in range(width):
        for y in (0, height - 1):
            if is_background_candidate(out.getpixel((x, y))):
                queue.append((x, y)); seen.add((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if is_background_candidate(out.getpixel((x, y))) and (x, y) not in seen:
                queue.append((x, y)); seen.add((x, y))

    removed = 0
    while queue:
        x, y = queue.popleft()
        r, g, b, _ = out.getpixel((x, y))
        out.putpixel((x, y), (r, g, b, 0))
        removed += 1
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height or (nx, ny) in seen:
                continue
            if is_background_candidate(out.getpixel((nx, ny))):
                seen.add((nx, ny)); queue.append((nx, ny))

    if removed < 500:
        raise RuntimeError(f"background cleanup removed too few pixels: {removed}")

    out.save(NAV, format="PNG", optimize=False, compress_level=9)
    return {
        "sourceAlreadyCleaned": False,
        "beforeSha256": before_sha,
        "afterSha256": sha(NAV),
        "removedPixels": removed,
    }


def patch_renderer_scale() -> None:
    text = RENDERER.read_text(encoding="utf-8")
    old = """            DrawRect(batch, new Rectangle((int)center.X - 54, (int)center.Y + 9, 108, 18), new Color(49, 34, 31) * 0.92f);\n            DrawRect(batch, new Rectangle((int)center.X - 46, (int)center.Y + 7, 92, 7), new Color(177, 118, 57) * 0.78f);\n            DrawRect(batch, new Rectangle((int)center.X - 54, (int)center.Y - 55, 108, 72), accent * (0.055f + pulse * 0.035f));\n            DrawRect(batch, new Rectangle((int)center.X - 38, (int)center.Y - 42, 76, 52), accent * (0.065f + pulse * 0.045f));\n            Rectangle dst = new((int)center.X - 52, (int)center.Y - 70, 104, 104);\n"""
    new = """            // 0696D3-B: keep the D3-A grounded footprint but pull visual mass closer to native Stardew scale.\n            DrawRect(batch, new Rectangle((int)center.X - 48, (int)center.Y + 9, 96, 16), new Color(49, 34, 31) * 0.92f);\n            DrawRect(batch, new Rectangle((int)center.X - 41, (int)center.Y + 7, 82, 6), new Color(177, 118, 57) * 0.78f);\n            DrawRect(batch, new Rectangle((int)center.X - 48, (int)center.Y - 49, 96, 64), accent * (0.050f + pulse * 0.032f));\n            DrawRect(batch, new Rectangle((int)center.X - 34, (int)center.Y - 38, 68, 47), accent * (0.060f + pulse * 0.040f));\n            Rectangle dst = new((int)center.X - 48, (int)center.Y - 64, 96, 96);\n"""
    text = replace_once(text, old, new, "upgrade machine visual scale")
    RENDERER.write_text(text, encoding="utf-8")


def patch_radar_collision() -> None:
    text = DECK.read_text(encoding="utf-8")
    pattern = re.compile(r'(<layer id="3" name="Buildings" width="24" height="14">.*?<data encoding="csv">)(.*?)(</data>.*?</layer>)', re.S)
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
    if "CardchaD3BIntegration" not in text:
        text = text.replace(
            '  <property name="CardchaD3AIntegration" value="upgrade-footprints|dedicated-travel-gate|gameplay-first" />\n',
            '  <property name="CardchaD3AIntegration" value="upgrade-footprints|dedicated-travel-gate|gameplay-first" />\n  <property name="CardchaD3BIntegration" value="radar-background-cleanup|radar-footprint|machine-scale-normalization" />\n',
            1,
        )
    DECK.write_text(text, encoding="utf-8")


def validate(cleanup: dict | None = None) -> dict:
    renderer = RENDERER.read_text(encoding="utf-8")
    deck = DECK.read_text(encoding="utf-8")
    with Image.open(NAV) as image:
        image.load()
        pixels = list(image.getdata())
        edge_candidates = 0
        for x in range(image.width):
            edge_candidates += int(is_background_candidate(image.getpixel((x, 0))))
            edge_candidates += int(is_background_candidate(image.getpixel((x, image.height - 1))))
        for y in range(image.height):
            edge_candidates += int(is_background_candidate(image.getpixel((0, y))))
            edge_candidates += int(is_background_candidate(image.getpixel((image.width - 1, y))))
        transparent = sum(1 for p in pixels if p[3] == 0)
        image_contract = image.format == "PNG" and image.size == NAV_SIZE and image.mode == "RGBA"

    pattern = re.compile(r'<layer id="3" name="Buildings" width="24" height="14">.*?<data encoding="csv">(.*?)</data>', re.S)
    match = pattern.search(deck)
    radar_collision_ok = False
    if match:
        values = [int(x.strip()) for x in match.group(1).replace("\n", "").split(",") if x.strip()]
        radar_collision_ok = len(values) == 24 * 14 and all(values[y * 24 + x] == COLLISION_GID for x, y in RADAR_COLLISION)

    checks = {
        "navigationConsolePngContract": image_contract,
        "yellowBeigeEdgeBackgroundRemoved": edge_candidates == 0,
        "navigationConsoleHasTransparency": transparent > 2000,
        "upgradeMachinesNormalizedTo96px": "Rectangle dst = new((int)center.X - 48, (int)center.Y - 64, 96, 96);" in renderer,
        "d3ATravelGatePreserved": "DrawTravelGate0696D3A(batch, phase);" in renderer,
        "radarCollisionFootprint": radar_collision_ok,
        "deckD3BProperty": "CardchaD3BIntegration" in deck,
    }
    report = {
        "phase": "0696D3-B",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "navigationConsole": {
            "path": str(NAV.relative_to(ROOT)),
            "sourceSha256": EXPECTED_NAV_SOURCE_SHA,
            "currentSha256": sha(NAV),
            "backgroundSeedRgb": list(BACKGROUND_RGB),
            "backgroundDistance": BACKGROUND_DISTANCE,
            "edgeBackgroundCandidatesRemaining": edge_candidates,
            "transparentPixels": transparent,
            "cleanup": cleanup,
        },
        "radarCollisionTiles": [list(p) for p in RADAR_COLLISION],
        "upgradeMachineVisualSize": [96, 96],
        "checks": checks,
        "scopeDeferred": ["room1-border", "entrance-arch-x2", "window-size-adjustment"],
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
    cleanup = None
    if args.apply:
        cleanup = clean_navigation_console()
        patch_renderer_scale()
        patch_radar_collision()
    if args.validate:
        print(json.dumps(validate(cleanup), indent=2))


if __name__ == "__main__":
    main()

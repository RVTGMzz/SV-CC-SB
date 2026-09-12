#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from collections import deque
import hashlib
import json
import subprocess
from PIL import Image, ImageDraw

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
HANDOFF = ROOT / "handoff/ALPHA28_0696D1S_AIRSHIP_MOTION_REPAIR.md"
LATEST = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"

BASELINE_COMMIT = "8fe52dfc23ec58b00138c4b129d91a3dd9121d81"  # verified .67 D1R materialized source
BRANCH = "cardcha-alpha28-0696d1s-airship-motion-repair"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.67"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.68"

# The actual airship is embedded in the approved Window source. The previous D1R mistake
# treated four legacy overlay files as four airship animation frames; 2..4 are actually
# window/transition slices. D1S extracts ONE real airship sprite from the approved source,
# removes only its original static placement, and animates that sprite independently.
SOURCE_BOX = (87, 29, 107, 46)  # search box around the approved airship
BACKGROUND_PALETTE_BOX = (65, 29, 85, 46)
RGB_DISTANCE_THRESHOLD = 30.0

# Exact 15x9 patch replacement proven visually clean enough at native 1x. This removes the
# original static airship without altering any furniture/window-frame pixels.
PATCH_SOURCE = (71, 33, 86, 42)
PATCH_TARGET = (89, 33, 104, 42)

# Four actual AIRSHIP positions across the center pane. No legacy window columns move.
AIRSHIP_POSITIONS = [(62, 33), (71, 33), (80, 33), (89, 33)]


def git_show_bytes(rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASELINE_COMMIT}:{rel}"], cwd=ROOT)


def restore_baseline_base() -> Image.Image:
    rel = BASE.relative_to(ROOT).as_posix()
    raw = git_show_bytes(rel)
    BASE.write_bytes(raw)
    return Image.open(BASE).convert("RGBA")


def rgb_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5


def largest_component(mask: list[list[bool]]) -> set[tuple[int, int]]:
    h = len(mask)
    w = len(mask[0]) if h else 0
    remaining = {(x, y) for y in range(h) for x in range(w) if mask[y][x]}
    best: set[tuple[int, int]] = set()
    while remaining:
        start = next(iter(remaining))
        remaining.remove(start)
        q = deque([start])
        comp = {start}
        while q:
            x, y = q.popleft()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    p = (x + dx, y + dy)
                    if p in remaining:
                        remaining.remove(p)
                        comp.add(p)
                        q.append(p)
        if len(comp) > len(best):
            best = comp
    return best


def extract_airship(base: Image.Image) -> tuple[Image.Image, dict]:
    src = base.convert("RGBA")
    x0, y0, x1, y1 = SOURCE_BOX
    bx0, by0, bx1, by1 = BACKGROUND_PALETTE_BOX
    palette = [src.getpixel((x, y))[:3] for y in range(by0, by1) for x in range(bx0, bx1)]
    palette = list(dict.fromkeys(palette))

    mask: list[list[bool]] = []
    for y in range(y0, y1):
        row = []
        for x in range(x0, x1):
            rgb = src.getpixel((x, y))[:3]
            d = min(rgb_distance(rgb, p) for p in palette)
            row.append(d > RGB_DISTANCE_THRESHOLD and y <= 43)
        mask.append(row)

    comp = largest_component(mask)
    if len(comp) < 70:
        raise RuntimeError(f"Airship extraction unexpectedly small: {len(comp)} pixels")

    xs = [x for x, _ in comp]
    ys = [y for _, y in comp]
    cx0, cy0, cx1, cy1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    sprite = Image.new("RGBA", (cx1 - cx0, cy1 - cy0), (0, 0, 0, 0))
    for rx, ry in comp:
        gx, gy = x0 + rx, y0 + ry
        sprite.putpixel((rx - cx0, ry - cy0), src.getpixel((gx, gy)))

    return sprite, {
        "searchBox": list(SOURCE_BOX),
        "componentPixels": len(comp),
        "componentBoxRelative": [cx0, cy0, cx1, cy1],
        "componentBoxGlobal": [x0 + cx0, y0 + cy0, x0 + cx1, y0 + cy1],
        "spriteSize": list(sprite.size),
        "spriteAlphaPixels": sum(1 for a in sprite.getchannel("A").getdata() if a > 0),
    }


def remove_static_airship(base: Image.Image) -> Image.Image:
    out = base.convert("RGBA").copy()
    sx0, sy0, sx1, sy1 = PATCH_SOURCE
    tx0, ty0, tx1, ty1 = PATCH_TARGET
    if (sx1-sx0, sy1-sy0) != (tx1-tx0, ty1-ty0):
        raise RuntimeError("Patch source/target dimensions differ")
    patch = out.crop(PATCH_SOURCE)
    out.paste(patch, (tx0, ty0))
    return out


def update_versions() -> None:
    for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
        p = CARDCHA / rel
        if p.exists():
            text = p.read_text(encoding="utf-8")
            text = text.replace(OLD_VERSION, NEW_VERSION)
            text = text.replace("0696D1R WINDOW BOUNDED CLEANUP TEST", "0696D1S AIRSHIP MOTION REPAIR TEST")
            p.write_text(text, encoding="utf-8")


def update_ambient_manifest() -> None:
    data = json.loads(AMBIENT.read_text(encoding="utf-8"))
    data["version"] = NEW_VERSION
    data["workstream"] = "0696D1S-airship-motion-repair"
    ow = data["observationWindow"]
    ow["productionStatus"] = "D1S_REAL_AIRSHIP_SPRITE_MOTION_D2_PENDING"
    ow["airshipMotion"] = {
        "source": "approved-window-source-airship",
        "runtimeSprite": "assets/airship_props/set01_redux/window_runtime/observation_window_airship.png",
        "positionsPx": [[x, y] for x, y in AIRSHIP_POSITIONS],
        "legacyOverlayCycling": False,
        "legacyOverlayReason": "overlay_2..4 are window/transition slices, not airship frames",
        "acceptance": "PENDING-RON-VISUAL",
    }
    AMBIENT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def render_preview(clean_base: Image.Image, sprite: Image.Image) -> None:
    scale = 4
    w, h = clean_base.size
    margin = 14
    label_h = 26
    card_w, card_h = w * scale, h * scale
    canvas = Image.new("RGBA", (margin * 5 + card_w * 4, label_h + card_h + 36), (18, 18, 25, 255))
    d = ImageDraw.Draw(canvas)
    for i, (px, py) in enumerate(AIRSHIP_POSITIONS):
        frame = clean_base.copy()
        frame.alpha_composite(sprite, (px, py))
        frame = frame.resize((card_w, card_h), Image.Resampling.NEAREST)
        x = margin + i * (card_w + margin)
        canvas.alpha_composite(frame, (x, label_h))
        d.text((x, 6), f"REAL AIRSHIP {i+1}  x={px}", fill=(235, 235, 242, 255))
    d.text((margin, label_h + card_h + 12),
           "D1S: only the airship moves. Legacy overlay_2..4 window columns are not rendered.",
           fill=(186, 224, 205, 255))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PREVIEW)


def write_docs(report: dict) -> None:
    HANDOFF.write_text(f'''# Alpha 28 / 0696D1S — Real Airship Motion Repair

## Status
- Branch: `{BRANCH}`
- Build: `{NEW_VERSION}`
- Visual acceptance: **PENDING-RON-VISUAL**

## Root cause
D1R incorrectly interpreted `observation_window_overlay_1..4.png` as four animation frames. They are not. Overlay 1 contains the visible sky/airship scene, while overlays 2–4 are window/transition slices. Cycling them therefore made vertical window columns appear to fly across the view.

## D1S correction
- legacy four-overlay cycling is completely disabled;
- the real airship is extracted from the approved `.67` Window source as one transparent sprite;
- the original static airship placement is patched out of the map-native Window source;
- runtime moves only that airship sprite across four center-pane positions;
- no window pillar, frame, plant, lamp, telescope or scenery slice is animated;
- D2 season/time/weather matrix is still deferred.

## Evidence
- extracted sprite size: **{report['airship']['spriteSize'][0]}x{report['airship']['spriteSize'][1]}**
- extracted opaque sprite pixels: **{report['airship']['spriteAlphaPixels']}**
- runtime positions: **{AIRSHIP_POSITIONS}**
- old overlay cycling active: **FALSE**

## Next gate
Ron checks the D1S preview/TEST. If the airship motion is visually accepted, proceed to D2 and apply the same independent-airship concept to the season/time/weather matrix.
''', encoding="utf-8")

    LATEST.write_text(f'''# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
`{BRANCH}`

Current build candidate:
`{NEW_VERSION}`

Current handoff:
`handoff/ALPHA28_0696D1S_AIRSHIP_MOTION_REPAIR.md`

## Status
- 0696D1 `.65`: visual rejected for clipping/hollowing/bleed.
- 0696D1R `.67`: source/alpha geometry repaired, but Ron caught a semantic animation bug: overlay 2–4 are window-column/transition slices, not airship frames.
- 0696D1S `.68`: removes legacy overlay cycling and animates one extracted real airship sprite across the center pane.
- Window furniture/body remains map-native and static.
- D2 season/time/weather matrix and D3 Navigation Console remain deferred.
- Visual acceptance: **PENDING-RON-VISUAL**.

## Continuation order
1. 0696D1S Real Airship Motion Repair — current acceptance gate
2. 0696D2 Window Environment Matrix Rebuild
3. 0696D3 Navigation Console Source Cleanup
4. 0696D4 Deck Integration & Acceptance

Do not proceed to D2 until Ron accepts the actual airship motion.
''', encoding="utf-8")


def main() -> None:
    base = restore_baseline_base()
    if base.size != (160, 80):
        raise RuntimeError(f"Unexpected Window size: {base.size}")

    sprite, airship_stats = extract_airship(base)
    clean = remove_static_airship(base)

    WINDOW.mkdir(parents=True, exist_ok=True)
    clean.save(BASE)
    clean.save(FRAME)
    sprite.save(AIRSHIP)

    update_versions()
    update_ambient_manifest()

    report = {
        "phase": "0696D1S-airship-motion-repair",
        "branch": BRANCH,
        "version": NEW_VERSION,
        "baselineCommit": BASELINE_COMMIT,
        "airship": airship_stats,
        "patchSource": list(PATCH_SOURCE),
        "patchTarget": list(PATCH_TARGET),
        "positions": [[x, y] for x, y in AIRSHIP_POSITIONS],
        "contracts": {
            "legacyOverlayCycling": False,
            "windowColumnsAnimated": False,
            "onlyAirshipMoves": True,
            "windowSize": [160, 80],
            "d2EnvironmentMatrixTouched": False,
            "d3NavigationConsoleTouched": False,
        },
        "baseSha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
        "airshipSha256": hashlib.sha256(AIRSHIP.read_bytes()).hexdigest(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    render_preview(clean, sprite)
    write_docs(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, deque
from pathlib import Path
import hashlib
import json
import re
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"
PROP_ROOT = CARDCHA / "assets/airship_props/set01_redux"
WINDOW_DIR = PROP_ROOT / "window_runtime"
BASE_PATH = PROP_ROOT / "observation_window_base.png"
OVERLAY1_PATH = PROP_ROOT / "observation_window_overlay_1.png"
FRAME_PATH = WINDOW_DIR / "observation_window_frame.png"
MASK_PATH = WINDOW_DIR / "observation_window_view_mask.png"
MANIFEST_PATH = PROP_ROOT / "airship_ambient_manifest.json"
REPORT_PATH = ROOT / "handoff/AIRSHIP_0696D1_WINDOW_SOURCE_CLEANUP_VALIDATION.json"
PREVIEW_PATH = ROOT / "handoff/AIRSHIP_0696D1_WINDOW_SOURCE_CLEANUP_PREVIEW.png"
HANDOFF_PATH = ROOT / "handoff/ALPHA28_0696D1_OBSERVATION_WINDOW_SOURCE_CLEANUP.md"
LATEST_PATH = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.65"
BRANCH = "cardcha-alpha28-0696d1-observation-window-source-cleanup"

# Source matte colors found in the approved 0690 window export. The cleanup is deliberately
# conservative: only pixels connected to the outer canvas AND near this matte palette lose alpha.
MATTE_SEEDS = [
    (244, 214, 168),
    (244, 210, 156),
    (238, 204, 156),
]
MATTE_DISTANCE = 24


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rgb_sha(im: Image.Image) -> str:
    return sha256_bytes(im.convert("RGB").tobytes())


def alpha_sha(im: Image.Image) -> str:
    return sha256_bytes(im.convert("RGBA").getchannel("A").tobytes())


def is_matte_candidate(px: tuple[int, int, int, int]) -> bool:
    r, g, b, a = px
    if a == 0:
        return True
    threshold2 = MATTE_DISTANCE * MATTE_DISTANCE
    return min((r-sr)**2 + (g-sg)**2 + (b-sb)**2 for sr, sg, sb in MATTE_SEEDS) <= threshold2


def border_connected_matte(im: Image.Image) -> set[tuple[int, int]]:
    rgba = im.convert("RGBA")
    w, h = rgba.size
    q: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    def offer(x: int, y: int) -> None:
        p = (x, y)
        if p in seen:
            return
        if is_matte_candidate(rgba.getpixel(p)):
            seen.add(p)
            q.append(p)

    for x in range(w):
        offer(x, 0)
        offer(x, h - 1)
    for y in range(h):
        offer(0, y)
        offer(w - 1, y)

    while q:
        x, y = q.popleft()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                offer(nx, ny)
    return seen


def clean_source(base: Image.Image) -> tuple[Image.Image, dict]:
    src = base.convert("RGBA")
    connected = border_connected_matte(src)
    out = src.copy()
    px = out.load()
    changed_opaque = 0
    already_transparent = 0
    for x, y in connected:
        r, g, b, a = px[x, y]
        if a == 0:
            already_transparent += 1
            continue
        px[x, y] = (r, g, b, 0)
        changed_opaque += 1

    # RGB bytes are intentionally untouched. D1 is an alpha-matte cleanup, not a redraw.
    assert rgb_sha(src) == rgb_sha(out), "0696D1 must not repaint Observation Window RGB data"
    return out, {
        "borderConnectedCandidateCount": len(connected),
        "opaqueMattePixelsMadeTransparent": changed_opaque,
        "alreadyTransparentCandidates": already_transparent,
        "rgbShaBefore": rgb_sha(src),
        "rgbShaAfter": rgb_sha(out),
        "alphaShaBefore": alpha_sha(src),
        "alphaShaAfter": alpha_sha(out),
        "transparentPixelsBefore": sum(1 for a in src.getchannel("A").getdata() if a == 0),
        "transparentPixelsAfter": sum(1 for a in out.getchannel("A").getdata() if a == 0),
    }


def rebuild_runtime_frame(clean_base: Image.Image) -> dict:
    overlay1 = Image.open(OVERLAY1_PATH).convert("RGBA")
    if clean_base.size != (160, 80) or overlay1.size != clean_base.size:
        raise RuntimeError("Observation Window dimensions drifted")

    aperture_alpha = overlay1.getchannel("A")
    frame = clean_base.copy()
    fp = frame.load()
    ap = aperture_alpha.load()
    aperture_pixels = 0
    for y in range(frame.height):
        for x in range(frame.width):
            if ap[x, y] > 0:
                r, g, b, _ = fp[x, y]
                fp[x, y] = (r, g, b, 0)
                aperture_pixels += 1

    mask = Image.new("RGBA", clean_base.size, (0, 0, 0, 0))
    mp = mask.load()
    for y in range(mask.height):
        for x in range(mask.width):
            if ap[x, y] > 0:
                mp[x, y] = (255, 255, 255, 255)

    WINDOW_DIR.mkdir(parents=True, exist_ok=True)
    frame.save(FRAME_PATH)
    mask.save(MASK_PATH)
    return {
        "aperturePixels": aperture_pixels,
        "frameTransparentPixels": sum(1 for a in frame.getchannel("A").getdata() if a == 0),
        "frameBorderConnectedMatteOpaquePixels": sum(
            1 for x, y in border_connected_matte(frame) if frame.getpixel((x, y))[3] > 0
        ),
    }


def checker(size: tuple[int, int], cell: int = 8) -> Image.Image:
    w, h = size
    out = Image.new("RGBA", size, (34, 34, 46, 255))
    d = ImageDraw.Draw(out)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            fill = (62, 62, 80, 255) if ((x // cell) + (y // cell)) % 2 == 0 else (38, 38, 50, 255)
            d.rectangle((x, y, min(x+cell-1,w-1), min(y+cell-1,h-1)), fill=fill)
    return out


def render_preview(original: Image.Image, cleaned: Image.Image, frame: Image.Image, stats: dict) -> None:
    scale = 3
    tile_w, tile_h = 160 * scale, 80 * scale
    margin = 20
    header = 46
    canvas = Image.new("RGBA", (margin*4 + tile_w*3, header + tile_h + 50), (18, 18, 25, 255))
    d = ImageDraw.Draw(canvas)
    labels = ["BEFORE: matte export", "AFTER: clean base", "RUNTIME FRAME: clean alpha"]
    images = [original, cleaned, frame]
    for i, (label, im) in enumerate(zip(labels, images)):
        x = margin + i * (tile_w + margin)
        y = header
        bg = checker(im.size)
        bg.alpha_composite(im)
        bg = bg.resize((tile_w, tile_h), Image.Resampling.NEAREST)
        canvas.alpha_composite(bg, (x, y))
        d.text((x, 14), label, fill=(240,240,245,255))
    d.text((margin, header + tile_h + 16),
           f"Removed opaque border matte: {stats['opaqueMattePixelsMadeTransparent']} px | RGB artwork unchanged",
           fill=(205, 221, 235, 255))
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PREVIEW_PATH)


def update_versions() -> None:
    old = "0.3.0-alpha.28.0.4.14.4.5.12.64"
    for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
        path = CARDCHA / rel
        if path.exists():
            text = path.read_text(encoding="utf-8")
            text = text.replace(old, NEW_VERSION)
            text = text.replace("0696C AIRSHIP DECK VISUAL RECOVERY TEST", "0696D1 OBSERVATION WINDOW SOURCE CLEANUP TEST")
            path.write_text(text, encoding="utf-8")


def update_manifest_contract() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["version"] = NEW_VERSION
    manifest["workstream"] = "0696D1-observation-window-source-cleanup"
    ow = manifest["observationWindow"]
    ow["productionStatus"] = "SOURCE_CLEANED_D1_MATRIX_REBUILD_PENDING_D2"
    ow["sourceCleanup"] = {
        "mode": "border-connected-matte-alpha-removal",
        "rgbArtworkPreserved": True,
        "sourcePath": "assets/airship_props/set01_redux/observation_window_base.png",
        "framePath": "assets/airship_props/set01_redux/window_runtime/observation_window_frame.png",
        "acceptance": "PENDING-RON-VISUAL",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def update_source_pack_hash() -> None:
    path = ROOT / "handoff/AIRSHIP_SOURCE_PACK_0696.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    for rec in data.get("assets", []):
        if rec.get("path") == "src/Cardcha/assets/airship_props/set01_redux/observation_window_base.png":
            im = Image.open(BASE_PATH).convert("RGBA")
            rec["sha256"] = hashlib.sha256(BASE_PATH.read_bytes()).hexdigest()
            rec["dimensions"] = [im.width, im.height]
            rec["mode"] = "RGBA"
            rec["alpha_bbox"] = list(im.getchannel("A").getbbox() or (0,0,0,0))
            rec["nontransparent_pixels"] = sum(1 for a in im.getchannel("A").getdata() if a)
            rec["status"] = "source-faithful-alpha-cleanup-0696D1"
            rec["approved_operations"] = ["alpha-matte-cleanup", "grid-split", "depth-slice", "transparent-padding-preserved"]
            break
    data["source_policy"] = "Approved repo sprite geometry/RGB preserved. 0696D1 removes only border-connected export matte through alpha cleanup; no redraw or rescale."
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_handoff(report: dict) -> None:
    HANDOFF_PATH.write_text(f'''# Alpha 28 / 0696D.1 — Observation Window Source Cleanup

## Status
- Branch: `{BRANCH}`
- Build: `{NEW_VERSION}`
- Scope: Observation Window source only
- Technical validation: **PASS when CI validates this materialized output**
- Visual acceptance: **PENDING-RON-VISUAL**

## Why this pass exists
Ron rejected the remaining pale/yellow rectangle around the Observation Window. Inspection confirmed the rectangle is not merely a debug overlay: `observation_window_base.png` itself contains a large opaque export matte connected to the canvas edge.

## D1 rule
This pass is deliberately narrow. It does **not** rebuild the 80 environment states and does **not** touch Navigation Console cleanup. Those are separate passes D2 and D3.

## What D1 changes
- preserves the exact 160x80 footprint;
- preserves every RGB pixel of the approved Observation Window artwork;
- changes alpha only for border-connected pixels near the known matte palette;
- rebuilds `window_runtime/observation_window_frame.png` from the cleaned source;
- preserves the current aperture mask and 80-state environment matrix for D2;
- leaves Navigation Console source untouched for D3.

## Cleanup evidence
- opaque matte pixels made transparent: **{report['cleanup']['opaqueMattePixelsMadeTransparent']}**
- transparent pixels before: **{report['cleanup']['transparentPixelsBefore']}**
- transparent pixels after: **{report['cleanup']['transparentPixelsAfter']}**
- RGB SHA before: `{report['cleanup']['rgbShaBefore']}`
- RGB SHA after: `{report['cleanup']['rgbShaAfter']}`
- RGB identity preserved: **{str(report['cleanup']['rgbShaBefore'] == report['cleanup']['rgbShaAfter']).upper()}**

## Non-goals
- no console cleanup;
- no environment-matrix repaint/rebuild;
- no layer/collision redesign;
- no room-shell change;
- no rescale or redraw.

## Next pass
After Ron confirms the source/frame matte is gone, continue with **0696D.2 — Window Environment Matrix Rebuild**, using this clean source as the only allowed frame/base input.
''', encoding="utf-8")

    LATEST_PATH.write_text(f'''# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
`{BRANCH}`

Current build candidate:
`{NEW_VERSION}`

Current handoff:
`handoff/ALPHA28_0696D1_OBSERVATION_WINDOW_SOURCE_CLEANUP.md`

## Status
- 0696C `.64`: technical PASS but visually rejected for remaining yellow/matte hero-prop source contamination.
- 0696D.1 isolates **Observation Window source cleanup only**.
- Window footprint remains 160x80 / 10x5 tiles.
- RGB artwork is byte-identical before/after cleanup; only alpha for border-connected matte pixels changes.
- Navigation Console is intentionally deferred to 0696D.3.
- Window season/time/weather matrix is intentionally deferred to 0696D.2.
- Visual acceptance remains **PENDING-RON-VISUAL**.

## Continuation order
1. 0696D.1 Observation Window Source Cleanup
2. 0696D.2 Window Environment Matrix Rebuild
3. 0696D.3 Navigation Console Source Cleanup
4. 0696D.4 Deck Integration & Acceptance

## Non-negotiable rule
Do not merge the four passes into one recovery blob. Each pass must pass independently before the next is promoted.
''', encoding="utf-8")


def main() -> None:
    original = Image.open(BASE_PATH).convert("RGBA")
    if original.size != (160, 80):
        raise RuntimeError(f"Observation Window footprint drifted: {original.size}")

    cleaned, cleanup = clean_source(original)
    cleaned.save(BASE_PATH)
    frame_stats = rebuild_runtime_frame(cleaned)
    frame = Image.open(FRAME_PATH).convert("RGBA")

    update_versions()
    update_manifest_contract()
    update_source_pack_hash()

    report = {
        "phase": "0696D1-observation-window-source-cleanup",
        "branch": BRANCH,
        "version": NEW_VERSION,
        "technicalValidation": "MATERIALIZED_PENDING_VALIDATOR",
        "visualAcceptance": "PENDING-RON-VISUAL",
        "footprintPx": [160, 80],
        "footprintTiles": [10, 5],
        "cleanup": cleanup,
        "runtimeFrame": frame_stats,
        "scopeLock": {
            "windowSourceChanged": True,
            "consoleSourceChanged": False,
            "environmentMatrixRebuilt": False,
            "roomShellChanged": False,
            "collisionChanged": False,
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    render_preview(original, cleaned, frame, cleanup)
    write_handoff(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

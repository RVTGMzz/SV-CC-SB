#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
from pathlib import Path
import hashlib
import io
import json
import subprocess
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"
PROP = CARDCHA / "assets/airship_props/set01_redux"
WINDOW = PROP / "window_runtime"
BASE = PROP / "observation_window_base.png"
OVERLAYS = [PROP / f"observation_window_overlay_{i}.png" for i in range(1, 5)]
FRAME = WINDOW / "observation_window_frame.png"
MANIFEST = PROP / "airship_ambient_manifest.json"
SOURCE_PACK = ROOT / "handoff/AIRSHIP_SOURCE_PACK_0696.json"
REPORT = ROOT / "handoff/AIRSHIP_0696D1R_WINDOW_BOUNDED_VALIDATION.json"
PREVIEW = ROOT / "handoff/AIRSHIP_0696D1R_WINDOW_FRAMES_PREVIEW.png"
HANDOFF = ROOT / "handoff/ALPHA28_0696D1R_WINDOW_BOUNDED_CLEANUP.md"
LATEST = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"

BASELINE_COMMIT = "0b13de1ac30dfa019061d3626c478c5460dab89f"  # verified 0696C .64 source
BRANCH = "cardcha-alpha28-0696d1-observation-window-source-cleanup"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.65"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.66"
EXPECTED_SIZE = (160, 80)
MATTE_RGB = {
    (244, 214, 168),
    (244, 210, 156),
    (238, 204, 156),
}


def git_show_bytes(rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASELINE_COMMIT}:{rel}"], cwd=ROOT)


def restore_authoritative_sources() -> dict[str, str]:
    paths = [BASE, *OVERLAYS]
    hashes = {}
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        raw = git_show_bytes(rel)
        path.write_bytes(raw)
        hashes[rel] = hashlib.sha256(raw).hexdigest()
    return hashes


def rgb_sha(im: Image.Image) -> str:
    return hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()


def rgba_sha(im: Image.Image) -> str:
    return hashlib.sha256(im.convert("RGBA").tobytes()).hexdigest()


def border_connected_exact_matte(src: Image.Image) -> set[tuple[int, int]]:
    im = src.convert("RGBA")
    w, h = im.size
    q: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    def candidate(x: int, y: int) -> bool:
        r, g, b, a = im.getpixel((x, y))
        return a == 0 or (r, g, b) in MATTE_RGB

    def offer(x: int, y: int) -> None:
        p = (x, y)
        if p in seen or not candidate(x, y):
            return
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


def clean_base(original: Image.Image) -> tuple[Image.Image, dict]:
    src = original.convert("RGBA")
    out = src.copy()
    connected = border_connected_exact_matte(src)
    changed = []
    for x, y in connected:
        r, g, b, a = src.getpixel((x, y))
        if a > 0 and (r, g, b) in MATTE_RGB:
            out.putpixel((x, y), (r, g, b, 0))
            changed.append((x, y))

    # Hard safety gate: D1R is allowed to change alpha only on exact known matte colors.
    for y in range(src.height):
        for x in range(src.width):
            before = src.getpixel((x, y))
            after = out.getpixel((x, y))
            if before == after:
                continue
            assert before[:3] in MATTE_RGB, (x, y, before, after)
            assert after[:3] == before[:3] and after[3] == 0, (x, y, before, after)

    assert rgb_sha(src) == rgb_sha(out), "D1R must never repaint Window RGB artwork"
    return out, {
        "method": "border-connected exact matte RGB only",
        "changedOpaquePixels": len(changed),
        "transparentBefore": sum(a == 0 for a in src.getchannel("A").getdata()),
        "transparentAfter": sum(a == 0 for a in out.getchannel("A").getdata()),
        "rgbShaBefore": rgb_sha(src),
        "rgbShaAfter": rgb_sha(out),
        "rgbaShaBefore": rgba_sha(src),
        "rgbaShaAfter": rgba_sha(out),
        "changedBounds": list(Image.new("1", src.size).getbbox() or (0,0,0,0)),
    }


def sanitize_overlay(original: Image.Image, index: int) -> tuple[Image.Image, dict]:
    src = original.convert("RGBA")
    out = src.copy()
    removed = 0
    preserved_nonblack = 0
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = src.getpixel((x, y))
            if a > 0 and (r, g, b) == (0, 0, 0):
                out.putpixel((x, y), (0, 0, 0, 0))
                removed += 1
            elif a > 0:
                preserved_nonblack += 1

    # Hard safety gate: non-black RGBA data must remain byte-identical.
    for y in range(src.height):
        for x in range(src.width):
            before = src.getpixel((x, y))
            after = out.getpixel((x, y))
            if before[:3] != (0,0,0):
                assert before == after, (index, x, y, before, after)
            elif before[3] == 0:
                assert after == before, (index, x, y, before, after)
            else:
                assert after == (0,0,0,0), (index, x, y, before, after)

    return out, {
        "frame": index,
        "size": list(src.size),
        "opaquePureBlackRemoved": removed,
        "nonBlackOpaquePixelsPreserved": preserved_nonblack,
        "rgbaShaBefore": rgba_sha(src),
        "rgbaShaAfter": rgba_sha(out),
        "alphaBBoxBefore": list(src.getchannel("A").getbbox() or (0,0,0,0)),
        "alphaBBoxAfter": list(out.getchannel("A").getbbox() or (0,0,0,0)),
    }


def checker(size: tuple[int,int], cell: int = 8) -> Image.Image:
    out = Image.new("RGBA", size, (38,38,50,255))
    draw = ImageDraw.Draw(out)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            c = (67,67,86,255) if ((x//cell)+(y//cell)) % 2 == 0 else (38,38,50,255)
            draw.rectangle((x,y,min(x+cell-1,size[0]-1),min(y+cell-1,size[1]-1)), fill=c)
    return out


def composite_for_preview(base: Image.Image, overlay: Image.Image) -> Image.Image:
    bg = checker(base.size)
    bg.alpha_composite(base.convert("RGBA"))
    bg.alpha_composite(overlay.convert("RGBA"))
    return bg


def render_preview(orig_base: Image.Image, orig_overlays: list[Image.Image], fixed_base: Image.Image, fixed_overlays: list[Image.Image]) -> None:
    scale = 3
    card_w, card_h = EXPECTED_SIZE[0]*scale, EXPECTED_SIZE[1]*scale
    margin, top, row_gap = 18, 46, 52
    width = margin*5 + card_w*4
    height = top + card_h*2 + row_gap + 50
    canvas = Image.new("RGBA", (width, height), (16,17,24,255))
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 14), "0696D1R | TOP = .64 ORIGINAL | BOTTOM = BOUNDED FIX | each file stays 160x80", fill=(238,240,246,255))

    for i in range(4):
        x = margin + i*(card_w+margin)
        before = composite_for_preview(orig_base, orig_overlays[i]).resize((card_w,card_h), Image.Resampling.NEAREST)
        after = composite_for_preview(fixed_base, fixed_overlays[i]).resize((card_w,card_h), Image.Resampling.NEAREST)
        canvas.alpha_composite(before, (x, top))
        canvas.alpha_composite(after, (x, top+card_h+row_gap))
        draw.text((x, top-20), f"ORIGINAL frame {i+1}", fill=(225,198,150,255))
        draw.text((x, top+card_h+row_gap-20), f"FIXED frame {i+1}", fill=(155,230,190,255))

    draw.text((margin, height-30), "No crop. No shift. No strip packing. No aperture cutout. Pure-black overlay export masks become alpha=0 only.", fill=(205,214,230,255))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PREVIEW)


def update_versions() -> None:
    for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
        p = CARDCHA / rel
        if p.exists():
            text = p.read_text(encoding="utf-8")
            text = text.replace(OLD_VERSION, NEW_VERSION)
            text = text.replace("0696D1 OBSERVATION WINDOW SOURCE CLEANUP TEST", "0696D1R WINDOW BOUNDED CLEANUP TEST")
            p.write_text(text, encoding="utf-8")


def update_manifest() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["version"] = NEW_VERSION
    data["workstream"] = "0696D1R-window-bounded-cleanup"
    ow = data["observationWindow"]
    ow["productionStatus"] = "D1R_BOUNDED_SOURCE_CLEAN_4_OVERLAYS_ACTIVE_D2_PENDING"
    ow["sourceCleanup"] = {
        "mode": "exact-border-matte-only-plus-pure-black-overlay-alpha-repair",
        "baselineCommit": BASELINE_COMMIT,
        "framePacking": "forbidden",
        "crop": "forbidden",
        "shift": "forbidden",
        "apertureCutout": "forbidden",
        "overlayFiles": [f"assets/airship_props/set01_redux/observation_window_overlay_{i}.png" for i in range(1,5)],
        "acceptance": "PENDING-RON-VISUAL",
    }
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def update_source_pack() -> None:
    if not SOURCE_PACK.exists():
        return
    data = json.loads(SOURCE_PACK.read_text(encoding="utf-8"))
    targets = {str(p.relative_to(ROOT)).replace("\\","/"): p for p in [BASE, *OVERLAYS]}
    for rec in data.get("assets", []):
        rel = rec.get("path")
        if rel not in targets:
            continue
        p = targets[rel]
        im = Image.open(p).convert("RGBA")
        rec["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        rec["dimensions"] = list(im.size)
        rec["mode"] = "RGBA"
        rec["alpha_bbox"] = list(im.getchannel("A").getbbox() or (0,0,0,0))
        rec["nontransparent_pixels"] = sum(a > 0 for a in im.getchannel("A").getdata())
        rec["status"] = "source-faithful-bounded-cleanup-0696D1R"
    data["source_policy"] = "0696D1R restores verified .64 source first, then applies only exact border matte alpha cleanup to the base and pure-black alpha repair to each independent 160x80 window overlay. No crop, shift, packing, redraw, or aperture cutout."
    SOURCE_PACK.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_docs(report: dict) -> None:
    removed = [x["opaquePureBlackRemoved"] for x in report["overlays"]]
    HANDOFF.write_text(f'''# Alpha 28 / 0696D1R — Observation Window Bounded Cleanup

## Status
- Branch: `{BRANCH}`
- Build: `{NEW_VERSION}`
- Baseline restored before cleanup: `{BASELINE_COMMIT}` (.64)
- Visual acceptance: **PENDING-RON-VISUAL**

## Why D1R exists
0696D1 `.65` is **VISUAL REJECTED by Ron**. The fuzzy matte cleanup clipped real left/right sprite detail, and the runtime frame was incorrectly hollowed even though the approved 0690 contract already provides four independent transparent moving-sky overlays.

## Locked D1R rules
- source-of-truth is restored from verified `.64` before every materialization;
- base stays exactly 160x80 and is never cropped or shifted;
- only exact known pale export-matte colors connected to the canvas edge may lose alpha;
- all non-matte base pixels must remain RGBA-identical;
- four animation overlays remain four separate 160x80 files;
- overlay repair changes only opaque pure-black export-mask pixels to transparent;
- non-black overlay pixels remain RGBA-identical;
- no strip packing, no neighbor spill, no aperture/hollow-frame cutout.

## Materialized evidence
- base matte pixels removed: **{report['base']['changedOpaquePixels']}**
- overlay pure-black pixels removed by frame: **{removed}**
- all five Window source files: **160x80**
- runtime contract for this isolated pass: TMX owns the static body; runtime cycles the four repaired transparent overlays.

## Scope lock
D1R does not rebuild the season/time/weather matrix and does not touch Navigation Console. Those remain D2 and D3.

## Next step
Ron visually checks the D1R preview/TEST. Only after Window source/animation geometry is accepted should D2 rebuild the environmental matrix from this clean four-overlay source.
''', encoding="utf-8")

    LATEST.write_text(f'''# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
`{BRANCH}`

Current build candidate:
`{NEW_VERSION}`

Current handoff:
`handoff/ALPHA28_0696D1R_WINDOW_BOUNDED_CLEANUP.md`

## Status
- 0696D1 `.65`: **VISUAL REJECTED by Ron** for clipped sprite edges, incorrect hollow aperture, and apparent spill/bleed toward neighboring sprite space.
- 0696D1R `.66`: bounded rework. It restores `.64` source first and then performs only exact allowed alpha repairs.
- Observation Window remains 160x80 / 10x5 tiles.
- Four approved animation overlays remain four independent 160x80 files.
- No crop, shift, strip packing, or aperture cutout is allowed.
- Navigation Console remains deferred to D3.
- Season/time/weather matrix remains deferred to D2.
- Visual acceptance: **PENDING-RON-VISUAL**.

## Continuation order
1. 0696D1R Window bounded source/overlay cleanup — current
2. 0696D2 Window Environment Matrix Rebuild
3. 0696D3 Navigation Console Source Cleanup
4. 0696D4 Deck Integration & Acceptance

## Non-negotiable rule
Do not proceed to D2 until Ron accepts Window geometry/alpha behavior. Technical PASS never equals visual PASS.
''', encoding="utf-8")


def main() -> None:
    baseline_hashes = restore_authoritative_sources()
    orig_base = Image.open(BASE).convert("RGBA")
    orig_overlays = [Image.open(p).convert("RGBA") for p in OVERLAYS]
    assert orig_base.size == EXPECTED_SIZE
    assert all(im.size == EXPECTED_SIZE for im in orig_overlays)

    fixed_base, base_stats = clean_base(orig_base)
    fixed_overlays = []
    overlay_stats = []
    for i, original in enumerate(orig_overlays, 1):
        fixed, stats = sanitize_overlay(original, i)
        fixed.save(OVERLAYS[i-1])
        fixed_overlays.append(fixed)
        overlay_stats.append(stats)

    fixed_base.save(BASE)
    WINDOW.mkdir(parents=True, exist_ok=True)
    # D1R explicitly forbids the rejected hollow frame. Keep a full clean-frame copy only.
    fixed_base.save(FRAME)

    update_versions()
    update_manifest()
    update_source_pack()

    report = {
        "phase": "0696D1R-window-bounded-cleanup",
        "branch": BRANCH,
        "version": NEW_VERSION,
        "baselineCommit": BASELINE_COMMIT,
        "technicalValidation": "MATERIALIZED_PENDING_VALIDATOR",
        "visualAcceptance": "PENDING-RON-VISUAL",
        "baselineSourceSha256": baseline_hashes,
        "base": base_stats,
        "overlays": overlay_stats,
        "contracts": {
            "dimensions": [160,80],
            "overlayFileCount": 4,
            "cropAllowed": False,
            "shiftAllowed": False,
            "stripPackingAllowed": False,
            "apertureCutoutAllowed": False,
            "consoleTouched": False,
            "environmentMatrixTouched": False,
        },
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    render_preview(orig_base, orig_overlays, fixed_base, fixed_overlays)
    write_docs(report)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()

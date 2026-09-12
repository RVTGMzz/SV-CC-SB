#!/usr/bin/env python3
"""0696 Airship Gate + Window + Set01 full-footprint audit.

This is intentionally an evidence-only pass. It does not edit TMX or artwork.
It measures the exact Set01 Redux PNGs, resolves their production TMX tilesets,
and checks whether every occupied 16x16 source cell is represented as a coherent
full-footprint placement in a runtime-visible map layer.

Visual acceptance always remains PENDING-RON-IN-GAME.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SET01 = ROOT / "src/Cardcha/assets/airship_props/set01_redux"
MAPS = {
    "deck": ROOT / "src/Cardcha/assets/airship_deck.tmx",
    "sky_dock": ROOT / "src/Cardcha/assets/sky_dock_interior.tmx",
}
OUT_JSON = ROOT / "handoff/AIRSHIP_SET01_FULL_FOOTPRINT_AUDIT_0696.json"
OUT_MD = ROOT / "handoff/ALPHA28_0696_AIRSHIP_SET01_FULL_FOOTPRINT_AUDIT.md"
OUT_SHEET = ROOT / "handoff/AIRSHIP_SET01_FULL_FOOTPRINT_AUDIT_0696.png"
TILE = 16
VISIBLE_LAYERS = {"Back", "Buildings", "Front", "AlwaysFront"}
NONVISIBLE_KNOWN = {"BackDecor"}

# Static physical source-of-truth files. Overlays are intentionally runtime-owned.
STATIC_PROPS = {
    "route_notice_board.png": {"room": "sky_dock", "kind": "physical"},
    "boarding_gate_arch.png": {"room": "sky_dock", "kind": "physical", "focus": True},
    "signal_lamp.png": {"room": "both", "kind": "physical"},
    "cargo_parcel_crate.png": {"room": "sky_dock", "kind": "physical"},
    "observation_window_base.png": {"room": "deck", "kind": "physical", "focus": True},
    "navigation_console_base.png": {"room": "deck", "kind": "physical"},
    "collision_blocker.png": {"room": "both", "kind": "collision"},
}

FAMILY_ALIASES = {
    "route_notice_board.png": ["route_notice_board"],
    "boarding_gate_arch.png": ["boarding_gate_arch", "boarding_gate"],
    "signal_lamp.png": ["signal_lamp"],
    "cargo_parcel_crate.png": ["cargo_parcel_crate", "cargo_crate"],
    "observation_window_base.png": ["observation_window", "observation_window_base"],
    "navigation_console_base.png": ["navigation_console", "navigation_console_base"],
    "collision_blocker.png": ["collision_blocker", "collision"],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rgba_stats(path: Path) -> dict:
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    if w % TILE or h % TILE:
        grid_w = math.ceil(w / TILE)
        grid_h = math.ceil(h / TILE)
    else:
        grid_w, grid_h = w // TILE, h // TILE

    alpha = im.getchannel("A")
    bbox = alpha.getbbox()
    occupied = []
    near_black_opaque = 0
    opaque = 0
    nontransparent = 0

    pixels = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a:
                nontransparent += 1
            if a >= 250:
                opaque += 1
                if r <= 8 and g <= 8 and b <= 8:
                    near_black_opaque += 1

    for ty in range(grid_h):
        for tx in range(grid_w):
            x0, y0 = tx * TILE, ty * TILE
            x1, y1 = min(x0 + TILE, w), min(y0 + TILE, h)
            nonzero = 0
            black_opaque = 0
            total = max(1, (x1 - x0) * (y1 - y0))
            for y in range(y0, y1):
                for x in range(x0, x1):
                    r, g, b, a = pixels[x, y]
                    if a:
                        nonzero += 1
                    if a >= 250 and r <= 8 and g <= 8 and b <= 8:
                        black_opaque += 1
            if nonzero:
                occupied.append({
                    "tx": tx,
                    "ty": ty,
                    "local_id": ty * grid_w + tx,
                    "alpha_coverage": round(nonzero / total, 6),
                    "opaque_black_coverage": round(black_opaque / total, 6),
                })

    return {
        "width": w,
        "height": h,
        "tile_width": grid_w,
        "tile_height": grid_h,
        "tile_aligned": (w % TILE == 0 and h % TILE == 0),
        "alpha_bbox": list(bbox) if bbox else None,
        "occupied_cell_count": len(occupied),
        "occupied_cells": occupied,
        "nontransparent_pixels": nontransparent,
        "opaque_pixels": opaque,
        "opaque_near_black_pixels": near_black_opaque,
        "opaque_near_black_ratio_of_opaque": round(near_black_opaque / opaque, 6) if opaque else 0.0,
    }


def parse_csv(text: str) -> List[int]:
    return [int(x.strip()) for x in text.replace("\n", "").split(",") if x.strip()]


def resolve_image(map_path: Path, source: str) -> Path:
    return (map_path.parent / source).resolve()


def parse_map(map_path: Path) -> dict:
    root = ET.parse(map_path).getroot()
    width = int(root.attrib["width"])
    height = int(root.attrib["height"])
    tilesets = []
    for ts in root.findall("tileset"):
        firstgid = int(ts.attrib["firstgid"])
        image = ts.find("image")
        if image is None:
            continue
        source = image.attrib.get("source", "")
        tilecount = int(ts.attrib.get("tilecount", "0"))
        columns = int(ts.attrib.get("columns", "0"))
        image_path = resolve_image(map_path, source)
        tilesets.append({
            "firstgid": firstgid,
            "name": ts.attrib.get("name", ""),
            "tilecount": tilecount,
            "columns": columns,
            "source": source,
            "image_path": image_path,
            "image_exists": image_path.exists(),
            "image_sha256": sha256(image_path) if image_path.exists() else None,
            "image_size": list(Image.open(image_path).size) if image_path.exists() else None,
        })

    layers = {}
    placements_by_gid = defaultdict(list)
    for layer in root.findall("layer"):
        name = layer.attrib.get("name", "")
        lw = int(layer.attrib.get("width", width))
        lh = int(layer.attrib.get("height", height))
        data = layer.find("data")
        if data is None or data.attrib.get("encoding") != "csv":
            continue
        gids = parse_csv(data.text or "")
        if len(gids) != lw * lh:
            raise RuntimeError(f"{map_path}: layer {name} has {len(gids)} gids, expected {lw*lh}")
        layers[name] = gids
        for i, gid in enumerate(gids):
            if gid:
                placements_by_gid[gid].append({"layer": name, "x": i % lw, "y": i // lw})

    return {
        "path": str(map_path.relative_to(ROOT)).replace("\\", "/"),
        "width": width,
        "height": height,
        "tilesets": tilesets,
        "layers": layers,
        "placements_by_gid": dict(placements_by_gid),
    }


def normalize_name(s: str) -> str:
    s = Path(s).stem.lower()
    s = re.sub(r"^airship_\d+_", "", s)
    s = re.sub(r"\d+$", "", s)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def choose_tileset(prop_name: str, map_info: dict, source_stats: dict) -> Optional[dict]:
    aliases = FAMILY_ALIASES[prop_name]
    candidates = []
    for ts in map_info["tilesets"]:
        hay = f"{normalize_name(ts['source'])} {normalize_name(ts['name'])}"
        alias_hit = any(a in hay for a in aliases)
        same_size = ts["image_size"] == [source_stats["width"], source_stats["height"]]
        if alias_hit:
            score = 100 + (10 if same_size else 0)
            candidates.append((score, ts))
    if not candidates:
        return None
    candidates.sort(key=lambda z: (z[0], z[1]["firstgid"]), reverse=True)
    return candidates[0][1]


def compare_images(a: Path, b: Path) -> dict:
    if not a.exists() or not b.exists():
        return {"exists": False, "pixel_equal": False, "reason": "missing-image"}
    ia = Image.open(a).convert("RGBA")
    ib = Image.open(b).convert("RGBA")
    if ia.size != ib.size:
        return {"exists": True, "pixel_equal": False, "same_size": False, "a_size": list(ia.size), "b_size": list(ib.size)}
    return {
        "exists": True,
        "same_size": True,
        "pixel_equal": ia.tobytes() == ib.tobytes(),
        "a_sha256": sha256(a),
        "b_sha256": sha256(b),
    }


def footprint_instances(prop_name: str, source_stats: dict, ts: dict, map_info: dict) -> dict:
    occupied = source_stats["occupied_cells"]
    if not occupied:
        return {"anchors": [], "complete_instances": [], "best_instance": None}

    by_gid = map_info["placements_by_gid"]
    anchor_votes = Counter()
    placements_for_local = {}
    for cell in occupied:
        gid = ts["firstgid"] + cell["local_id"]
        pls = by_gid.get(gid, [])
        placements_for_local[cell["local_id"]] = pls
        for p in pls:
            anchor_votes[(p["layer"], p["x"] - cell["tx"], p["y"] - cell["ty"])] += 1

    expected = len(occupied)
    anchors = []
    complete = []
    for (layer, ax, ay), votes in anchor_votes.most_common():
        represented = []
        missing = []
        for cell in occupied:
            gid = ts["firstgid"] + cell["local_id"]
            target = (ax + cell["tx"], ay + cell["ty"])
            hit = any(p["layer"] == layer and (p["x"], p["y"]) == target for p in by_gid.get(gid, []))
            (represented if hit else missing).append(cell["local_id"])
        rec = {
            "layer": layer,
            "anchor": [ax, ay],
            "represented_occupied_cells": len(represented),
            "expected_occupied_cells": expected,
            "coverage": round(len(represented) / expected, 6),
            "missing_local_ids": missing,
            "runtime_visible_layer": layer in VISIBLE_LAYERS,
        }
        anchors.append(rec)
        if not missing:
            complete.append(rec)

    best = max(anchors, key=lambda x: x["coverage"], default=None)
    return {
        "placements_by_local_id": {str(k): v for k, v in placements_for_local.items()},
        "anchors": anchors[:20],
        "complete_instances": complete,
        "best_instance": best,
    }


def scan_runtime_references(filename: str) -> List[str]:
    stem = Path(filename).stem
    hits = []
    for ext in ("*.cs", "*.json", "*.py"):
        for path in (ROOT / "src").rglob(ext):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if stem in text or filename in text:
                hits.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return sorted(set(hits))


def add_finding(findings: List[dict], severity: str, code: str, subject: str, detail: str, **extra) -> None:
    rec = {"severity": severity, "code": code, "subject": subject, "detail": detail}
    rec.update(extra)
    findings.append(rec)


def build_contact_sheet(asset_records: List[dict], path: Path) -> None:
    cards = []
    for rec in asset_records:
        p = ROOT / rec["path"]
        im = Image.open(p).convert("RGBA")
        scale = max(1, min(3, 160 // max(1, im.width)))
        disp = im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
        card_w = max(220, disp.width + 20)
        card_h = disp.height + 72
        cards.append((rec, disp, card_w, card_h))
    cols = 3
    rows = math.ceil(len(cards) / cols)
    col_w = max(c[2] for c in cards) if cards else 220
    row_h = max(c[3] for c in cards) if cards else 120
    sheet = Image.new("RGBA", (cols * col_w, rows * row_h), (28, 28, 32, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (rec, im, cw, ch) in enumerate(cards):
        cx, cy = (i % cols) * col_w, (i // cols) * row_h
        checker = Image.new("RGBA", im.size, (62, 62, 68, 255))
        sheet.alpha_composite(checker, (cx + 10, cy + 10))
        sheet.alpha_composite(im, (cx + 10, cy + 10))
        draw.rectangle((cx + 9, cy + 9, cx + 10 + im.width, cy + 10 + im.height), outline=(180, 180, 190, 255))
        draw.text((cx + 10, cy + 18 + im.height), Path(rec["path"]).name, fill=(240, 240, 245, 255))
        s = rec["stats"]
        draw.text((cx + 10, cy + 35 + im.height), f"{s['width']}x{s['height']} | {s['tile_width']}x{s['tile_height']} tiles | occ {s['occupied_cell_count']}", fill=(200, 200, 210, 255))
        draw.text((cx + 10, cy + 52 + im.height), rec["sha256"][:16], fill=(170, 210, 220, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def audit() -> dict:
    findings: List[dict] = []
    maps = {name: parse_map(path) for name, path in MAPS.items()}

    pngs = sorted(SET01.glob("*.png"))
    if not pngs:
        raise RuntimeError(f"No PNGs found in {SET01}")

    assets = []
    stats_by_name = {}
    for p in pngs:
        stats = rgba_stats(p)
        stats_by_name[p.name] = stats
        rec = {
            "path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(p),
            "stats": stats,
            "role": ("runtime-overlay" if "_overlay_" in p.name else STATIC_PROPS.get(p.name, {}).get("kind", "unclassified")),
        }
        if "_overlay_" in p.name:
            rec["runtime_reference_files"] = scan_runtime_references(p.name)
        assets.append(rec)
        if not stats["tile_aligned"]:
            add_finding(findings, "ERROR", "SOURCE_NOT_TILE_ALIGNED", p.name, f"Source is {stats['width']}x{stats['height']}, not divisible by 16.")
        if stats["opaque_near_black_ratio_of_opaque"] > 0.70 and p.name != "collision_blocker.png":
            add_finding(findings, "WARN", "HEAVY_OPAQUE_NEAR_BLACK", p.name, "More than 70% of opaque pixels are near-black; inspect for accidental black fill/canvas.", ratio=stats["opaque_near_black_ratio_of_opaque"])

    physical_audits = []
    for prop_name, spec in STATIC_PROPS.items():
        source = SET01 / prop_name
        if not source.exists():
            add_finding(findings, "ERROR", "MISSING_SET01_SOURCE", prop_name, "Authoritative Set01 source file is missing.")
            continue
        stats = stats_by_name[prop_name]
        target_rooms = list(maps.keys()) if spec["room"] == "both" else [spec["room"]]
        for room in target_rooms:
            mi = maps[room]
            ts = choose_tileset(prop_name, mi, stats)
            entry = {"asset": prop_name, "room": room, "focus": bool(spec.get("focus")), "kind": spec["kind"]}
            if ts is None:
                entry["tileset"] = None
                physical_audits.append(entry)
                # Signal lamp/collision must exist in both; other room-specific props must exist in assigned room.
                add_finding(findings, "ERROR", "TMX_TILESET_NOT_FOUND", f"{room}:{prop_name}", "No production TMX tileset could be resolved for this Set01 source.")
                continue
            entry["tileset"] = {k: (str(v.relative_to(ROOT)).replace("\\", "/") if k == "image_path" and isinstance(v, Path) else v) for k, v in ts.items()}
            prod_img = ts["image_path"]
            cmp = compare_images(source, prod_img)
            entry["source_vs_tmx_image"] = cmp
            if not cmp.get("same_size", False):
                add_finding(findings, "ERROR", "TMX_COPY_SIZE_MISMATCH", f"{room}:{prop_name}", "TMX production image dimensions differ from Set01 source.", comparison=cmp)
            elif not cmp.get("pixel_equal", False):
                add_finding(findings, "ERROR", "TMX_COPY_PIXEL_MISMATCH", f"{room}:{prop_name}", "TMX production image is not pixel-identical to the Set01 source. This is a stale/substituted asset path.", comparison=cmp)

            fp = footprint_instances(prop_name, stats, ts, mi)
            entry["footprint"] = fp
            physical_audits.append(entry)

            complete = fp.get("complete_instances", [])
            visible_complete = [x for x in complete if x["runtime_visible_layer"]]
            best = fp.get("best_instance")
            if spec["kind"] == "collision":
                if not complete:
                    add_finding(findings, "ERROR", "COLLISION_FOOTPRINT_MISSING", f"{room}:{prop_name}", "Collision blocker source GID is not placed as a coherent instance.", best_instance=best)
                # Collision is expected to live on Buildings in current maps.
                elif not any(x["layer"] == "Buildings" for x in complete):
                    add_finding(findings, "ERROR", "COLLISION_WRONG_LAYER", f"{room}:{prop_name}", "Collision blocker is not owned by Buildings.", complete_instances=complete)
                continue

            if not complete:
                add_finding(findings, "ERROR", "PARTIAL_OR_FRAGMENTED_FOOTPRINT", f"{room}:{prop_name}", "No complete coherent placement contains every occupied 16x16 source cell.", best_instance=best)
            elif not visible_complete:
                layers = sorted({x["layer"] for x in complete})
                add_finding(findings, "ERROR", "FULL_FOOTPRINT_ON_NONVISIBLE_LAYER", f"{room}:{prop_name}", "Full source footprint exists, but only on non-standard/non-runtime-visible layer(s).", layers=layers, complete_instances=complete)
            else:
                add_finding(findings, "INFO", "VISIBLE_FULL_FOOTPRINT", f"{room}:{prop_name}", "At least one complete source footprint exists on a standard visible TMX layer.", complete_instances=visible_complete)

    # Runtime overlay integrity. Overlay PNGs should not be forced into TMX, but must have an ownership/reference trail.
    overlays = [a for a in assets if a["role"] == "runtime-overlay"]
    for a in overlays:
        name = Path(a["path"]).name
        refs = a.get("runtime_reference_files", [])
        if not refs:
            add_finding(findings, "WARN", "OVERLAY_WITHOUT_DIRECT_RUNTIME_REFERENCE", name, "Overlay has no direct filename/stem reference under src; verify generated/copy naming or loader ownership.")

    counts = Counter(f["severity"] for f in findings)
    focus = {}
    for prop in ("boarding_gate_arch.png", "observation_window_base.png"):
        focus[prop] = [x for x in physical_audits if x["asset"] == prop]

    return {
        "audit": "0696 Gate + Window + Set01 full-footprint audit",
        "branch_contract": "cardcha-alpha28-0696-airship-concept-faithful-visible-integration",
        "tile_size": TILE,
        "visual_acceptance": "PENDING-RON-IN-GAME",
        "runtime_visible_layers": sorted(VISIBLE_LAYERS),
        "known_nonvisible_layer": "BackDecor",
        "set01_asset_count": len(assets),
        "assets": assets,
        "maps": {
            k: {
                "path": v["path"],
                "width": v["width"],
                "height": v["height"],
                "layer_names": list(v["layers"].keys()),
                "tilesets": [{kk: (str(vv.relative_to(ROOT)).replace("\\", "/") if kk == "image_path" and isinstance(vv, Path) else vv) for kk, vv in t.items()} for t in v["tilesets"]],
            }
            for k, v in maps.items()
        },
        "physical_prop_audits": physical_audits,
        "focus_gate_window": focus,
        "findings": findings,
        "summary": {
            "errors": counts.get("ERROR", 0),
            "warnings": counts.get("WARN", 0),
            "info": counts.get("INFO", 0),
            "strict_pass": counts.get("ERROR", 0) == 0,
        },
    }


def write_markdown(report: dict) -> None:
    lines = [
        "# Alpha 28 / 0696 — Gate + Window + Set01 Full-Footprint Audit",
        "",
        "**Scope:** exact Set01 Redux source pixels → production TMX image → 16×16 occupied-cell footprint → layer/placement.",
        "",
        f"**Visual acceptance:** `{report['visual_acceptance']}`",
        "",
        "This audit is evidence-only. A CI PASS does not constitute in-game visual acceptance.",
        "",
        "## Summary",
        "",
        f"- Set01 PNGs inventoried: **{report['set01_asset_count']}**",
        f"- Errors: **{report['summary']['errors']}**",
        f"- Warnings: **{report['summary']['warnings']}**",
        f"- Informational confirmations: **{report['summary']['info']}**",
        f"- Strict audit: **{'PASS' if report['summary']['strict_pass'] else 'FAIL'}**",
        "",
        "## Gate + Window focus",
        "",
    ]
    for asset in ("boarding_gate_arch.png", "observation_window_base.png"):
        lines.append(f"### `{asset}`")
        entries = report["focus_gate_window"].get(asset, [])
        for e in entries:
            room = e["room"]
            ts = e.get("tileset")
            if not ts:
                lines.append(f"- `{room}`: production tileset **NOT FOUND**")
                continue
            cmp = e.get("source_vs_tmx_image", {})
            best = e.get("footprint", {}).get("best_instance")
            complete = e.get("footprint", {}).get("complete_instances", [])
            lines.append(f"- `{room}` tileset `{ts['name']}` firstgid `{ts['firstgid']}`")
            lines.append(f"  - Set01 ↔ TMX image pixel-identical: **{cmp.get('pixel_equal', False)}**")
            lines.append(f"  - complete footprint instances: **{len(complete)}**")
            if best:
                lines.append(f"  - best: layer `{best['layer']}`, anchor `{best['anchor']}`, coverage **{best['coverage']:.1%}**, runtime-visible: **{best['runtime_visible_layer']}**")
        lines.append("")

    lines += ["## Findings", ""]
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for f in sorted(report["findings"], key=lambda x: (order.get(x["severity"], 9), x["code"], x["subject"])):
        lines.append(f"- **{f['severity']}** `{f['code']}` — `{f['subject']}`: {f['detail']}")

    lines += [
        "",
        "## Contract for the next integration step",
        "",
        "1. Do not redraw, rescale, crop, or substitute Gate/Window/Set01 art.",
        "2. Static physical art must retain its full occupied source footprint in standard runtime-visible TMX layers.",
        "3. Runtime overlays may remain runtime-owned, but the physical base stays TMX-owned.",
        "4. Collision remains separate from art ownership.",
        "5. `BackDecor` presence is not accepted as proof that a prop is visible in game.",
        "6. Final visual acceptance requires Ron's in-game test.",
        "",
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="Exit non-zero when ERROR findings exist.")
    args = ap.parse_args()

    report = audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(report)
    build_contact_sheet(report["assets"], OUT_SHEET)

    print(json.dumps(report["summary"], indent=2))
    print(f"JSON: {OUT_JSON.relative_to(ROOT)}")
    print(f"MD:   {OUT_MD.relative_to(ROOT)}")
    print(f"PNG:  {OUT_SHEET.relative_to(ROOT)}")
    if args.strict and not report["summary"]["strict_pass"]:
        print("STRICT AUDIT FAILED: error findings remain.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json"
OUT = ROOT / "handoff/AIRSHIP_SOURCE_PACK_0696.json"
TILE = 16

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def inspect_png(path: Path) -> dict:
    im = Image.open(path).convert("RGBA")
    alpha = im.getchannel("A")
    bbox = alpha.getbbox()
    w, h = im.size
    occupied = []
    for ty in range((h + TILE - 1) // TILE):
        for tx in range((w + TILE - 1) // TILE):
            x0, y0 = tx * TILE, ty * TILE
            crop = alpha.crop((x0, y0, min(x0 + TILE, w), min(y0 + TILE, h)))
            if crop.getbbox() is not None:
                occupied.append([tx, ty])
    return {
        "sha256": sha256(path),
        "dimensions": [w, h],
        "mode": "RGBA",
        "alpha_bbox": list(bbox) if bbox else None,
        "tile_footprint": [(w + TILE - 1) // TILE, (h + TILE - 1) // TILE],
        "occupied_cells": occupied,
        "nontransparent_pixels": sum(1 for a in alpha.getdata() if a),
    }

def main() -> None:
    bp = json.loads(BLUEPRINT.read_text(encoding="utf-8"))
    records = {}
    for room_name, room in bp["rooms"].items():
        for prop in room["props"]:
            rel = prop["asset"]
            if rel in records:
                records[rel]["used_by"].append({"room": room_name, "id": prop["id"], "anchor": prop["anchor"]})
            else:
                path = ROOT / rel
                records[rel] = ({
                    "path": rel,
                    "status": "exact",
                    **inspect_png(path),
                    "used_by": [{"room": room_name, "id": prop["id"], "anchor": prop["anchor"]}],
                    "scale_factor": 1.0,
                    "approved_operations": ["grid-split", "depth-slice", "transparent-padding-preserved"],
                } if path.exists() else {
                    "path": rel,
                    "status": "missing",
                    "used_by": [{"room": room_name, "id": prop["id"], "anchor": prop["anchor"]}],
                })

            for overlay in prop.get("runtime_overlays", []):
                if overlay in records:
                    records[overlay]["used_by"].append({"room": room_name, "id": prop["id"], "role": "runtime-overlay"})
                    continue
                op = ROOT / overlay
                records[overlay] = ({
                    "path": overlay,
                    "status": "exact",
                    **inspect_png(op),
                    "used_by": [{"room": room_name, "id": prop["id"], "role": "runtime-overlay"}],
                    "scale_factor": 1.0,
                    "runtime_owner": "VFX-only",
                } if op.exists() else {
                    "path": overlay,
                    "status": "missing",
                    "used_by": [{"room": room_name, "id": prop["id"], "role": "runtime-overlay"}],
                })

    collision_rel = "src/Cardcha/assets/airship_props/set01_redux/collision_blocker.png"
    if collision_rel not in records:
        cp = ROOT / collision_rel
        records[collision_rel] = ({
            "path": collision_rel,
            "status": "exact",
            **inspect_png(cp),
            "used_by": [{"room": "both", "role": "base-Buildings-collision-primitive"}],
            "scale_factor": 1.0,
            "runtime_owner": "base Buildings collision only",
        } if cp.exists() else {
            "path": collision_rel,
            "status": "missing",
            "used_by": [{"room": "both", "role": "base-Buildings-collision-primitive"}],
        })

    missing = sorted(k for k, v in records.items() if v["status"] != "exact")
    output = {
        "schema_version": 1,
        "workstream": "0696 Airship Visual Recovery",
        "phase": "0696A-visible-architecture-recovery",
        "visual_acceptance": "PENDING-RON-IN-GAME",
        "source_policy": "Exact repo-recovered approved sprites only; no redraw, no rescale, no silent substitute.",
        "repo_recovered_asset_count": sum(1 for v in records.values() if v["status"] == "exact"),
        "repo_recovered_assets_complete": not missing,
        "external_source_pack_complete": False,
        "external_source_gap": bp["external_source_gap"],
        "assets": [records[k] for k in sorted(records)],
        "missing_repo_assets": missing,
    }
    OUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"0696 source manifest: {output['repo_recovered_asset_count']} exact repo assets; missing={len(missing)}")
    if missing:
        raise SystemExit("Required repo-recovered production asset missing: " + ", ".join(missing))

if __name__ == "__main__":
    main()

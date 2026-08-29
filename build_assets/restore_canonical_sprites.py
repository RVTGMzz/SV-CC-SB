#!/usr/bin/env python3
"""Fail-closed visual guard for approved Cardcha assets.

The canonical manifest records the approved decoded RGBA hash + dimensions. This guard
never rewrites user-authored art. If any protected asset changes unexpectedly, CI fails
and requires an explicit approved asset update instead of silently restoring/replacing it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "build_assets" / "canonical_sprites" / "manifest.json"
DEFAULT_ASSET_DIR = REPO_ROOT / "src" / "Cardcha" / "assets"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest() -> dict:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if data.get("schema") != 2:
        raise SystemExit(f"Unsupported canonical sprite schema: {data.get('schema')}")
    return data


def verify_asset(asset_dir: Path, name: str, meta: dict) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required: python3 -m pip install pillow") from exc

    path = asset_dir / name
    if not path.is_file():
        raise SystemExit(f"Protected visual asset missing: {path}")

    with Image.open(path) as image:
        image.load()
        rgba = image.convert("RGBA")
        expected_size = (int(meta["width"]), int(meta["height"]))
        if rgba.size != expected_size:
            raise SystemExit(
                f"Protected visual dimensions changed for {name}: {rgba.size} != {expected_size}"
            )
        got = sha256(rgba.tobytes())

    want = meta["rgba_sha256"]
    if got != want:
        policy = meta.get("policy", "restore")
        label = "USER-LOCKED" if policy == "verify_only" else "APPROVED-CANONICAL"
        raise SystemExit(
            f"{label} visual mismatch: {name}: RGBA {got} != {want}. "
            "Do not auto-rewrite this asset. Update the approved manifest only after an explicit user-approved asset change."
        )

    print(
        f"VERIFIED {name} {expected_size[0]}x{expected_size[1]} "
        f"policy={meta.get('policy', 'restore')} rgba={got}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-dir", type=Path, default=DEFAULT_ASSET_DIR)
    # Kept only for compatibility with older CI commands; no rewriting is performed.
    parser.add_argument("--restore", action="store_true", help="deprecated; guard is intentionally fail-closed")
    args = parser.parse_args()

    manifest = load_manifest()
    for name, meta in manifest["assets"].items():
        verify_asset(args.asset_dir, name, meta)

    print("Canonical visual guard PASS (fail-closed; no asset rewriting)")


if __name__ == "__main__":
    main()

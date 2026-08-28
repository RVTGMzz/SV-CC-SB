#!/usr/bin/env python3
"""Restore and verify Cardcha's approved canonical sprite PNGs.

The canonical source files live under build_assets/canonical_sprites/source/. They are
immutable approved binaries. The manifest records both exact PNG SHA256 and decoded
RGBA SHA256. Normal builds restore exact bytes from canonical source into src/Cardcha/assets.
CI additionally decodes the PNGs with Pillow and verifies visual pixel identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANON_ROOT = REPO_ROOT / "build_assets" / "canonical_sprites"
MANIFEST = CANON_ROOT / "manifest.json"
SOURCE_DIR = CANON_ROOT / "source"
DEFAULT_ASSET_DIR = REPO_ROOT / "src" / "Cardcha" / "assets"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_size(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("not a PNG")
    return struct.unpack(">II", data[16:24])


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def verify_source(name: str, meta: dict) -> bytes:
    path = SOURCE_DIR / name
    if not path.is_file():
        raise SystemExit(f"Canonical source missing: {path}")
    data = path.read_bytes()
    got = sha256(data)
    want = meta["png_sha256"]
    if got != want:
        raise SystemExit(f"Canonical source hash mismatch for {name}: {got} != {want}")
    size = png_size(data)
    expected = (meta["width"], meta["height"])
    if size != expected:
        raise SystemExit(f"Canonical source dimensions mismatch for {name}: {size} != {expected}")
    return data


def restore(asset_dir: Path, manifest: dict) -> None:
    asset_dir.mkdir(parents=True, exist_ok=True)
    for name, meta in manifest["assets"].items():
        data = verify_source(name, meta)
        dest = asset_dir / name
        if not dest.exists() or dest.read_bytes() != data:
            dest.write_bytes(data)
            print(f"RESTORED {name}")
        else:
            print(f"OK {name}")


def verify(asset_dir: Path, manifest: dict) -> None:
    for name, meta in manifest["assets"].items():
        verify_source(name, meta)
        path = asset_dir / name
        if not path.is_file():
            raise SystemExit(f"Asset missing: {path}")
        data = path.read_bytes()
        got = sha256(data)
        want = meta["png_sha256"]
        if got != want:
            raise SystemExit(f"Asset hash mismatch for {name}: {got} != {want}")
        size = png_size(data)
        expected = (meta["width"], meta["height"])
        if size != expected:
            raise SystemExit(f"Asset dimensions mismatch for {name}: {size} != {expected}")
        print(f"VERIFIED-PNG {name} {size[0]}x{size[1]}")


def verify_pixels(asset_dir: Path, manifest: dict) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("--verify-pixels requires Pillow (pip install pillow)") from exc
    for name, meta in manifest["assets"].items():
        path = asset_dir / name
        with Image.open(path) as image:
            image.load()
            rgba = image.convert("RGBA")
            expected_size = (meta["width"], meta["height"])
            if rgba.size != expected_size:
                raise SystemExit(f"Pixel dimensions mismatch for {name}: {rgba.size} != {expected_size}")
            got = sha256(rgba.tobytes())
        want = meta["rgba_sha256"]
        if got != want:
            raise SystemExit(f"RGBA pixel hash mismatch for {name}: {got} != {want}")
        print(f"VERIFIED-RGBA {name} {got}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-dir", type=Path, default=DEFAULT_ASSET_DIR)
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verify-pixels", action="store_true")
    args = parser.parse_args()
    if not (args.restore or args.verify or args.verify_pixels):
        parser.error("choose --restore and/or --verify and/or --verify-pixels")
    manifest = load_manifest()
    if args.restore:
        restore(args.asset_dir, manifest)
    if args.verify:
        verify(args.asset_dir, manifest)
    if args.verify_pixels:
        verify_pixels(args.asset_dir, manifest)
    print("Canonical sprite guard PASS")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Restore/verify approved Cardcha visual assets from text-safe canonical RGBA data.

Policy:
- restore: CI may rebuild the PNG when decoded pixels differ from the approved canonical image.
- verify_only: user-locked source. CI verifies it, but NEVER rewrites it automatically.

This intentionally protects MiMi's user-authored animation sheet from future accidental edits.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANON_ROOT = REPO_ROOT / "build_assets" / "canonical_sprites"
DATA_DIR = CANON_ROOT / "data"
MANIFEST_PATH = CANON_ROOT / "manifest.json"
DEFAULT_ASSET_DIR = REPO_ROOT / "src" / "Cardcha" / "assets"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest() -> dict:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if data.get("schema") != 2:
        raise SystemExit(f"Unsupported canonical sprite schema: {data.get('schema')}")
    return data


def decode_canonical(name: str, meta: dict) -> bytes:
    if meta.get("encoding") != "lzma+base85-rgba-v1":
        raise SystemExit(f"Unsupported encoding for {name}: {meta.get('encoding')}")
    parts = []
    for chunk in meta.get("chunks", []):
        path = DATA_DIR / chunk
        if not path.is_file():
            raise SystemExit(f"Canonical chunk missing for {name}: {path}")
        parts.append(path.read_text(encoding="ascii").strip())
    if not parts:
        raise SystemExit(f"No canonical chunks listed for {name}")
    packed = base64.b85decode("".join(parts).encode("ascii"))
    rgba = lzma.decompress(packed)
    expected_len = int(meta["width"]) * int(meta["height"]) * 4
    if len(rgba) != expected_len:
        raise SystemExit(f"Canonical RGBA length mismatch for {name}: {len(rgba)} != {expected_len}")
    got = sha256(rgba)
    want = meta["rgba_sha256"]
    if got != want:
        raise SystemExit(f"Canonical RGBA hash mismatch for {name}: {got} != {want}")
    return rgba


def load_asset_rgba(path: Path, expected_size: tuple[int, int]) -> bytes:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required: python3 -m pip install pillow") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    with Image.open(path) as image:
        image.load()
        rgba = image.convert("RGBA")
        if rgba.size != expected_size:
            raise ValueError(f"dimensions {rgba.size} != {expected_size}")
        return rgba.tobytes()


def write_rgba_png(path: Path, rgba: bytes, size: tuple[int, int]) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required: python3 -m pip install pillow") from exc
    image = Image.frombytes("RGBA", size, rgba)
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out.getvalue())


def process(asset_dir: Path, manifest: dict, restore: bool) -> None:
    for name, meta in manifest["assets"].items():
        size = (int(meta["width"]), int(meta["height"]))
        canonical = decode_canonical(name, meta)
        path = asset_dir / name
        policy = meta.get("policy", "restore")

        try:
            current = load_asset_rgba(path, size)
            current_hash = sha256(current)
        except (FileNotFoundError, ValueError) as exc:
            current = None
            current_hash = None
            load_error = str(exc)
        else:
            load_error = None

        if current == canonical:
            print(f"VERIFIED {name} {size[0]}x{size[1]} policy={policy}")
            continue

        if policy == "verify_only":
            reason = load_error or f"RGBA {current_hash} != {meta['rgba_sha256']}"
            raise SystemExit(
                f"USER-LOCKED asset mismatch: {name}: {reason}. "
                "Do not auto-rewrite it; update only after explicit user approval."
            )

        if not restore:
            reason = load_error or f"RGBA {current_hash} != {meta['rgba_sha256']}"
            raise SystemExit(f"Canonical asset mismatch: {name}: {reason}")

        write_rgba_png(path, canonical, size)
        check = load_asset_rgba(path, size)
        if check != canonical:
            raise SystemExit(f"Self-heal verification failed for {name}")
        print(f"RESTORED {name} {size[0]}x{size[1]} policy={policy}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-dir", type=Path, default=DEFAULT_ASSET_DIR)
    parser.add_argument("--restore", action="store_true", help="self-heal restore-policy assets before verification")
    args = parser.parse_args()
    manifest = load_manifest()
    process(args.asset_dir, manifest, restore=args.restore)
    print("Canonical visual guard PASS")


if __name__ == "__main__":
    main()

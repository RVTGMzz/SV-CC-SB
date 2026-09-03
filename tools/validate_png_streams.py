#!/usr/bin/env python3
"""Validate PNG structure, chunk CRCs, and the actual zlib-compressed IDAT stream.

This catches a failure class which a signature/CRC-only check can miss: a PNG can have
valid chunk CRCs while its IDAT payload is internally corrupt and unreadable by SMAPI.
"""
from __future__ import annotations

import argparse
import binascii
import struct
import sys
import zlib
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def validate_png(path: Path) -> None:
    data = path.read_bytes()
    if not data.startswith(PNG_SIG):
        raise ValueError("invalid PNG signature")

    pos = len(PNG_SIG)
    idat = bytearray()
    saw_iend = False

    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated PNG chunk header")

        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        payload_start = pos + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise ValueError(f"chunk {chunk_type!r} overruns file")

        payload = data[payload_start:payload_end]
        stored_crc = struct.unpack(">I", data[payload_end:crc_end])[0]
        actual_crc = binascii.crc32(chunk_type)
        actual_crc = binascii.crc32(payload, actual_crc) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            raise ValueError(f"CRC mismatch in {chunk_type.decode('latin-1')}")

        if chunk_type == b"IDAT":
            idat.extend(payload)
        elif chunk_type == b"IEND":
            saw_iend = True
            break

        pos = crc_end

    if not saw_iend:
        raise ValueError("missing IEND")
    if not idat:
        raise ValueError("missing IDAT")

    try:
        zlib.decompress(bytes(idat))
    except zlib.error as exc:
        raise ValueError(f"broken IDAT zlib stream: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="src/Cardcha/assets")
    args = parser.parse_args()

    root = Path(args.root)
    files = sorted(root.rglob("*.png")) if root.is_dir() else [root]
    if not files:
        print(f"No PNG files found under {root}", file=sys.stderr)
        return 2

    failures: list[tuple[Path, Exception]] = []
    for path in files:
        try:
            validate_png(path)
            print(f"PASS {path}")
        except Exception as exc:
            failures.append((path, exc))
            print(f"FAIL {path}: {exc}", file=sys.stderr)

    print(f"PNG stream validation: {len(files) - len(failures)}/{len(files)} PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

from pathlib import Path
import struct
import binascii

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "Cardcha" / "assets"
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def repair_png(path: Path) -> bool:
    data = path.read_bytes()
    if not data.startswith(PNG_SIG):
        raise SystemExit(f"Not a PNG: {path}")

    out = bytearray(PNG_SIG)
    pos = len(PNG_SIG)
    changed = False
    saw_iend = False

    while pos < len(data):
        if pos + 12 > len(data):
            raise SystemExit(f"Truncated PNG chunk header: {path}")
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(data):
            raise SystemExit(f"Truncated PNG chunk {ctype!r}: {path}")
        payload = data[pos + 8:pos + 8 + length]
        old_crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        crc = binascii.crc32(ctype)
        crc = binascii.crc32(payload, crc) & 0xFFFFFFFF
        if crc != old_crc:
            changed = True
        out += data[pos:pos + 8 + length]
        out += struct.pack(">I", crc)
        pos = end
        if ctype == b"IEND":
            saw_iend = True
            break

    if not saw_iend:
        raise SystemExit(f"PNG missing IEND: {path}")
    if pos != len(data):
        out += data[pos:]
    if changed:
        path.write_bytes(out)
    return changed


def validate_png(path: Path) -> None:
    data = path.read_bytes()
    if not data.startswith(PNG_SIG):
        raise SystemExit(f"Bad PNG signature: {path}")
    pos = len(PNG_SIG)
    saw_iend = False
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        stored = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        crc = binascii.crc32(ctype)
        crc = binascii.crc32(payload, crc) & 0xFFFFFFFF
        if stored != crc:
            raise SystemExit(f"CRC mismatch in {path}: {ctype.decode('ascii', 'replace')}")
        pos += 12 + length
        if ctype == b"IEND":
            saw_iend = True
            break
    if not saw_iend:
        raise SystemExit(f"PNG missing IEND: {path}")


changed = []
for path in sorted(ASSETS.rglob("*.png")):
    if repair_png(path):
        changed.append(path.relative_to(ROOT).as_posix())

for path in sorted(ASSETS.rglob("*.png")):
    validate_png(path)

print(f"PNG CRC validation PASS ({len(list(ASSETS.rglob('*.png')))} PNGs); repaired={len(changed)}")
for rel in changed:
    print(f"  repaired: {rel}")

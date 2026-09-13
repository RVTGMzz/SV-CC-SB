#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"

APPROVED = {
    "morning": {
        "sha256": "9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0",
        "target": "assets/airship_props/set01_redux/window_runtime/window_scene_default_morning_clear.png",
    },
    "noon": {
        "sha256": "fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff",
        "target": "assets/airship_props/set01_redux/window_runtime/window_scene_default_noon_clear.png",
    },
    "evening": {
        "sha256": "b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638",
        "target": "assets/airship_props/set01_redux/window_runtime/window_scene_default_evening_clear.png",
    },
    "night": {
        "sha256": "f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990",
        "target": "assets/airship_props/set01_redux/window_runtime/window_scene_default_night_clear.png",
    },
}
SHA_TO_STATE = {item["sha256"]: state for state, item in APPROVED.items()}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect_png(data: bytes) -> dict:
    if len(data) < 33 or data[:8] != PNG_SIGNATURE:
        return {"validPngHeader": False}
    length = struct.unpack(">I", data[8:12])[0]
    chunk_type = data[12:16]
    if length != 13 or chunk_type != b"IHDR":
        return {"validPngHeader": False}
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data[16:29]
    )
    return {
        "validPngHeader": True,
        "width": width,
        "height": height,
        "bitDepth": bit_depth,
        "colorType": color_type,
        "rgba8": width == 160 and height == 80 and bit_depth == 8 and color_type == 6,
        "compression": compression,
        "filter": filtering,
        "interlace": interlace,
    }


def candidate_record(label: str, data: bytes) -> tuple[str | None, dict | None]:
    digest = sha256(data)
    state = SHA_TO_STATE.get(digest)
    if state is None:
        return None, None
    png = inspect_png(data)
    if not png.get("rgba8"):
        raise RuntimeError(
            f"Exact SHA match for {state} has unexpected PNG contract at {label}: {png}"
        )
    return state, {
        "source": label,
        "sha256": digest,
        "byteLength": len(data),
        "png": png,
    }


def add_bytes(label: str, data: bytes, matches: dict, payloads: dict) -> None:
    state, record = candidate_record(label, data)
    if state is None:
        return
    matches[state].append(record)
    payloads.setdefault(state, data)


def scan_zip(path: Path, matches: dict, payloads: dict, warnings: list[str]) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir() or not info.filename.lower().endswith(".png"):
                    continue
                try:
                    data = archive.read(info)
                except Exception as exc:
                    warnings.append(f"ZIP member unreadable: {path}!{info.filename}: {exc}")
                    continue
                add_bytes(f"{path}!{info.filename}", data, matches, payloads)
    except Exception as exc:
        warnings.append(f"ZIP unreadable: {path}: {exc}")


def find_7z() -> str | None:
    for name in ("7z", "7zz", "7za"):
        found = shutil.which(name)
        if found:
            return found
    return None


def scan_rar(path: Path, matches: dict, payloads: dict, warnings: list[str]) -> None:
    exe = find_7z()
    if exe is None:
        warnings.append(
            f"RAR skipped because 7-Zip is unavailable: {path}. Install 7z/7zz/7za or extract the archive first."
        )
        return
    with tempfile.TemporaryDirectory(prefix="cardcha-0696d2-rar-") as tmp:
        proc = subprocess.run(
            [exe, "x", "-y", f"-o{tmp}", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            warnings.append(f"RAR extraction failed: {path} (exit {proc.returncode})")
            return
        scan_directory(Path(tmp), matches, payloads, warnings, source_prefix=f"{path}!")


def scan_directory(
    root: Path,
    matches: dict,
    payloads: dict,
    warnings: list[str],
    source_prefix: str = "",
) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".png":
            try:
                data = path.read_bytes()
            except Exception as exc:
                warnings.append(f"PNG unreadable: {path}: {exc}")
                continue
            relative = path.relative_to(root).as_posix()
            label = f"{source_prefix}{relative}" if source_prefix else str(path)
            add_bytes(label, data, matches, payloads)
        elif suffix == ".zip":
            scan_zip(path, matches, payloads, warnings)
        elif suffix == ".rar":
            scan_rar(path, matches, payloads, warnings)


def scan_input(path: Path, matches: dict, payloads: dict, warnings: list[str]) -> None:
    if not path.exists():
        warnings.append(f"Input missing: {path}")
        return
    if path.is_dir():
        scan_directory(path, matches, payloads, warnings)
        return
    suffix = path.suffix.lower()
    if suffix == ".png":
        add_bytes(str(path), path.read_bytes(), matches, payloads)
    elif suffix == ".zip":
        scan_zip(path, matches, payloads, warnings)
    elif suffix == ".rar":
        scan_rar(path, matches, payloads, warnings)
    else:
        warnings.append(f"Unsupported input type: {path}")


def install_exact(payloads: dict) -> list[dict]:
    missing = [state for state in APPROVED if state not in payloads]
    if missing:
        raise RuntimeError("Refusing install; exact sources missing: " + ", ".join(missing))
    installed = []
    for state, item in APPROVED.items():
        target = CARDCHA / item["target"]
        data = payloads[state]
        if sha256(data) != item["sha256"]:
            raise RuntimeError(f"Internal recovery mismatch for {state}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)  # exact byte copy; never decode/re-encode
        installed.append({
            "state": state,
            "target": str(target.relative_to(ROOT)),
            "sha256": sha256(target.read_bytes()),
            "byteLength": target.stat().st_size,
        })
    return installed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find the four exact approved 0696D2 PNG byte streams by SHA256 without transforming them."
    )
    parser.add_argument("inputs", nargs="+", help="PNG, directory, ZIP, or RAR candidates")
    parser.add_argument(
        "--install",
        action="store_true",
        help="Copy exact matched bytes into the four production target paths only when all four are found.",
    )
    parser.add_argument("--report", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    matches = {state: [] for state in APPROVED}
    payloads: dict[str, bytes] = {}
    warnings: list[str] = []
    for raw in args.inputs:
        scan_input(Path(raw).expanduser().resolve(), matches, payloads, warnings)

    found = sorted(payloads)
    missing = [state for state in APPROVED if state not in payloads]
    report = {
        "phase": "0696D2-exact-source-recovery",
        "contract": "SHA256 exact bytes only; no resize/recolor/re-encode/substitution",
        "found": found,
        "missing": missing,
        "matches": matches,
        "warnings": warnings,
        "readyToInstall": not missing,
        "installed": [],
    }

    if args.install:
        report["installed"] = install_exact(payloads)

    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")

    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())

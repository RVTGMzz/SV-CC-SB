#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import io
import json

from PIL import Image, __version__ as PILLOW_VERSION

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"
MASTER_DIR = ROOT / "recovery/0696d2-concept-masters/01_approved_time_of_day_masters"
WINDOW = CARDCHA / "assets/airship_props/set01_redux/window_runtime"
MANIFEST = ROOT / "handoff/AIRSHIP_0696D2_REBASELINE_CANONICAL.json"

PINNED_PILLOW = "11.3.0"
MASTER_SIZE = (1774, 887)
TARGET_SIZE = (160, 80)

STATES = {
    "morning": {
        "master": "observation_window_master_morning.png",
        "masterSha256": "e42ce1e1199f30ac8d30ab592ecbec01b9176388ed2a6572b68005b812e2bc85",
        "output": "window_scene_default_morning_clear.png",
        "historicalLostSha256": "9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0",
    },
    "noon": {
        "master": "observation_window_master_noon.png",
        "masterSha256": "c6f99df25a7dee04d0aeab8f1d9ac928a7e6dcb1af43db092187e1ad7831ae9e",
        "output": "window_scene_default_noon_clear.png",
        "historicalLostSha256": "fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff",
    },
    "evening": {
        "master": "observation_window_master_evening.png",
        "masterSha256": "650adec1a8d08631d02b31a59c45bc3dda96a49706a68feea3508996ee2a4fbe",
        "output": "window_scene_default_evening_clear.png",
        "historicalLostSha256": "b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638",
    },
    "night": {
        "master": "observation_window_master_night.png",
        "masterSha256": "7788da7428b7a808794c2ba14716c1ed0c25b59a3f2990f1d6c8437a92b55ee8",
        "output": "window_scene_default_night_clear.png",
        "historicalLostSha256": "f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990",
    },
}


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def ensure_toolchain() -> None:
    if PILLOW_VERSION != PINNED_PILLOW:
        raise RuntimeError(
            f"0696D2 re-baseline requires Pillow {PINNED_PILLOW}; got {PILLOW_VERSION}"
        )


def expected_png_bytes(state: str) -> bytes:
    ensure_toolchain()
    spec = STATES[state]
    master = MASTER_DIR / spec["master"]
    if not master.is_file():
        raise RuntimeError(f"{state}: missing recovered master {master}")
    if sha256_path(master) != spec["masterSha256"]:
        raise RuntimeError(f"{state}: recovered master SHA256 drifted")

    with Image.open(master) as source:
        source.load()
        if source.format != "PNG":
            raise RuntimeError(f"{state}: master must be PNG, got {source.format}")
        if source.size != MASTER_SIZE:
            raise RuntimeError(f"{state}: master must be {MASTER_SIZE}, got {source.size}")
        if source.mode != "RGBA":
            raise RuntimeError(f"{state}: master must be RGBA, got {source.mode}")

        # Rebuild an RGBA image from pixel bytes so source metadata cannot leak
        # into the canonical production PNG. The masters are already exact 2:1,
        # so the production transform is a full-frame downscale with no crop.
        clean = Image.frombytes("RGBA", source.size, source.tobytes())
        resized = clean.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        out = io.BytesIO()
        resized.save(out, format="PNG", optimize=False, compress_level=9)
        return out.getvalue()


def canonical_outputs() -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for state, spec in STATES.items():
        raw = expected_png_bytes(state)
        relative = f"assets/airship_props/set01_redux/window_runtime/{spec['output']}"
        result[state] = (relative, sha256_bytes(raw))
    return result


def build_report(require_materialized: bool) -> dict:
    outputs = {}
    for state, spec in STATES.items():
        expected = expected_png_bytes(state)
        target = WINDOW / spec["output"]
        item = {
            "masterPath": str((MASTER_DIR / spec["master"]).relative_to(ROOT)),
            "masterSha256": spec["masterSha256"],
            "masterSize": list(MASTER_SIZE),
            "masterMode": "RGBA",
            "productionPath": str(target.relative_to(ROOT)),
            "canonicalSha256": sha256_bytes(expected),
            "productionSize": list(TARGET_SIZE),
            "productionMode": "RGBA",
            "historicalLostSha256": spec["historicalLostSha256"],
        }
        if target.is_file():
            actual = target.read_bytes()
            item["materialized"] = True
            item["actualSha256"] = sha256_bytes(actual)
            item["exactCanonicalBytes"] = actual == expected
            if require_materialized and actual != expected:
                raise RuntimeError(f"{state}: production bytes differ from deterministic canonical output")
        else:
            item["materialized"] = False
            item["exactCanonicalBytes"] = False
            if require_materialized:
                raise RuntimeError(f"{state}: production PNG is not materialized")
        outputs[state] = item

    return {
        "phase": "0696D2-rebaseline",
        "decision": "APPROVED-rebaseline-from-recovered-masters",
        "pipeline": {
            "pillowVersion": PINNED_PILLOW,
            "resampler": "LANCZOS",
            "crop": "none-full-frame-2-to-1",
            "targetSize": list(TARGET_SIZE),
            "mode": "RGBA",
            "pngOptimize": False,
            "pngCompressLevel": 9,
            "sourceMetadataCopied": False,
        },
        "states": outputs,
    }


def materialize() -> dict:
    WINDOW.mkdir(parents=True, exist_ok=True)
    for state, spec in STATES.items():
        (WINDOW / spec["output"]).write_bytes(expected_png_bytes(state))
    report = build_report(require_materialized=True)
    MANIFEST.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def verify() -> dict:
    return build_report(require_materialized=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--materialize", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--print-contract", action="store_true")
    args = parser.parse_args()

    if args.materialize:
        print(json.dumps(materialize(), indent=2))
    elif args.verify:
        print(json.dumps(verify(), indent=2))
    else:
        print(json.dumps(build_report(require_materialized=False), indent=2))


if __name__ == "__main__":
    main()

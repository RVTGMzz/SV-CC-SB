#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PATCHER_PATH = ROOT / "tools/alpha28_0696d3c_room_shell_and_entrances.py"
AMBIENT = ROOT / "src/Cardcha/Services/AirshipAmbientAnimationService.cs"
EXACT_SHELL_SHA = "f2e0ef5128ecb9b1083588a419b9b1c57fcf2b9034326b59e4b8483d4713eddd"


def load_patcher():
    spec = importlib.util.spec_from_file_location("cardcha_d3c_patcher", PATCHER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load D3-C patcher")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fix_environment_local_name() -> None:
    text = AMBIENT.read_text(encoding="utf-8")
    decl = "Rectangle presentation = ResolveObservationWindowPresentation(config, propTopLeft);"
    if "Rectangle environmentPresentation = ResolveObservationWindowPresentation(config, propTopLeft);" not in text:
        pos = text.find(decl)
        if pos < 0:
            raise RuntimeError("D3-C environment presentation declaration not found")
        text = text[:pos] + text[pos:].replace(
            decl,
            "Rectangle environmentPresentation = ResolveObservationWindowPresentation(config, propTopLeft);",
            1,
        )

        use_pos = text.find("batch.Draw(\n                    environment,", pos)
        if use_pos < 0:
            raise RuntimeError("D3-C environment draw call not found")
        end_pos = text.find(");", use_pos)
        if end_pos < 0:
            raise RuntimeError("D3-C environment draw call end not found")
        block = text[use_pos:end_pos]
        if "                    presentation," not in block:
            raise RuntimeError("D3-C environment destination use not found")
        block = block.replace(
            "                    presentation,",
            "                    environmentPresentation,",
            1,
        )
        text = text[:use_pos] + block + text[end_pos:]
        AMBIENT.write_text(text, encoding="utf-8")


def main() -> None:
    patcher = load_patcher()
    patcher.EXPECTED_SHELL_SHA = EXACT_SHELL_SHA
    patcher.patch_room1_shell()
    patcher.patch_outdoor_gate()
    patcher.patch_window_presentation()
    fix_environment_local_name()
    report = patcher.validate()
    if report.get("status") != "PASS":
        raise SystemExit(2)
    print("0696D3-C finalization PASS")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.62"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.63"
BRANCH = "cardcha-alpha28-0696-airship-concept-faithful-visible-integration"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def bump_versions() -> None:
    for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
        p = SRC / rel
        if not p.exists():
            continue
        text = read(p).replace(OLD_VERSION, NEW_VERSION)
        text = text.replace(
            "0696A AIRSHIP VISIBLE ARCHITECTURE RECOVERY TEST",
            "0696B AIRSHIP AMBIENT RUNTIME FOUNDATION TEST",
        )
        write(p, text)


def patch_renderer() -> None:
    p = SRC / "Services/AirshipInteriorStardewRenderer.cs"
    text = read(p)
    old = "        Draw0690WindowOverlay(batch);\n        Draw0690ConsoleOverlay(batch);"
    new = "        AirshipAmbientAnimationService.DrawDeckAmbient(batch);"
    if new not in text:
        if old not in text:
            raise RuntimeError("0696B renderer anchor missing")
        text = text.replace(old, new, 1)
    write(p, text)


def update_render_audit() -> None:
    p = ROOT / "render_depth_audit.json"
    data = json.loads(read(p))
    data["branch"] = BRANCH
    done = data.setdefault("completedDepthMigrations", [])
    marker = "0696B Airship ambient runtime manifest+resolver; hero animation remains VFX-only with approved 0690 fallback"
    if marker not in done:
        done.append(marker)
    write(p, json.dumps(data, indent=2) + "\n")


def update_handoff() -> None:
    handoff = ROOT / "handoff/ALPHA28_0696B_AIRSHIP_AMBIENT_RUNTIME_FOUNDATION.md"
    handoff.write_text(
        f"""# Alpha 28 / 0696B — Airship Ambient Runtime Foundation

## Source of truth
- Branch: `{BRANCH}`
- Build: `{NEW_VERSION}`
- Parent verified checkpoint: 0696A `.62`
- Visual acceptance: **PENDING-RON-IN-GAME**
- New ambient art: **PENDING PRODUCTION**

## What this pass establishes
- manifest-driven Airship ambient contract at `src/Cardcha/assets/airship_props/set01_redux/airship_ambient_manifest.json`;
- typed C# manifest model;
- loader/resolver for season, time-of-day, weather and deterministic frame selection;
- runtime draw service for Observation Window + Navigation Console;
- exact approved 0690 overlay frames remain the fallback while new 0696B art is missing;
- the Airship renderer now calls the 0696B ambient service instead of hardcoding the two old hero overlay calls.

## Observation Window contract
- fixed footprint: 160x80 / 10x5 source tiles;
- fixed map anchor: tile (7,1);
- target viewport: x=16, y=14, w=128, h=42 source pixels;
- backdrop resolution order: exact season+time -> default season+time -> season+fallback time -> default+fallback time;
- weather priority: storm -> snow -> rain -> clear;
- lightning is a separate optional overlay with randomized interval;
- clean frame asset is REQUIRED before the new ambient mode activates.

## Navigation Console contract
- fixed footprint: 112x80 / 7x5 source tiles;
- fixed map anchor: tile (9,5);
- target radar viewport: x=18, y=8, w=48, h=32 source pixels;
- radar sweep is the only required new animation layer;
- radar background, pings, glow and clean console frame are optional enhancement layers;
- until the sweep exists, runtime uses the approved 0690 console overlay frames.

## Safety / ownership
- no collision changes;
- collision remains owned by base `Buildings`;
- `BackDecor` remains forbidden;
- new ambient drawing is VFX-only and does not reintroduce runtime physical furniture;
- no missing art is invented or silently substituted.

## Next production step
Produce the actual clean transparent frame/backdrop/weather/radar assets declared by the manifest, beginning with:
1. `window_runtime/observation_window_frame.png` with the flat yellow external background removed and window aperture separated;
2. four default time-of-day backdrops;
3. `console_runtime/radar_sweep_strip.png`;
4. rain/snow/lightning and radar ping/glow layers;
5. full season variants.

This handoff is a runtime foundation, not visual acceptance of 0696B.
""",
        encoding="utf-8",
    )

    latest = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"
    latest.write_text(
        f"""# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
Continue on:
`{BRANCH}`

Current build:
`{NEW_VERSION}`

Current handoff:
`handoff/ALPHA28_0696B_AIRSHIP_AMBIENT_RUNTIME_FOUNDATION.md`

Ambient asset contract:
`src/Cardcha/assets/airship_props/set01_redux/airship_ambient_manifest.json`

0696A verified architecture handoff remains:
`handoff/ALPHA28_0696A_AIRSHIP_VISIBLE_ARCHITECTURE_RECOVERY.md`

## Current state
- 0696A physical Airship architecture: **TECHNICAL PASS / PENDING-RON-IN-GAME**.
- 0696B ambient runtime foundation: materialized by its workflow.
- Observation Window and Navigation Console selection/fallback logic is now manifest-driven.
- New 0696B art remains **PENDING PRODUCTION**; approved 0690 overlay animation is retained as fallback.
- Full 0696 Airship composition remains **WIP** because the external approved source pack is still missing.

## Non-negotiable continuation rule
Do not redraw, shrink, or silently substitute missing approved full-room source sprites. For 0696B hero animation, produce only the explicitly declared ambient assets and preserve the locked 0696A footprints/collision.

## Next step
Materialize clean transparent Observation Window frame + time-of-day sky assets and the Radar sweep strip, then run the ambient asset validator before enabling the new visual mode in-game.
""",
        encoding="utf-8",
    )


def main() -> None:
    bump_versions()
    patch_renderer()
    update_render_audit()
    update_handoff()
    print(f"0696B ambient runtime foundation materialized: {NEW_VERSION}")


if __name__ == "__main__":
    main()

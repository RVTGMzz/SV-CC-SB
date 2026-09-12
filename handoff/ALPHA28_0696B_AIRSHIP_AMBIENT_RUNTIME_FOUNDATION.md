# Alpha 28 / 0696B — Airship Ambient Runtime Foundation

## Source of truth
- Branch: `cardcha-alpha28-0696-airship-concept-faithful-visible-integration`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.63`
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

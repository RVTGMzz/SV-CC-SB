# Alpha 28 / 0696B — Airship Ambient Runtime Foundation

## Source of truth
- Branch: `cardcha-alpha28-0696-airship-concept-faithful-visible-integration`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.63`
- Parent verified checkpoint: 0696A `.62`
- Materialized source head: `c71a8256c772c048cf93e782b584b05dc5ecb9ff`
- Authoritative successful workflow run: `34690399069`
- Artifact ID: `10296378327`
- Artifact digest: `sha256:20ef10946db86b5023d24d5756aaa69373ecb38091ac61e1bf70a59a489aab23`
- Verified inner TEST ZIP SHA256: `8913eef9fc15a4bc76a511e6d91b2da9d05bebb40bf893610298b5ed5c2657fa`
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
- clean frame asset is required before the new ambient mode fully replaces the legacy fallback.

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

## Validation result
Authoritative run `34690399069` passed:
- 0696B runtime materializer;
- repository render-depth contract;
- ambient manifest/runtime contract validator;
- 0696A map/content freeze;
- SMAPI compile;
- source + handoff materialization;
- TEST package audit;
- artifact upload.

The generated contract report records 33 declared new ambient production assets, currently 0 present / 33 pending, while all 8 approved legacy fallback frames are present. This is intentional for the runtime-foundation checkpoint.

The downloaded artifact was independently unpacked after CI. Packaged manifest version and ambient manifest version both equal `.63`; `Cardcha.dll` has a valid PE header and is 1,051,648 bytes. The inner TEST ZIP SHA256 matches its `.sha256` file exactly.

## TEST package
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.63_0696B_AirshipAmbientRuntimeFoundation_TEST.zip`

SHA256:
`8913eef9fc15a4bc76a511e6d91b2da9d05bebb40bf893610298b5ed5c2657fa`

## Next production step
Produce the actual clean transparent frame/backdrop/weather/radar assets declared by the manifest, beginning with:
1. `window_runtime/observation_window_frame.png` with the flat yellow external background removed and the window aperture separated;
2. four default time-of-day backdrops;
3. `console_runtime/radar_sweep_strip.png`;
4. rain/snow/lightning and radar ping/glow layers;
5. full season variants.

This handoff is a runtime foundation, not visual acceptance of 0696B.

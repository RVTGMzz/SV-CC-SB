# LATEST CARDCHA HANDOFF

Updated: 2026-09-18

Repository: `ronvotri/CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.72`  
Current phase: `0696D3-H Density + Runner + Interaction Polish`  
Current status: **CI PASS / PACKAGE READY / RUNTIME RETEST REQUIRED**

## Read first

1. `handoff/AIRSHIP_0696D3H_CI_RELEASE_CHECKPOINT.md`
2. `handoff/AIRSHIP_0696D3H_DENSITY_RUNNER_INTERACTION_POLISH.md`
3. `handoff/SESSION_HANDOFF_2026-09-18_CARDCHA_0696D3H.md`
4. `handoff/AIRSHIP_0696D3H_STATIC_API_AUDIT.json`
5. `handoff/AIRSHIP_0696D3G_ASSET_SEPARATION_NATURAL_COLLISION_DAYLIGHT_RECOVERY.md`

## Current authority

D2 and D3-A/B/C/D/E/F/G are historical checkpoints. Do not restart or redo them.

Newest runtime authority is Ron's 2026-09-18 post-D3-G 12-image retest.

D3-H has already been materialized against that feedback.

## D3-H source state

- Room 1 resized to `24x15`, exactly 2/3 old area.
- Room 1 daylight increased.
- Waiting bench, Lost & Found board and luggage cart visually scaled ~2/3 via nearest-neighbor.
- Lost & Found interaction moved off the waiting bench.
- Waiting bench / luggage / cargo get separate info interactions.
- Native collision uses `5400` solid bases with open front interaction rows.
- Bench/luggage/cargo are no longer full-body `Front2` blockers.
- New Stardew-style pixel runner is map-owned on `Back2` in both rooms.
- D3-H console restores original full machine detail with hard alpha.
- Console stays out of `Front2`.
- TRAVEL presentation is 1.5x.
- Navigation upgrade presentation is 2x.
- Four canonical upgrade sockets remain preserved.
- Remaining lamp moved and blocked.
- Observation Window is exact 4.0x wall footprint.
- Forced Farmer-position collision correction remains forbidden.

## Static audit

Evidence:

`handoff/AIRSHIP_0696D3H_STATIC_API_AUDIT.json`

Result: **PASS**.

This is not CI PASS.

## CI / package checkpoint

Successful D3-H workflow run: `35351129941`  
Job: `105619257646`  
Package/source commit: `cb71e28e321f1a45d3a73eac126c291e5cc455ea`

Tag: `cardcha-0696d3h-test-cb71e28e`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.72_0696D3H_DensityRunnerInteractionPolish_TEST.zip`

SHA256:

`7103dfa6bba242a3a14de9d8886e2c9d238e37c649e0c9a978c9c0296c640c99`

Release:

`https://github.com/ronvotri/CC-SB/releases/tag/cardcha-0696d3h-test-cb71e28e`

Direct package:

`https://github.com/ronvotri/CC-SB/releases/download/cardcha-0696d3h-test-cb71e28e/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.72_0696D3H_DensityRunnerInteractionPolish_TEST.zip`

## Local fallback

`tools/build_0696d3h_local.ps1` is the canonical Windows fallback if GitHub-hosted Actions remains blocked. It validates, compiles Release, packages, audits and emits SHA256.

## Package

The canonical D3-H .72 TEST package is ready and must be the artifact Ron tests.

Runtime is still **RETEST REQUIRED**.

## Resume instruction

Continue from **D3-H .72 CI PASS / PACKAGE READY / RUNTIME RETEST REQUIRED**.

Ron must now test the exact D3-H .72 package in game. Only Ron's explicit confirmation may change Runtime status to PASS.

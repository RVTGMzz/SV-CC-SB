# LATEST CARDCHA HANDOFF

Updated: 2026-09-18

Repository: `ronvotri/Cardcha-Shardbound`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.72`  
Current phase: `0696D3-H Density + Runner + Interaction Polish`  
Current status: **STATIC/API PASS / CI BLOCKED BEFORE RUNNER / PACKAGE NOT BUILT / RUNTIME PENDING**

## Read first

1. `handoff/AIRSHIP_0696D3H_DENSITY_RUNNER_INTERACTION_POLISH.md`
2. `handoff/SESSION_HANDOFF_2026-09-18_CARDCHA_0696D3H.md`
3. `handoff/AIRSHIP_0696D3H_STATIC_API_AUDIT.json`
4. `handoff/AIRSHIP_0696D3G_ASSET_SEPARATION_NATURAL_COLLISION_DAYLIGHT_RECOVERY.md`

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

## CI blocker

D3-H workflow run: `35347643349`  
Attempts: `3`  
Jobs: `105607896700`, `105608153047`, `105611724798`

All three failed before `Set up job`; zero steps executed and no hosted runner was allocated.

Last known full working CI remains D3-G run `35287327146`.

## Package

There is currently **no valid D3-H .72 TEST package**.

The D3-G `.71` package must not be relabeled because D3-H changes C# runtime behavior and requires a fresh DLL.

## Resume instruction

Continue from **D3-H .72 source/static PASS**.

First restore a working build executor / GitHub-hosted runner, then run the already-authored D3-H workflow, compile Release, package, audit, and publish.

Do not modify gameplay merely to make the infrastructure failure disappear.

After a real D3-H package exists, Ron must test it in game. Only Ron's explicit confirmation may change Runtime status to PASS.

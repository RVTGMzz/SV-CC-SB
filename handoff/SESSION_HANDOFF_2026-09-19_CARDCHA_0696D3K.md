# SESSION HANDOFF — 2026-09-19 — CARDCHA 0696D3-K

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Read first

1. `handoff/AIRSHIP_0696D3K_COLLISION_HOOK_RUNTIME_FIX.md`
2. `handoff/LATEST_CARDCHA_HANDOFF.md`
3. `handoff/AIRSHIP_0696D3J_COLLISION_LANES_CHECKPOINT.md`

## Current state

Version: `0.3.0-alpha.28.0.4.14.4.5.12.75`

Phase: `0696D3-K Collision Hook Runtime Fix`

Status:
- source/static: **PASS**
- Release compile: **PASS**
- package audit: **PASS**
- prerelease: **PASS**
- Runtime: **RETEST REQUIRED**

Run: `35429945303`  
Job: `105862613287`  
Source/package commit: `4431c51f8f999779c39b9a41ce0d33c6020f4a0b`

Package:

`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3k-test-4431c51f/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.75_0696D3K_CollisionHookRuntimeFix_TEST.zip`

SHA256:

`be00e20fc67b5f08d784c55d5ebeba86abd3e2449d6d1832e31174ffad79f163`

## What changed from D3-J

- fixed failed runtime resolution of `GameLocation.isCollidingPosition`;
- collision hook now discovers compatible overloads dynamically;
- postfix reads runtime arguments generically;
- D3-J TMX collision footprints are preserved;
- no forced Farmer-position logic returns;
- removed stale hard-coded `.69 / 0686` startup identity;
- runtime version banner now comes from ModManifest.

## Runtime proof required

Expected lines:

`0696D3-K installed collision hooks on <N> GameLocation.isCollidingPosition overload(s).`

`Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.75 0696D3-K COLLISION HOOK RUNTIME FIX TEST`

If the collision hook count is zero or the old resolver error remains, Runtime FAIL.

If those lines are correct, test collision against every Airship/Sky Dock prop before promoting Runtime PASS.

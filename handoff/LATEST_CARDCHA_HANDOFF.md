# LATEST CARDCHA HANDOFF

Updated: 2026-09-19

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.75`  
Current phase: `0696D3-K Collision Hook Runtime Fix`  
Current status: **CI PASS / PACKAGE READY / RUNTIME RETEST REQUIRED**

## Read first

1. `handoff/REPOSITORY_RELOCATION_2026-09-19.md`
2. `handoff/AIRSHIP_0696D3K_COLLISION_HOOK_RUNTIME_FIX.md`
3. `handoff/SESSION_HANDOFF_2026-09-19_CARDCHA_0696D3K.md`
4. `handoff/AIRSHIP_0696D3J_COLLISION_LANES_CHECKPOINT.md`
5. `handoff/REPOSITORY_RELOCATION_CI_RECHECK_2026-09-19.md`

## Newest runtime authority

D3-J SMAPI runtime showed the collision query Harmony patch did not install:

`0696D3-J couldn't resolve GameLocation.isCollidingPosition`

It also showed an obsolete hard-coded startup identity for `.69 / 0686`.

D3-K is the direct fix for those two runtime failures.

## D3-K

- dynamically scans compatible `GameLocation.isCollidingPosition` overloads;
- patches all bool-returning overloads whose first parameter is XNA Rectangle;
- generic postfix resolves `isFarmer` and `Character` from the actual method metadata;
- preserves D3-J TMX/native collision footprints;
- never rewinds or sets Farmer.Position;
- startup banner now uses `ModManifest.Version`;
- current identity is `.75 / 0696D3-K`.

## CI / package

Run: `35429945303`  
Job: `105862613287`  
Source/package commit: `4431c51f8f999779c39b9a41ce0d33c6020f4a0b`

Tag: `cardcha-0696d3k-test-4431c51f`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.75_0696D3K_CollisionHookRuntimeFix_TEST.zip`

SHA256:

`be00e20fc67b5f08d784c55d5ebeba86abd3e2449d6d1832e31174ffad79f163`

Release:

`https://github.com/RVTGMzz/SV-CC-SB/releases/tag/cardcha-0696d3k-test-4431c51f`

Direct package:

`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3k-test-4431c51f/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.75_0696D3K_CollisionHookRuntimeFix_TEST.zip`

## Runtime acceptance

Before testing room collision, verify SMAPI prints:

`0696D3-K installed collision hooks on <N> GameLocation.isCollidingPosition overload(s).`

where `N > 0`.

It must also print:

`Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.75 0696D3-K COLLISION HOOK RUNTIME FIX TEST`

Only explicit in-game confirmation may set Runtime PASS.

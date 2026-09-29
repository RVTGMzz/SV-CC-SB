# LATEST CARDCHA HANDOFF

Updated: 2026-09-29

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.77`  
Current phase: `0696D3-M Room Lighting + TMX Collision + Layer Order Runtime Fix`  
Current status: **CI PASS / PACKAGE READY / RUNTIME RETEST REQUIRED**

## Read first

1. `handoff/AIRSHIP_0696D3M_ROOM_LIGHTING_COLLISION_LAYER_FIX.md`
2. `handoff/RUNTIME_FEEDBACK_2026-09-29_D3L_ROOM_COLLISION_LIGHTING.md`
3. `handoff/AIRSHIP_0696D3L_LOAD_SAFE_SIGNATURE_PROBE.md`
4. `handoff/AIRSHIP_0696D3J_COLLISION_LANES_CHECKPOINT.md`

## Latest runtime authority

Ron reached the playable world on the D3-L-era setup and supplied screenshots showing three concrete room regressions:

- Room 1 almost completely black;
- Room 2 UPGRADE stations walkable through their visible machine bodies;
- Room 2 Window/console presentation layering covering Farmer/companion incorrectly.

That supersedes the earlier save-load investigation for Cardcha. Do not reopen D3-K/L collision-hook work.

## D3-M .77 corrections

### Room 1
- runtime indoor ambient guard: `255 250 240`;
- previous ambient saved on entry and restored on exit;
- authored TMX ambient raised to `255 250 240`;
- authored night ambient raised to `225 215 200`.

### Room 2 collision
- Observation Window lower sill: `x7..16, y5`;
- Engine UPGRADE: `x3..5, y7..8`;
- Navigation UPGRADE: `x18..20, y7..8`;
- Hull UPGRADE: `x6..8, y10..11`;
- Reactor UPGRADE: `x15..17, y10..11`.

All use native TMX Buildings collision. No forced Farmer position correction is used.

### Room 2 layer/depth
Window/console transient presentation now uses true background layer depths instead of the old ~0.884/0.885 values, including Window lightning.

## Carry-forward locks

- no broad `GameLocation.isCollidingPosition` Harmony postfix;
- no `Farmer.Position` pin/rewind/restore;
- TRAVEL center lane remains open;
- BOARD AIRSHIP center throat remains open;
- Resonance interaction remains reachable;
- D3-L load-safe startup architecture remains.

## CI / package

CI run: `36572926010`  
Job: `109421122962`  
Canonical source/package commit: `5a95978cfb16d40e128c248d66f0b313d8e4294b`  
Conclusion: **SUCCESS**

Tag: `cardcha-0696d3m-test-5a95978c`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.77_0696D3M_RoomLightingCollisionLayer_TEST.zip`

SHA256:
`98d5b7e4e53e05e2ae731b94d266c27f5778d2b3bbc48fa01b221025b50ca412`

Direct package:
`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3m-test-5a95978c/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.77_0696D3M_RoomLightingCollisionLayer_TEST.zip`

Static / CI:
- D3-M room runtime validator: PASS
- no legacy Window overlay reuse: PASS
- render-depth contract: PASS
- validator non-mutation: PASS
- Release compile: PASS, 0 errors
- package audit: PASS
- prerelease publication: PASS

The existing project emits 55 SMAPI analyzer warnings, mostly NetField guidance outside the D3-M patch. Do not misreport this build as zero-warning.

## Runtime retest focus

Test only the exact .77 package.

1. Room 1 readable instead of near-black.
2. Ambient returns to normal when leaving Room 1.
3. Cannot stand inside any of four UPGRADE machines.
4. UPGRADE interaction remains available from adjacent lane.
5. Cannot enter Window lower sill.
6. Window/console no longer blanket-cover player/companion.
7. TRAVEL, BOARD AIRSHIP, and Resonance interactions still work.
8. No ghost-body / forced-position regression.

Do not call Runtime PASS until Ron confirms this in game.

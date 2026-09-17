# LATEST CARDCHA HANDOFF

Updated: 2026-09-18

Repository: `ronvotri/Cardcha-Shardbound`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.71`  
Current phase: `0696D3-G Asset Separation + Natural Collision + Daylight Recovery`  
Current status: **CI PASS / RUNTIME RETEST REQUIRED**

## Read first

1. `handoff/AIRSHIP_0696D3G_ASSET_SEPARATION_NATURAL_COLLISION_DAYLIGHT_RECOVERY.md`
2. `handoff/SESSION_HANDOFF_2026-09-18_CARDCHA_0696D3G.md`
3. `handoff/AIRSHIP_0696D3F_PHYSICAL_BLOCKING_TRAVEL_DEPTH_RECOVERY.md`
4. `handoff/AIRSHIP_0696D3E_RUNTIME_INTERACTION_RENDER_DEPTH_FIX.md`

## Current authority

D2 and D3-A/B/C/D/E/F are historical checkpoints. Do not restart or redo them.

Newest runtime authority is Ron's 2026-09-18 D3-F retest. D3-F was CI PASS but Runtime FAIL.

D3-G has now been materialized specifically against those failures:

- forced Farmer-position blocker removed;
- Room 1 / Room 2 owned collision moved to native TMX `5400` footprints;
- Forest gate uses segmented collision query, center passage open;
- real transparent console production asset authored;
- console removed from `Front2` blanket ownership;
- Observation Window shell moved to `Back2`;
- left lamp removed from interior TRAVEL gate footprint;
- native day/night bridge ambient properties added;
- four upgrade stations + TRAVEL preserved.

D3-G has not yet been runtime accepted.

## CI / package checkpoint

Final successful workflow run: `35287327146`  
Job: `105422447116`  
Package/source commit: `cd056a680ba50ee5d03b0f7d200537eb76e7f276`

Result:

- D3-D historical gameplay/asset invariants: PASS
- D3-G static/asset/TMX contract: PASS
- no-legacy Window overlay guard: PASS
- render-depth contract: PASS
- Release compile: PASS
- package audit: PASS
- prerelease publication: PASS

D3-F workflow is manual-only now because its forced-position validator is intentionally obsolete under D3-G.

## Current TEST package

Tag:

`cardcha-0696d3g-test-cd056a68`

Release:

`https://github.com/ronvotri/Cardcha-Shardbound/releases/tag/cardcha-0696d3g-test-cd056a68`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.71_0696D3G_AssetSeparationNaturalCollisionDaylightRecovery_TEST.zip`

Asset ID:

`571374818`

SHA256:

`05f367c54359223c882b2123cb4529f9eb04dc841e6cb5f099758504018437d8`

Direct package:

`https://github.com/ronvotri/Cardcha-Shardbound/releases/download/cardcha-0696d3g-test-cd056a68/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.71_0696D3G_AssetSeparationNaturalCollisionDaylightRecovery_TEST.zip`

## Runtime acceptance checklist

1. Room 1 collision feels native and no ghost/body desync remains.
2. Console beige/yellow matte is gone.
3. Observation Window and console do not blanket-cover the Farmer.
4. Four upgrade stations remain visible/interactable.
5. TRAVEL works and radar remains a valid alternate travel control.
6. Interior lamp/gate intersection is gone.
7. Daytime bridge is visibly brighter/readable than night.
8. Forest gate blocks solid wood/posts while center passage remains usable.
9. No central walking lane or natural interaction radius regresses.

Only Ron's explicit in-game confirmation may change this checkpoint to Runtime PASS.

## Resume instruction

Resume from **D3-G `.71` CI PASS / Runtime RETEST REQUIRED**.

Do not restore forced player-position correction, the legacy beige console base, console `Front2` blanket ownership, or full `DrawDeckMarkers` replay.

If Ron reports a problem, patch incrementally from D3-G and use the observed runtime behavior as authority.

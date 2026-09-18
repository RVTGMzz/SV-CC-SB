# LATEST CARDCHA HANDOFF

Updated: 2026-09-18

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.74`  
Current phase: `0696D3-J Collision Lanes`  
Current status: **CI PASS / PACKAGE READY / RUNTIME RETEST REQUIRED**

## Read first

1. `handoff/REPOSITORY_RELOCATION_2026-09-19.md`
2. `handoff/AIRSHIP_0696D3J_COLLISION_LANES_CHECKPOINT.md`
3. `handoff/SESSION_HANDOFF_2026-09-18_CARDCHA_0696D3J.md`
4. `handoff/AIRSHIP_0696D3I_RUNTIME_CORRECTION_CHECKPOINT.md`

## Newest authority

Ron explicitly reasserted the original 12-point room requirements after D3-I and called out that the requested object blocking had not been sufficiently delivered.

D3-J therefore prioritizes collision over further cosmetic work.

## D3-J

Room 1:
- full-body collision for notice board, Lost & Found, bench, luggage, cargo;
- side collision for boarding gate while center remains open;
- lamp collision;
- exact open front interaction lanes;
- bench/luggage reflow so runner is not blocked;
- much brighter ambient light.

Room 2:
- Navigation console full-body collision;
- segmented TRAVEL collision;
- four UPGRADE bases blocked;
- lamp blocked;
- 2x Resonance machine blocked with front interaction lane;
- runner rerouted so no runner tile intersects collision.

Runtime collision-query rectangles mirror TMX collision and never move Farmer.

## CI / package

Run: `35364163371`  
Job: `105662423365`  
Source/package commit: `d9665fdf34db95ff98abdd5ccbee2dcf628a9331`

Tag: `cardcha-0696d3j-test-d9665fdf`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.74_0696D3J_CollisionLanes_TEST.zip`

SHA256:

`66e41d4ae5d55228951ea2ea04acf9f8d1e4de5e52fac1a8bbcacc492e22ddf4`

Release:

`https://github.com/RVTGMzz/SV-CC-SB/releases/tag/cardcha-0696d3j-test-d9665fdf`

Direct package:

`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3j-test-d9665fdf/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.74_0696D3J_CollisionLanes_TEST.zip`

## Resume instruction

Continue from **D3-J .74 CI PASS / PACKAGE READY / RUNTIME RETEST REQUIRED**.

Ron should now test collision deliberately against every prop.

Only explicit in-game confirmation may set Runtime PASS.

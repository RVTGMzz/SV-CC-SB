# AIRSHIP 0696D3-J — COLLISION LANES CHECKPOINT

Updated: 2026-09-18

Repository: `ronvotri/CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Version: `0.3.0-alpha.28.0.4.14.4.5.12.74`

## Status

**SOURCE / TMX / COLLISION VALIDATOR / RELEASE COMPILE / PACKAGE AUDIT / PRERELEASE: PASS**  
**RUNTIME: RETEST REQUIRED**

D3-J exists because Ron reasserted the original room requirement after D3-I: visual fixes were landing, but collision/blocking was still not sufficiently materialized in game.

## Collision architecture

D3-J uses two matching layers:

1. TMX `Buildings` collision tiles (`5400`) on authored solid footprints;
2. `GameLocation.isCollidingPosition` postfix answers for the same segmented rectangles.

The collision query only answers whether a move collides. It never:
- assigns `Farmer.Position`;
- rewinds;
- pins;
- teleports;
- or restores a last-safe position.

## Room 1

- Room remains `24x15`.
- Day ambient raised to `230 225 215`.
- Night ambient raised to `160 150 140`.
- Waiting bench shifted left to `x2..7, y9..11`.
- Luggage cart shifted to `x8..11, y9..12` so the boarding runner stays clear.

Full-body blocked footprints:
- Notice board: `x2..6, y5..7`
- Lost & Found: `x8..13, y5..6`
- Waiting bench: `x2..7, y9..11`
- Luggage cart: `x8..11, y9..12`
- Cargo: `x20..22, y9..11`
- Boarding left side: `x14..16, y5..8`
- Boarding right side: `x18..20, y5..8`
- Lamp: `x21..22, y5..6`

Open interaction lanes:
- Notice board: `y8`
- Lost & Found: `y7`
- Waiting bench: `y12`
- Luggage: `y13`
- Cargo: `y12`
- Boarding center throat: `x17, y5..8`

BOARD AIRSHIP remains at `(17,7)` and the runner never crosses a blocked tile.

## Room 2

Blocked footprints:
- TRAVEL left side: `x2..3, y4..6`
- TRAVEL right side: `x5..6, y4..6`
- Navigation console full body: `x9..15, y5..9`
- Engine UPGRADE base: `x3..5, y8`
- Navigation UPGRADE base: `x18..20, y8`
- Hull UPGRADE base: `x6..8, y11`
- Reactor UPGRADE base: `x15..17, y11`
- Signal lamp: `x18..19, y6`
- 2x ChaCha Resonance machine: `x20..22, y5..6`

Open lanes:
- Navigation console front lane: `x9..15, y10`
- TRAVEL center: `x4`
- Resonance front lane: `x20..22, y7`

Resonance interaction tile moved to `(21,7)`.

The TRAVEL runner was rerouted around the Engine base:
- it never touches a `5400` tile;
- it enters TRAVEL through the open center.

## CI provenance

Run: `35364163371`  
Job: `105662423365`  
Source/package commit: `d9665fdf34db95ff98abdd5ccbee2dcf628a9331`

All stages PASS:
- console materialization;
- D3-J collision lane validator;
- no-legacy Window guard;
- render-depth guard;
- non-mutation;
- SMAPI build environment;
- Release compile;
- package audit;
- CI evidence;
- prerelease publication.

## Canonical TEST package

Tag: `cardcha-0696d3j-test-d9665fdf`

Release ID: `391594061`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.74_0696D3J_CollisionLanes_TEST.zip`

Asset ID: `572929038`

SHA256:

`66e41d4ae5d55228951ea2ea04acf9f8d1e4de5e52fac1a8bbcacc492e22ddf4`

Release:

`https://github.com/ronvotri/CC-SB/releases/tag/cardcha-0696d3j-test-d9665fdf`

Direct package:

`https://github.com/ronvotri/CC-SB/releases/download/cardcha-0696d3j-test-d9665fdf/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.74_0696D3J_CollisionLanes_TEST.zip`

## Runtime retest focus

Ron should deliberately try to walk through every numbered prop from the original 12-point feedback.

Especially verify:
1. Room 1 notice board cannot be entered from sides/back; front lane works.
2. Lost & Found cannot be entered; front lane/info works.
3. Waiting bench cannot be crossed.
4. Luggage/cart cannot be crossed and no longer blocks runner.
5. Cargo cannot be crossed.
6. Boarding gate side furniture is solid; center path to BOARD AIRSHIP is open.
7. Navigation console cannot be walked through; front lane remains usable.
8. TRAVEL side structure is solid; center remains usable.
9. All four UPGRADE bases physically stop Farmer.
10. Lamp stops Farmer.
11. Resonance machine stops Farmer while its y7 front interaction works.
12. No ghost/body desync or forced-position behavior appears.
13. Room 1 is visibly brighter.

Only Ron's explicit in-game confirmation may promote D3-J to Runtime PASS.

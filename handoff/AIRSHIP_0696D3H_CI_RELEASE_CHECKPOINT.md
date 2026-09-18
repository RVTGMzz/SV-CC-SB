# AIRSHIP 0696D3-H — CI / RELEASE CHECKPOINT

Updated: 2026-09-18

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Version: `0.3.0-alpha.28.0.4.14.4.5.12.72`

## Status

**SOURCE / ASSET / TMX / STATIC VALIDATION: PASS**  
**RELEASE COMPILE: PASS**  
**PACKAGE AUDIT: PASS**  
**PRERELEASE: PASS**  
**RUNTIME: RETEST REQUIRED**

Do not call Runtime PASS until Ron tests the exact D3-H package below in Stardew Valley and explicitly confirms.

## Public-repo transition

The repository was renamed from `ronvotri/Cardcha-Shardbound` to `RVTGMzz/SV-CC-SB` and made public on 2026-09-18.

Earlier D3-H runs failed before `Set up job` because no hosted runner was allocated while the repository was private. After the repository became public, run `35351129941` received a hosted runner and executed the full pipeline.

## Canonical CI provenance

Workflow run: `35351129941`  
Job: `105619257646`  
Package/source commit: `cb71e28e321f1a45d3a73eac126c291e5cc455ea`

Successful stages:
- checkout: PASS
- deterministic Pillow setup: PASS
- D3-H runtime-feedback contract validator: PASS
- no-legacy Window overlay guard: PASS
- render-depth contract: PASS
- validator non-mutation proof: PASS
- SMAPI build environment: PASS
- Release compile: PASS
- D3-H package audit: PASS
- CI evidence generation: PASS
- prerelease publication: PASS

## Canonical D3-H TEST package

Tag:

`cardcha-0696d3h-test-cb71e28e`

Release ID:

`391501708`

Release:

`https://github.com/RVTGMzz/SV-CC-SB/releases/tag/cardcha-0696d3h-test-cb71e28e`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.72_0696D3H_DensityRunnerInteractionPolish_TEST.zip`

Package asset ID:

`572700371`

SHA256:

`7103dfa6bba242a3a14de9d8886e2c9d238e37c649e0c9a978c9c0296c640c99`

Direct package:

`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3h-test-cb71e28e/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.72_0696D3H_DensityRunnerInteractionPolish_TEST.zip`

## What Ron should test

1. Room 1 is visibly denser and no longer feels over-spaced.
2. Daytime Room 1 is bright/readable.
3. Waiting bench is a waiting bench, not Lost & Found.
4. Large wall board is Lost & Found and its interaction is correct.
5. Bench / luggage / cargo have natural front interaction and do not cut the Farmer's head.
6. Runner/carpet looks like Stardew pixel art rather than a flat 2D pasted rectangle.
7. Runner points naturally toward BOARD AIRSHIP / TRAVEL.
8. BOARD AIRSHIP pad sits on the rug and reads clearly as the upstairs direction.
9. Console keeps full machine detail and no beige/yellow matte returns.
10. Console does not blanket-cover the Farmer.
11. TRAVEL gate feels ~1.5x larger and remains usable.
12. Navigation upgrade machine feels ~2x larger.
13. All four upgrade stations remain visible/interactable and their collision feels natural.
14. Signal lamp is blocked and no longer intersects the important gate/station space.
15. Observation Window sits against the wall and does not blanket-cover the Farmer.
16. No ghost/body desync or forced-position behavior returns.

Only Ron's explicit in-game confirmation may promote D3-H to Runtime PASS.

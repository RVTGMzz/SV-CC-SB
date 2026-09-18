# AIRSHIP 0696D3-I — RUNTIME CORRECTION CHECKPOINT

Updated: 2026-09-18

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Version: `0.3.0-alpha.28.0.4.14.4.5.12.73`

## Status

**SOURCE / TMX / VALIDATOR / RELEASE COMPILE / PACKAGE AUDIT / PRERELEASE: PASS**  
**RUNTIME: RETEST REQUIRED**

Newest authority is Ron's post-D3-H in-game feedback. D3-H was CI PASS but Runtime FAIL on four remaining points.

## D3-I fixes

### 1. Navigation console matte + oversized electronic sweep

- D3-H restored full machine detail but also restored the source beige matte.
- D3-I generates `navigation_console_body_d3i.png` deterministically from `navigation_console_base.png`.
- Only beige components connected to the canvas edge are alpha-removed.
- Interior brass/light detail is preserved.
- Package validator requires:
  - 112x80 RGBA;
  - hard alpha only;
  - >= 3000 transparent pixels;
  - <= 250 surviving beige candidate pixels;
  - >= 5000 opaque detail pixels.
- Radar sweep/electronic needle is reduced to `0.58x`.
- Radar glow/pings are reduced to `0.72x`.
- Static monitor/body size stays unchanged.

### 2. Observation Window head occlusion

- The physical Window shell is removed from all TMX layers.
- Environment, moving airship and `observation_window_frame.png` are now all drawn in the pre-Farmer pass.
- Frame remains exactly `4.0x` at the same wall anchor.
- Farmer is always drawn after the entire Window presentation.

### 3. Correct machine scaled to 2x

- D3-H incorrectly enlarged Navigation UPGRADE.
- D3-I restores all four UPGRADE stations to canonical `96x96`.
- The actual ChaCha Resonance station at visual tile `(21,5)` is enlarged to 2x.
- Signal lamp moved away from that station to `x18-19`; collision moved with it.

### 4. BOARD AIRSHIP pad inside gate

- Boarding pad moved from `(17,8)` to `(17,7)`.
- Runner now continues through `(17,8)` and ends on the glowing pad at `(17,7)`.
- Interaction resolver, pre-Farmer visual and dock magic anchor all use the new tile.

## CI provenance

Run: `35359955694`  
Job: `105648479702`  
Source/package commit: `9d583dc025b3549e1a6894496146a30007c8aa31`

All gates PASS:
- deterministic console materialization;
- D3-I runtime correction validator;
- no-legacy Window guard;
- render-depth guard;
- tracked-input non-mutation;
- SMAPI build environment;
- Release compile;
- package audit;
- CI evidence;
- prerelease publication.

## Canonical TEST package

Tag: `cardcha-0696d3i-test-9d583dc0`

Release ID: `391565570`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.73_0696D3I_RuntimeCorrection_TEST.zip`

Asset ID: `572856034`

SHA256:

`9c1d87c0be737cfbb1477447295448440102ea483b93ad4e2b5710d9cdd131fe`

Release:

`https://github.com/RVTGMzz/SV-CC-SB/releases/tag/cardcha-0696d3i-test-9d583dc0`

Direct package:

`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3i-test-9d583dc0/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.73_0696D3I_RuntimeCorrection_TEST.zip`

## Runtime retest checklist

1. Console has no beige/yellow background matte.
2. Electronic sweep/gauge no longer looks oversized.
3. Console keeps the full machine detail.
4. Window never covers the Farmer's head/body when walking in front.
5. Window still visually sits against the wall.
6. All four UPGRADE machines are back to coherent normal size.
7. Actual ChaCha Resonance machine above is visibly 2x larger.
8. Signal lamp no longer overlaps the Resonance machine.
9. BOARD AIRSHIP pad sits on the rug inside the gate.
10. BOARD AIRSHIP interaction still works from the intended lane.
11. TRAVEL and four UPGRADE interactions remain intact.
12. No forced-position/ghost-body regression returns.

Only Ron's explicit in-game confirmation of this exact package may promote D3-I to Runtime PASS.

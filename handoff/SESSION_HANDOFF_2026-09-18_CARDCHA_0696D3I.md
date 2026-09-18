# SESSION HANDOFF — 2026-09-18 — CARDCHA 0696D3-I

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Read first

1. `handoff/AIRSHIP_0696D3I_RUNTIME_CORRECTION_CHECKPOINT.md`
2. `handoff/LATEST_CARDCHA_HANDOFF.md`
3. `handoff/AIRSHIP_0696D3H_CI_RELEASE_CHECKPOINT.md`

## Current state

Version: `0.3.0-alpha.28.0.4.14.4.5.12.73`

Phase: `0696D3-I Runtime Correction`

Status:
- source/TMX: **PASS**
- validator: **PASS**
- Release compile: **PASS**
- package audit: **PASS**
- prerelease: **PASS**
- Runtime: **RETEST REQUIRED**

Canonical run: `35359955694`  
Canonical source/package commit: `9d583dc025b3549e1a6894496146a30007c8aa31`

Package:

`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3i-test-9d583dc0/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.73_0696D3I_RuntimeCorrection_TEST.zip`

SHA256:

`9c1d87c0be737cfbb1477447295448440102ea483b93ad4e2b5710d9cdd131fe`

## Guards

Do not reintroduce:
- D3-H Navigation-only 192x192 UPGRADE scaling;
- console beige edge matte;
- Window physical shell on TMX suffix layers;
- BOARD AIRSHIP pad at y=8 outside the gate;
- forced Farmer position correction;
- full DrawDeckMarkers replay.

Preserve:
- four canonical UPGRADE sockets;
- TRAVEL;
- runner/carpet style;
- Room 1 density and daylight recovery;
- natural collision/front interaction lanes.

## Next action

Ron tests the exact D3-I .73 package.

If runtime feedback remains, patch incrementally from D3-I. Do not restart D2 and do not redo D3-A/B/C/D/E/F/G/H.

Static/CI PASS is not Runtime PASS.

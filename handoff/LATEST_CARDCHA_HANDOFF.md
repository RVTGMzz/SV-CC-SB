# LATEST CARDCHA HANDOFF

Updated: 2026-09-18

Repository: `ronvotri/CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.73`  
Current phase: `0696D3-I Runtime Correction`  
Current status: **CI PASS / PACKAGE READY / RUNTIME RETEST REQUIRED**

## Read first

1. `handoff/AIRSHIP_0696D3I_RUNTIME_CORRECTION_CHECKPOINT.md`
2. `handoff/SESSION_HANDOFF_2026-09-18_CARDCHA_0696D3I.md`
3. `handoff/AIRSHIP_0696D3H_CI_RELEASE_CHECKPOINT.md`

## Newest runtime authority

Ron's post-D3-H retest identified four remaining failures:
- console beige/yellow matte remained;
- electronic sweep/gauge was oversized;
- Window still covered the Farmer's head;
- wrong machine was enlarged;
- BOARD AIRSHIP pad was still outside the gate.

D3-I directly addresses those failures.

## D3-I implementation

- deterministic edge-connected beige matte removal for console;
- console sweep `0.58x`, glow/pings `0.72x`;
- Window physical shell removed from TMX;
- Window frame now drawn pre-Farmer with the environment/airship;
- all four UPGRADE stations restored to `96x96`;
- actual ChaCha Resonance station at `(21,5)` enlarged to 2x;
- signal lamp moved to `x18-19`, with collision moved too;
- BOARD AIRSHIP pad moved to `(17,7)` inside the gate.

## CI / package

Run: `35359955694`  
Job: `105648479702`  
Source/package commit: `9d583dc025b3549e1a6894496146a30007c8aa31`

Tag: `cardcha-0696d3i-test-9d583dc0`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.73_0696D3I_RuntimeCorrection_TEST.zip`

SHA256:

`9c1d87c0be737cfbb1477447295448440102ea483b93ad4e2b5710d9cdd131fe`

Release:

`https://github.com/ronvotri/CC-SB/releases/tag/cardcha-0696d3i-test-9d583dc0`

Direct package:

`https://github.com/ronvotri/CC-SB/releases/download/cardcha-0696d3i-test-9d583dc0/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.73_0696D3I_RuntimeCorrection_TEST.zip`

## Resume instruction

Continue from **D3-I .73 CI PASS / PACKAGE READY / RUNTIME RETEST REQUIRED**.

Ron must test this exact package. Only explicit in-game confirmation may set Runtime PASS.

If a runtime issue remains, patch incrementally from D3-I and treat Ron's screenshot/gameplay feedback as newest authority.

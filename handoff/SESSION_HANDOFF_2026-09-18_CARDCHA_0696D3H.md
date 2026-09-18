# SESSION HANDOFF — 2026-09-18 — CARDCHA 0696D3-H

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Read first

1. `handoff/AIRSHIP_0696D3H_DENSITY_RUNNER_INTERACTION_POLISH.md`
2. `handoff/AIRSHIP_0696D3H_STATIC_API_AUDIT.json`
3. `handoff/LATEST_CARDCHA_HANDOFF.md`

## Resume state

Current version: `0.3.0-alpha.28.0.4.14.4.5.12.72`

Current phase: `0696D3-H Density + Runner + Interaction Polish`

Current status:

- source/assets/TMX: **PASS**
- static/API audit: **PASS**
- GitHub CI: **PASS**
- Release compile: **PASS**
- package audit: **PASS**
- D3-H TEST ZIP: **READY**
- Runtime: **RETEST REQUIRED**

Do not restart D2 or redo D3-A/B/C/D/E/F/G.

## Newest runtime authority

Ron's post-D3-G 12-image feedback is authoritative.

The important user-visible changes now present in source are:
- Room 1 24x15, exactly 2/3 old area;
- three oversized Room 1 props reduced to ~2/3 via nearest-neighbor;
- Lost & Found moved off waiting bench;
- separate prop interactions added;
- native base collision + open front interaction lanes;
- bench/luggage/cargo removed from Front2;
- map-native Stardew-style runner in both rooms;
- brighter Room 1 daytime;
- full-detail hard-alpha console restored;
- TRAVEL 1.5x;
- Navigation upgrade 2x;
- stronger four-station glow;
- lamp moved/blocked;
- Window exact 4.0x wall footprint;
- no forced Farmer-position blocker.

## Canonical CI / package checkpoint

Run: `35351129941`  
Job: `105619257646`  
Source/package commit: `cb71e28e321f1a45d3a73eac126c291e5cc455ea`  
Tag: `cardcha-0696d3h-test-cb71e28e`  
Package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.72_0696D3H_DensityRunnerInteractionPolish_TEST.zip`  
SHA256: `7103dfa6bba242a3a14de9d8886e2c9d238e37c649e0c9a978c9c0296c640c99`

Release:

`https://github.com/RVTGMzz/SV-CC-SB/releases/tag/cardcha-0696d3h-test-cb71e28e`

Direct package:

`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3h-test-cb71e28e/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.72_0696D3H_DensityRunnerInteractionPolish_TEST.zip`

The earlier zero-step runner failures are historical and were resolved after the repository became public.

## Local fallback

If GitHub-hosted Actions remains blocked, use `tools/build_0696d3h_local.ps1` on a Windows checkout with a working Stardew/SMAPI ModBuildConfig environment. It performs validation, Release compile, ZIP assembly, package audit and SHA256 generation.

## Next action

Ron should now test the exact D3-H .72 TEST package above in Stardew Valley against the 16-point runtime checklist in `handoff/AIRSHIP_0696D3H_CI_RELEASE_CHECKPOINT.md`.

If Ron reports a runtime problem, patch incrementally from D3-H. Do not restart D2 and do not redo D3-A/B/C/D/E/F/G.

## Runtime promotion rule

Static PASS is not CI PASS.  
CI PASS is not Runtime PASS.  
Only Ron's test of the exact future D3-H package can set Runtime PASS.

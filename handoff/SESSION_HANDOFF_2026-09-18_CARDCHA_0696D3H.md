# SESSION HANDOFF — 2026-09-18 — CARDCHA 0696D3-H

Repository: `ronvotri/Cardcha-Shardbound`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Read first

1. `handoff/AIRSHIP_0696D3H_DENSITY_RUNNER_INTERACTION_POLISH.md`
2. `handoff/AIRSHIP_0696D3H_STATIC_API_AUDIT.json`
3. `handoff/LATEST_CARDCHA_HANDOFF.md`

## Resume state

Current version: `0.3.0-alpha.28.0.4.14.4.5.12.72`

Current phase: `0696D3-H Density + Runner + Interaction Polish`

Current status:

- source/assets/TMX: **MATERIALIZED**
- static/API audit: **PASS**
- GitHub CI: **BLOCKED BEFORE RUNNER**
- Release compile: **NOT EXECUTED**
- package audit: **NOT EXECUTED**
- D3-H TEST ZIP: **NOT BUILT**
- Runtime: **PENDING**

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

## CI infrastructure blocker

Workflow run `35347643349` failed three times before any step executed.

Jobs:
- `105607896700`
- `105608153047`
- `105611724798`

No runner was allocated and no `Set up job` step appeared.

D3-G run `35287327146` is the last known successful full CI/package run.

Do not interpret the D3-H run as a code/test failure because neither code nor tests executed.

## Local fallback

If GitHub-hosted Actions remains blocked, use `tools/build_0696d3h_local.ps1` on a Windows checkout with a working Stardew/SMAPI ModBuildConfig environment. It performs validation, Release compile, ZIP assembly, package audit and SHA256 generation.

## Next action

First priority is to restore a usable build executor for the private repository, then run the existing D3-H workflow unchanged.

When an executor is available:
1. run `tools/alpha28_0696d3h_density_runner_interaction_polish.py`;
2. run no-legacy Window guard;
3. run render-depth guard;
4. compile Release;
5. package version `.72`;
6. run `tools/alpha28_0696d3h_package_audit.py`;
7. publish D3-H prerelease;
8. give that exact ZIP to Ron;
9. wait for Ron runtime test before Runtime PASS.

Do not fake the package using the old D3-G DLL.

## Runtime promotion rule

Static PASS is not CI PASS.  
CI PASS is not Runtime PASS.  
Only Ron's test of the exact future D3-H package can set Runtime PASS.

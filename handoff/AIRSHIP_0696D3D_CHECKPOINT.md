# Cardcha 0696D3-D checkpoint

Date: 2026-09-15
Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Version: `0.3.0-alpha.28.0.4.14.4.5.12.70`

## Status

**STATIC REGRESSION: PASS**
**RELEASE COMPILE: PASS**
**PACKAGE AUDIT: PASS**
**RUNTIME / IN-GAME ACCEPTANCE: PENDING-RON-IN-GAME**

This checkpoint does not claim Runtime PASS. GitHub Actions verified source, assets, contracts, compilation and final packaged bytes only. Ron still needs to install the TEST package and perform visual/gameplay acceptance in Stardew Valley.

## Lineage

- Corrected D3-D radar tooling commit: `0f91514b5871d24dc19589f4e7623d0b9d04bc55`
- Corrected D3-B materialized baseline: `979056bf8552d4586b03a52fa3c35e089c7cd50f`
- D3-D read-only regression tool: `2f0cd839e2086d609a6a4bc6451aa7e37b9769bb`
- D3-D package-audit tool: `fa0125b24ee82e17a5bc725e0b9c7fe5e485d1c8`
- D3-D CI/package source commit: `b3fc4d9db866c7c87dc438a736169c52b15baf84`

The D3-D CI harness is validation/package-only. It does not materialize or redesign approved production visuals.

## Successful workflow

Workflow: `Cardcha 0696D3-D Regression and TEST Package`
Run: `34932478977`
Run result: `success`
Source SHA: `b3fc4d9db866c7c87dc438a736169c52b15baf84`

Successful steps include:
- read-only D3-D regression;
- no-legacy-Window-overlay validation;
- render-depth validation;
- approved-production-input mutation guard;
- SMAPI build environment setup;
- Release compilation;
- post-build `.70` source-contract guard;
- `.70 TEST` packaging;
- final packaged-byte audit;
- artifact upload and identity recording.

## TEST package

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3D_RoomIntegrationRegression_TEST.zip`

Package SHA256:
`5bb1368d44fe111f9d07b4b762cd05507ca483cc4ba5b6efd1b07f3f180aa302`

Main GitHub artifact:
- name: `cardcha-alpha28-0696D3D-room-integration-regression-test`
- artifact ID: `10382330518`
- artifact digest: `sha256:11bb4759b6339937d489ee9f40c7e1092671363b0ff6ab88fad934ffa11c25ac`
- artifact size: `3556672` bytes

CI identity artifact:
- name: `cardcha-alpha28-0696D3D-ci-evidence`
- artifact ID: `10381618139`
- artifact digest: `sha256:7f0c63217e4d18c44a830bb7599212a858ea464f9c008238d4d1d093b92c0171`

The downloaded main artifact archive was independently hashed after retrieval and matched the GitHub artifact digest exactly:
`11bb4759b6339937d489ee9f40c7e1092671363b0ff6ab88fad934ffa11c25ac`

## Regression evidence

All D3-A current validator checks passed, including dedicated travel-gate ownership, four upgrade systems, grounded plinths and upgrade collision footprints.

All D3-B current validator checks passed, including:
- approved navigation-console PNG contract;
- approved yellow/beige radar backing preserved;
- exact reference backing preserved;
- machine visuals normalized to 96 px;
- D3-A travel gate preserved;
- radar collision footprint preserved;
- corrected D3-B deck property present.

All D3-C current validator checks passed, including:
- room-1 shared shell asset and shell tiles;
- doorway shell contract;
- approximately x2 outdoor gate presentation with bottom anchor;
- scaled gate use radius;
- Observation Window presentation scale `4.25` with centered overscan;
- D2 canonical Window bytes frozen.

Frozen D2 Observation Window SHA256 values:
- morning: `93f6d4fcd403838d5758be012448c44978e65a8a4cb8bb33d4b24e4fb00802c0`
- noon: `38cf1e47d73b7374c21932ca6fbd957a3f55d833385698d0b415721ebaddb29f`
- evening: `2b3fb1ec4e4dd8d0bb7b2a3cf511ce7f8757e8dbbbb9ba54493f791df6aa0b5f`
- night: `5d9ec8cbb2f13221d0463e474209d5a7bb3fbc4d1eb05bee28a15483b4c1173b`

Frozen D1S independent airship SHA256:
`58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce`

Approved radar/navigation-console SHA256:
`5cbe64fc2f8c9a9f8b34dd6b6c90fd8ad56038248413a6f60df599c797bf0e62`

Room-shell asset SHA256:
`f2e0ef5128ecb9b1083588a419b9b1c57fcf2b9034326b59e4b8483d4713eddd`

## Final package audit

Final ZIP audit reported `PASS`.

Verified:
- manifest version is exactly `.70`;
- compiled `Cardcha.dll` is present and valid PE output (`1056256` bytes);
- package has a single `Cardcha/` production root;
- no `.cs`, `.csproj`, `.targets`, `.pdb`, `bin`, `obj`, `tools`, `handoff` or `.git` developer clutter is packaged;
- i18n and assets are present;
- all four D2 Window images match canonical bytes and PNG contracts;
- D1S independent airship matches frozen bytes;
- radar matches the approved yellow/golden-backed reference bytes;
- room-shell asset matches frozen bytes;
- D3-A/D3-B shell/gameplay map contracts are present;
- legacy environment overlay reuse remains disabled;
- independent `.68` D1S airship layer remains active.

## Next gate

Ron installs the `.70 TEST` package and checks in game:
- all four time buckets of the Observation Window;
- small independent airship motion;
- all four upgrade machines after reload and interaction reachability;
- dedicated boarding/travel gate approach and actual route travel;
- machine/radar collision feel at physical bases;
- room 1 and room 2 shell/borders visually;
- enlarged entrance arch alignment/opening;
- slight Observation Window enlargement;
- radar/workstation keeps its intended yellow/golden backing and approved presentation.

Only after that in-game check may this checkpoint be promoted to Runtime/Visual acceptance.

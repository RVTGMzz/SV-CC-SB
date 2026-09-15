# Cardcha session handoff — 2026-09-15 — 0696D3-D

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.70`

## Current status

0696D3-D **static regression, Release compile and TEST packaging are complete and PASS**.

Runtime / in-game acceptance is **NOT revalidated yet** and remains `PENDING-RON-IN-GAME`.

Authoritative checkpoint:
`handoff/AIRSHIP_0696D3D_CHECKPOINT.md`

## Final D3-D evidence

- Corrected radar tooling commit: `0f91514b5871d24dc19589f4e7623d0b9d04bc55`
- Corrected D3-B materialized baseline: `979056bf8552d4586b03a52fa3c35e089c7cd50f`
- D3-D regression tool commit: `2f0cd839e2086d609a6a4bc6451aa7e37b9769bb`
- D3-D package-audit tool commit: `fa0125b24ee82e17a5bc725e0b9c7fe5e485d1c8`
- D3-D workflow/source commit: `b3fc4d9db866c7c87dc438a736169c52b15baf84`
- Successful workflow run: `34932478977`
- Checkpoint commit: `c6466fa52b7dbc6b68ddd9da80b38d644420b320`

Main artifact:
- artifact ID: `10382330518`
- digest: `sha256:11bb4759b6339937d489ee9f40c7e1092671363b0ff6ab88fad934ffa11c25ac`

TEST package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3D_RoomIntegrationRegression_TEST.zip`

Package SHA256:
`5bb1368d44fe111f9d07b4b762cd05507ca483cc4ba5b6efd1b07f3f180aa302`

## What D3-D proved

Current D3-A, D3-B and D3-C validators all PASS on the packaged source line.

D3-D additionally proves:
- Morning / Noon / Evening / Night D2 Observation Window canonical bytes are frozen;
- D1S independent small-airship art is frozen;
- approved radar/navigation-console bytes are frozen;
- the intentional yellow/golden radar backing is preserved;
- corrected D3-B map marker is present;
- four upgrade systems and their physical-base collision contract remain present;
- dedicated travel-gate source/render contract remains present;
- room 1 and room 2 shell contracts remain present;
- enlarged entrance-gate source contract remains present;
- slight Observation Window `4.25` centered presentation scale remains present;
- no legacy Window environment overlay reuse is restored;
- render-depth contract remains valid;
- the validation pass does not mutate approved production inputs;
- Release compilation succeeds;
- final `.70` packaged bytes pass the package audit;
- package contains production files only and no source/dev clutter.

Approved radar SHA256:
`5cbe64fc2f8c9a9f8b34dd6b6c90fd8ad56038248413a6f60df599c797bf0e62`

## Ron correction remains authoritative

The radar/navigation workstation deliberately keeps its warm yellow/golden backing/background. Do not strip this backing for transparency and do not recreate the radar from memory.

Upgrade-pedestal integration and restoring the intended floor-2 upgrade machines remain one combined task, not two separate checklist items.

## Resume point

The next step is **Ron in-game acceptance of the `.70 TEST` package**, not another CI rebuild.

Ron should check:
1. four Observation Window time buckets and small independent airship motion;
2. four upgrade machines after reload plus interaction reachability;
3. dedicated boarding/travel gate approach and actual route travel;
4. machine/radar physical-base collision feel;
5. room 1 / room 2 shell presentation;
6. enlarged entrance arch alignment and usable opening;
7. slight Observation Window enlargement;
8. radar keeps the approved yellow/golden backing/presentation.

Do not claim Runtime PASS until Ron actually tests this package in Stardew Valley.

## Read first next time

1. `handoff/AIRSHIP_0696D3D_CHECKPOINT.md`
2. `handoff/SESSION_HANDOFF_2026-09-15_CARDCHA_0696D3D.md`
3. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_FEEDBACK.md`
4. `handoff/AIRSHIP_0696D3C_ROOM_SHELL_ENTRANCES_VALIDATION.json`
5. `handoff/AIRSHIP_0696D3B_PROP_INTEGRATION_VALIDATION.json`
6. `handoff/AIRSHIP_0696D3A_GAMEPLAY_ROOM_INTEGRATION_VALIDATION.json`
7. `handoff/AIRSHIP_0696D2_REBASELINE_CANONICAL.json`

When Ron returns with runtime feedback, continue from that evidence. Do not restart D2 or redo D3-A/B/C from scratch.

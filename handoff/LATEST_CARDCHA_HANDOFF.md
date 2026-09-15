# LATEST CARDCHA HANDOFF

Updated: 2026-09-15

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.70`

## Read first

1. `handoff/AIRSHIP_0696D3D_CHECKPOINT.md`
2. `handoff/SESSION_HANDOFF_2026-09-15_CARDCHA_0696D3D.md`
3. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_FEEDBACK.md`
4. `handoff/AIRSHIP_0696D3C_ROOM_SHELL_ENTRANCES_VALIDATION.json`
5. `handoff/AIRSHIP_0696D3B_PROP_INTEGRATION_VALIDATION.json`
6. `handoff/AIRSHIP_0696D3A_GAMEPLAY_ROOM_INTEGRATION_VALIDATION.json`
7. `handoff/AIRSHIP_0696D2_REBASELINE_CANONICAL.json`

## Current status

0696D2.1 source recovery/re-baseline is complete. Do not restart it.

0696D3 room integration:
- D3-A gameplay integration: PASS.
- D3-B prop integration with corrected yellow/golden radar backing contract: PASS.
- D3-C room shell / entrances / slight Observation Window enlargement: PASS.
- D3-D static regression: PASS.
- D3-D Release compile: PASS.
- D3-D `.70 TEST` package audit: PASS.
- Runtime / visual acceptance: **PENDING-RON-IN-GAME**.

Successful D3-D workflow run:
`34932478977`

D3-D workflow/source commit:
`b3fc4d9db866c7c87dc438a736169c52b15baf84`

D3-D checkpoint commit:
`c6466fa52b7dbc6b68ddd9da80b38d644420b320`

TEST package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3D_RoomIntegrationRegression_TEST.zip`

Package SHA256:
`5bb1368d44fe111f9d07b4b762cd05507ca483cc4ba5b6efd1b07f3f180aa302`

Main artifact ID:
`10382330518`

Main artifact digest:
`sha256:11bb4759b6339937d489ee9f40c7e1092671363b0ff6ab88fad934ffa11c25ac`

## Critical Ron correction

The radar/navigation workstation must keep the deliberate yellow/golden backing/background from Ron's supplied reference. This contract is now enforced by the corrected D3-B validator and the D3-D package audit.

Approved radar SHA256:
`5cbe64fc2f8c9a9f8b34dd6b6c90fd8ad56038248413a6f60df599c797bf0e62`

Do not strip the backing for transparency and do not recreate the radar from memory.

Upgrade-pedestal integration and restoring the intended floor-2 upgrade machines remain one combined task.

## Resume instruction

The next gate is Ron's in-game test of the `.70 TEST` package. Do not create another package merely to repeat CI that is already green.

Test the four Window time buckets, D1S small-airship motion, all four upgrade machines and interactions, boarding/travel route, collision feel, room shells, entrance arch, slight Window enlargement and approved radar presentation.

Do not claim Runtime PASS until Ron reports successful in-game testing.

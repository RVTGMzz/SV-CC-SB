# LATEST CARDCHA HANDOFF

Updated: 2026-09-15

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Read first

1. `handoff/SESSION_HANDOFF_2026-09-15_CARDCHA_0696D3D.md`
2. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_FEEDBACK.md`
3. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_PLAN.md`
4. `handoff/AIRSHIP_0696D3C_ROOM_SHELL_ENTRANCES_VALIDATION.json`
5. `handoff/AIRSHIP_0696D3A_CHECKPOINT.md`
6. `handoff/AIRSHIP_0696D2_REBASELINE_CANONICAL.json`

## Current status

0696D2.1 source recovery/re-baseline is complete. Do not restart it.

0696D3 room-integration batches:
- D3-A gameplay-critical room objects: IMPLEMENTED + CI PASS.
- D3-B prop integration: implementation + CI PASS exists, but its original radar-background-removal decision was later corrected by Ron.
- D3-C room shell / entrances / slight Observation Window enlargement: PASS.
- D3-D regression + next TEST package: **CURRENT TASK, NOT FINISHED YET**.

Current TEST version in source is:
`0.3.0-alpha.28.0.4.14.4.5.12.70`

Version bump commit:
`25fa61c66253e73a78609b41859ee57e9f7a0db0`

Radar correction commit:
`7f988f492bd5b7f0a6bee14b0db4ffacdf19c8fe`

## Critical Ron correction

The radar/navigation workstation must follow Ron's supplied reference and **keep the deliberate yellow/golden backing/background**. The earlier D3-B instruction to remove that backing was wrong and is superseded.

Do not blindly rerun the old D3-B materializer/workflow until its expectations are reconciled with this correction, otherwise it may remove the restored backing again.

Also keep this checklist interpretation:
- rebuilding the upgrade pedestal area and restoring missing floor-2 upgrade machines are **one combined task**, not two.

## Resume instruction

When Ron says `tiếp`, resume **D3-D** immediately:
1. reconcile D3-B regression tooling with the corrected radar requirement;
2. run final room/window/gate/upgrade/collision regressions;
3. compile Release;
4. package/audit the `.70 TEST` artifact;
5. record final D3-D validation, artifact metadata and SHA256;
6. give Ron the TEST package for visual/gameplay acceptance.

There is no completed `.70 TEST` package or D3-D CI PASS to claim at this checkpoint.

D1S independent small-airship art remains frozen. Weather/season runtime variants remain out of scope for this finish unless Ron explicitly expands scope.

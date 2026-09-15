# README FOR NEXT SESSION — Cardcha 0696D3-D

Updated: 2026-09-15
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

Read these first:
1. `handoff/SESSION_HANDOFF_2026-09-15_CARDCHA_0696D3D.md`
2. `handoff/LATEST_CARDCHA_HANDOFF.md`
3. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_FEEDBACK.md`
4. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_PLAN.md`

## Status

0696D2.1 recovery/re-baseline is finished and must not be restarted.

0696D3-A is implemented + CI PASS.
0696D3-B implementation + CI PASS exists, but its original radar-background-removal rule was corrected later.
0696D3-C validation is PASS.

Current task: **0696D3-D regression + `.70 TEST` packaging**.

Current source version:
`0.3.0-alpha.28.0.4.14.4.5.12.70`

Important latest commits:
- radar backing restoration: `7f988f492bd5b7f0a6bee14b0db4ffacdf19c8fe`
- `.70` version bump: `25fa61c66253e73a78609b41859ee57e9f7a0db0`

## Critical guard

Ron's supplied radar/workstation reference intentionally includes the warm yellow/golden backing. Preserve it. Do not rerun old D3-B cleanup logic if it will strip that backing.

The full exact resume procedure, completed batch details, hashes, regression checklist and do-not-do list are in:
`handoff/SESSION_HANDOFF_2026-09-15_CARDCHA_0696D3D.md`

When Ron says `tiếp`, continue D3-D immediately and finish regression, Release compile, package audit and the `.70 TEST` artifact. Do not ask Ron to restate the checklist.

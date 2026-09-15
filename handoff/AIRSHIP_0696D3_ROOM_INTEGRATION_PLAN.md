# AIRSHIP 0696D3 ROOM INTEGRATION PLAN

Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Starting checkpoint: `a2d74a1a85c3e4b557a3b694dfb58d78ab8e87e2`
Updated: 2026-09-15

Goal: finish room integration in durable batches. Each batch must end with a committed checkpoint before the next batch starts.

## Batch D3-A — Gameplay-critical room objects

1. Rebuild the upgrade-machine area as one combined task, including restoration of the missing floor-2 upgrade machines and replacement/integration of the old fake-looking pedestal presentation.
2. Make map travel / boarding gate visible, discoverable and functional.
3. Restore collision for machines so the player cannot walk through solid bases.
4. Restore interaction/action behavior for intended interactive machines.

Acceptance: player can identify and use the travel gate; upgrade machines are present; machines block movement appropriately; intended interactables respond.

Status: **IMPLEMENTED + CI PASS**.
Checkpoint: `handoff/AIRSHIP_0696D3A_CHECKPOINT.md`
Materialized commit: `fa23a9ba178d36da5d1cf55080d3594ea20a16ff`
Workflow run: `34895005876`

## Batch D3-B — Prop integration and visual believability

1. Reposition/scale props so the room reads naturally instead of pasted onto the floor.
2. Correct oversized machines and physical footprints.
3. Preserve Ron's supplied radar/navigation-workstation design and its characteristic **yellow/golden backing/background**. Do not recreate it from memory and do not remove the backing merely because it is opaque/yellow.
4. Preserve intended detail while removing only genuinely unintended artifacts that are not part of the supplied reference.

Acceptance: room reads as one coherent interior; prop scale and spacing feel native to Stardew; radar/workstation remains faithful to Ron's supplied reference including the yellow/golden backing.

Status: **IMPLEMENTATION + CI PASS EXISTS, THEN CORRECTED**.
Historical D3-B materialized commit: `f3bde3e46934d0d7d1830ef71d888360b3a4807d`
Historical workflow run: `34895825578`
Radar backing correction commit: `7f988f492bd5b7f0a6bee14b0db4ffacdf19c8fe`

Important: the old D3-B checkpoint/script was authored under the now-superseded assumption that the yellow/beige backing should be removed. Do not blindly rerun old D3-B materialization until its expectations are reconciled with Ron's correction.

## Batch D3-C — Room shell and entrances

1. Add/restore the missing border/shell treatment for room 1 so it matches room 2's finished-room presentation.
2. Fix entrance arch alignment.
3. Increase entrance arch size to approximately 2x while preserving a usable walking opening and collision.
4. Slightly increase Observation Window presentation size without changing the approved D2.1 environment source set.

Acceptance: both rooms have coherent borders; entrance arch is centered, larger and usable; window feels correctly proportioned.

Status: **PASS**.
Validation: `handoff/AIRSHIP_0696D3C_ROOM_SHELL_ENTRANCES_VALIDATION.json`
Materialized commit: `167fd9e6aceca142ea2d767466961c2cb6d7793b`

Validated values:
- outdoor entrance gate scale `1.48 -> 2.88`;
- gate use distance `160 -> 256`;
- Observation Window presentation `4.0 -> 4.25` (`+6.25%`), centered runtime overscan;
- D2.1 canonical Observation Window bytes unchanged.

## Batch D3-D — Regression + test package

Status: **CURRENT TASK, NOT FINISHED**.

Current source TEST version:
`0.3.0-alpha.28.0.4.14.4.5.12.70`

Version bump commit:
`25fa61c66253e73a78609b41859ee57e9f7a0db0`

Before packaging:
1. Reconcile D3-B regression tooling so it preserves the restored yellow/golden radar backing.
2. Regression-check Observation Window Morning/Noon/Evening/Night.
3. Confirm D1S independent airship animation remains preserved.
4. Confirm four upgrade stations remain present and intended interactions survive reload.
5. Confirm travel gate works from normal approach.
6. Confirm major machinery/radar blocks walk-through only at physical bases.
7. Confirm room 1 and room 2 borders render correctly.
8. Confirm entrance arch alignment/scale remains correct and usable.
9. Confirm Observation Window remains only slightly enlarged.
10. Confirm radar/workstation still matches Ron's supplied reference including the yellow/golden backing.
11. Compile Release, package `.70 TEST`, run package audit, record artifact metadata/SHA256 and create final D3-D validation/checkpoint.

There is no completed `.70 TEST` package or D3-D CI PASS to claim yet.

## Session policy

Do not attempt unrelated work before D3-D closes. Resume from `handoff/SESSION_HANDOFF_2026-09-15_CARDCHA_0696D3D.md`, not from the old D2 audit.

When Ron says `tiếp`, continue D3-D immediately. Do not ask him to restate the checklist.

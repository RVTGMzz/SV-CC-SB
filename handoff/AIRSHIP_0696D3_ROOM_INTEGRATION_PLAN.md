# AIRSHIP 0696D3 ROOM INTEGRATION PLAN

Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Starting checkpoint: `a2d74a1a85c3e4b557a3b694dfb58d78ab8e87e2`

Goal: finish room integration without cramming unrelated fixes into one session. Each batch must end with a durable commit/checkpoint before the next batch starts.

## Batch D3-A — Gameplay-critical room objects

1. Rebuild the upgrade-machine area as one task. This includes restoring the missing floor-2 upgrade machines and replacing the old fake-looking upgrade pedestals with a more natural room-integrated layout.
2. Make the map-travel / boarding gate visible, discoverable and actually functional.
3. Restore collision for machines so the player cannot walk through them.
4. Restore interaction/action behavior for intended interactive machines.

Acceptance: player can identify and use the travel gate; upgrade machines are present; machines block movement appropriately; intended interactables respond.

Status: IMPLEMENTED + CI PASS in `handoff/AIRSHIP_0696D3A_CHECKPOINT.md`.

## Batch D3-B — Prop integration and visual believability

1. Reposition/scale props to match the concept more naturally instead of looking pasted onto the floor.
2. Correct oversized machines and physical footprints.
3. Rework the radar/navigation machine using Ron's supplied reference. Preserve the approved steampunk desk/radar design, but REMOVE the unintended yellow/beige baked background. Do not invent a different radar machine.
4. Remove unintended cutout/background artifacts while preserving the machine itself and its intended detail.

Acceptance: room reads as one coherent interior; prop scale and spacing feel native to Stardew; radar machine matches Ron's reference and no longer carries the yellow/beige rectangular background.

## Batch D3-C — Room shell and entrances

1. Add/restore the missing border/shell treatment for room 1 so it matches room 2's finished-room presentation.
2. Fix entrance arch alignment.
3. Increase entrance arch size to approximately 2x as requested, while preserving a usable walking opening and collision.
4. Slightly increase Observation Window presentation size without changing the approved D2.1 environment source set.

Acceptance: both rooms have coherent borders; entrance arch is centered, larger and usable; window feels correctly proportioned.

## Batch D3-D — Regression + test package

Regression checklist:
- Observation Window Morning/Noon/Evening/Night still resolves correctly.
- D1S independent airship animation is preserved.
- Navigation Console design is not replaced with an improvised machine.
- Upgrade machines remain present and interactive after reload.
- Gate travel works from normal player approach.
- No unintended walk-through on major machines/props.
- Room 1 and room 2 borders render correctly.
- Entrance arch alignment/scale remains correct.

Then compile, package and produce the next TEST artifact for Ron visual/gameplay acceptance.

## Session policy

Do not attempt all batches in one chat if that risks incomplete work. Finish the current batch, commit it, update handoff status, then continue in the same or a later session. A later session should resume from this file and the latest batch checkpoint, not restart the audit.

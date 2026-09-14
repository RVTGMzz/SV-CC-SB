# LATEST CARDCHA HANDOFF

Updated: 2026-09-14

Read first:
1. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_PLAN.md`
2. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_FEEDBACK.md`
3. `README_FOR_NEXT_SESSION.md`
4. `handoff/HANDOFF_CURRENT.md`
5. `handoff/AIRSHIP_0696D2_REBASELINE_CANONICAL.json`

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Status

0696D2.1 re-baseline is complete and `.69 TEST` compiled successfully.
Ron completed the first in-game room review. Observation Window production is usable, but overall room integration still needs work.

Do not restart source recovery.

## Current workstream

Proceed with **0696D3 Room Integration** in small durable batches. Do not cram all fixes into one session.

Batch order:
- D3-A: gameplay-critical upgrade machines, boarding/map-travel gate, collision and interaction.
- D3-B: prop scale/placement and radar reference fidelity.
- D3-C: room 1 border, entrance arch alignment + ~2x scale, slight Observation Window presentation enlargement.
- D3-D: regression, compile and next TEST package.

Important clarification from Ron:
- rebuilding old upgrade pedestals and restoring the missing floor-2 upgrade machines are ONE combined task;
- radar/machine art must follow Ron's supplied reference, including the characteristic yellow/gold background, not an invented replacement.

Full task acceptance criteria live in `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_PLAN.md`.

D1S airship remains frozen. Navigation Console remains deferred unless a later explicit task requires it.

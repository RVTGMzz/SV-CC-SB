# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
`cardcha-alpha28-0696d1s-airship-motion-repair`

Current build candidate:
`0.3.0-alpha.28.0.4.14.4.5.12.68`

Current handoff:
`handoff/ALPHA28_0696D1S_AIRSHIP_MOTION_REPAIR.md`

## Status
- 0696D1 `.65`: visual rejected for clipping/hollowing/bleed.
- 0696D1R `.67`: source/alpha geometry repaired, but Ron caught a semantic animation bug: overlay 2–4 are window-column/transition slices, not airship frames.
- 0696D1S `.68`: removes legacy overlay cycling and animates one extracted real airship sprite across the center pane.
- Window furniture/body remains map-native and static.
- D2 season/time/weather matrix and D3 Navigation Console remain deferred.
- Visual acceptance: **PENDING-RON-VISUAL**.

## Continuation order
1. 0696D1S Real Airship Motion Repair — current acceptance gate
2. 0696D2 Window Environment Matrix Rebuild
3. 0696D3 Navigation Console Source Cleanup
4. 0696D4 Deck Integration & Acceptance

Do not proceed to D2 until Ron accepts the actual airship motion.

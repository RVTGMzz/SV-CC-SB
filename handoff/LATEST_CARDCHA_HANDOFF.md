# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
`cardcha-alpha28-0696d1-observation-window-source-cleanup`

Current build candidate:
`0.3.0-alpha.28.0.4.14.4.5.12.65`

Current handoff:
`handoff/ALPHA28_0696D1_OBSERVATION_WINDOW_SOURCE_CLEANUP.md`

## Status
- 0696C `.64`: technical PASS but visually rejected for remaining yellow/matte hero-prop source contamination.
- 0696D.1 isolates **Observation Window source cleanup only**.
- Window footprint remains 160x80 / 10x5 tiles.
- RGB artwork is byte-identical before/after cleanup; only alpha for border-connected matte pixels changes.
- Navigation Console is intentionally deferred to 0696D.3.
- Window season/time/weather matrix is intentionally deferred to 0696D.2.
- Visual acceptance remains **PENDING-RON-VISUAL**.

## Continuation order
1. 0696D.1 Observation Window Source Cleanup
2. 0696D.2 Window Environment Matrix Rebuild
3. 0696D.3 Navigation Console Source Cleanup
4. 0696D.4 Deck Integration & Acceptance

## Non-negotiable rule
Do not merge the four passes into one recovery blob. Each pass must pass independently before the next is promoted.

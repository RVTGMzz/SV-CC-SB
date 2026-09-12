# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
`cardcha-alpha28-0696d1-observation-window-source-cleanup`

Current build candidate:
`0.3.0-alpha.28.0.4.14.4.5.12.66`

Current handoff:
`handoff/ALPHA28_0696D1R_WINDOW_BOUNDED_CLEANUP.md`

## Status
- 0696D1 `.65`: **VISUAL REJECTED by Ron** for clipped sprite edges, incorrect hollow aperture, and apparent spill/bleed toward neighboring sprite space.
- 0696D1R `.66`: bounded rework. It restores `.64` source first and then performs only exact allowed alpha repairs.
- Observation Window remains 160x80 / 10x5 tiles.
- Four approved animation overlays remain four independent 160x80 files.
- No crop, shift, strip packing, or aperture cutout is allowed.
- Navigation Console remains deferred to D3.
- Season/time/weather matrix remains deferred to D2.
- Visual acceptance: **PENDING-RON-VISUAL**.

## Continuation order
1. 0696D1R Window bounded source/overlay cleanup — current
2. 0696D2 Window Environment Matrix Rebuild
3. 0696D3 Navigation Console Source Cleanup
4. 0696D4 Deck Integration & Acceptance

## Non-negotiable rule
Do not proceed to D2 until Ron accepts Window geometry/alpha behavior. Technical PASS never equals visual PASS.

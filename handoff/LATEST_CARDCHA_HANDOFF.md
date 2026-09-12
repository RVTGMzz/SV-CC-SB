# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
`cardcha-alpha28-0696d1-observation-window-source-cleanup`

Current build candidate:
`0.3.0-alpha.28.0.4.14.4.5.12.67`

Current handoff:
`handoff/ALPHA28_0696D1R_WINDOW_BOUNDED_CLEANUP.md`

## Status
- 0696D1 `.65`: **VISUAL REJECTED by Ron** for clipping/hollowing/bleed.
- D1R internal `.66`: technically passed, but self-review caught detached edge fragments before release.
- D1R `.67`: final bounded source pass, including detached-edge-component cleanup without touching the main connected Window body.
- 4 approved animation overlays remain independent 160x80 files.
- no crop, shift, strip packing, or aperture cutout.
- Navigation Console is D3; season/time/weather matrix is D2.
- Visual acceptance: **PENDING-RON-VISUAL**.

## Continuation order
1. 0696D1R Window bounded source/overlay cleanup — current acceptance gate
2. 0696D2 Window Environment Matrix Rebuild
3. 0696D3 Navigation Console Source Cleanup
4. 0696D4 Deck Integration & Acceptance

Do not proceed to D2 until Ron accepts the Window source geometry/alpha behavior.

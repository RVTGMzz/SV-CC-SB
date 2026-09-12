# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
`cardcha-alpha28-0696d1-observation-window-source-cleanup`

Current build candidate:
`0.3.0-alpha.28.0.4.14.4.5.12.67`

Current handoff:
`handoff/ALPHA28_0696D1R_WINDOW_BOUNDED_CLEANUP.md`

## Verified D1R checkpoint
- Materialized source: `8fe52dfc23ec58b00138c4b129d91a3dd9121d81`
- Successful CI run: `34702756885`
- Artifact ID: `10300676229`
- Artifact digest: `sha256:29682998ce4c19d76cace6f9541d4d8045594664ce761898fac7729ac1db205e`
- TEST ZIP SHA256: `3e0a9f77e67c957e93f125388bf975ffa389e86ffaffb0bac578db531a37071d`
- Technical validation: **PASS**
- Visual acceptance: **PENDING-RON-VISUAL**

## Status
- 0696D1 `.65`: **VISUAL REJECTED by Ron** for clipping/hollowing/bleed.
- D1R internal `.66`: technically passed, but self-review caught three detached edge fragments before release.
- D1R `.67`: final bounded source pass.
- Exact pale matte cleanup removed 2558 pixels.
- Detached left-edge bleed removed 101 pixels in three components: 59 px bbox `[0,63,5,79]`, 38 px bbox `[0,33,3,51]`, and 4 px bbox `[0,8,1,12]`.
- Remaining detached edge components: **0**.
- Main Window component remains intact at bbox `[11,6,159,79]` with 9977 pixels.
- Four approved animation overlays remain four independent 160x80 files.
- Overlay export-mask repair removed pure-black masks `[0,2324,2072,1820]` pixels from frames 1..4; remaining opaque pure-black pixels: **0**.
- No crop, shift, strip packing, or aperture cutout.
- Runtime ownership is restored to the approved 0690 contract: TMX owns the static body; runtime cycles the four repaired transparent overlays.
- Navigation Console remains D3; season/time/weather matrix remains D2.

## Continuation order
1. 0696D1R Window bounded source/overlay cleanup — **TECH PASS / VISUAL PENDING**
2. 0696D2 Window Environment Matrix Rebuild
3. 0696D3 Navigation Console Source Cleanup
4. 0696D4 Deck Integration & Acceptance

## Non-negotiable rule
Do not proceed to D2 until Ron accepts the Window source geometry and alpha behavior. Technical PASS never equals visual PASS.

# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
`cardcha-alpha28-0696d1-observation-window-source-cleanup`

Current build candidate:
`0.3.0-alpha.28.0.4.14.4.5.12.65`

Current handoff:
`handoff/ALPHA28_0696D1_OBSERVATION_WINDOW_SOURCE_CLEANUP.md`

## Verified D1 checkpoint
- Materialized source: `eb86afa9f35e723f2de96e102ef2ac8e7e3c66fd`
- Successful CI run: `34699808416`
- Artifact ID: `10299991654`
- Artifact digest: `sha256:7ad9adfe81ee20ddef346e6c676d9c6b9c15b833b9e30ca9109d89d707c0b947`
- TEST ZIP SHA256: `1d9884df003280f4bce8bd12af19c26c9ec88af4e5f53a77d9db5969e01c6949`
- Technical validation: **PASS**
- Visual acceptance: **PENDING-RON-VISUAL**

## Status
- 0696C `.64`: technical PASS but visually rejected for remaining yellow/matte hero-prop source contamination.
- 0696D.1 isolates **Observation Window source cleanup only** and is now technically complete.
- 2625 opaque matte pixels were made transparent.
- Window footprint remains 160x80 / 10x5 tiles.
- RGB artwork SHA is identical before/after cleanup; only alpha changed.
- Validator confirms 0 border-connected opaque matte pixels remain on both base and runtime frame.
- Navigation Console is intentionally deferred to 0696D.3.
- Window season/time/weather matrix is intentionally deferred to 0696D.2.

## Continuation order
1. 0696D.1 Observation Window Source Cleanup — **TECH PASS / VISUAL PENDING**
2. 0696D.2 Window Environment Matrix Rebuild
3. 0696D.3 Navigation Console Source Cleanup
4. 0696D.4 Deck Integration & Acceptance

## Non-negotiable rule
Do not merge the four passes into one recovery blob. Each pass must pass independently before the next is promoted.

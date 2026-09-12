# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
`cardcha-alpha28-0696-airship-concept-faithful-visible-integration`

Current build candidate:
`0.3.0-alpha.28.0.4.14.4.5.12.64`

Current handoff:
`handoff/ALPHA28_0696C_AIRSHIP_DECK_VISUAL_RECOVERY.md`

## Verified 0696C checkpoint
- Materialized source: `58e3d80147e6e5490d32b83527587ca4156ff0cc`
- Successful CI run: `34698643517`
- Artifact ID: `10298949682`
- TEST ZIP SHA256: `d8128de076f0d22d60ae8c9a8dc8b51a4040e67d047121ce833ca440e7bf7cce`
- Technical validation: **PASS**
- Visual acceptance: **PENDING-RON-IN-GAME**

## Status
- 0696A architecture: technical baseline.
- 0696B `.63`: **VISUAL REJECTED by Ron** from in-game screenshots.
- 0696C `.64`: repairs explicit season/time/weather window matrix, removes black window fallback frames, restores four upgrade stations, adds visible room shell, and guards the Deck from black-void escape.
- All 80 window backdrops are package-gated fully opaque; rain/snow/cloud motion remains a separate runtime FX layer and storm keeps lightning overlay behavior.
- Sky Dock and unrelated Region maps were frozen during 0696C.

## Next acceptance step
Ron should replace `.63` with the verified `.64` TEST package and inspect the Airship Deck in game. Report visual/layer problems with screenshots; do not promote the pass based on CI alone.

## Non-negotiable rule
Technical PASS never equals visual PASS. Preserve exact hero prop footprints and base `Buildings` collision ownership. Never reintroduce `BackDecor`.

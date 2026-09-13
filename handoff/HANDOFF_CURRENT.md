# CARDCHA CURRENT HANDOFF

Updated: 2026-09-14
Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Current HEAD after successful materialization: `f6a05a786937f0a8e5f8a2ab01aa14a06e7def7a`

## Current state

0696D2.1 has been **intentionally re-baselined from the recovered approved master artwork**.

Safe historical base: `.68`
Current TEST candidate: `0.3.0-alpha.28.0.4.14.4.5.12.69`
Status: **BUILD/PACKAGE PASS, PENDING RON IN-GAME VISUAL ACCEPTANCE**

Do not restart image recovery and do not return to the old exact-byte blocker unless Ron explicitly asks for historical archaeology.

## Canonical master source

Approved masters are preserved under:

`recovery/0696d2-concept-masters/01_approved_time_of_day_masters/`

Decision record:
`handoff/AIRSHIP_0696D2_REBASELINE_DECISION.md`

Deterministic canonical manifest:
`handoff/AIRSHIP_0696D2_REBASELINE_CANONICAL.json`

Pipeline:

- source: exact recovered 1774x887 RGBA masters
- target: 160x80 RGBA
- no crop because source is already exact 2:1
- Pillow 11.3.0
- LANCZOS
- PNG optimize false
- compression level 9
- no source metadata copied

## New canonical production SHA256

- Morning: `93f6d4fcd403838d5758be012448c44978e65a8a4cb8bb33d4b24e4fb00802c0`
- Noon: `38cf1e47d73b7374c21932ca6fbd957a3f55d833385698d0b415721ebaddb29f`
- Evening: `2b3fb1ec4e4dd8d0bb7b2a3cf511ce7f8757e8dbbbb9ba54493f791df6aa0b5f`
- Night: `5d9ec8cbb2f13221d0463e474209d5a7bb3fbc4d1eb05bee28a15483b4c1173b`

The old 160x80 SHA set remains documented as historical lost identities only. The new files do not impersonate those hashes.

## CI / package result

Workflow run: `34780451317`
Conclusion: **SUCCESS**

Passed:

- deterministic master-to-production materialization
- exact canonical byte verification
- D2 runtime apply/validate
- no legacy Window overlay reuse
- render-depth contract
- D1S ship / Console / map freeze
- SMAPI build environment
- Cardcha Release compile
- canonical output commit
- `.69` package audit
- artifact upload

Generated output commit:
`f6a05a786937f0a8e5f8a2ab01aa14a06e7def7a`

`.69 TEST` ZIP SHA256:
`0d0891dfa60eff914c0d4eccbe481bce8c5d28b8cdd5429e7a07a0a5ca4b04bd`

Validation report:
`handoff/AIRSHIP_0696D2_WINDOW_ENVIRONMENT_MATRIX_VALIDATION.json`

## Frozen invariants

- D1S airship unchanged, SHA256 `58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce`
- Navigation Console untouched/deferred
- weather runtime variants deferred
- seasonal runtime variants deferred
- legacy observation overlays are not reused as D2 environments

## Next action

Ron installs `.69 TEST` and visually checks the Observation Window across the four time buckets:

- Morning 06:00-11:50
- Noon 12:00-16:50
- Evening 17:00-19:50
- Night otherwise

If visual PASS: freeze D2.1 and continue later D2 weather/season work.
If visual FAIL: adjust the deterministic production transform deliberately from the preserved masters, record a new canonical SHA set, and rebuild. Never edit the master bytes.

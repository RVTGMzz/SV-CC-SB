# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
Continue on:
`cardcha-alpha28-0696-airship-concept-faithful-visible-integration`

Current recovery handoff:
`handoff/ALPHA28_0696A_AIRSHIP_VISIBLE_ARCHITECTURE_RECOVERY.md`

Authoritative blueprint:
`handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json`

Authoritative repo-source inventory:
`handoff/AIRSHIP_SOURCE_PACK_0696.json`

Authoritative technical validation:
`handoff/AIRSHIP_VISIBLE_INTEGRATION_VALIDATION_0696.json`

Preview report:
`handoff/AIRSHIP_PREVIEW_REPORT_0696.json`

## 0696A verified checkpoint
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.62`
- Materialized source head: `e6d84d22e59030dc38eb37902d32424d50902814`
- Successful workflow run: `34685463138`
- Artifact ID: `10295536254`
- Artifact digest: `sha256:46fa1682ebebcc7aae0c03d2126c6bc6001b51a87e01d9fab3d831ab8b27d7f6`
- TEST ZIP: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.62_0696A_AirshipVisibleArchitectureRecovery_TEST.zip`
- TEST SHA256: `b22a90d02a8835d87b7b54206bf0362af07ae898ead3ddb358fd0ae1ff022301`
- Technical validation: **PASS**
- Visual acceptance: **PENDING-RON-IN-GAME**

## Current state
- 0696A runtime-visible architecture recovery is materialized and independently package-verified.
- Exact repo-recovered Set01 + Set02 physical sprites are represented at full native footprint on supported TMX layers.
- `BackDecor` is retired from Airship production maps.
- Collision is owned by base `Buildings`; Gate walk-through opening and Sky Dock center spine are verified open.
- 0696 full Airship composition is still **WIP**.
- External source gap remains: `concept(1).rar` 6 PNGs + `sprite(1).rar` 22 PNGs are not recoverable from repo.

## Non-negotiable continuation rule
Do not redraw, shrink, or silently substitute the missing approved source sprites. Continue source-first when the exact source pack becomes available. Technical PASS never changes visual acceptance without Ron's in-game confirmation.

## Next acceptance step
Ron should test the `.62` 0696A TEST package in game and report the visual read of both Airship Deck and Sky Dock. Treat that report as the acceptance gate for the recovered architecture, not as approval of the still-missing full 0696 composition.

0695 remains the last pre-0696 production baseline:
`cardcha-alpha28-0695-region1-prop-integration`

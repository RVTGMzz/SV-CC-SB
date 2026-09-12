# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream
Continue on:
`cardcha-alpha28-0696-airship-concept-faithful-visible-integration`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.63`

Current handoff:
`handoff/ALPHA28_0696B_AIRSHIP_AMBIENT_RUNTIME_FOUNDATION.md`

Ambient asset contract:
`src/Cardcha/assets/airship_props/set01_redux/airship_ambient_manifest.json`

Ambient technical validation:
`handoff/AIRSHIP_AMBIENT_CONTRACT_VALIDATION_0696B.json`

0696A verified architecture handoff remains:
`handoff/ALPHA28_0696A_AIRSHIP_VISIBLE_ARCHITECTURE_RECOVERY.md`

## Verified 0696B checkpoint
- Materialized source head: `c71a8256c772c048cf93e782b584b05dc5ecb9ff`
- Successful workflow run: `34690399069`
- Artifact ID: `10296378327`
- Artifact digest: `sha256:20ef10946db86b5023d24d5756aaa69373ecb38091ac61e1bf70a59a489aab23`
- TEST ZIP: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.63_0696B_AirshipAmbientRuntimeFoundation_TEST.zip`
- TEST SHA256: `8913eef9fc15a4bc76a511e6d91b2da9d05bebb40bf893610298b5ed5c2657fa`
- Technical validation: **PASS**
- Visual acceptance: **PENDING-RON-IN-GAME**

## Current state
- 0696A physical Airship architecture: **TECHNICAL PASS / PENDING-RON-IN-GAME**.
- 0696B ambient runtime foundation: **TECHNICAL PASS**.
- Observation Window and Navigation Console selection/fallback logic is now manifest-driven.
- Resolver supports season + time bucket + weather priority + deterministic animation frame selection.
- Runtime supports optional storm lightning and layered radar animation.
- New 0696B production art remains **PENDING PRODUCTION**; all 8 approved 0690 fallback frames remain present.
- Contract currently declares 33 new ambient assets: 0 present / 33 pending.
- Full 0696 Airship composition remains **WIP** because the external approved source pack is still missing.

## Non-negotiable continuation rule
Do not redraw, shrink, or silently substitute missing approved full-room source sprites. For 0696B hero animation, produce only the explicitly declared ambient assets and preserve the locked 0696A footprints/collision.

## Next step
Materialize the first production ambient art slice:
1. transparent/clean Observation Window frame with the flat yellow external background removed;
2. default morning/noon/evening/night outside views;
3. clean console base + radar sweep strip;
then validate and package before adding weather and full season variants.

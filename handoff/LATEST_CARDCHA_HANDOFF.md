# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0646a-mimi-home-stability-portrait`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.11.1`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0646A_MIMI_HOME_STABILITY_PORTRAIT.md`

Previous MiMi handoffs:
- `handoff/ALPHA28_0646_MIMI_SECRET_TV_ROUTINE.md`
- `handoff/ALPHA28_0645_MIMI_ATTIC_LIVING_LORE.md`
- `handoff/ALPHA28_0643_MIMI_ATTIC_STARDew_REBUILD.md`

Previous Airship visual handoff:
- `handoff/ALPHA28_0642_AIRSHIP_INTERIOR_STARDew_REWORK.md`

## Current verified state
- `.5.11` MiMi Secret TV Routine remains the feature baseline: 6+ hearts, TV nook from 17:30 until 22:00, then personal-corner wind-down.
- `.5.11.1` hotfix addresses the concrete in-game screenshot issues from `.5.11`.
- MiMi home routine tiles are now cached per routine state so collision resolution no longer ping-pongs her between nearby tiles every tick.
- MiMi social/home dialogue now uses the same sharp in-memory portrait pipeline as Cardcha story dialogue instead of the coarse native runtime64 fallback.
- Empty-hand TV-routine talk is owned by HomeService so routine-specific dialogue is preserved; gifting remains native Stardew handling.
- New `cardcha_test_gate` command warps directly beside the Forest Arcane Gate and enables runtime-only test access without changing the save/story Airship unlock.
- Stable attic location remains `Cardcha_MiMiAttic`.
- 2-heart attic access, 6-heart TV requirement, 17:30 start and 22:00 end remain unchanged.

## Verified build
- workflow run: `33954172247` SUCCESS
- materialization commit: `ba292a9c763aab31943607636ca179fb3dca0a07`
- artifact ID: `9965803745`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.11.1_MiMiHomeStabilityPortrait_TEST.zip`
- package SHA-256: `a76a43fbf507af3c94f2a083649565c0e9478026e33b164c9aeefb116d1a29cb`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate uses 160px action distance and `CollisionEdits=NONE`.
- Locked Airship exterior `airship_visual.png` unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses remain unchanged.

## Next action
In-game accept `.5.11.1`: verify MiMi no longer blinks between tiles, portrait is sharp during social and TV-routine dialogue, 17:30/22:00 routine transitions happen once and remain stable, and `cardcha_test_gate` places the farmer beside a usable Forest gate without altering persistent unlock state.

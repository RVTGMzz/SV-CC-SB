# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0643-mimi-attic-stardew-rebuild`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.9`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0643_MIMI_ATTIC_STARDew_REBUILD.md`

Previous Airship visual handoff:
`handoff/ALPHA28_0642_AIRSHIP_INTERIOR_STARDew_REWORK.md`

## Current verified state
- `.5.8` Airship full Stardew interior rework: CI/build/package PASS; in-game visual acceptance still pending screenshots.
- `.5.9` MiMi Attic Stardew rebuild: CI/build/package PASS; in-game visual acceptance pending screenshots.
- MiMi Attic no longer uses the room-sized `mimi_attic_room_frame.png` overlay. The actual `townInterior` TMX + vanilla furniture own room presentation.
- Stable location remains `Cardcha_MiMiAttic`.
- Five MiMi zones remain: landing, research, personal/bed, TV secret, ChaCha/upgrade.
- 2-heart attic access and 6-heart / 17:30 secret-TV eligibility remain unchanged.

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate uses 160px action distance and `CollisionEdits=NONE`.
- Locked Airship exterior `airship_visual.png` remains unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses remain unchanged.

## Next action
Install `.5.9`, screenshot MiMi Attic full room + research/bed/TV/ChaCha zones, and patch only concrete in-game layout/readability issues. Re-test `.5.8` Airship Sky Dock/Bridge and Forest gate when convenient.

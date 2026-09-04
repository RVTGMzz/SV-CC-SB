# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0646-mimi-secret-tv-routine`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.11`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0646_MIMI_SECRET_TV_ROUTINE.md`

Previous MiMi handoffs:
- `handoff/ALPHA28_0645_MIMI_ATTIC_LIVING_LORE.md`
- `handoff/ALPHA28_0643_MIMI_ATTIC_STARDew_REBUILD.md`

Previous Airship visual handoff:
- `handoff/ALPHA28_0642_AIRSHIP_INTERIOR_STARDew_REWORK.md`

## Current verified state
- `.5.8` Airship full Stardew interior rework: CI/build/package PASS; in-game visual acceptance still pending screenshots.
- `.5.9` MiMi Attic Stardew rebuild: CI/build/package PASS; room-sized overlay removed; true `townInterior` TMX + vanilla furniture own the room.
- `.5.10` MiMi Attic Living Lore: layered research/TV/ChaCha/personal inspect dialogue active.
- `.5.11` MiMi Secret TV Routine: CI/build/materialization/package/upload PASS.
- At 6+ hearts, MiMi now physically uses the TV nook from 17:30 until 22:00 and faces the TV.
- At 22:00+, high-friendship MiMi winds down by her personal/bed corner.
- Routine-specific talk text exists for early/late evening and when ChaCha is loaned.
- TV inspect text distinguishes active routine vs post-routine state.
- HomeService same-location repositioning bug was fixed so time-based movement inside the attic actually occurs.
- Stable location remains `Cardcha_MiMiAttic`.
- 2-heart attic access unchanged.
- No SaveData field/schema bump for the routine.

## Verified build
- workflow run: `33861687099` SUCCESS
- materialization commit: `a1b022c3f0cf1dce0fe1a87d155837fcba849732`
- artifact ID: `9932363536`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.11_MiMiSecretTvRoutine_TEST.zip`
- package SHA-256: `aca4128a84df63d09259158c0307b53076ecb22fdaaac225b131948d884f8b11`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate uses 160px action distance and `CollisionEdits=NONE`.
- Locked Airship exterior `airship_visual.png` unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses remain unchanged.

## Next action
Test `.5.11` in-game at 6+ hearts around 17:20, 17:30, 20:00 and 22:00. Confirm MiMi moves to the TV nook, faces the TV, gives routine-specific talk, then leaves for the personal corner at 22:00. Also test below 6 hearts to confirm no routine. Patch only concrete positioning/hitbox/dialogue issues from screenshots or logs.

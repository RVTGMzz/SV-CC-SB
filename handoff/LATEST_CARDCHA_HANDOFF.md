# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0645-mimi-attic-living-lore`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.10`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0645_MIMI_ATTIC_LIVING_LORE.md`

Previous visual handoffs:
- `handoff/ALPHA28_0643_MIMI_ATTIC_STARDew_REBUILD.md`
- `handoff/ALPHA28_0642_AIRSHIP_INTERIOR_STARDew_REWORK.md`

## Current verified state
- `.5.8` Airship full Stardew interior rework: CI/build/package PASS; in-game visual acceptance still pending screenshots.
- `.5.9` MiMi Attic Stardew rebuild: CI/build/package PASS; room-sized overlay removed; true `townInterior` TMX + vanilla furniture own the room.
- `.5.10` MiMi Attic Living Lore: CI/build/materialization/package/upload PASS.
- Research desk, TV nook and ChaCha corner now use layered inspect dialogue instead of one fixed line.
- Inspect dialogue can vary by friendship, time, repeated inspection and ChaCha loan state.
- Personal bed/dresser corner gained lightweight environmental storytelling.
- Inspect repetition memory is day-local only; no SaveData field or schema bump.
- Stable location remains `Cardcha_MiMiAttic`.
- 2-heart attic access and 6-heart / 17:30 secret-TV eligibility remain unchanged.
- Actual 17:30 private TV routine is still deferred.

## Verified build
- workflow run: `33860738098` SUCCESS
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.10_MiMiAtticLivingLore_TEST.zip`
- package SHA-256: `117ba6168d2d0149e2257ed419604c16dd46031b43728c3855fc1cfdd174b8e3`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate uses 160px action distance and `CollisionEdits=NONE`.
- Locked Airship exterior `airship_visual.png` unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses remain unchanged.

## Next action
Test `.5.10` MiMi Attic interactions in-game: desk repeated / 4+ / 8+ hearts, TV before and after 17:30 at 6+ hearts, ChaCha corner while ChaCha is loaned, and personal corner after 22:00. Patch only concrete hitbox/dialogue issues. After acceptance, the next larger milestone can implement the real MiMi 17:30 / 6-heart private TV routine.

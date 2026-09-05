# ALPHA28 0646C MiMi Home Routine + Portrait

## Branch
`cardcha-alpha28-0646c-mimi-home-routine-portrait`

## Build
`0.3.0-alpha.28.0.4.14.4.5.11.3`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.11.3_MiMiHomeRoutinePortrait_TEST.zip`

SHA-256:
`2eee858eb53616d1824d42e549f83c055b1c948ce1fa4939a50d12b689e31131`

CI run:
`33955959541` SUCCESS

Artifact ID:
`9966370900`

Materialized source commit:
`85819777e7d1d35bc70e82d2bbb1eeef554b71f8`

## Concrete fixes from in-game screenshots

### MiMi home movement
- 0646B only changed fixed state anchors, which made MiMi feel like a statue between schedule transitions.
- 0646C adds real lightweight in-room idle movement.
- `home`, `tv`, and `late` each own a small deterministic tile loop.
- MiMi walks between points with animated walking frames and short pauses instead of being reset to the anchor every tick.
- Movement pauses while dialogue/menu is open.
- State transitions remain stable and do not use the old collision-based ping-pong resolver.
- Runtime TEST override now remains authoritative even on a clean/pre-meetup test save, without mutating save progression.

Debug:
`cardcha_test_mimi_routine <home|tv|late|auto>`

### MiMi portrait at home
- Empty-hand interaction with MiMi anywhere in `Cardcha_MiMiAttic` is now owned by `MimiHomeService`.
- `MimiSocialService` defers all empty-hand attic talk to HomeService.
- Home talk uses the same master-derived Cardcha portrait dialogue path as Cardcha story dialogue through `TryShowCrispPortraitDialogue`.
- This prevents vanilla `NPC.checkAction()` from silently swapping the conversation back to the small native `mimi_portraits_runtime64.png` asset.
- Gifting remains native Stardew behavior.
- The attic remains a home only. It never opens MiMi's shop.
- Home talk still records the normal once-per-day talk friendship state.

New localized home lines exist in EN and VI.

## Routine canon
- 2 hearts: attic access.
- 6+ hearts: secret TV routine eligible.
- 17:30 to before 22:00: TV state.
- 22:00+: late/personal state.
- Otherwise outside work hours: home state.
- Weekday merchant/work behavior remains unchanged outside the attic.

## Forest gate inheritance from 0646B
- Gate relocation remains the reachable-side resolver targeting the open meadow immediately right of the pink blossom tree.
- `cardcha_test_gate` remains runtime-only.
- Interaction distance remains 160px.
- `CollisionEdits=NONE` remains locked.

## Locked regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Locked `airship_visual.png` SHA-256 remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route, upgrades/costs, deferred gameplay bonuses unchanged.

## Acceptance test
1. Install only `.5.11.3`.
2. `cardcha_test_attic`.
3. Run `cardcha_test_mimi_routine home`, watch for roughly 10 seconds and confirm MiMi walks around the upper home cluster.
4. Run `cardcha_test_mimi_routine tv`, confirm immediate relocation to the TV side and continued gentle movement there.
5. Run `cardcha_test_mimi_routine late`, confirm immediate relocation toward the bed/personal side and continued gentle movement there.
6. Run `cardcha_test_mimi_routine auto`.
7. Talk to MiMi empty-handed in the attic and compare portrait sharpness with normal Cardcha story dialogue.
8. Confirm repeated empty-hand talk in the attic never opens the shop.
9. Re-test normal 17:30 and 22:00 transitions at 6+ hearts.

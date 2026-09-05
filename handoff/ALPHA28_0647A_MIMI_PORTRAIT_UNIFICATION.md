# ALPHA28 0647A: MiMi Portrait Unification + Home Wander Safety

Branch:
`cardcha-alpha28-0647a-mimi-portrait-unification`

Build:
`0.3.0-alpha.28.0.4.14.4.5.12.1`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.1_MiMiPortraitUnified_TEST.zip`

Package SHA-256:
`607409ab95c156885b1f0a2c753bbeb3dfc76b31f57ad58c537e2ba62bc10673`

Verified CI:
- workflow run `33958161204`: SUCCESS
- job `101285144806`: SUCCESS
- artifact ID `9967046225`
- outer artifact digest `sha256:6d025d8a175a62717cfa4e3b3346f02e54070f638730ef3ef5e3044b309b55d3`

## Portrait contract

`assets/mimi_portraits.png` is now the single canonical on-disk MiMi portrait source.

Removed from source/package:
- `assets/mimi_portraits_runtime64.png`
- `assets/mimi_npc_portraits.png`

All Cardcha MiMi dialogue paths continue to route through the same master-derived portrait pipeline:
- Story scenes
- mystery/Town dialogue
- merchant dialogue
- social dialogue
- MiMi Attic/home dialogue
- secret TV routine dialogue

Vanilla Stardew `DialogueBox` still expects 64x64 portrait frames. Cardcha therefore creates a compatibility texture in RAM from the 128px master. This build changes that conversion from alpha/box averaging to nearest-neighbour sampling, preserving hard pixel edges and avoiding the soft/blurred look. No secondary 64px PNG is stored or packaged.

If the in-game result is still visually too soft, the next step should be a custom high-resolution portrait renderer rather than adding another portrait asset.

## MiMi home movement safety

0646C living movement is retained, with safer floor anchors so MiMi no longer starts on the upper wall/window row:
- home anchor `(10,6)`
- TV anchor `(5,9)`
- late anchor `(13,7)`

Idle pools are now open-floor clusters for each state. If a visual/furniture pass blocks an anchor or all listed idle points, HomeService resolves a nearby clear tile instead of freezing on a blocked pool entry.

`cardcha_story_status` / Home diagnostics now include:
- `RoutineState`
- `WanderTarget`
- current Actor tile/location

Runtime test command remains:
`cardcha_test_mimi_routine <home|tv|late|auto>`

## 0647 inherited room architecture

The 0647 Airship/Sky Dock room architecture pass is inherited unchanged:
- real Stardew-style walls/collision
- two-tile bottom doorways
- wider physical portal/door trigger zones
- fixed arrival positions
- vanilla furniture/depth
- no room-sized custom backdrop in the two Airship interior TMX maps

## Locked canon/regression guard

Preserved and CI validated:
- Save schema 19
- Boss Form duration 10 seconds
- Boss Energy gain scale 1/3
- 76/76 active card audit PASS
- Forest Arcane Gate canonical action distance 160px
- `CollisionEdits=NONE`
- locked `airship_visual.png` SHA-256 `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`
- Airship route/upgrade menu/costs unchanged
- deferred Airship gameplay bonuses remain disabled

## Acceptance checklist

1. Load `.5.12.1` and confirm `cardcha_version`.
2. Enter MiMi Attic with `cardcha_test_attic`.
3. Talk to MiMi and compare portrait against Town/story/merchant dialogue. It should use the same expression art and retain crisp hard edges.
4. Run `cardcha_test_mimi_routine home`, wait 10-15 seconds, and verify MiMi moves around the center/open floor instead of standing at the window.
5. Run `cardcha_story_status` and confirm `RoutineState=home`, a changing/relevant `WanderTarget`, and Actor in `Cardcha_MiMiAttic`.
6. Repeat with `tv` and `late`. MiMi should move within different room zones.
7. Return to normal scheduling with `cardcha_test_mimi_routine auto`.
8. Re-test actual 17:30 and 22:00 transitions at 6+ hearts.

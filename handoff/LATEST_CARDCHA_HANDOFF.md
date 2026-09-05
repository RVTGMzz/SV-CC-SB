# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0648a-airship-mimi-acceptance-hotfix`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.7`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0648A_AIRSHIP_MIMI_ACCEPTANCE_HOTFIX.md`

Previous handoffs:
- `handoff/ALPHA28_0648_STARDew_VISUAL_PASS1.md`
- `handoff/ALPHA28_0647E_AIRSHIP_PHYSICAL_DEPTH_REBUILD.md`
- `handoff/ALPHA28_0647D_FIXED_GATE_STATION_IDENTITY.md`
- `handoff/ALPHA28_0647C_AIRSHIP_TMX_CSV_HOTFIX.md`
- `handoff/ALPHA28_0647B_MIMI_PORTRAIT_RUNTIME_HOTFIX.md`
- `handoff/ALPHA28_0647A_MIMI_PORTRAIT_UNIFICATION.md`
- `handoff/ALPHA28_0647_AIRSHIP_ROOM_ARCHITECTURE.md`
- `handoff/ALPHA28_0646C_MIMI_HOME_ROUTINE_PORTRAIT.md`

## Current verified state
- `.5.12.7` is the screenshot-driven acceptance hotfix for 0648.
- Airship wall rows 0-7 and Sky Dock wall rows 0-8 now have continuous physical collision.
- Bottom room shell is sealed except the exact two-tile doorway: Airship `[11,12]`, Sky Dock `[14,15]`; the old third gap that let the player enter black void is removed.
- Visual floor now begins at the same row as the walkable floor, so the farmer no longer appears to walk on wall/window art.
- Four upgrade support pads are recentered to the exact runtime machine anchors; machine render is lowered to seat the sprite into its base.
- Airship/Sky Dock ambient is warmer/brighter and all four upgrade machines now have a soft always-on powered glow, including level 0.
- ChaCha Resonance has separate visual/use anchors: visual `(21,5)`, floor interaction `(21,8)`, keeping the right console from blocking access.
- `cardcha_test_attic` now turns on a runtime-only MiMi clock preview for acceptance testing without changing hearts/story: 17:20 HOME, 17:30 TV, 20:00 TV, 22:00 LATE.
- Normal MiMi TV gameplay still requires 6 hearts.
- MiMi default home anchor moved away from the window to `(9,8)` with a floor-only idle pool.
- MiMi single-source portrait remains `mimi_portraits.png`; deprecated portrait PNGs stay absent.

## Verified build
- workflow run: `33980136589` SUCCESS
- job: `101343778226` SUCCESS
- materialization commit: `9a3e306274326baa53e1279ad86193f1722f1964`
- artifact ID: `9973503051`
- outer artifact digest: `sha256:724d062543ac8db42e0903885c8b13c3a439615209a97604a03d424ded2e83c5`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.7_AirshipMiMiAcceptanceHotfix_TEST.zip`
- package SHA-256: `d6ecf532e3218cf7e28521c9fbade8b4f2a31ad152f1526835011b54b23702b2`
- compiled DLL size: `764416` bytes

## Materialized visual hashes
- `airship_deck_stardew.png`: `59b44c565074ca296269900c039234ccd09982c9a5e0ec4812af7566625642c5`
- `sky_dock_stardew.png`: `5da83b825c779a929f811ead5b1ad06b489852631774b4a23ae52a2a14f2ba6f`
- `airship_upgrade_visuals.png`: `54e685feb0e8611c69c5e07f840ad8f43282c7edb53f04ec0ffb8931ed64b861`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate action distance remains 160px and `CollisionEdits=NONE` remains locked.
- locked `airship_visual.png` SHA unchanged: `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- Airship upgrade menu/costs/levels and deferred gameplay bonuses unchanged.
- No pickup Airship furniture is reintroduced.

## Next action
Replace the whole Cardcha folder and restart SMAPI. Test Airship wall/bottom collision, machine alignment/glow and ChaCha Resonance access. Then run `cardcha_test_attic` followed by `world_settime 1720`, `1730`, `2000`, `2200` and verify MiMi transitions HOME -> TV -> TV -> LATE. If MiMi still does not move, capture `cardcha_story_status` diagnostics.

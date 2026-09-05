# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0647-airship-room-architecture`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0647_AIRSHIP_ROOM_ARCHITECTURE.md`

Previous MiMi handoff:
- `handoff/ALPHA28_0646C_MIMI_HOME_ROUTINE_PORTRAIT.md`
- `handoff/ALPHA28_0646B_MIMI_ROUTINE_GATE_FIX.md`
- `handoff/ALPHA28_0646A_MIMI_HOME_STABILITY_PORTRAIT.md`
- `handoff/ALPHA28_0646_MIMI_SECRET_TV_ROUTINE.md`
- `handoff/ALPHA28_0645_MIMI_ATTIC_LIVING_LORE.md`

Previous Airship visual handoff:
- `handoff/ALPHA28_0642_AIRSHIP_INTERIOR_STARDew_REWORK.md`

## Current verified state
- `.5.12` is the current acceptance build.
- Airship Bridge and Sky Dock interior no longer use room-sized custom backdrop PNGs in their TMX maps.
- Both rooms use vanilla `townInterior` architecture with real top/side/bottom `Buildings` collision.
- Bottom exits are narrowed to exactly two center tiles, preventing side escape into black/out-of-room space.
- Auto transitions no longer require exact marker-tile equality: Sky Dock bay uses a 3x3 trigger area and bottom doorway thresholds use the two physical doorway tiles.
- Arrival positions are fixed, so a doorway/arrival marker cannot shift as nearby collision state changes.
- Animated exit dots are removed; exit threshold visuals are static.
- Both rooms receive real vanilla Stardew furniture for native scale/collision/depth, while Cardcha machinery remains limited to small accents.
- Forest Arcane Gate still targets the reachable meadow near the right side of the pink blossom tree and keeps `CollisionEdits=NONE`.
- `.5.11.3` MiMi home portrait and living-routine fixes are inherited unchanged.

## Verified build
- workflow run: `33956304229` SUCCESS
- materialization commit: `8b5caaa0ee500e8226a1bd7e4577a7f918d2e468`
- artifact ID: `9966480177`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12_AirshipRoomArchitecture_TEST.zip`
- package SHA-256: `79ad985ed2c0da8a16b8975f9d86a0b9607294cedb2eb80f8e4d7bbb0e9e3e0a`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate action distance 160px and `CollisionEdits=NONE`.
- locked `airship_visual.png` unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses unchanged.

## Next action
In-game acceptance for `.5.12`: walk hard into every window/wall in both Cardcha Airship rooms; verify no overlap. Test both center doorways without aiming for a dot, verify no side escape into the black surround, and confirm doorway visuals stay fixed while approaching. Judge the new vanilla Stardew room language before adding any further visual polish.

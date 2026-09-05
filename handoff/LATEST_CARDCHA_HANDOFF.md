# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0647e-airship-physical-depth-rebuild`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.5`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0647E_AIRSHIP_PHYSICAL_DEPTH_REBUILD.md`

Previous handoffs:
- `handoff/ALPHA28_0647D_FIXED_GATE_STATION_IDENTITY.md`
- `handoff/ALPHA28_0647C_AIRSHIP_TMX_CSV_HOTFIX.md`
- `handoff/ALPHA28_0647B_MIMI_PORTRAIT_RUNTIME_HOTFIX.md`
- `handoff/ALPHA28_0647A_MIMI_PORTRAIT_UNIFICATION.md`
- `handoff/ALPHA28_0647_AIRSHIP_ROOM_ARCHITECTURE.md`
- `handoff/ALPHA28_0646C_MIMI_HOME_ROUTINE_PORTRAIT.md`
- `handoff/ALPHA28_0646B_MIMI_ROUTINE_GATE_FIX.md`
- `handoff/ALPHA28_0646A_MIMI_HOME_STABILITY_PORTRAIT.md`
- `handoff/ALPHA28_0646_MIMI_SECRET_TV_ROUTINE.md`
- `handoff/ALPHA28_0645_MIMI_ATTIC_LIVING_LORE.md`

## Current verified state
- `.5.12.5` is a structural Airship/Sky Dock rebuild after `.5.12.4` was rejected in game for sparse rooms, weak visual checkpoints, pickup furniture and incorrect gate/player depth.
- Airship Deck restores `airship_deck_stardew.png` as the complete 24x14 Back layer and uses Buildings tiles for real helm/console/upgrade/ChaCha collision.
- Sky Dock restores `sky_dock_stardew.png` as the complete 30x18 Back layer and uses Buildings tiles for route-console/boarding-side/service collision.
- Four dynamic upgrade machines remain level-aware and render at 112x112 with physical footprints larger than their sprites.
- Upgrade interaction is 176px and helm interaction is 160px so visible machines can be used from their front edge without remembering hidden checkpoint coordinates.
- Airship/Sky Dock runtime furniture placement is removed. Old movable tables/plant and the pickup/sellable `Viên Pha Lê Nhỏ` are no longer seeded.
- Forest gate is no longer drawn from `RenderedWorld`. `AirshipGateDepthPatch` draws it immediately before or after the local Farmer based on whether the farmer is in front of or behind the gate threshold.
- Forest test/return landing now prefers clear tiles 3-4 rows below the gate instead of spawning inside the arch.
- Deterministic gate placement from 0647D remains unchanged at Farm-warp offset `(-23,+10)` and action distance remains 160px.
- Route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`; no MiMi-attic Airship routing exists.
- 0647C valid TMX CSV guarantees remain enforced.
- MiMi portrait/home/routine regressions remain fixed.

## Verified build
- workflow run: `33972296434` SUCCESS
- job: `101322832825` SUCCESS
- materialization commit: `dc8ff00b222c172e22e03bca38e6d890e4ecdb8a`
- artifact ID: `9971284329`
- outer artifact digest: `sha256:596dc982958c5db7ea28d152248f8f0268ac549ee34f439640c86a909ff24a31`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.5_AirshipPhysicalDepthRebuild_TEST.zip`
- package SHA-256: `22eeeac5b28f745d20ba9e6850ad460e6825c9fdec67eef8f3f66f0e62d7db93`
- compiled DLL size in package: 762,368 bytes

## Independent package verification
- Airship TMX is 24x14 with exactly 336 tokens/layer; Back is 336/336 Cardcha backdrop GIDs.
- Sky Dock TMX is 30x18 with exactly 540 tokens/layer; Back is 540/540 Cardcha backdrop GIDs.
- Key helm/four-upgrade/route-console anchors are nonzero on Buildings while central travel/boarding/exit lanes are zero/unblocked.
- `airship_deck_stardew.png`, `sky_dock_stardew.png`, `airship_upgrade_visuals.png` and locked `airship_visual.png` are packaged.
- locked `airship_visual.png` SHA remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Deprecated MiMi portrait files remain absent.

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate action distance 160px and Forest map `CollisionEdits=NONE` contract remains intact.
- Airship route, upgrade menu/costs and deferred gameplay bonuses unchanged.

## Next action
Install `.5.12.5` by replacing the whole Cardcha folder and fully restart SMAPI. Test the Forest gate front/behind depth, then enter Sky Dock and Airship Deck. Confirm restored Airship architecture, collision-backed machines/consoles, clear central lanes, usable visible stations and absence of pickup Airship décor.

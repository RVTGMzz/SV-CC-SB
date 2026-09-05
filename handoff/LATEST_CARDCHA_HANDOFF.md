# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0647c-airship-tmx-csv-hotfix`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.3`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0647C_AIRSHIP_TMX_CSV_HOTFIX.md`

Previous handoffs:
- `handoff/ALPHA28_0647B_MIMI_PORTRAIT_RUNTIME_HOTFIX.md`
- `handoff/ALPHA28_0647A_MIMI_PORTRAIT_UNIFICATION.md`
- `handoff/ALPHA28_0647_AIRSHIP_ROOM_ARCHITECTURE.md`
- `handoff/ALPHA28_0646C_MIMI_HOME_ROUTINE_PORTRAIT.md`
- `handoff/ALPHA28_0646B_MIMI_ROUTINE_GATE_FIX.md`
- `handoff/ALPHA28_0646A_MIMI_HOME_STABILITY_PORTRAIT.md`
- `handoff/ALPHA28_0646_MIMI_SECRET_TV_ROUTINE.md`
- `handoff/ALPHA28_0645_MIMI_ATTIC_LIVING_LORE.md`

## Current verified state
- `.5.12.3` is the Airship/Sky Dock TMX CSV parser hotfix acceptance build.
- Root cause of the reported Airship/Sky Dock load crash was a terminal comma emitted by 0647 `csv_layer()`, creating an empty final token for TMXTile's `UInt32.Parse` decoder.
- `tools/alpha28_0647_airship_room_architecture.py` is fixed at the source so future reruns do not reintroduce the malformed CSV.
- `airship_deck.tmx` has exactly 336 UInt32 tokens per layer and no terminal comma.
- `sky_dock_interior.tmx` has exactly 540 UInt32 tokens per layer and no terminal comma.
- CI now validates every TMX CSV token, exact `width * height` count, UInt32 range, and absence of empty/terminal tokens.
- 0647 Airship room architecture, collision, route logic, furniture/decor behavior and upgrade logic are unchanged.
- 0647B MiMi portrait runtime fix remains intact and byte-audited after compile.

## Verified build
- workflow run: `33960369762` SUCCESS
- job: `101291101925` SUCCESS
- materialization commit: `94b334e2b1ce69eba0c3490caad878c7d405885d`
- artifact ID: `9967741016`
- outer artifact digest: `sha256:c46c808b6e80a4200455c0b6215908b90aebad52f14f296529c63e384f3ff529`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.3_AirshipTmxCsvHotfix_TEST.zip`
- package SHA-256: `1983dcc07760f76cba12f9ed1c120205c3a28096082b094ec44a41208a98355c`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate action distance 160px and `CollisionEdits=NONE`.
- locked `airship_visual.png` unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses unchanged.

## Next action
Install `.5.12.3` by replacing the previous Cardcha mod folder and fully restarting SMAPI. Verify the log no longer shows `FormatException` / `UInt32.Parse` failures for `Maps/Cardcha_AirshipDeck.vi` and `Maps/Cardcha_SkyDockInterior.vi`, then enter both rooms in game and report any visual/collision issue separately.

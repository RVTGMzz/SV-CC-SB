# ALPHA28_0647C Airship TMX CSV Hotfix

Branch:
`cardcha-alpha28-0647c-airship-tmx-csv-hotfix`

Build:
`0.3.0-alpha.28.0.4.14.4.5.12.3`

## Root cause
The 0647 Airship room generator emitted CSV tile layers with a terminal comma. TMXTile splits the full CSV body on commas and parses every token with `UInt32.Parse`; the terminal delimiter created one final empty token and caused `FormatException` while loading both `assets/airship_deck.tmx` and `assets/sky_dock_interior.tmx`.

Faulty generator code:
`return '\n'.join(','.join(str(v) for v in row) + ',' for row in rows)`

## Fix
- Patched `tools/alpha28_0647_airship_room_architecture.py` so `csv_layer()` uses commas between rows but never emits a terminal comma.
- Normalized every `<data encoding="csv">` block in:
  - `src/Cardcha/assets/airship_deck.tmx`
  - `src/Cardcha/assets/sky_dock_interior.tmx`
- Added fail-closed CI validation that reproduces TMXTile's essential parse contract:
  - every CSV token must be non-empty;
  - every token must parse as decimal UInt32;
  - each layer must contain exactly `width * height` tokens;
  - no layer body may end with a comma.

## Independent artifact verification
- `airship_deck.tmx`: Back/Buildings/Front each `336/336` tokens, no empty token, no terminal comma.
- `sky_dock_interior.tmx`: Back/Buildings/Front each `540/540` tokens, no empty token, no terminal comma.
- manifest version: `0.3.0-alpha.28.0.4.14.4.5.12.3`.
- compiled `Cardcha.dll` present.
- 0647B portrait runtime fix remains intact: no obsolete `mimi_portraits_runtime64.png` or `mimi_npc_portraits.png` packaged; canonical `mimi_portraits.png` remains present.

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
- 0647 room architecture and 0647B MiMi portrait single-owner pipeline are inherited unchanged.

## Next action
Install `.5.12.3` by replacing the Cardcha mod folder and fully restart SMAPI. Load a save and verify there are no `FormatException` / `UInt32.Parse` errors for `Maps/Cardcha_AirshipDeck.vi` or `Maps/Cardcha_SkyDockInterior.vi`. Then test entering the Airship deck and Sky Dock interior normally.

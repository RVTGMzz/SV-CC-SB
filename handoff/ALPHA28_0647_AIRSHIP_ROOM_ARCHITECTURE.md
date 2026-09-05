# ALPHA28 0647 Airship Room Architecture

## Branch
`cardcha-alpha28-0647-airship-room-architecture`

## Build
`0.3.0-alpha.28.0.4.14.4.5.12`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12_AirshipRoomArchitecture_TEST.zip`

SHA-256:
`79ad985ed2c0da8a16b8975f9d86a0b9607294cedb2eb80f8e4d7bbb0e9e3e0a`

CI run:
`33956304229` SUCCESS

Artifact ID:
`9966480177`

Materialized source commit:
`8b5caaa0ee500e8226a1bd7e4577a7f918d2e468`

## Why this pass exists
In-game screenshots showed the old Airship Bridge and Sky Dock interior behaving like painted background images rather than real Stardew rooms:
- farmer could walk visually onto windows/walls because the room-sized PNG lived only on `Back` and `Buildings` was mostly empty;
- doorway/portal feedback looked like it shifted as the farmer approached;
- auto transitions required the exact marker tile;
- bottom openings were wide enough to allow walking around the intended exit and into black/out-of-room space;
- both rooms had a custom flat illustration style that did not read like native Stardew Valley interiors.

## 0647 architecture rebuild
### Airship Bridge
`src/Cardcha/assets/airship_deck.tmx`
- removes the room-sized `airship_deck_stardew.png` tileset from the TMX;
- uses only vanilla `townInterior` tiles for walls, floor, trim, side walls and doorway shell;
- top wall has real `Buildings` collision;
- left/right walls have real `Buildings` collision;
- bottom wall is closed except for one two-tile center doorway;
- a short two-tile threshold continues into the black surround in normal Stardew interior fashion;
- old backdrop PNG remains packaged only as an unused legacy asset for now.

### Sky Dock interior
`src/Cardcha/assets/sky_dock_interior.tmx`
- removes the room-sized `sky_dock_stardew.png` tileset from the TMX;
- rebuilt from vanilla `townInterior` tiles;
- real top/side/bottom collision;
- only a two-tile center exit opening;
- no Back-only fake walls/windows.

## Vanilla furniture pass
`AirshipFoundationService` now adds real vanilla furniture to both Cardcha rooms at runtime.
These pieces provide native scale, shadow, draw depth and collision while Cardcha-specific machinery remains small accent art.

Deck examples:
- vanilla wall windows;
- service shelf / storage;
- warm lamps;
- helm rug;
- two work tables with small crystal/plant props.

Sky Dock examples:
- vanilla windows;
- bookcase/storage;
- lamps;
- route table;
- rug + couch/service waiting corner;
- central arrival/exit lane remains clear.

Marker key:
`Ronvotri.Cardcha/AirshipInteriorDecor`

Decor version:
`alpha.28.0.4.14.4.5.12`

## Door and transition fix
The old auto-transition logic used exact tile equality.
0647 changes this to broad physical zones:
- Sky Dock boarding bay: 3x3 tile trigger around the bay anchor;
- bottom exits: the actual two center doorway tiles trigger the transition as soon as the farmer reaches the threshold;
- action interaction distance for Cardcha-owned boarding is raised to 160px;
- arrival anchors inside both rooms are fixed instead of re-running a nearest-clear resolver each time.

Result: the player does not need to hit one tiny dot and the visible doorway cannot appear to relocate based on nearby state.

## Static doorway visuals
`AirshipInteriorStardewRenderer`
- removes the pulsing floor-dot exit marker;
- removes fake animated deck-window star movement;
- uses a fixed two-tile threshold line for exits;
- retains only small Cardcha helm/upgrade/console accents.

## Forest gate contract
The external Forest Arcane Gate changes from 0646B remain inherited:
- reachable-side placement targeted near the right side of the pink blossom tree;
- test command remains `cardcha_test_gate`;
- action distance remains locked to 160px by the relocation patch;
- `CollisionEdits=NONE` remains unchanged for the Forest map.

## MiMi 0646C inheritance
0647 is based on the materialized `.5.11.3` branch and preserves:
- master-derived Cardcha portrait path for empty-hand MiMi attic dialogue;
- no shop inside MiMi's attic;
- living home/TV/late idle movement;
- `cardcha_test_mimi_routine <home|tv|late|auto>`.

## Locked regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- locked `airship_visual.png` SHA-256 unchanged: `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route logic, upgrade levels/costs and deferred gameplay bonuses unchanged.

## Acceptance checklist
1. `cardcha_test_airship` enters the Airship Bridge.
2. Walk into every top/side wall and window area. Farmer must stop at the real wall and never overlap the wall/window art.
3. Walk around the lower-left/lower-right edges. Farmer must not slip into the black surround.
4. Walk through the center two-tile exit without aiming for a tiny marker. It should transition naturally.
5. In Sky Dock interior, test the same wall/bottom collision.
6. Approach the boarding bay from adjacent tiles. It should transition without exact-dot positioning.
7. Watch the doorway marker while moving nearby. Its geometry must remain fixed.
8. Judge both rooms for vanilla Stardew scale and furniture language before any further Cardcha-specific visual embellishment.

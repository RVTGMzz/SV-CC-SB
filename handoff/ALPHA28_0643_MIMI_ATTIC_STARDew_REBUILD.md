# Alpha28.0.4.14.4.5.9 MiMi Attic Stardew Rebuild

## Canonical branch
`cardcha-alpha28-0643-mimi-attic-stardew-rebuild`

## Build materialization commit
`004121745c8c93f9ae3447be4d8f7508d0ed05ab`

Materialization commit message:
`chore: materialize alpha28.0.4.14.4.5.9 MiMi Attic Stardew rebuild [skip ci]`

## CI
Verified workflow run: `33855697624`
Conclusion: **SUCCESS**

Generation, visual/gameplay validation, compile, materialization, packaging and artifact upload all passed.

## TEST package
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.9_MiMiAtticStardewRebuild_TEST.zip`

Verified package SHA-256:
`574639628314b9c249b18640f7caa77007b0f1a95be67ae9ca262f382323d551`

GitHub Actions artifact:
- artifact ID: `9930086933`
- artifact name: `cardcha-alpha28-0643-mimi-attic-stardew-rebuild`
- artifact archive digest: `sha256:c4c71e0c56f4c5648d43c4e544519a8564b795d1816b812a13a6854cca9ef094`

## What changed
MiMi Attic now uses its actual Stardew map + vanilla furniture presentation instead of a room-sized concept-art overlay.

- stable location remains `Cardcha_MiMiAttic`;
- `mimi_attic.tmx` remains 22x14 and uses vanilla `townInterior`;
- all five locked zones remain: landing, research, personal/bed, TV secret nook, ChaCha/upgrade corner;
- runtime vanilla furniture still provides object scale, collision, shadows and draw order;
- obsolete `mimi_attic_room_frame.png` was removed;
- `RoomFrameSpritePath` / `DrawRoomFrame` runtime overlay code was removed;
- inspect points remain for desk, TV and ChaCha corner;
- 2-heart attic access remains unchanged;
- secret TV eligibility remains 6 hearts / 17:30;
- no new MiMi gameplay or event logic was enabled in this visual rebuild.

## Locked gameplay/canon preserved
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate remains 160px action distance with `CollisionEdits=NONE`.
- locked Airship exterior `airship_visual.png` hash remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- `.5.8` Airship Stardew interior assets remain present.
- Airship routes, upgrade menu/costs and deferred gameplay bonuses remain unchanged.

## Immediate next-session checklist
1. Install `.5.9` TEST over the previous Cardcha test build.
2. Enter `Cardcha_MiMiAttic` using the existing attic/test-access flow.
3. Capture one full-room screenshot plus close screenshots of research, bed, TV and ChaCha zones.
4. Judge whether the room now reads as a genuine Stardew interior: tile language, furniture depth, empty-space balance, cozy/secretive MiMi personality and farmer occlusion.
5. Patch only concrete in-game visual/layout issues from those screenshots.
6. Also re-test `.5.8` Airship Sky Dock / Bridge and Forest gate when convenient; their prior visual acceptance is still pending.

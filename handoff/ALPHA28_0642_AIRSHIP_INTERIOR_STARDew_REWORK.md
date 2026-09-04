# Alpha28.0.4.14.4.5.8 Airship Interior Full Stardew Rework

## Canonical branch
`cardcha-alpha28-0642-airship-interior-stardew-rework`

## Current branch head
`b0fa64450dcd0e3df786c9afcbccb6d93240e5a6`

Latest materialization commit message:
`chore: materialize alpha28.0.4.14.4.5.8 Airship Stardew interior [skip ci]`

## CI
Latest verified workflow run: `33853178719`
Conclusion: SUCCESS

Build, asset generation, validation, compile, materialization, packaging and artifact upload all passed.

## TEST package
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.8_AirshipInteriorStardewRework_TEST.zip`

Latest verified SHA-256:
`286216b031fd601921ef3e58ac070b2f532dc30d3c169c71791a3b54495bfcc2`

## Materialized visual assets
- `src/Cardcha/assets/airship_deck_stardew.png`
- `src/Cardcha/assets/sky_dock_stardew.png`
- `src/Cardcha/assets/airship_upgrade_visuals.png`
- updated `src/Cardcha/assets/airship_deck.tmx`
- updated `src/Cardcha/assets/sky_dock_interior.tmx`
- `src/Cardcha/Patches/AirshipInteriorStardewRenderer.cs`

## Visual direction locked by user feedback
The Airship interior should look like a real Stardew Valley space, not soft concept art or flat procedural overlay.

Required qualities:
- clear dark pixel outlines / stroke;
- blocky Stardew-style shading instead of soft airbrush gradients;
- warm wood + brass construction;
- violet/cyan magic used as accents, not giant translucent overlays;
- visible depth through architecture and object masses without foreground bars crossing the farmer;
- Sky Dock should feel occupied and functional, not empty;
- Helm, route console and four upgrade systems must read as different gameplay objects;
- upgrade systems remain levels 0 through 3 and preserve existing upgrade logic.

## Gameplay/canon preserved
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate uses 160px action distance through current relocation patch and `CollisionEdits=NONE`.
- Locked exterior `src/Cardcha/assets/airship_visual.png` remains unchanged with SHA256 `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Travel route, upgrade menu and costs remain unchanged.
- Deferred Airship gameplay bonuses are still NOT enabled.

## Previous adjacent work to remember
### ChaCha
- `cardcha_max_all` maxes all 76 active cards and all four ChaCha skills for testing.
- Support Cast feedback was strengthened in `.5.6.1.3` with visible pulse/icons/text so the player can tell when ChaCha buffs fire.
- Permanent ChaCha energy bar HUD was removed earlier.

### Forest Gate
- User repeatedly reported old gate placement did not visibly move. `.5.6.1.3` added a hard relocation patch based on the actual rendered gate location. Re-test from the current `.5.8` build before touching it again.

### MiMi Attic
A local-only `.5.7` visual experiment exists outside this branch. It used a richer room-frame concept and was NOT merged into `.5.8` because user requested Airship work next. Do not assume MiMi visual rebuild is present in this branch. Future milestone should materialize a real Stardew-style MiMi Attic rebuild using actual tile/prop assets rather than a flat concept-room background.

## Immediate next-session checklist
1. User installs and screenshots `.5.8` Sky Dock and Airship Bridge.
2. Judge stroke, pixel language, empty-space balance, readability and player occlusion from screenshots.
3. Patch only concrete visual problems found in-game.
4. After Airship approval, return to MiMi Attic visual rebuild and materialize it properly in repo/CI.

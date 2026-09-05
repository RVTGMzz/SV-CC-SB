# Cardcha alpha28 0647E Airship Physical Depth Rebuild

## Canonical branch
`cardcha-alpha28-0647e-airship-physical-depth-rebuild`

## Build
- Version: `0.3.0-alpha.28.0.4.14.4.5.12.5`
- Package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.5_AirshipPhysicalDepthRebuild_TEST.zip`
- Package SHA-256: `22eeeac5b28f745d20ba9e6850ad460e6825c9fdec67eef8f3f66f0e62d7db93`
- Workflow run: `33972296434` SUCCESS
- Job: `101322832825` SUCCESS
- Artifact ID: `9971284329`
- Outer artifact digest: `sha256:596dc982958c5db7ea28d152248f8f0268ac549ee34f439640c86a909ff24a31`
- Materialization commit: `dc8ff00b222c172e22e03bca38e6d890e4ecdb8a`

## Why 0647E exists
0647D was rejected in game because the Airship/Sky Dock had become sparse vanilla wood rooms, runtime furniture could overlap the farmer, the small decorative crystal was a normal pickup/sellable furniture item, machine checkpoints were visually weak, and the Forest Arcane Gate was painted after the farmer so it could cover the player incorrectly.

0647E is a structural rebuild, not another cosmetic overlay patch.

## Airship Deck architecture
- `assets/airship_deck_stardew.png` is restored as the complete 24x14 map Back layer.
- The room no longer depends on vanilla furniture to create its identity.
- Helm/navigation dais, side bridge consoles, all four upgrade-machine footprints, ChaCha alcove, outer shell and borders are represented on the TMX `Buildings` layer for real collision.
- Central approach/exit lane remains open at x=12 through the room.
- Four upgrade stations remain dynamic by level through `airship_upgrade_visuals.png` and now render at 112x112, with larger physical footprints than the sprite.
- Interaction radius is widened to 176px for upgrade machines and 160px for helm so the player interacts from the visible front of the machine instead of memorizing a hidden checkpoint.

### Physical machine anchors
- Engine: `(5,9)`
- Navigation: `(18,9)`
- Hull: `(8,10)`
- Reactor: `(15,10)`
- Helm: `(12,4)`
- ChaCha alcove: around `(19,5)`

## Sky Dock architecture
- `assets/sky_dock_stardew.png` is restored as the complete 30x18 map Back layer.
- Route console, boarding aperture side posts, service cabinets, shell and borders have real Buildings collision.
- Boarding center at `(24,7)` and the bottom exit corridor around x=15 remain walkable.
- Route/bay interaction radius is widened to 176px.
- Sky Dock no longer uses home-style movable furniture.

## Pickup-prop fix
`EnsureDeckVanillaFurniture()` and `EnsureSkyDockVanillaFurniture()` now clear old runtime furniture and intentionally add none.

This removes the old pickup/sellable `Viên Pha Lê Nhỏ` and other movable table/plant/furniture props from Cardcha-owned Airship rooms. All identity is owned by the map/backdrop plus Cardcha dynamic machinery.

## Forest Arcane Gate depth fix
The gate is no longer drawn from `RenderedWorld`, which always painted it over the farmer.

New patch:
`src/Cardcha/Patches/AirshipGateDepthPatch.cs`

It wraps the local `Farmer.draw(SpriteBatch)` call:
- farmer in front/below gate threshold -> gate is drawn before farmer;
- farmer behind/above gate threshold -> gate is drawn after farmer.

The gate still uses one deterministic placement owner in `ResolveSkyDockTile()` and does not edit Forest collision/pathing.

Exterior test/return warp now uses `ResolveForestGateLandingTile()` and prefers clear tiles 3-4 rows below the gate instead of spawning the player inside the arch artwork.

## Independent package verification
Verified after downloading the actual CI artifact:
- manifest version is `.5.12.5`;
- compiled `Cardcha.dll` exists, size 762,368 bytes;
- `airship_deck.tmx`: 24x14, exactly 336 UInt32 tokens on every layer;
- `sky_dock_interior.tmx`: 30x18, exactly 540 UInt32 tokens on every layer;
- both Back layers are entirely Cardcha custom backdrop GIDs (`>=4096`);
- deck machine/helm anchors have Buildings collision;
- central deck lane remains zero/unblocked on Buildings;
- Dock route console has collision while boarding/exit lanes remain open;
- `airship_deck_stardew.png`, `sky_dock_stardew.png`, `airship_upgrade_visuals.png` are packaged;
- locked `airship_visual.png` SHA remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`;
- deprecated MiMi portrait assets remain absent.

## Locked gameplay/canon preserved
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active-card audit PASS.
- Forest Arcane Gate action distance 160px.
- Forest `CollisionEdits=NONE` contract remains: 0647E only changes gate render depth, not Forest map collision/pathing.
- Airship route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- Airship upgrade costs/levels and deferred gameplay bonuses unchanged.
- MiMi attic/routine/portrait work remains intact.

## Acceptance test
Install `.5.12.5` by replacing the whole Cardcha folder and fully restart SMAPI.

1. `cardcha_version`
2. `cardcha_test_gate`
   - walk in front of the gate: farmer must render in front;
   - move behind/above the gate: arch may correctly cover the farmer;
   - gate position must remain fixed.
3. Enter Sky Dock and Airship Deck normally.
   - architecture should be the restored Cardcha Airship/Sky Dock, not an empty vanilla wood room;
   - route console and four upgrade machines should read visually without memorizing hidden checkpoint coordinates;
   - walking into physical machine/console footprints must be blocked;
   - central passage/boarding/exit lanes must remain usable.
4. Confirm there is no pickup/sellable small crystal or other Airship décor furniture.

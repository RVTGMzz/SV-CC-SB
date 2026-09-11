# Alpha 28 0693 — Airship Interior Density Rebuild

## Source of truth
- Branch: `cardcha-alpha28-0693-airship-interior-density-rebuild`
- Parent: `cardcha-alpha28-0692-airship-rgba-gate-restore` @ `18eef43802d9261b287fab06258daa78526940a5`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.60`
- Materialized source head: `e235e33826dddbf158837d3f5cdbc6af505136b6`
- Materialized tree: `8aac8966fa07e7fd3d3a04e144b181628fb42d13`
- Authoritative successful workflow run: `34631829934`
- Artifact ID: `10275959178`
- Artifact bundle digest: `sha256:1d8fd9705d76e8f3a9d9427cc0e8650b7cc053131c34d6281c6fa1bcdd030130`
- Verified inner TEST ZIP SHA256: `7c7e572bec7ba682a91af519482922e6ec9cb80677ae1d731002fd83d2d0c649`

## Trigger
Ron tested the Airship rooms and reported that the approved concept felt rich, but the actual rooms still read as almost empty. The issue was structural: old runtime decor was removed for rendering-depth safety, while only a small subset of replacements had been migrated into TMX.

## 0693 change
This pass restores room-level composition as map-native art instead of turning the old runtime physical renderer back on.

### Sky Dock
- dense departures/service board cluster;
- substantial harbor desk / route service area;
- waiting nook with seating, lamp, plants and side table;
- luggage/boarding cluster;
- existing 0692 authored boarding gate retained;
- center x=14..16 arrival/exit spine remains open.

### Airship Deck
- existing Observation Window and Navigation Console remain hero props;
- bookshelf/work library on left wall;
- telescope observation corner on right wall;
- tea cart and gramophone corner props;
- central Cardcha rug and extra plants/clock detail;
- all four upgrade sockets and lower doorway remain reachable.

## Rendering contract
- New physical density art is generated directly at full map-native resolution: Dock 480x288 and Deck 384x224.
- No tiny source sprite is enlarged to fake detail.
- Physical art is owned by TMX `BackDecor` + native collision.
- `DrawDeckStardewDecor()` / `DrawDockStardewDecor()` remain unused; they are not re-enabled.
- Existing 0690 window/console moving pixels remain VFX-only.
- Existing 0692 exterior gate farmer-depth fix is frozen.
- Density textures preserve the 0692 runtime-load fix by using flat root-level RGBA PNG paths.

## Gameplay anchors protected
CI explicitly verifies that decor collision does not block:
- Sky Dock route console `(7,7)`;
- boarding bay `(23,8)`;
- Lost & Found `(5,11)`;
- arrival / lower exit `(15,14)` and `(15,16)`;
- central Sky Dock spine x=14..16;
- Deck helm `(12,6)`;
- Deck exit `(12,12)`;
- all four upgrade sockets `(4,8)`, `(19,8)`, `(7,11)`, `(16,11)`.

## Validation
Authoritative run `34631829934` completed successfully.

PASS:
- native-resolution dense asset generator;
- flat RGBA runtime texture materializer;
- Airship Deck + Sky Dock TMX integration;
- protected gameplay-anchor clear pass;
- repository rendering-depth contract;
- 0693 density/map/collision validator;
- 0692 exterior gate/runtime freeze;
- inherited Boss/Region freeze;
- SMAPI build environment;
- `dotnet build`;
- source/handoff materialization;
- TEST package audit;
- artifact upload.

The downloaded artifact was independently unpacked after CI. The inner TEST ZIP was re-audited:
- manifest version = `0.3.0-alpha.28.0.4.14.4.5.12.60`;
- `Cardcha.dll` PE header valid, 1,021,440 bytes;
- `airship_0693_sky_dock_density.png` = 480x288 RGBA;
- `airship_0693_deck_density.png` = 384x224 RGBA;
- Sky Dock TMX points to `airship_0693_sky_dock_density.png`;
- Deck TMX points to `airship_0693_deck_density.png`;
- both maps carry the 0693 flat-RGBA texture contract;
- independently computed inner ZIP SHA256 matches the CI `.sha256` file exactly.

## TEST package
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.60_0693_AirshipInterior_DensityRebuild_TEST.zip`

SHA256:
`7c7e572bec7ba682a91af519482922e6ec9cb80677ae1d731002fd83d2d0c649`

## Acceptance
Repository / CI / compile / package validation: **PASS**.

In-game visual acceptance remains **PENDING** until Ron tests the 0693 TEST package. Do not claim that the concept-to-game visual gap is solved until Ron reports the actual in-game result.

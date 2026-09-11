# Alpha 28 0693 — Airship Interior Density Rebuild

## Source of truth
- Branch: `cardcha-alpha28-0693-airship-interior-density-rebuild`
- Parent: `cardcha-alpha28-0692-airship-rgba-gate-restore` @ `18eef43802d9261b287fab06258daa78526940a5`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.60`

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

## Acceptance
CI/compile/package validation is required. In-game visual acceptance remains PENDING until Ron tests the 0693 TEST package.

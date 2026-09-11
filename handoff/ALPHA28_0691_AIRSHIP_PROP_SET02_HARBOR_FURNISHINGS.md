# Alpha 28 0691 — Airship Prop Set 02 / Harbor Furnishings Integration

## Source of truth
- Current implementation branch: `cardcha-alpha28-0691-airship-prop-set02-harbor-furnishings`
- Parent source-of-truth: `cardcha-alpha28-0690-airship-interior-visual-rebuild` @ `ceec814e76e3f79d1d34259a532e354a2c731362`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.58`
- Materialized source head: `1dbaeb6e432fe27ba7a40fb00978df68e1112480`
- Authoritative successful workflow run: `34619719276`
- Artifact ID: `10272096937`
- Artifact bundle digest: `sha256:63c1baf622a29fec2d66e25ca1a442597b4cf6a7e5ae40369085f202f59e4a89`
- Verified inner TEST ZIP SHA256: `87aa1f220aac0ff1d54feb402032e82ea56be9bc55975fab2aaef3d625543ca2`
- 0690 and 0691 in-game visual acceptance remain pending.

## Purpose
Extend the approved 0690 Airship language with a restrained, map-native Sky Dock furnishing pass. The goal is stronger harbor/station identity without cluttering the central route or reintroducing vanilla furniture.

## 0691 Set 02 — integrated
- Departures Schedule Board: 96x64, left/service information zone.
- Waiting Bench: 96x48, lower-left waiting zone.
- Luggage Cart: 64x64, lower-right boarding/luggage zone.

Asset library:
`src/Cardcha/assets/airship_props/set02_harbor/`

All three props are authored at native production resolution. No tiny draft is upscaled.

## Rendering contract
- All Set 02 physical art is owned by `sky_dock_interior.tmx`.
- 0691 adds no new runtime visual overlay and no new physical `RenderedWorld` drawing.
- Existing 0690 Observation Window / Navigation Console overlay behavior is frozen.
- Airship Deck physical map is frozen for this pass.
- Boss and Region content inherited from 0690 is frozen by CI.
- Repository render-depth contract remains green and `Airship.physicalAllowed` remains false.

## Composition
- Departures information reinforces the left/service side.
- Waiting bench creates a readable passenger nook without entering the center lane.
- Luggage cart reinforces the right/boarding side.
- Center x=14..16 arrival/exit spine remains free of Set 02 art.
- Existing route interaction, boarding bay and lower exit anchors remain reachable.

## Validation
Authoritative run `34619719276` completed successfully.

PASS:
- 0691 native-resolution asset materializer
- 0691 Sky Dock TMX integration
- repository rendering-depth contract
- 0691 map/asset/collision validator
- inherited 0690 Airship Deck/hero overlay freeze
- inherited Boss/Region freeze
- SMAPI compile
- source + handoff materialization
- TEST package audit
- artifact upload

The downloaded artifact was independently unpacked after CI. The inner TEST ZIP was re-audited:
- manifest version = `0.3.0-alpha.28.0.4.14.4.5.12.58`
- `Cardcha.dll` PE header valid, 1,021,440 bytes
- Set 02 PNG sizes verified: 96x64 / 96x48 / 64x64
- Sky Dock Set 02 GIDs verified: 5500 / 5600 / 5700
- independently computed inner ZIP SHA256 matches the CI `.sha256` file exactly

## TEST package
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.58_0691_AirshipPropSet02_HarborFurnishings_TEST.zip`

SHA256:
`87aa1f220aac0ff1d54feb402032e82ea56be9bc55975fab2aaef3d625543ca2`

## Acceptance state
Repository/build/package validation: **PASS**.

In-game visual acceptance: **PENDING** until Ron tests it. Do not claim that the Airship visual direction is accepted in-game before Ron reports that result.

## Continuation
Use this branch as the next source-of-truth.

Do not add more Harbor props merely to fill space. The next Airship step should be driven by Ron's eventual in-game visual read:
- if composition reads well, keep Set 02 restrained and continue to the next planned system/content slice;
- if a visual problem is found, make a targeted 0692 Airship acceptance/polish pass without reintroducing post-world physical furniture.

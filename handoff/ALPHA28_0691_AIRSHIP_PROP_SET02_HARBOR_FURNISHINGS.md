# Alpha 28 0691 — Airship Prop Set 02 / Harbor Furnishings Integration

## Source of truth
- Current implementation branch: `cardcha-alpha28-0691-airship-prop-set02-harbor-furnishings`
- Parent source-of-truth: `cardcha-alpha28-0690-airship-interior-visual-rebuild` @ `ceec814e76e3f79d1d34259a532e354a2c731362`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.58`
- 0690 in-game visual acceptance remains pending.

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

## Composition
- Departures information reinforces the left/service side.
- Waiting bench creates a readable passenger nook without entering the center lane.
- Luggage cart reinforces the right/boarding side.
- Center x=14..16 arrival/exit spine remains free of Set 02 art.
- Existing route interaction, boarding bay and lower exit anchors remain reachable.

## Acceptance state
Repository validation, compile and package status must be taken from the completed 0691 GitHub Actions run.
In-game visual acceptance is pending Ron's later test. Do not claim visual acceptance until Ron reports it.

## Continuation
After CI success, record the materialized source head, workflow run, artifact ID, verified inner TEST ZIP SHA256, and keep the real TEST ZIP as the handoff package.

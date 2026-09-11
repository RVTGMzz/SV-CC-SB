# Alpha 28 0692 — Airship RGBA + Gate Restore Hotfix

## Source of truth
- Branch: `cardcha-alpha28-0692-airship-rgba-gate-restore`
- Parent: `cardcha-alpha28-0691-airship-prop-set02-harbor-furnishings` @ `91b9166e915f0b50a3dd23b0cb5e8fb888191974`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.59`

## Trigger
Ron tested 0691 in-game and reported a visual regression:
- the authored outdoor boarding gate was missing;
- the new Airship/Sky Dock physical prop group was largely absent even though the assets were present in the package;
- the room therefore fell back visually to sparse inherited/procedural elements.

## Root causes addressed
1. 0690/0691 TMX prop PNGs were left as indexed/palette PNGs on the production path. 0692 normalizes every physical Airship TMX prop to true RGBA and points TMX at flat, same-directory production copies.
2. `AirshipGateDepthPatch` suppresses legacy `DrawSkyDock()` by design, but the valid farmer-depth draw path also called `DrawSkyDock()`. 0692 introduces `DrawSkyDockCore()`; the Harmony-blocked wrapper stays legacy-only while farmer-depth rendering calls the unpatched core directly.

## Visual design
No visual redesign. The approved `boarding_gate_arch.png` remains the gate design. No old gate is restored.

## Rendering contract
- Interior physical props remain TMX-owned.
- Existing 0690 window/console motion remains VFX-only.
- No new physical `RenderedWorld` furniture is introduced.
- Exterior gate stays farmer-depth injected via the existing Harmony contract.

## Acceptance
CI/build/package status is determined by the 0692 workflow.
In-game visual acceptance remains PENDING until Ron tests the resulting TEST package.

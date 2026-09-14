# Cardcha 0696D3 Room Integration Feedback

Date: 2026-09-14
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Source: Ron in-game visual test of `.69`.

## Verdict

0696D2 Observation Window itself is usable, but the room/map integration is not accepted yet.

## Required fixes

1. Old upgrade pedestals/stations look visually fake and detached from the room.
   - Rework placement, scale, depth/shadow/footing and spatial integration.
   - They should read as functional machinery, not pasted decoration.
   - Add real collision/interaction footprint.

2. Map travel / boarding gate is effectively missing to the player.
   - `sky_dock_interior.tmx` declares a BoardingGate tileset and a visible boarding-pad role, but the current TMX does not expose an obvious actionable Warp/Action tile.
   - Make the gate visually unmistakable and functional for travel/testing combat maps.
   - Keep the interaction discoverable without hidden knowledge.

3. Restore missing floor-2 upgrade machines.

4. Add/fix collision for machines and props so the player cannot walk through them.

5. Add interactions to machines that are intended to be usable.

6. Re-scale oversized props to believable Stardew room proportions.

7. Observation Window should be slightly larger while keeping the approved time-of-day behavior.

8. Radar/navigation machine still has an unwanted background and must be properly separated/transparent.

9. Room shell/border is visible in room 2 but missing/inconsistent in room 1.

10. Entrance arch/gate is misaligned and too small.
    - Reposition.
    - Target roughly 2x current visual size.

11. Overall scene dressing should follow the approved concept more naturally instead of placing props as isolated rectangles.

## Current map diagnosis

- `sky_dock_interior.tmx` declares `airship-transit-dock|route-board|visible-boarding-pad|service-zone|forest-return` and includes `CardchaBoardingGate0690`, but there is no obvious direct Warp/Action property in the current TMX checkpoint.
- `airship_deck.tmx` declares `four-independent-upgrade-stations`, but there is no obvious direct Action property in the current TMX checkpoint.

This explains why the current build can visually contain props while still feeling non-interactive or undiscoverable.

## Next implementation priority

Gameplay integration first:
1. travel gate / warp,
2. upgrade stations and interactions,
3. collision footprints,
4. restore missing machines,
then visual placement/scale polish.

Do not reopen 0696D2 source recovery. The re-baselined Window source work remains complete.

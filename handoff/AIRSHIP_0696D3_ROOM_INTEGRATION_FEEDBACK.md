# Cardcha 0696D3 Room Integration Feedback

Date: 2026-09-15
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Source: Ron in-game visual test of `.69`, plus follow-up correction to the implementation checklist.

## Verdict

0696D2 Observation Window time-of-day switching is working, but the room/map integration is not accepted yet. Visual acceptance remains pending until the slight Window enlargement and the D3 integration fixes are retested in-game.

## Required fixes

1. Rework the upgrade-machine/pedestal cluster **and restore the missing floor-2 upgrade machines as one combined task**.
   - These are not two separate checklist items.
   - Restore/rework the expected four independent upgrade stations where the architecture calls for them.
   - Rework placement, scale, depth/shadow/footing and spatial integration.
   - They should read as functional machinery, not pasted decoration.
   - Add proper base-footprint collision and reachable interaction points.
   - Restoration alone is insufficient because the old pedestal presentation itself was rejected visually.

2. Map travel / boarding gate is effectively missing to the player.
   - `sky_dock_interior.tmx` declares a BoardingGate tileset and a visible boarding-pad role, but the current TMX does not expose an obvious actionable Warp/Action tile in the inspected map data.
   - Runtime handling may exist elsewhere and must be inspected before adding duplicate systems.
   - Make the gate visually unmistakable and functional for travel/testing combat maps.
   - Keep the interaction discoverable without hidden knowledge.

3. Add/fix collision for remaining machines and props so the player cannot walk through solid bases.
   - Block the physical base/footprint rather than the full tall sprite rectangle.
   - Keep front interaction tiles reachable.

4. Add/fix interactions for machines that are intended to be usable.

5. Re-scale and reposition oversized props to believable Stardew room proportions and a more natural concept-like arrangement.

6. Rework the radar/navigation workstation from Ron's supplied reference image.
   - The supplied reference is authoritative. Do not recreate it from memory.
   - Preserve the deliberate warm **yellow/golden backing/background** and ornate wood/gold workstation structure.
   - Keep the central turquoise/green radar/map screen and surrounding instrument/decor language from the reference.
   - Do **not** interpret the backing as an unwanted opaque background and do not make it transparent merely for transparency's sake.

7. Room shell/border is visible in room 2 but missing/inconsistent in room 1. Add a consistent room-1 shell/border without breaking the walking path or doorway.

8. Entrance/boarding arch is misaligned and too small.
   - Reposition/center it against the intended doorway/pad.
   - Target roughly **2x** the current visual size, per Ron's explicit feedback.
   - Keep collision at the physical base so the enlarged upper sprite does not create an oversized invisible wall.

9. Observation Window should be **slightly larger**, not 2x, while keeping the approved Morning/Noon/Evening/Night behavior.
   - Preserve the independent frozen D1S small-airship overlay/art and its motion.
   - If production bytes/dimensions change, regenerate/document the canonical outputs and hashes.

10. Overall scene dressing should follow the approved concept more naturally instead of placing props as isolated rectangles.

## Current map diagnosis

- `sky_dock_interior.tmx` declares `airship-transit-dock|route-board|visible-boarding-pad|service-zone|forest-return` and includes `CardchaBoardingGate0690`, but there was no obvious direct `Warp`/`Action` property in the inspected TMX checkpoint. This does **not** prove that no runtime travel handler exists elsewhere.
- `airship_deck.tmx` declares `four-independent-upgrade-stations`, but there was no obvious direct `Action` property in the inspected TMX checkpoint. Runtime input/action handling must be checked before implementing new triggers.

## Next implementation priority

1. Combined upgrade-machine/pedestal rebuild + floor-2 restoration.
2. Functional, obvious map-travel / boarding gate.
3. Collision and interaction footprints for the remaining machinery.
4. Prop scale and placement pass.
5. Radar/navigation workstation matched to Ron's reference, including the yellow/golden backing.
6. Room-1 border/shell consistency.
7. Entrance/boarding arch alignment + approximately 2x visual size.
8. Slight Observation Window enlargement with the four time buckets preserved.
9. Final room-integration regression pass and package audit.

Do not reopen 0696D2 source recovery. The re-baselined Window source work remains complete, and the historical lost production-byte identities remain archival only.
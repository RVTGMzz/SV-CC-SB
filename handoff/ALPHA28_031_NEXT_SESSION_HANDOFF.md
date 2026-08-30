# Cardcha Alpha.28 — Next Session Handoff

Date: 2026-08-31
Branch: `cardcha-alpha28-airship-foundation`
Latest canonical commit: `c36b2870212d61e0c9a7c6c1dd154d5d6586ef5c`
Latest canonical build: `0.3.0-alpha.28.0.3.0`

## Current goal
Build the new Cardcha Airship gameplay loop before expanding the Boss system.

## Design decisions locked
- Stardew Druid is **reference only**. Do NOT copy its source code, sprites, tilesheets, maps, or other assets into Cardcha. Recreate equivalent ideas with Cardcha-owned/vanilla-compatible assets to avoid dependency/copyright issues.
- Airship should become an early-game farming hub, especially for vanilla players who otherwise may not have enough monster density to farm Cardcha scraps/cards.
- A mysterious airship flyby happens before MiMi appears. It is foreshadowing only and should not reveal MiMi immediately.
- First Scrap remains the trigger for the existing MiMi story flow.
- After the MiMi/Wizard handoff, Airship access unlocks.
- Main access point is **Sky Dock**, located in the Forest just below Farm and offset left so it is immediately visible when leaving Farm. Do not use the Wizard area as the main access point; it is too far for repeated farming.
- Sky Dock exterior must avoid conflicts with vanilla Stardew NPCs/gameplay: no blocking collision, no pathing edits, no permanent obstruction of normal NPC routes. Prefer runtime-safe placement near the Farm→Forest transition rather than hard-coded vanilla-only coordinates.
- Sky Dock should have a separate interior hub. Exterior is only a compact access point.
- Interior hub should feel like Stardew Valley: wood, rope, lanterns, cloth, practical handcrafted construction, with only a light magical touch. Avoid overly polished/high-fantasy/steampunk styling.
- Travel loop: Farm → Sky Dock → Sky Dock Interior → choose destination → departure cutscene → destination. Returning should show a return/docking cutscene → Sky Dock Interior → Forest.
- Departure/return cutscenes should be short and skippable eventually; they should make the airship feel real without making repeated farming tedious.
- Airship farm progression has 4 regions:
  - Region I: 0–20 unique cards
  - Region II: 21–40 unique cards
  - Region III: 41–60 unique cards
  - Region IV: 61–80 unique cards
- Regions remain revisit-able. Unlocking a later region must NOT close earlier regions.
- Each region is a monster-farming area. Monster spawns should be randomized from a region-specific monster pool rather than fixed enemy positions.
- Boss gate is separate from normal farming access. Region I can be entered/farmed before 20 cards, but its Boss Gate requires 20 unique cards. Likewise later gates use 40/60/80 thresholds.
- First Boss progression remains: 20 unique cards → Boss I → reward Portable Cardcha Machine. Do not silently replace this with an automatic reward just for hitting 20.

## Flight fee design
- First-ever flight is free.
- Region I subsequent departure: 100g.
- Future planned fees: Region II 250g, Region III 500g, Region IV 1000g.
- Return flights are always free so the player cannot be stranded by lack of gold.
- Fee is thematically associated with MiMi/airship operation, but keep the first trip welcoming.
- Alpha.28.0.3 currently activates the Region I/100g framework; later prices are only reserved design values.

## Latest implemented build
Alpha.28.0.3.0 — Sky Dock Interior + Flight Cutscenes.
Implemented:
- `Cardcha_SkyDockInterior`, 30×18.
- Exterior Sky Dock entry in Forest.
- Interior has entrance/exit, route board, airship bay, and reserved space for future MiMi/ChaCha/utility content.
- Route selection currently uses Region I as the active route/staging destination.
- First flight is free; later Region I flights charge 100g.
- Return is free.
- Departure and return cutscene foundation is implemented.
- Save state stores relevant airship progression/travel state.
- Canonical GitHub Actions recheck passed on commit `c36b2870212d61e0c9a7c6c1dd154d5d6586ef5c`.
- Canonical artifact ID: `9730514621`.

## Important: current build is a foundation, not full Region I
Region I monster-farming map, randomized monster spawning, and real Boss Gate/arena are NOT completed yet. Current destination is still the airship/staging location.

## Next implementation step
Build **Alpha.28.0.4 — Region I Hunting Map**:
1. Create a Cardcha-owned Region I map using vanilla/Cardcha-created art; no Stardew Druid assets.
2. Make the region feel like a natural Stardew-area adventure map, distinct enough to read as an airship destination.
3. Add safe player traversal/collision.
4. Add randomized monster spawning from a Region I monster pool.
5. Reuse existing Cardcha monster/card Scrap/drop logic where possible; do not invent a second incompatible loot economy.
6. Keep the region accessible before 20 cards for farming.
7. Add a visible Boss Gate in Region I, locked below 20 unique cards, with a clear Vietnamese progress message.
8. At 20 unique cards, allow entry into the Boss arena/staging area; Boss I itself can be implemented as the following build if the gate flow is stable.
9. Keep old regions reusable and design Region I as a template for Regions II–IV.

## Testing priority
Test in this order:
- Farm → Forest → Sky Dock is easy to find.
- No NPC pathing/collision interference.
- Sky Dock Interior loads and exits safely.
- First flight costs 0g.
- Subsequent Region I departure costs exactly 100g.
- Return costs 0g.
- Departure/return cutscenes do not trap the player.
- Save/reload preserves airship unlock state.
- Region I can be farmed below 20 cards.
- Boss Gate blocks below 20 and permits at/above 20.

## Historical fixes to preserve
Do not regress the previously fixed Binder/controller behavior:
- Controller selection state must remain independent per selected card.
- Favorite and Equip actions must use the same state-change semantics as mouse-left activation.
- Favorite/Equip must not read stale action state or invert the current state.
- Favorite/Equip notification should be a short popup (~3s), not a persistent stacked blue message.
- Collection ↔ Favorite ↔ Equipment controller navigation should remain direct and predictable.
- MiMi friend-list mugshot uses the approved MiMi mugshot asset and should remain scaled like other NPC mugshots.
- MiMi friend-list outline should remain subtle and close to the sprite if still present; do not use a harsh black oversized stroke.
- MiMi broom animation uses the approved older/locked version and scale; do not revert to the rejected newer flying animation.
- Portable Cardcha Machine remains non-placeable only when it is the handheld/portable version; the normal fixed Cardcha machine must remain placeable.
- MiMi room/Sky Dock/map edits must not accidentally regress NPC collision/pathing.

## Design tone
Cardcha should feel indie, friendly, slightly humorous, and grounded in Stardew. Avoid making the mod sound more famous/popular than it really is. Do not overstate community attention.

## Suggested future content after Region I foundation
- Boss I encounter + Portable Cardcha Machine reward.
- Region II (21–40) with its own monster pool/theme.
- Region III (41–60).
- Region IV (61–80), endgame.
- MiMi secret TV content around the previously planned friendship progression remains future content and should not be mixed into the Airship foundation unless specifically requested.
- 40-card ChaCha fusion progression remains planned: fixed Cardcha machine + Portable machine → Binder direct access.

## Session instruction
When continuing from this file, first inspect the current branch/source and latest CI result. Do not assume an earlier build artifact is still canonical. Continue from the latest successful GitHub commit, preserve the locked design above, and make the smallest coherent next change rather than rewriting the travel system.
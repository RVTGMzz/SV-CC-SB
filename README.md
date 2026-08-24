# Cardcha: Shardbound v0.1.17-alpha.11.8 — MiMi Visual Pass

This build keeps the alpha.11.3 story flow and fixes the pre-Scrap Town presentation.

## Changes
- MiMi now anchors at the Town central red-brick plaza area (`45,62`).
- MiMi occasionally walks a short loop around the plaza instead of standing still.
- Native MiMi sprite frames are advanced while moving for a real walk-cycle feel.
- ChaCha remains beside MiMi and moves with her until he is lent to the player.
- Mystery reaction bubbles are limited to a curated list of human Stardew villagers.
- Pokémon, monsters, pets, and other creature NPCs are excluded from the reaction system.
- For testing, the mystery Town broom window is temporarily 10:00–15:00. The next-day Farm visit, WizardHouse meetup, merchant routine, and pre-Binder buff lock remain unchanged.

## Handoff
Always continue from `NEXT_SESSION_START_HERE.md`, `BUILD_HISTORY.md`, and `CARDCHA_PROJECT_STATE.json`.

## Alpha.11.5
Fixed the next-day Farm arrival where MiMi and ChaCha looked tiny. MiMi broom event now uses the same readable 2x presentation scale as the Town broom flight.

## Alpha.11.8 visual pass
- MiMi mystery test hours: 10:00–15:00 in Town.
- MiMi visual scale +15% in story/broom scenes.
- Six portrait expressions with context-sensitive portrait commands.
- ChaCha 2x beside MiMi with safer spacing.
- Floating `???` world label removed; mystery name is shown in dialogue UI.

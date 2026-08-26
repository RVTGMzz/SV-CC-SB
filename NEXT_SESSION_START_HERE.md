# NEXT SESSION — Cardcha v0.3.0-alpha.15 Gacha + Controller + Minimap

## Current candidate
- Version: `0.3.0-alpha.15`
- Build label: `Cardcha! v0.3.0-alpha.15 GACHA + CONTROLLER + MINIMAP`
- Baseline: alpha.14 / alpha.13 Compile Hotfix 1 line.

## Exact fixes
1. Gacha pull seed now includes fresh runtime entropy; resetting to the same save state is no longer guaranteed to repeat the exact same card.
2. Controller: A locks the selected card and that selection persists across unlimited cursor movements. Only A on another collection card changes the selection.
3. Action buttons have an explicit stable navigation graph.
4. Page seals are literal `<` / `>` because Unicode triangle glyphs rendered as stars in Stardew's font.
5. Normal/Shiny Scrap count numbers are roughly 2x larger.
6. At scheduled arrival, MiMi remains hidden until the broom actor is already positioned off-screen, eliminating the one-frame plaza flash.
7. NPC Map Locations compatibility uses its official `Mods/Bouhm.NPCMapLocations/NPCs` content asset with `MarkerCropOffset=1`; Vanilla marker mode gets a corrected `MugShotSourceRect`. `assets/mimi_minimap_icon.png` is the approved face-icon design reference: front-facing MiMi head, red bow, purple hair, no broom/background.

## Inherited behavior that must remain
- Alpha.14 larger MiMi/???/ChaCha shadows and Binder X button.
- Alpha.13 MiMi name reveal, +/- shop quantity selector, portable purchase feedback, full off-screen broom flights, official broom art +10% runtime scale.
- Alpha.13 compile hotfix: CardchaMachineMenu passes ResourceService into CardchaBinderMenu.
- Binder 80-card collection, Favorite persistence, rarity filters, resource rail, 5 normal + Boss + ChaCha layout.

## Test first
- Pull/reload the same pre-pull save multiple times and confirm the result isn't forced identical every time.
- A-select card #03, move cursor around several cells/buttons, then Equip/Favorite/Upgrade: every action must still target #03 until A selects a different card.
- Footer shows `<` and `>` rather than stars.
- Scrap counts are easy to read.
- Watch exact 10:00/11:00 MiMi arrival for any one-frame ground flash.
- With NPC Map Locations 3.5.x, confirm MiMi appears in the NPC list/minimap and inspect the head crop.

## Artifacts
- `Cardcha_v0.3.0-alpha.15_GachaControllerMinimap_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.15_SOURCE_SNAPSHOT.zip`

Static validation passed in the container; real Windows compile with Stardew/SMAPI refs is still required.
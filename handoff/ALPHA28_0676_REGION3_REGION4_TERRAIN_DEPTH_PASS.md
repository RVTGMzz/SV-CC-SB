# Alpha28 0676 - Region III / IV Terrain Depth Pass

Build: `0.3.0-alpha.28.0.4.14.4.5.12.45`  
Branch: `cardcha-alpha28-0676-region3-region4-terrain-depth-pass`
Status: CI validation first, in-game visual acceptance pending.

## What 0676 changes
- Mirrorwild gains a dedicated 512x64 authored terrain atlas with a central reflection basin, bilateral reflection rings, pale clearings, shard dust, bloom beds and fern mats.
- Resonance Verge gains a separate 512x64 terrain atlas with a tricolor resonance core and distinct Ignis, Vita and Aether ground formations.
- Terrain clusters are low-profile ground art at fixed Stardew 4x pixel scale. No new fake collider, no full-screen tint and no enlarged monster art.
- Existing 0675 enemy silhouettes and proxy suppression remain unchanged.
- Existing 0675 decor remains unchanged; 0676 reorganizes its placement into stronger Mirrorwild bilateral composition and Resonance triad composition.
- The TMX Back layer gets safe ground-only variation around landmark clearings. Buildings/collision layers and combat lanes are untouched.

## Frozen gameplay contract
- Region III/IV remain three-wave expeditions.
- Region III full clear remains 47 Scrap + 3 Shiny.
- Region IV full clear remains 69 Scrap + 6 Shiny.
- Region III fare remains 500g; Region IV fare remains 1000g.
- Unbanked extraction and return flight remain unchanged.
- Boss II/III/IV 40/60/80-card milestone priority remains unchanged.
- Save schema remains 19 and the active card audit remains 76/80.
- Enemy HP/speed/archetype selection from 0674/0675 is unchanged.

## In-game acceptance
1. `cardcha_test_region3`: confirm the center reads as a reflective wilderness landmark and the left/right composition feels intentionally mirrored.
2. Run/clear all three Region III waves. Verify authored enemies are still targetable and no vanilla Bat/Bug/Slime art bleeds through.
3. `cardcha_test_region4`: confirm the center reads as a resonance core and the three elemental ground languages are visually distinct without screen tinting.
4. Run/clear all three Region IV waves and verify target/damage/death/drop behavior is unchanged.
5. Capture one screenshot of each region with enemies active. Judge map density, landmark readability and whether any ground cluster covers the player awkwardly.
6. Extract once from each region and confirm the frozen 0674 reward totals and return flight.

## Next decision after screenshots
- If density is good, continue Region III/IV encounter identity/replayability rather than adding more decoration.
- If any cluster reads like a fake obstacle, move it to the perimeter or convert it into lower ground art. Do not solve it by enlarging enemy sprites.

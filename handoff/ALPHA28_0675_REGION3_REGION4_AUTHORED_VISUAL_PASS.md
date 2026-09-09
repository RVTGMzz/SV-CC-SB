# Alpha28 0675 - Region III / IV Authored Visual Pass

Build: `0.3.0-alpha.28.0.4.14.4.5.12.44`  
Branch: `cardcha-alpha28-0675-region3-region4-authored-visual-pass`
Status: CI validation first, in-game visual acceptance pending.

## What 0675 changes
- Mirrorwild now has a dedicated authored decor atlas and four native 32px enemy silhouettes: Mirror Wisp, Glass Scarab, Echo Slime, Mirror Sentinel.
- Resonance Verge now has a separate authored decor atlas and four native 32px enemy silhouettes: Ignis Echo, Vita Husk, Aether Mite, Resonant Prime.
- All authored actors render at the fixed Stardew `4x` world pixel scale. There is no per-enemy blow-up multiplier.
- Vanilla GreenSlime/Bat/Bug actors remain authoritative for AI, collision, damage, team targeting, death and Scrap drops, but their visible draw is suppressed only when marked as Region III/IV expedition proxies.
- Biome identity uses small physical props and edge clusters. No full-screen tint, giant sci-fi overlay, or floating room labels.

## Frozen 0674 gameplay contract
- Region III and IV remain three-wave expeditions.
- Region III full clear remains 47 Scrap + 3 Shiny.
- Region IV full clear remains 69 Scrap + 6 Shiny.
- Unbanked extraction behavior is unchanged.
- Region III fare remains 500g; Region IV fare remains 1000g.
- 40/60/80-card milestone priority and Boss II/III/IV behavior are unchanged.
- Save schema remains 19.

## In-game acceptance
1. `cardcha_test_region3`: inspect all four Mirrorwild silhouettes across waves. No vanilla Bat/Bug/Slime art should bleed through.
2. `cardcha_expedition_clear`: advance waves and verify all enemies remain targetable/damageable.
3. Confirm Mirrorwild reads as pale reflective wilderness, not a recolored test room.
4. `cardcha_test_region4`: inspect Ignis/Vita/Aether differentiation and Resonant Prime.
5. Confirm Resonance Verge looks materially different from Mirrorwild without a screen tint.
6. Complete/extract once from each region and verify 0674 reward totals and return flight remain unchanged.
7. If screenshots still feel sparse, 0676 should deepen authored terrain clusters rather than enlarge sprites.

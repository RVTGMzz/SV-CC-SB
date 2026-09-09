# Cardcha alpha28 0674 — Region III / IV Gameplay Foundation

## Current branch / build
- Branch: `cardcha-alpha28-0674-region3-region4-gameplay-foundation`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.43`
- Base: 0673 Milestone Progression Boss Route

## 0674 gameplay contract
- Region III `Mirrorwild` unlock requires Boss II reward `mirror_archive` + `AirshipHighestRegionUnlocked >= 3`.
- Region IV `Resonance Verge` unlock requires Boss III reward `tricolor_resonance` + `AirshipHighestRegionUnlocked >= 4`.
- Sky Dock route console keeps milestone-boss priority at exact 60/80 thresholds.
- Between boss thresholds it opens expeditions: Region III while farming toward 60 cards; Region IV while farming toward 80 cards.
- If both expedition regions are open, the route console presents a destination choice.
- Region III fare = 500g; Region IV fare = 1000g, reusing Airship fare/flight telemetry.
- External region flights reuse the existing Airship flight cutscene.
- Each expedition is 3 waves with unbanked Scrap/Shiny Scrap; extraction banks rewards.
- Unexpected exit loses only unbanked expedition cargo.
- Enemy foundation uses native-size Stardew monster proxies with Cardcha role metadata. No render scaling/enlargement.
- New maps are Cardcha-owned vanilla-tile TMX maps with distinct route silhouettes; visual/authored-enemy polish remains pending.

## Region identity
### Region III — Mirrorwild
- Mirrored trail layout.
- Mirror Wisp / Glass Scarab / Echo Slime proxy archetypes.
- Wave 3 Mirror Sentinel elite.
- Rewards: 47 Scrap + 3 Shiny Scrap for full clear.

### Region IV — Resonance Verge
- Central resonance lane + three-spoke layout.
- Ignis Echo / Vita Husk / Aether Mite proxy archetypes.
- Wave 3 Resonant Prime elite.
- Rewards: 69 Scrap + 6 Shiny Scrap for full clear.

## Debug
- `cardcha_expedition_status`
- `cardcha_test_region3`
- `cardcha_test_region4`
- `cardcha_expedition_clear`

## Frozen / regression guards
- Save schema stays 19.
- Region I Hunt Run 2.0 helm flow remains intact.
- 0673 real Boss 40/60/80 route remains intact and has priority at boss thresholds.
- Boss I / Totems / 0669 Region I visuals unchanged.
- 0671 milestone boss arena/art assets unchanged.
- 0672 Boss II/III/IV encounter depth unchanged.
- Boss Form duration 10s; Boss Energy gain 1/3 unchanged.
- MiMi remains final boss at 80 cards.
- `mimi_walk.png` remains locked.
- 76 active normal-card audit / 80 source entries unchanged.
- Strict TMX CSV validation required.

## In-game acceptance order
1. Real progression: clear Boss II → route console before 60 cards → Region III expedition available.
2. Confirm 500g fare, Airship cutscene, Mirrorwild arrival.
3. Clear all 3 waves; verify native-size enemies, reward totals and southern extraction.
4. Early extraction after wave 1/2 banks only current unbanked cargo.
5. Unexpected warp/death loses unbanked cargo only.
6. At 60 cards, route console must prioritize Boss III rather than Region III.
7. Clear Boss III → Region IV route becomes available while under 80 cards.
8. Region IV full 3-wave clear + 1000g fare + extraction.
9. At 80 cards, route console must prioritize MiMi.
10. Verify Region I helm still starts Hunt Run 2.0 unchanged.

## Next likely pass
- 0675 should be authored Region III/IV enemy + environment art only after 0674 gameplay acceptance/screenshots.

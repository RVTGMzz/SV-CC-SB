# Alpha28 0670 - Remaining Boss Foundation

Build: `0.3.0-alpha.28.0.4.14.4.5.12.39`
Branch: `cardcha-alpha28-0670-remaining-boss-foundation`
Status: CI/package and in-game acceptance pending.

## User override / sequencing
0669 has not yet received in-game acceptance because the user cannot test it right now. The user explicitly asked development to continue on the remaining bosses. 0670 therefore forks from materialized 0669 but does not modify Boss I/0669 visual-auth work. Any later 0669 regression must be fixed separately and then forward-ported carefully.

## Boss II - 40 cards: The Hollow Curator
- 2200 HP.
- Phase 1 Observation: Card Volley + Scan/Adapt.
- Phase 2 Reflection: adds Mirror Burst and faster pressure.
- Phase 3 Curator's Truth: Archive Collapse + empowered reflection.
- Adaptation stacks rise to 3 and strengthen Curator attack damage.
- Runtime teleport/reposition every few decisions.
- First clear unlocks Boss Card id `mirror_archive` and raises highest region to at least 3.

## Boss III - 60 cards: The Tricolor Resonance
- Three independently damageable guardians: Ignis, Vita, Aether, 780 HP each.
- Ignis = heavy area pressure.
- Vita = heals surviving guardians + vine pressure.
- Aether = ranged zone pressure.
- Only after all three fall does Phase 4 `Unified Resonance` spawn at 1650 HP.
- First clear unlocks Boss Card id `tricolor_resonance` and raises highest region to at least 4.

## Boss IV - 80 cards: MiMi, The Resonance Master
- MiMi remains the final 80-card boss.
- 3600 HP, four runtime phases at 75/50/25 percent thresholds.
- Phase 1 Familiar Power.
- Phase 2 Refined Control.
- Phase 3 True Resonance.
- Final phase combines arena/mirror/tricolor pressure.
- First clear unlocks Boss Card id `mimis_resonance`.
- `mimi_walk.png` is NOT modified. Boss runtime presentation is separate.

## Architecture / regression guards
- Save schema remains 19. No new save fields.
- Boss completion persistence uses the existing `BossCardsUnlocked` set.
- Region progression uses existing `AirshipHighestRegionUnlocked`.
- Milestone boss GreenSlime proxies remain engine-visible (`isInvisible=false`) but their vanilla draw is Harmony-suppressed.
- Milestone boss proxies do not receive knockback and do not trigger normal Scrap/loot death routing.
- Boss I, Hunt Run, MiMi social/home assets, 76-card audit, controller contract and Airship gate identity remain untouched.

## TEST commands
- `cardcha_test_boss2`
- `cardcha_test_boss3`
- `cardcha_test_boss4`
- `cardcha_boss_milestone_status`

These TEST commands bypass 40/60/80 ownership gates only for direct arena testing. Normal Region II/III/IV route integration remains later work.

## Visual status
0670 is a functional boss foundation. Boss II/III/IV use custom runtime silhouettes, telegraphs and HUD rather than final authored concept-quality sprite sheets. Dedicated native-size art, unique arenas, ChaCha Mirror/Trinity/Resonance forms and full Boss Card runtime effects remain later passes.

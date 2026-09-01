# Cardcha active-card runtime audit — alpha.28.0.4.14.1

Scope: all 76 active Base Set cards plus legacy Mythic IDs 77–80.

Status key:
- **PASS**: runtime behavior and per-star values match the player-facing rule closely enough.
- **CLARIFY**: runtime exists, but wording/feedback is broader or the implementation is an approximation that should be made explicit.
- **BUG**: missing hook, wrong values, wrong trigger/state lifetime, or materially incomplete mechanic.

Summary: **50 PASS / 12 CLARIFY / 14 BUG** among active IDs 1–76.

| # | ID | Status | Audit note |
|---:|---|---|---|
| 1 | `iron_edge` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 2 | `quick_hands` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 3 | `keen_eye` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 4 | `heavy_blow` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 5 | `first_strike` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 6 | `finisher` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 7 | `hunters_focus` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 8 | `steady_grip` | **CLARIFY** | Runtime uses moving-average stabilization of non-crit-like hits; close to text, but not direct vanilla damage-RNG variance. |
| 9 | `thick_hide` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 10 | `vitality` | **BUG** | No runtime reference/hook for vitality. +Max HP text is currently nonfunctional. |
| 11 | `second_breath` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 12 | `guard_step` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 13 | `swift_feet` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 14 | `backstep` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 15 | `stalwart` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 16 | `last_push` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 17 | `calm_heart` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 18 | `scavenger` | **PASS** | Runtime hook and star scaling match the current card rule; wording was made exact in `.4.14.1`. |
| 19 | `essence_finder` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 20 | `victory_charge` | **BUG** | No runtime reference/hook and no Boss Energy subsystem exists. Active card is nonfunctional by design gap. |
| 21 | `lucky_pocket` | **CLARIFY** | Runtime is exactly 2/3/4/5/6% per kill for +25g, not generic money/low-value loot. |
| 22 | `treasure_magnet` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 23 | `explorer` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 24 | `patient_hunter` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 25 | `rhythm` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 26 | `bruiser` | **CLARIFY** | Runtime threshold is MaxHealth >= 300; UI never states the 300 HP threshold. |
| 27 | `resilient` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 28 | `momentum` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 29 | `blood_fang` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 30 | `executioner` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 31 | `opening_gambit` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 32 | `deadeye` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 33 | `predator` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 34 | `adrenaline` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 35 | `counterforce` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 36 | `iron_will` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 37 | `field_medic` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 38 | `lifeline` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 39 | `armor_breaker` | **BUG** | Runtime stores hit counts per Monster; switching away and back resumes old stacks instead of resetting. |
| 40 | `crushing_impact` | **BUG** | Runtime implements crit-like knockback multiplier only; no 0.20–0.35s stagger implementation. |
| 41 | `fleet_hunter` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 42 | `treasure_eye` | **CLARIFY** | Runtime awards +1 Cardboard Scrap, not a generic extra vanilla loot roll. |
| 43 | `card_seeker` | **CLARIFY** | Runtime multiplies NORMAL Cardboard Scrap chance only; never Shiny Scrap. UI wording is too broad. |
| 44 | `dust_collector` | **CLARIFY** | Runtime gives a 15/20/25/30% chance for +1 extra Dust only when a max-star duplicate already converts to Dust; UI sounds like +15–30% Dust amount on all duplicates. |
| 45 | `fortune_chain` | **CLARIFY** | Runtime is a 5/7/9/11% chance for +1 Cardboard Scrap once no-hit streak >=5; UI says generic loot. |
| 46 | `battle_trance` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 47 | `vanguard` | **CLARIFY** | Runtime refreshes shield after an area becomes clear and monsters appear again, so semantics are once per encounter, not strictly once per location entry. |
| 48 | `marked_prey` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 49 | `unyielding` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 50 | `collectors_instinct` | **CLARIFY** | Runtime bonus is specifically +1 Cardboard Scrap on BossLike enemies, not generic gacha resource. |
| 51 | `berserker_soul` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 52 | `chain_hunter` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 53 | `soul_siphon` | **BUG** | Lifesteal floors each individual hit; normal hits often yield 0 HP forever. Needs fractional carry/accumulator. |
| 54 | `phantom_step` | **CLARIFY** | No actual dodge event exists; runtime infers dodge from >=48px movement/250ms with no recent hit. Can proc on fast movement without a true dodge. |
| 55 | `reapers_mark` | **BUG** | Text says 6s mark. Runtime grants bonus permanently after 4 hits until target dies. |
| 56 | `stoneheart` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 57 | `last_stand` | **BUG** | Text says 6s and limited per encounter. Runtime is continuously active whenever HP <=25%. |
| 58 | `war_drum` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 59 | `treasure_hunter` | **CLARIFY** | Runtime bonus is specifically +1 Cardboard Scrap on BossLike enemies, not generic non-exclusive reward. |
| 60 | `golden_hand` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 61 | `arcane_recycler` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 62 | `mirror_guard` | **BUG** | Big hit threshold is >=25% max HP. A big hit during cooldown can arm the effect and bank it until cooldown ends; stale triggers should not be banked. |
| 63 | `relentless` | **BUG** | Switching targets does not reset because per-target hit counts persist; misses are not observed at all, so the advertised miss reset is also absent. |
| 64 | `overclock` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 65 | `lucky_break` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 66 | `battle_scholar` | **BUG** | `3 monster types/day` progress is transient and is cleared on save reload, so same-day reload loses progress. |
| 67 | `phoenix_heart` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 68 | `void_walker` | **BUG** | Proc is rolled before the triggering hit and reduces that hit; phase duration only adds move speed, not damage reduction on subsequent hits. This contradicts `after taking damage, enter phase`. |
| 69 | `soul_eater` | **BUG** | Runtime stats are 7/5/5 kills, 8/10/12% heal+damage, duration 5/6/7s; UI says 6/5/4 kills, 10/12/15% heal+damage, 5s. |
| 70 | `time_breaker` | **CLARIFY** | No actual crit-result signal is used; runtime uses a >=1.65x moving damage baseline heuristic. Can classify some high non-crits as crit-like or miss low crits. |
| 71 | `titans_grip` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 72 | `perfect_hunter` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 73 | `kings_ransom` | **PASS** | Runtime hook and star scaling match the current card rule. |
| 74 | `cardmaster` | **BUG** | Uses global PullIndex rather than Standard-pull count, and does not implement the advertised next-pull +1/1.5/2% Rare+ weight at all. |
| 75 | `guardian_angel` | **BUG** | Runtime triggers only on a lethal incoming hit, leaves player at 1 HP, then grants shield. Text says trigger below 20% HP. It can also pre-empt Phoenix Heart. |
| 76 | `apex_predator` | **PASS** | Runtime hook and star scaling match the current card rule. |

## Legacy Mythic IDs 77–80

IDs 77–80 (`endless_hunt`, `fate_weaver`, `immortal_echo`, `worldbreaker`) are retained for save/migration safety but intentionally hidden from the active Binder/gacha pool by `CardRegistry`. They are **not counted as active-card runtime failures** in this audit.

## Cross-cutting compatibility finding

`MonsterDeathService.HandleCustomDeath` (observer-only custom enemies without a Stardew `Monster` instance) calls `Combat.OnEnemyKilled` but cannot call the monster-specific `CoreCardEffectsService.OnMonsterKilled`. Therefore monster-specific Core kill mechanics (e.g. Second Breath, Field Medic, Predator, Explorer/Momentum/Adrenaline/Fleet Hunter, War Drum, no-hit streak, Battle Scholar variety, boss-aware Overclock/Apex hooks) are guaranteed for normal/derived `Monster` enemies but not every observer-only custom enemy type.

## Release rule

Do not call the Base Set runtime-complete while any active **BUG** row remains. Do not invent a replacement effect for #20 Victory Charge until the Boss Energy system is either implemented or the card is explicitly redesigned.

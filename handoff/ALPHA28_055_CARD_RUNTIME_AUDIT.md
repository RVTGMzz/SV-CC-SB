# Cardcha alpha.28.0.4.14.2 — Full active-card runtime audit handoff

Branch: `cardcha-alpha28-055-card-runtime-audit`
Build: `0.3.0-alpha.28.0.4.14.2`
Workflow run: `33534159235` — PASS (source acceptance, compile, regression, package, artifact upload)

## Why this pass exists

User explicitly required a runtime audit of **all cards**, not just Scavenger #18. The audit covers all 76 active Base Set IDs. Legacy Mythic IDs 77–80 are retained for migration safety but are intentionally hidden from the active Binder/gacha pool.

Full per-card audit table:
`docs/CARD_RUNTIME_AUDIT_ALPHA28_055.md`

Initial audit result before remediation:
- 50 PASS
- 12 CLARIFY (runtime exists but player-facing wording was broader/approximate)
- 14 BUG

## `.4.14.2` remediation

All unambiguous BUG/CLARIFY findings were fixed or made exact except **#20 Victory Charge**. Victory Charge depends on a Boss Energy subsystem that does not exist in this repository. Do not invent a hidden substitute effect. Its TEST-build description explicitly says it is temporarily inactive pending Boss Energy implementation/redesign.

Major fixes include:
- #10 Vitality: real +Max HP runtime, removed before Stardew save and reapplied after save to prevent permanent/double stacking.
- #39 Armor Breaker + #63 Relentless: same-target stacks now reset when switching targets.
- #40 Crushing Impact: adds compatible Monster stun/stagger attempt in addition to knockback.
- #53 Soul Siphon: fractional lifesteal carry so ordinary hits can eventually heal.
- #55 Reaper's Mark: real 6-second mark window.
- #57 Last Stand: 6 seconds, once per monster encounter instead of always-on below 25% HP.
- #62 Mirror Guard: big hits during cooldown no longer bank a stale trigger.
- #66 Battle Scholar: monster-type progress persists across same-day save/reload and clears on a new day.
- #68 Void Walker: proc occurs after taking damage; phase reduces subsequent hits and grants movement during the phase.
- #69 Soul Eater: runtime values now match the Binder (6/5/4 kills, 10/12/15% heal+damage, 5 seconds).
- #74 Cardmaster: dedicated Standard-pull counter, every 10 Standard pulls grants Dust, next Standard pull gets the advertised small Rare+ chance nudge.
- #75 Guardian Angel: triggers after surviving a hit at <=20% HP and grants shield; no longer acts as a lethal 1-HP save or pre-empts Phoenix Heart.
- Observer-only custom enemies now feed generic Core kill progression instead of only the loot pipeline.
- Ambiguous text for loot/heuristic cards was rewritten to state the actual runtime mechanic exactly.

## Remaining known design blocker

### #20 Victory Charge
There is no Boss Energy subsystem in the current codebase. The card is still in the active Base Set, but `.4.14.2` labels it explicitly as temporarily inactive rather than pretending another effect is Boss Energy.

Before declaring the 76-card Base Set fully runtime-complete, either:
1. implement Boss Energy and wire Victory Charge to it; or
2. explicitly redesign/replace Victory Charge and update the public card design.

## Compatibility nuance to remember

Observer-only custom-enemy deaths now receive generic kill progression. However, encounter-presence checks such as `hasLivingMonster` still inspect Stardew `Monster` actors. A completely custom hostile `Character` that is not a `Monster` can therefore participate in kill rewards while not necessarily counting as an active monster for area-presence passives. Do not claim universal compatibility for every custom battle framework without an in-game test.

## Locked regressions

Do not modify unless explicitly requested:
- `assets/card_icons.png` SHA-256 `4d659e9a25b188ca7e5e0654aa1124ae562f28ca414236283fef1523df6700ee`
- `assets/airship_visual.png` SHA-256 `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`
- Forest Airship compatibility contract remains `CollisionEdits=NONE`.
- `.4.14.1` Airship controller/readability/bush-avoidance/auto-transition UX fixes remain intact.
- Do not start permanent Airship upgrade bonuses/balance in this card-audit pass.

## Test priority

For in-game validation, prioritize the cards that changed runtime rather than retesting all 76 manually in one session: Vitality, Armor Breaker/Relentless target switching, Soul Siphon low-damage healing, Reaper's Mark timer, Last Stand encounter limit, Mirror Guard cooldown, Battle Scholar save/reload, Void Walker phase, Soul Eater values, Cardmaster Standard-pull cadence, Guardian Angel + Phoenix Heart interaction, and one observer-only custom enemy if available.

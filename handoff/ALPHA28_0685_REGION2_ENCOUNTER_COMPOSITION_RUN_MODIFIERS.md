# Alpha.28 0685 Region II Encounter Composition + Run Modifiers

Branch: `cardcha-alpha28-0685-region2-encounter-composition-run-modifiers`
Build: `0.3.0-alpha.28.0.4.14.4.5.12.53`
Base: 0684 Region II Room-Specific Mechanics

## Purpose

0685 adds a run-level composition layer above the existing 6–9 node route and 0684 room hazards. Each Region II run receives one deterministic Archive Rule that changes route weighting, enemy archetype composition and selected enemy pacing. The goal is for repeat runs to differ in tactical rhythm, not merely in RNG order.

## Archive Rules

- **Loose Folios / Trang Rời:** weights Combat and Ambush more heavily. Encounter rolls favor Ink Moths; enemies receive lower HP scaling but +1 Speed.
- **Iron Bindings / Gáy Sắt:** weights Elite and Cache more heavily. Encounter rolls favor Dust Slimes; enemies receive higher HP scaling but -1 Speed with a safe floor.
- **Mirror Draft / Bản Nháp Gương:** weights Mirror Choice and Archive Event more heavily. Enemy archetypes use an even deterministic mix with no extra stat tax.
- **Redacted Ledger / Sổ Bôi Đen:** weights Cursed Archive, Cache and Restoration more heavily. Encounter rolls favor Paper Scarabs with a small HP premium, pairing recovery/reward opportunities with curse pressure.

The selected rule is derived from the run RNG after route length is chosen, so the same run seed is reproducible. The run intro displays the localized rule name and effect once.

## Encounter composition

The old `Ambush => all Ink Moths` and cyclic `(index + depth) % 3` composition are replaced by a deterministic weighted archetype roll driven by the active Archive Rule. The Archive Warden remains the forced first Elite actor. `cardcha_region2_rogue_status` now reports both the active modifier and the last spawned role mix.

## Preserved layers

- 0684 Reflected Trace, Ink Sweep and Warden Seal are unchanged.
- 0683 physical room interactions and route-end Final Cache remain physical/native.
- Curator Records You remains active and receives the same run record contract.
- Region II run target remains 6–9 nodes with checkpoints at 3 and 6.
- Region II fare remains 250g.
- Hollow Curator remains 2200 HP at the 40-card milestone.
- Save schema remains 19.
- Card audit remains 80 source / 76 active normal.
- Region III/IV, Boss III/IV and accepted map/art assets are untouched.

## Debug

- `cardcha_test_region2`
- `cardcha_expedition_clear`
- `cardcha_region2_rogue_status`
- `cardcha_region2_mechanic_status`
- `cardcha_test_region2_bossgate`

## Acceptance

CI proves deterministic composition, frozen contracts and compile/package health only. In-game acceptance is pending. Compare several fresh Region II runs and verify that the intro rule matches the observed route/enemy rhythm, that Loose Folios feels fast rather than unfair, Iron Bindings feels deliberate rather than spongey, Mirror Draft creates useful mixed encounters, and Redacted Ledger produces a legible risk/recovery cadence. Also re-check all 0684 hazard telegraphs because they now stack with different enemy pacing.

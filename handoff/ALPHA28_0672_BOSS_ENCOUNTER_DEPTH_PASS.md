# Alpha28 0672 - Boss Encounter Depth Pass

Build: `0.3.0-alpha.28.0.4.14.4.5.12.41`
Branch: `cardcha-alpha28-0672-boss-encounter-depth-pass`
Status: CI/package and in-game acceptance pending.

## Scope
- Boss II Hollow Curator gains memory-based Mirror Echo attacks that replay prior danger tiles.
- Boss III Tricolor Guardians no longer snap to fixed spawn pads; Ignis, Vita and Aether reposition by role.
- Unified Resonance cycles three distinct attack patterns.
- Boss IV MiMi gains Mirror Echo, Tricolor Cadence and final Resonance Mix mechanics in later phases.
- ChaCha Guardian/Mirror/Trinity/Resonance forms now have distinct pulse gameplay identities.
- Boss Form duration remains 10 seconds. Boss Energy gain pacing remains unchanged.

## ChaCha form identity
- Guardian Rabbit: 14 damage, 176px pulse, 2.0s cadence.
- Mirror Rabbit: 12 + 6 echo damage, 192px, 1.9s cadence.
- Trinity Rabbit: rotating Ignis/Vita/Aether pulse identity, 1.8s cadence.
- Resonance Rabbit: 16 + 5 echo damage, 224px, small self-heal, 1.7s cadence.

## Regression guards
- 0671 authored PNG/TMX assets remain present and are not redrawn in 0672.
- 0670 milestone HP/reward thresholds remain unchanged.
- Boss I/0669 remains untouched while acceptance is pending.
- Save schema remains 19.
- `mimi_walk.png` remains locked.
- Card audit remains 76 active / 80 source.

## TEST
- `cardcha_test_boss2`
- `cardcha_test_boss3`
- `cardcha_test_boss4`
- `cardcha_boss_milestone_status`
- `cardcha_chacha_boss_status`

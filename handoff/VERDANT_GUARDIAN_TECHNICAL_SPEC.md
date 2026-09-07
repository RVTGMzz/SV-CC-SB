# Boss I — Verdant Guardian technical design

Status: build contract for first functional Boss I implementation. Balance values are deliberately provisional and should be tuned only after in-game testing.

## 1. Runtime state names

`VerdantGuardianState`
- `Dormant`
- `Intro`
- `Decision`
- `SwipeTelegraph`
- `RootSpikesTelegraph`
- `SummonAdds`
- `ChargeTelegraph`
- `Charging`
- `VineTrapTelegraph`
- `VineTrapActive`
- `AreaSlamTelegraph`
- `PhaseTransition`
- `Defeated`
- `Victory`

The state machine uses a separate phase integer:
- Phase 1: 100% -> 70% HP
- Phase 2: 70% -> 35% HP
- Phase 3: 35% -> 0% HP

## 2. Transition conditions

- `Dormant -> Intro`: player enters `Cardcha_VerdantGuardianArena`.
- `Intro -> Decision`: intro lock finishes.
- `Decision -> attack state`: an attack is off cooldown and is selected by the phase-weighted selector.
- Any active combat state -> `PhaseTransition`: HP crosses 70% or 35% threshold and that phase transition has not already fired.
- `PhaseTransition -> Decision`: 1.6 s transition lock finishes, next phase becomes active.
- Any combat state -> `Defeated`: boss proxy HP reaches 0.
- `Defeated -> Victory`: first-clear reward/save work is resolved.
- `Victory -> return`: victory delay expires, player is warped back to the Region I boss-gate staging side.

## 3. Provisional cooldown table

| Move | Phase 1 | Phase 2 | Phase 3 | Telegraph |
|---|---:|---:|---:|---:|
| Swipe | 2200 ms | 1800 ms | 1500 ms | 700 ms |
| Root Spikes | 5200 ms | 4500 ms | 3600 ms | 900 ms |
| Summon Adds | 16000 ms | 14000 ms | 12500 ms | 600 ms |
| Charge | locked | 7000 ms | 5600 ms | 900 ms |
| Vine Trap | locked | 8500 ms | 6500 ms | 900 ms |
| Area Slam | locked | locked | 7200 ms | 1100 ms |

Global decision gap after an action:
- P1: 700 ms
- P2: 550 ms
- P3: 400 ms

These values are not balance canon. They only ensure the first product has readable pacing.

## 4. Pseudo-AI loop

```text
on every update while player is in boss arena:
    resolve boss proxy reference
    if boss HP <= 0:
        handle victory once
        return

    if HP crossed next phase threshold and not already transitioning:
        enter PhaseTransition
        return

    update current telegraph / active attack

    if current state != Decision:
        return

    if decision gap has not expired:
        return

    candidates = attacks allowed in current phase whose cooldowns expired
    prevent immediate repeat where alternatives exist
    select one candidate using a deterministic encounter RNG
    enter that attack state
```

Attack intent:
- Swipe: short-range punish around the boss.
- Root Spikes: snapshot player tile, paint ground warning, then erupt several tiles.
- Summon Adds: 2 / 3 / 3 adds by phase, with a hard active-add cap.
- Charge: snapshot direction, telegraph lane, then move the boss proxy through the arena.
- Vine Trap: snapshot player tile, telegraph a zone, leave a short-lived damaging control patch.
- Area Slam: Phase 3 only, large radial punish around the boss.

## 5. Persistent save fields / keys

Save schema remains **19**. No schema bump for this feature.

Fields:
- `Region1BossDefeated : bool`
- `BossCardsUnlocked : HashSet<string>`
- `EquippedBossCardId : string`

Stable Boss Card ID:
- `verdant_core`

First clear does all of the following exactly once:
1. `Region1BossDefeated = true`
2. add `verdant_core` to `BossCardsUnlocked`
3. if no Boss Card is equipped yet, set `EquippedBossCardId = "verdant_core"`
4. `AirshipHighestRegionUnlocked = max(current, 2)`
5. grant Portable Cardcha Machine if the player does not already own it
6. save immediately

## 6. Asset/file contract

Required for the first functional build:
- `src/Cardcha/assets/verdant_guardian_arena.tmx`
- `src/Cardcha/Services/VerdantGuardianBossService.cs`

Planned final-art files, not required to block the gameplay prototype:
- `src/Cardcha/assets/bosses/verdant_guardian.png`
- `src/Cardcha/assets/bosses/verdant_guardian_core_glow.png`
- `src/Cardcha/assets/bosses/verdant_root_spikes.png`
- `src/Cardcha/assets/bosses/verdant_vine_trap.png`
- `src/Cardcha/assets/bosses/verdant_sprout_add.png`
- `src/Cardcha/assets/cards/boss_verdant_core.png`
- `src/Cardcha/assets/chacha/chacha_guardian_rabbit.png`

The first gameplay build may use a clearly marked vanilla-monster proxy for the boss body while the custom sprite sheet is produced. Telegraphs, phase logic, persistence, first-clear reward, and routing must already function.

## Guardrails

Do not change:
- Save schema 19
- Boss Form duration 10 seconds
- Boss Energy gain scale 1/3
- 76/76 active-card audit
- Forest Arcane Gate behavior/collision
- accepted Airship visual/route
- MiMi Profile/Gift Log or Wizard stair pending acceptance
- 20/40/60/80 milestone structure

Boss concept follows `handoff/BOSS_CONCEPT_CANON.md`.

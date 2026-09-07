# Alpha.28 0650 — Verdant Guardian Boss I functional prototype

Status: implementation candidate; in-game acceptance pending.

## Product
- Region I Boss Gate at 20 unique cards now enters `Cardcha_VerdantGuardianArena`.
- Functional Boss I state machine: 3 phases, six attacks, telegraphs, HUD HP bar, adds, charge, retreat and victory return.
- First clear persists `Region1BossDefeated`, unlocks/equips `verdant_core`, unlocks Region II hook, and grants Portable Cardcha Machine if not already owned.
- Boss body is deliberately a vanilla GreenSlime proxy in this build. Approved custom Verdant Guardian art is a separate art pass; do not mistake the proxy for final visual canon.

## Locked technical contract
See `handoff/VERDANT_GUARDIAN_TECHNICAL_SPEC.md` and `handoff/BOSS_CONCEPT_CANON.md`.

## Balance
HP/damage/cooldowns are provisional. Tune only after in-game feel testing.

## Regression guard
- Save schema remains 19.
- Boss Form duration remains 10s.
- Boss Energy gain remains 1/3.
- 76/76 active-card audit untouched.
- Forest gate/Airship visuals/routes untouched.
- 0648J MiMi Profile/Gift Log scale and Wizard stair are still pending in-game acceptance.

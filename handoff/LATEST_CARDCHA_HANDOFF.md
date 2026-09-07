# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0651-verdant-animation-hook`

Current gameplay build:
`0.3.0-alpha.28.0.4.14.4.5.12.18`

Read first:
- `handoff/VERDANT_GUARDIAN_ANIMATION_HOOK_SPEC.md`
- `handoff/ALPHA28_0650_VERDANT_GUARDIAN_BOSS1.md`
- `handoff/VERDANT_GUARDIAN_TECHNICAL_SPEC.md`
- `handoff/BOSS_CONCEPT_CANON.md`

## Session status — 2026-09-07
- Boss I Verdant Guardian gameplay/state-machine prototype exists and compiles in .12.18; in-game acceptance remains pending.
- Verdant Guardian custom sprite/animation contract is now locked as a 64x64 horizontal-strip, feet-anchored visual pipeline.
- Animation must stay presentation-only for the first integration pass: existing boss state timings remain authoritative for damage/cooldowns/phases/rewards.
- Planned visual architecture keeps the GreenSlime proxy as the invisible gameplay actor and suppresses only its draw when a valid custom boss clip can be rendered. Missing assets must fall back safely to the vanilla proxy.
- Next implementation slice: `VerdantGuardianAnimationController` + narrow `VerdantGuardianDrawPatch`, then add approved PNG clips one by one.
- Region I Hunt Run 4-of-6 remains the route into the existing 20-card gate.
- 0648J MiMi Gift/Profile 50% + Wizard stair remains pending; do not silently mark accepted.

## Locked regression guard
Save schema 19; Boss Form 10 sec; Boss Energy 1/3; 76/76 active cards; Forest Arcane Gate and collision; Airship route/visual; MiMi HOME/TV/LATE; card canon.

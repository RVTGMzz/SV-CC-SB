# NEXT SESSION — Cardcha Alpha.27

## Current branches

- `main` = temporary rollback baseline `v0.3.0-alpha.26.5.3`.
- Active development branch = `cardcha-alpha27-mimi-real-npc`.
- Do **not** rebuild alpha.27 from old alpha.25/26 snapshots; continue from the active branch source.

## Current alpha.27 status

Latest compiled visual candidate:
- `v0.3.0-alpha.27.0.4 — MiMi Attic Visual Foundation TEST`
- CI compile: **PASS**.
- CI package: **PASS**.
- Current source milestone commit: `950df2a364fadec8b81dbeae64bbe3ac87799f21` (before this handoff-only docs commit).

Implemented alpha.27 foundation includes:
- MiMi real friendship/social NPC after Wizard-house meetup;
- Social tab + vanilla gifting;
- birthday **Spring 17**;
- controller-friendly one-button priority: held gift -> gifting, first empty-hand talk -> dialogue, later empty-hand action -> shop;
- stable attic location ID `Cardcha_MiMiAttic`;
- attic access at **2 hearts**;
- schedule foundation: 11:00–17:00 Monday–Friday work, attic outside work/weekends;
- Community Center workplace foundation for restored non-Joja route;
- Wizard House work fallback during harsh weather;
- staircase/access integration without wholesale WizardHouse replacement.

## Alpha.27.0.4 — MiMi Attic Visual Foundation

Implemented and CI-compiled. Awaiting in-game visual/interaction acceptance before further expansion.

Five locked zones are represented:
1. entrance / stair landing;
2. research desk;
3. bed / personal corner;
4. TV secret zone;
5. ChaCha / upgrade corner.

Implementation notes:
- keeps the safe vanilla `Maps/Shed` runtime base instead of replacing `WizardHouse`;
- overlays a small original Cardcha attic prop atlas (`assets/mimi_attic_props.png`);
- adds inspect groundwork for desk / TV / ChaCha;
- adds EN/VI flavor text for all three inspect points;
- keeps attic as MiMi's home, not the main shop;
- includes an intentionally unused eligibility hook for the later **17:30 / 6-heart** TV routine;
- does **not** implement the full TV event, full heart event, full ChaCha upgrade mechanic, or Community Center contribution mechanic yet.

## Canon MiMi assets

- `mimi_portraits.png` canonical size = **768x128**.
- Do not silently restore the rejected 1152x192 or 1536x256 portrait experiments.
- Alpha.27.0.4 CI package was checked and still contains the canonical 768x128 portrait.

## Next action

Use `v0.3.0-alpha.27.0.4_MiMiAttic_VisualFoundation_TEST` for the next in-game acceptance pass when a test machine is available. Fix layout/readability/collision/interaction issues found there before starting the full 17:30 event or ChaCha upgrade mechanic.

Do not merge alpha.27 into `main` automatically. Keep `main` at alpha.26.5.3 until the user explicitly accepts a newer rollback baseline.

## Read these docs before changing alpha.27

1. `docs/alpha27/MIMI_ATTIC_DESIGN_BIBLE.md`
2. `docs/alpha27/MIMI_CHARACTER_GIFTS_SCHEDULE.md`
3. `PROJECT_HANDOFF.md`
4. `docs/STORY_GAMEPLAY_BIBLE.md`

## Build rule

For each functional alpha.27 milestone, produce a **real CI-compiled TEST ZIP** before claiming completion.

## Controller regression note

Alpha.26.5.3 remains the rollback baseline because the final controller regression pass is still outstanding. Do not let that block alpha.27 development, but preserve the rollback point.

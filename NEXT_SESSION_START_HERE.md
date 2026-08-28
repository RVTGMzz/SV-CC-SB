# NEXT SESSION — Cardcha Alpha.27

## Current branches

- `main` = temporary rollback baseline `v0.3.0-alpha.26.5.3`.
- Active development branch = `cardcha-alpha27-mimi-real-npc`.
- Do **not** rebuild alpha.27 from old alpha.25/26 snapshots; continue from the active branch source.

## Current alpha.27 status

Latest compiled integration candidate before the next visual pass:
- `v0.3.0-alpha.27.0.3 — MiMi Real NPC Integration TEST`
- CI compile: PASS.

Implemented foundation includes:
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

## Canon MiMi assets

- `mimi_portraits.png` canonical size = **768x128**.
- Do not silently restore the rejected 1152x192 or 1536x256 portrait experiments.
- Latest user-approved TEST/package art remains canonical where GitHub binary art is still older.

## Current milestone

# `Alpha.27.0.4 — MiMi Attic Visual Foundation`

Build this next. The user explicitly asked to **build, not re-plan**.

Required attic layout is locked to five zones:
1. entrance / stair landing;
2. research desk;
3. bed / personal corner;
4. TV secret zone;
5. ChaCha / upgrade corner.

Visual tone:
- warm;
- eccentric;
- lived-in;
- slightly messy with intent;
- clear Cardcha/Scrap/ChaCha identity;
- still a home, not a workshop or second shop.

Technical rules:
- keep `Cardcha_MiMiAttic` stable;
- don't replace WizardHouse wholesale;
- preserve 2-heart access;
- add groundwork inspect interactions for desk / TV / ChaCha with EN/VI flavor text;
- leave hooks for the later 17:30 private routine at ~6 hearts.

Out of scope for alpha.27.0.4:
- full heart events;
- full 17:30 event;
- full ChaCha/Card Dust upgrade mechanic;
- full seasonal Community Center contribution mechanic.

## Read these docs before changing alpha.27

1. `docs/alpha27/MIMI_ATTIC_DESIGN_BIBLE.md`
2. `docs/alpha27/MIMI_CHARACTER_GIFTS_SCHEDULE.md`
3. `PROJECT_HANDOFF.md`
4. `docs/STORY_GAMEPLAY_BIBLE.md`

## Build rule

Produce a **real CI-compiled TEST ZIP** before claiming the milestone is complete. Keep alpha.27 work on `cardcha-alpha27-mimi-real-npc` until in-game acceptance; do not merge to `main` automatically.

## Controller regression note

Alpha.26.5.3 is still the rollback baseline because the user has not yet had a controller available for the final regression pass. Do not let that block alpha.27 development, but preserve the rollback point.

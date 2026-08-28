# NEXT SESSION — Cardcha Alpha.27

## Current branches

- `main` = temporary rollback baseline `v0.3.0-alpha.26.5.3`.
- Active development branch = `cardcha-alpha27-mimi-real-npc`.
- Do **not** rebuild alpha.27 from old alpha.25/26 snapshots; continue from the active branch source.

## Current alpha.27 status

Latest compiled visual candidate:
- `v0.3.0-alpha.27.0.5 — MiMi Attic Custom Interior TEST`
- CI compile: **PASS**.
- CI package: **PASS**.
- Current source milestone commit: `b02fa4116c6b3379a908d69f688bf0a5b0961c55` (before this handoff-only docs commit).
- TEST ZIP SHA256: `164337385dc8e734791249cf283d265dde8719330a0dc5049249d867b55dcacf`.

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

## Alpha.27.0.5 — MiMi Attic Custom Interior

Implemented and CI-compiled. This replaces the temporary vanilla `Maps/Shed` attic base with a dedicated Cardcha map asset while preserving the stable runtime location ID.

Five locked zones are represented in the actual room layout:
1. entrance / stair landing;
2. research desk;
3. bed / personal corner;
4. TV secret zone;
5. ChaCha / upgrade corner.

Implementation notes:
- attic map asset is registered as `Maps/Cardcha_MiMiAttic`;
- custom room source lives in `assets/mimi_attic.tmx`;
- custom pixel interior/tilesheet lives in `assets/mimi_attic_tiles.png` at **352x224**;
- map dimensions are **22x14 tiles** with Back / Buildings / Front layers;
- furniture/walls use the Buildings layer for collision groundwork;
- old runtime prop overlay is no longer used to draw the full room, preventing double visuals;
- desk / TV / ChaCha inspect groundwork and EN/VI flavor text remain active;
- attic remains MiMi's home, not the main shop;
- the later **17:30 / 6-heart** TV routine is still only an eligibility hook;
- full TV event, full heart event, full ChaCha upgrade mechanic, and Community Center contribution mechanic remain out of scope.

## Canon MiMi assets

- `mimi_portraits.png` canonical size = **768x128**.
- Do not silently restore the rejected 1152x192 or 1536x256 portrait experiments.
- Alpha.27.0.5 CI package was checked and still contains the canonical 768x128 portrait.

## Next action

Use `v0.3.0-alpha.27.0.5_MiMiAttic_CustomInterior_TEST` for the next in-game acceptance pass when a test machine is available. Verify that the custom TMX loads, the 2-heart staircase access works, MiMi can stand/move safely in the attic, collision feels natural, and desk / TV / ChaCha inspect points are reachable.

Only after this room passes acceptance should the project start the full 17:30 TV event or ChaCha upgrade mechanic.

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

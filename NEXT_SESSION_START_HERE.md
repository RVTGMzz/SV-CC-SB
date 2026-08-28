# NEXT SESSION — Cardcha Alpha.27

## Current branches

- `main` = temporary rollback baseline `v0.3.0-alpha.26.5.3`.
- Active development branch = `cardcha-alpha27-mimi-real-npc`.
- Do **not** rebuild alpha.27 from old alpha.25/26 snapshots; continue from the active branch source.
- Do **not** merge alpha.27 into `main` automatically.

## Current alpha.27 status

Latest compiled visual candidate:
- `v0.3.0-alpha.27.0.7 — MiMi Attic True Stardew Map TEST`.
- CI compile: **PASS**.
- CI package: **PASS**.
- Source milestone commit: `9c1fe1f2d032c2c57297018deb36369580f0fa4a` (before this handoff-only docs commit).
- TEST ZIP SHA256: `92727032dd9572a16a0e63b3675084ed1b0d7bab4b52fe9f6e9a2ef4953fd1f1`.

Implemented alpha.27 foundation still includes:
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

## Alpha.27.0.7 — MiMi Attic True Stardew Map

This milestone replaces the rejected alpha.27.0.6 visual technique. The user approved a concept with the normal Stardew indoor visual language: black void outside the room, warm wood/purple lived-in interior, research upper-left, personal/bed upper-right, TV nook lower-left, ChaCha corner lower-right, and bottom-center landing.

Important locked technical direction:
- **Do not return to a room-sized custom background PNG.**
- The room shell is a real **22x14 TMX tile map**.
- `assets/mimi_attic.tmx` references the game's vanilla `Maps/townInterior` tilesheet directly.
- The rejected `assets/mimi_attic_tiles.png` 352x224 full-room pseudo-tilesheet is intentionally removed from the 0.7 TEST package.
- Beds, tables, chairs, TV, couch, rugs, plants, dresser, window, posters, etc. are instantiated as real vanilla Stardew `Furniture` objects so the game owns their sprite proportions, shadows, draw ordering, and furniture collision.
- Keep custom Cardcha art subtle and add it only after the vanilla-base room passes visual/gameplay acceptance.

Five locked zones:
1. entrance / stair landing;
2. research desk;
3. bed / personal corner;
4. TV secret zone;
5. ChaCha / upgrade corner.

Current 0.7 layout intent:
- research / bookcase / desk: upper-left;
- bed / dresser / bedside: upper-right;
- TV + couch nook: lower-left;
- ChaCha / prototype table: lower-right;
- bottom-center doorway/landing and a clear central walking route.

Implementation notes:
- attic asset name remains `Maps/Cardcha_MiMiAttic`;
- runtime location ID remains `Cardcha_MiMiAttic`;
- map layers remain `Back`, `Buildings`, `Front`;
- inspect groundwork + EN/VI flavor text remain active for Desk / TV / ChaCha;
- attic remains MiMi's home, not the main shop;
- the **17:30 / 6-heart** TV routine remains only an eligibility hook;
- full TV event, full heart event, full ChaCha upgrade mechanic, and Community Center contribution mechanic remain out of scope.

## Canon MiMi assets

- `mimi_portraits.png` canonical size = **768x128**.
- Do not silently restore rejected portrait experiments.
- Alpha.27.0.7 TEST package was checked and still contains the canonical 768x128 portrait.

## 0.7 package verification

The produced TEST ZIP was unpacked and checked:
- `Cardcha.dll` exists;
- manifest version is `0.3.0-alpha.27.0.7`;
- `assets/mimi_attic.tmx` exists and references `Maps/townInterior`;
- `assets/mimi_attic_tiles.png` is absent as intended;
- `mimi_portraits.png` is 768x128;
- EN and VI contain `mimi.attic.inspect.desk`, `.tv`, and `.chacha`;
- ZIP integrity test passed;
- external SHA256 matches the workflow-generated `SHA256.txt`.

## Next action

Use `v0.3.0-alpha.27.0.7_MiMiAttic_TrueStardewMap_TEST` for the next **in-game acceptance pass**. Verify:
- TMX resolves vanilla `Maps/townInterior` without xTile/SMAPI errors;
- room shell and doorway read naturally at actual Stardew camera scale;
- all runtime vanilla furniture IDs render correctly in the installed Stardew version;
- MiMi and the player have a clear central path and do not spawn inside furniture;
- 2-heart attic access/exit still works;
- desk / TV / ChaCha inspect points are reachable;
- furniture cannot be picked up/moved in an undesirable way (if it can, harden selected decor as static map tiles next).

If visual adjustments are needed, change **layout / vanilla furniture choices / vanilla tile choices** inside this true-map system. Do not revert to the full-room custom PNG approach.

Only after this room passes acceptance should the project start the full 17:30 TV event or ChaCha upgrade mechanic.

## Read these docs before changing alpha.27

1. `docs/alpha27/MIMI_ATTIC_DESIGN_BIBLE.md`
2. `docs/alpha27/MIMI_CHARACTER_GIFTS_SCHEDULE.md`
3. `PROJECT_HANDOFF.md`
4. `docs/STORY_GAMEPLAY_BIBLE.md`

## Build rule

For each functional alpha.27 milestone, produce a **real CI-compiled TEST ZIP** before claiming completion.

## Controller regression note

Alpha.26.5.3 remains the rollback baseline because the final controller regression pass is still outstanding. Do not let that block alpha.27 development, but preserve the rollback point.

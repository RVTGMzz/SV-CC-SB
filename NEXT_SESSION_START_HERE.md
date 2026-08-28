# NEXT SESSION — Cardcha Alpha.27

> **READ FIRST:** `docs/PROJECT_WORKING_RULES.md` is the persistent Cardcha working contract. Read it before changing code, maps, assets, progression, or sending a TEST build.
>
> In particular, before asking the user to test anything that has gameplay prerequisites, always state the prerequisites and provide/propose a test-only bypass when appropriate. Every TEST handoff must include: **Prerequisites → How to test → Debug bypass → What to verify → Out of scope**.

## Current branches

- `main` = temporary rollback baseline `v0.3.0-alpha.26.5.3`.
- Active development branch = `cardcha-alpha27-mimi-real-npc`.
- Do **not** rebuild alpha.27 from old alpha.25/26 snapshots; continue from the active branch source.
- Do **not** merge alpha.27 into `main` automatically.

## Current alpha.27 status

Latest compiled candidate:
- `v0.3.0-alpha.27.0.7.1 — MiMi Attic Test Access TEST`.
- CI run `33150445901`: **SUCCESS**.
- CI compile: **PASS**.
- CI package: **PASS**.
- Source milestone commit: `8e289fd633bb82b434867697dde01334c8712458` (before this handoff-only docs commit).
- Artifact ID: `9677482228`, name `cardcha-alpha27-attic-test-access`.
- TEST ZIP SHA256: `7a6f8e9e5cbd425ab5d93c8b788bf42cb701568a9c946c00c9c7ba394767eeb0`.

Implemented alpha.27 foundation still includes:
- MiMi real friendship/social NPC after Wizard-house meetup;
- Social tab + vanilla gifting;
- birthday **Spring 17**;
- controller-friendly one-button priority: held gift -> gifting, first empty-hand talk -> dialogue, later empty-hand action -> shop;
- stable attic location ID `Cardcha_MiMiAttic`;
- normal attic access at **2 hearts** after the MiMi meetup/story prerequisite;
- schedule foundation: 11:00–17:00 Monday–Friday work, attic outside work/weekends;
- Community Center workplace foundation for restored non-Joja route;
- Wizard House work fallback during harsh weather;
- staircase/access integration without wholesale WizardHouse replacement.

## Alpha.27.0.7 — MiMi Attic True Stardew Map

This milestone replaces the rejected alpha.27.0.6 visual technique. Important locked technical direction:
- **Do not return to a room-sized custom background PNG.**
- The room shell is a real **22x14 TMX tile map**.
- `assets/mimi_attic.tmx` references the game's vanilla `Maps/townInterior` tilesheet directly.
- The rejected `assets/mimi_attic_tiles.png` 352x224 full-room pseudo-tilesheet is intentionally absent.
- Beds, tables, chairs, TV, couch, rugs, plants, dresser, window, posters, etc. are instantiated as real vanilla Stardew `Furniture` objects.
- Keep custom Cardcha art subtle and add it only after the vanilla-base room passes visual/gameplay acceptance.

Five locked zones:
1. entrance / stair landing;
2. research desk;
3. bed / personal corner;
4. TV secret zone;
5. ChaCha / upgrade corner.

Current layout intent:
- research / bookcase / desk: upper-left;
- bed / dresser / bedside: upper-right;
- TV + couch nook: lower-left;
- ChaCha / prototype table: lower-right;
- bottom-center doorway/landing and a clear central walking route.

## Alpha.27.0.7.1 — MiMi Attic Test Access

This milestone adds a **runtime-only tester bypass** so the attic can be validated without grinding friendship/story state.

Command:
- `cardcha_test_attic`
- from anywhere in a loaded save: warp directly into `Cardcha_MiMiAttic`;
- run it again while inside the attic: return to `WizardHouse`;
- test access enables attic vanilla furniture population and Desk / TV / ChaCha inspect handling even if the normal meetup prerequisite is not complete;
- the command does **not** add friendship points, set `MimiMeetupCompleted`, change story flags, or remove the real 2-heart gameplay requirement.

Normal gameplay remains unchanged:
- MiMi meetup/story prerequisite required;
- **2 hearts** required for normal attic access;
- normal entry remains through the WizardHouse attic interaction point.

## Canon MiMi assets

- `mimi_portraits.png` canonical size = **768x128**.
- Do not silently restore rejected portrait experiments.

## 0.7.1 package verification

The produced TEST ZIP was unpacked and checked:
- `Cardcha.dll` exists, 458752 bytes;
- manifest version is `0.3.0-alpha.27.0.7.1`;
- `assets/mimi_attic.tmx` exists and references `Maps/townInterior`;
- `assets/mimi_attic_tiles.png` is absent as intended;
- EN and VI contain `mimi.attic.inspect.desk`, `.tv`, and `.chacha`;
- ZIP integrity test passed;
- external SHA256 matches workflow `SHA256.txt`.

CI/artifact verification proves source/package validity. It does **not** yet prove in-game xTile rendering, vanilla furniture placement, collision, or the debug command behavior on the user's installed Stardew setup.

## Next action — in-game acceptance

Use `v0.3.0-alpha.27.0.7.1_MiMiAttic_TestAccess_TEST`.

**Prerequisites:**
- only a loaded save is required when using the test bypass;
- normal gameplay access still requires meetup + 2 hearts.

**How to test:**
- open the SMAPI console and run `cardcha_test_attic`;
- inspect the room;
- run `cardcha_test_attic` again to return to WizardHouse.

**What to verify:**
- command enters/exits without changing progression;
- TMX resolves vanilla `Maps/townInterior` without xTile/SMAPI errors;
- room shell and doorway read naturally at actual Stardew camera scale;
- all runtime vanilla furniture IDs render correctly;
- player has a clear central path and does not spawn inside furniture;
- Desk / TV / ChaCha inspect points can be triggered under test access;
- furniture cannot be picked up/moved in an undesirable way;
- if the save already meets normal prerequisites, normal 2-heart entry/exit still works too.

**Out of scope:**
- full 17:30 / 6-heart TV routine/event;
- full heart event;
- ChaCha upgrade system;
- Community Center contribution mechanic.

If visual adjustments are needed, change **layout / vanilla furniture choices / vanilla tile choices** inside this true-map system. Do not revert to the full-room custom PNG approach.

Only after the room passes in-game acceptance should the project start the full 17:30 TV event or ChaCha upgrade mechanic.

## Read these docs before changing alpha.27

1. `docs/PROJECT_WORKING_RULES.md`
2. `docs/alpha27/MIMI_ATTIC_DESIGN_BIBLE.md`
3. `docs/alpha27/MIMI_CHARACTER_GIFTS_SCHEDULE.md`
4. `PROJECT_HANDOFF.md`
5. `docs/STORY_GAMEPLAY_BIBLE.md`

## Build rule

For each functional alpha.27 milestone, produce a **real CI-compiled TEST ZIP** before claiming completion.

## Controller regression note

Alpha.26.5.3 remains the rollback baseline because the final controller regression pass is still outstanding. Do not let that block alpha.27 development, but preserve the rollback point.

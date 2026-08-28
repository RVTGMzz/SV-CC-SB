# NEXT SESSION — Cardcha Alpha.27

## Current branches

- `main` = temporary rollback baseline `v0.3.0-alpha.26.5.3`.
- Active development branch = `cardcha-alpha27-mimi-real-npc`.
- Do **not** rebuild alpha.27 from old alpha.25/26 snapshots; continue from the active branch source.

## Current alpha.27 status

Latest compiled visual candidate:
- `v0.3.0-alpha.27.0.6 — MiMi Attic Vanilla-Style Rework TEST`.
- CI compile: **PASS**.
- CI package: **PASS**.
- PNG was regenerated on the CI runner and then opened/decoded from the produced TEST ZIP successfully.
- Current source milestone commit: `b7b544d5c35189f5b03a75a5402f07dda7e0bee3` (before this handoff-only docs commit).
- TEST ZIP SHA256: `d843a2c19b7c998311570cefbaf420f13eb048b949d5361d8aa2f0ee8dc9b80f`.

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

## Alpha.27.0.6 — MiMi Attic Vanilla-Style Rework

This is the visual-direction correction after alpha.27.0.5. The user preferred a room that reads much closer to normal Stardew indoor maps: dark/black void around the room, stronger wall shell, a visually obvious doorway/stair opening, and furniture with darker outlines instead of a flat custom-background look.

Five locked zones are still represented:
1. entrance / stair landing;
2. research desk;
3. bed / personal corner;
4. TV secret zone;
5. ChaCha / upgrade corner.

Implementation notes:
- attic map asset remains `Maps/Cardcha_MiMiAttic`;
- map source remains `assets/mimi_attic.tmx` at **22x14 tiles** with Back / Buildings / Front layers;
- room pixel art remains `assets/mimi_attic_tiles.png` at **352x224**;
- visual shell now includes visible black exterior/void, heavier dark room edges, wood trim, and a bottom-center doorway/stairwell opening;
- sleeping corner, research desk, central lived-in rug/table, tucked-away TV corner, and ChaCha prototype corner were redrawn to feel more like a Stardew indoor room and less like a flat mockup/workshop;
- Buildings-layer collision was updated to keep the central route and landing clear while blocking walls/furniture groundwork;
- desk / TV / ChaCha inspect groundwork and EN/VI flavor text remain active;
- attic remains MiMi's home, not the main shop;
- the **17:30 / 6-heart** TV routine remains only an eligibility hook;
- full TV event, full heart event, full ChaCha upgrade mechanic, and Community Center contribution mechanic remain out of scope.

## Reproducible art generation

- `build_assets/make_mimi_attic_vanilla_style.py` is the text-source generator for the 0.6 room art.
- CI installs Pillow, regenerates `assets/mimi_attic_tiles.png`, opens/decodes the generated image, then compiles and packages the mod.
- This avoids binary corruption from direct connector upload and keeps the room art reproducible.

## Canon MiMi assets

- `mimi_portraits.png` canonical size = **768x128**.
- Do not silently restore the rejected 1152x192 or 1536x256 portrait experiments.
- Alpha.27.0.6 TEST package was checked and still contains the canonical 768x128 portrait.

## Next action

Use `v0.3.0-alpha.27.0.6_MiMiAttic_VanillaStyleRework_TEST` for the next in-game acceptance pass when a test machine is available. Verify:
- the custom TMX loads without SMAPI/xTile errors;
- black exterior/room shell looks natural at actual Stardew camera scale;
- bottom-center doorway/stairwell visually reads as the entrance/exit;
- the 2-heart staircase access still works;
- MiMi can stand/move safely in the attic;
- collisions do not trap the player or MiMi;
- desk / TV / ChaCha inspect points are reachable.

Only after the room passes in-game acceptance should the project start the full 17:30 TV event or ChaCha upgrade mechanic.

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

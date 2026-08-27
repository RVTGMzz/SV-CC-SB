# Cardcha! — Known Issues / Risks

This file tracks open or handoff-critical issues. It is not a list of every historical bug.

## P0 — Source-of-truth mismatch
**Status:** OPEN

The active GitHub branch documents alpha.23, but the checked-in `src/Cardcha/manifest.json` still reports alpha.10.

Risk: a new AI/developer may edit an obsolete source tree and accidentally reintroduce already-fixed bugs.

Required resolution:
- synchronize the alpha.23 source snapshot into GitHub;
- verify manifest/csproj both report alpha.23;
- compile on Windows;
- record exact last-known-good commit in `PROJECT_HANDOFF.md`.

## P0 — alpha.23 real compile/test not yet verified
**Status:** OPEN

Static validation passed, but the preparation environment did not have `dotnet` or Stardew/SMAPI assemblies.

Need:
- run `BUILD_ALPHA23_TEST.bat` on the user's Windows/Stardew environment;
- test generated ZIP in-game.

## P1 — Controller auto-detection can be hidden by Steam Input
**Status:** EXPECTED PLATFORM LIMITATION

Steam Input/Windows may expose Nintendo or PlayStation controllers as XInput/Xbox devices.

Mitigation already designed:
- layout override: Auto / Xbox / Nintendo / PlayStation / Generic;
- mapping override: Auto / Standard / NintendoNative;
- shared `ControllerProfileService`;
- `cardcha_controller_status` diagnostic command.

Do not “fix” one controller by hard-coding raw A/B/X/Y again.

## P1 — alpha.23 controller regression matrix pending user confirmation
Check:
- South only confirms/selects;
- East only favorites selected card;
- West only deselects;
- North only exits to gameplay;
- focus on Equip/Unequip/Upgrade + South executes the focused action;
- no second unintended exit button.

## P1 — Binder quick unequip regression pending alpha.23 confirmation
Historical regression: double activation of an equipped card stopped unequipping.

alpha.23 candidate restores quick toggle for both mouse double-click and controller double-confirm. Must verify in-game.

## P1 — Gacha visual cleanup pending alpha.23 confirmation
Need verify:
- result/reveal corners are visibly rounded;
- result icon is substantially larger;
- rarity text is removed from result cards;
- only localized Name + NEW/DUPLICATE remains;
- sparkle effect reads clearly when a card flips/reveals;
- old small inner rectangular aura is gone;
- full large outer panel pulses during resonance.

## P1 — EN/VI localization audit requires spot checks in game
alpha.23 candidate contains all 80 names/descriptions and localized per-star rules for EN/VI.

Need visual/content spot checks for:
- text wrapping/overflow;
- correct semantic pairing between languages;
- no leftover mixed-language fragments;
- clarified damage-variance wording.

## P2 — Builder log filename typo
`BUILD_ALPHA23_TEST.bat` currently writes `build-alpha22-log.txt`.

This does not affect compilation but should be renamed in the next builder revision to avoid confusion.

## P2 — CARDCHA_PROJECT_STATE.json contains historical sections
The state file intentionally contains older snapshots such as portable-machine 11.38 values, some marked HISTORICAL/SUPERSEDED.

Risk: future AI may quote an old price/milestone as current.

Rule: current handoff + Story/Gameplay Bible + latest candidate docs take precedence over explicitly historical sections.

## Design items intentionally TBD
These are not bugs and must not be silently decided:
- exact identities/mechanics of Boss 20 / 40 / 60;
- final exact MiMi boss lore/mechanics;
- airship name and precise map layout;
- exact Community Center contribution implementation details for every route/remixed bundle edge case;
- ChaCha passive internal cooldown duration;
- full list of ChaCha's 9 favorite foods and quest presentation per tier;
- future boss-expansion structure beyond the initial 80-card arc.

When one is explicitly decided, move it into the LOCKED section of `docs/STORY_GAMEPLAY_BIBLE.md` and update `PROJECT_HANDOFF.md` if it affects implementation safety.

# Cardcha! — Known Issues / Risks

This file tracks open or handoff-critical issues. It is not a list of every historical bug.

## RESOLVED — Source-of-truth mismatch
**Status:** RESOLVED

The current alpha.25 source is synchronized on `binder-v0.3-alpha1`.

Verified anchors:
- source anchor commit: `a083e0a0cb1eb94852964a6f732a73fd7f506b04`;
- `src/Cardcha/manifest.json`: `0.3.0-alpha.25`;
- `src/Cardcha/Cardcha.csproj`: `0.3.0-alpha.25`;
- exact `src/Cardcha` Git tree: `89cff25d67700762ed94399a5905bdf1a52e736f`.

That tree matches all 69 files in the alpha.25 source snapshot byte-for-byte.

## RESOLVED — Cinderbox/GMCM non-public API error
**Status:** FIXED IN alpha.24, retained in alpha.25

alpha.23 could log:
`Tried to map a mod-provided API to non-public interface 'Cardcha.Integrations.IGenericModConfigMenuApi'; must be a public interface.`

`IGenericModConfigMenuApi` is now public. Do not regress this visibility.

An unrelated button/remapping issue from another conversation was fixed separately and is not part of this Cardcha compatibility issue.

## CURRENT BASELINE — alpha.25 user acceptance
**Status:** ACCEPTED WORKING BASELINE

The user tested alpha.25 in game and considers it okay as the current reference version. Use it as the rollback/canonical baseline for subsequent development.

This does **not** prove exhaustive release QA across every controller/platform/save state.

## P1 — Controller auto-detection can be hidden by Steam Input / virtual runtimes
**Status:** EXPECTED PLATFORM LIMITATION

Steam Input or virtual gamepads may expose Nintendo/PlayStation/touch devices as XInput/Xbox devices.

Mitigations:
- layout override: Auto / Xbox / Nintendo / PlayStation / Generic;
- mapping override: Auto / Standard / NintendoNative;
- shared `ControllerProfileService`;
- `cardcha_controller_status` diagnostic command.

Do not fix one controller by hard-coding raw A/B/X/Y throughout menus.

## P1 — Controller regression matrix remains relevant after future changes
Check:
- South only confirms/selects;
- East only favorites selected card;
- West only deselects;
- North only exits;
- focused Equip/Unequip/Upgrade + South executes intended action;
- no unintended second exit button.

## P1 — Binder quick unequip must not regress
Double activation of an equipped card must unequip it for both mouse and semantic controller Confirm while preserving the locked-card selection model.

## P1 — Gacha alpha.25 visual contract must not regress
Verify Stationary and Portable rituals:
- results/reveal remain rounded;
- result icon remains large;
- rarity text stays removed from result cards;
- localized Name + NEW/DUPLICATE remains;
- sparkle effect remains readable;
- no old small rectangular machine aura;
- resonance uses a near-full-panel interior filter;
- the outer gold frame/border remains visually stable and does **not** pulse with the filter.

## P1 — EN/VI localization needs ongoing spot checks
Check text wrapping, semantic alignment, no accidental mixed-language fragments, and damage-variance wording whenever UI/card text changes.

## P1 — Default branch is older/diverged
Repository default branch `main` is still an older lineage and has diverged from `binder-v0.3-alpha1`.

Do not update `main` by copying only a handful of alpha.25 files. Reconcile it deliberately through a compare/merge/PR so history and all source/docs move together.

## P2 — CARDCHA_PROJECT_STATE.json contains historical sections
Older values can remain in historical/superseded sections. Current source + `PROJECT_HANDOFF.md` + Story/Gameplay Bible take precedence.

## Design items intentionally TBD
These are not bugs and must not be silently decided:
- exact identities/mechanics of Boss 20 / 40 / 60;
- final exact MiMi boss lore/mechanics;
- airship name and precise map layout;
- exact Community Center contribution edge cases;
- ChaCha passive internal cooldown;
- exact nine favorite foods / quest presentation per tier;
- future boss expansion beyond the initial 80-card arc.

When one is explicitly decided, move it into the LOCKED section of `docs/STORY_GAMEPLAY_BIBLE.md` and update `PROJECT_HANDOFF.md` if it affects implementation safety.

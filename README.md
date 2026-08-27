# Cardcha! / Cardcha-Shardbound

Cardcha! is a Stardew Valley SMAPI mod project centered on an 80-card collection, gacha pulls, combat cards, MiMi/ChaCha story progression, and a growing Binder UI/system.

## Current documented candidate
**v0.3.0-alpha.23 — Multi-Controller + Gacha Polish**

Important: the GitHub `src/` tree is not yet fully synchronized to the packaged alpha.23 source candidate. Read `PROJECT_HANDOFF.md` before editing anything.

## Start here
For a new developer, AI session, or account migration, read in this order:
1. `PROJECT_HANDOFF.md`
2. `NEXT_SESSION_START_HERE.md`
3. `docs/STORY_GAMEPLAY_BIBLE.md`
4. `BUILD.md`
5. `KNOWN_ISSUES.md`
6. `CHANGELOG.md`

## Current alpha.23 focus
- semantic multi-controller support instead of controller-brand-specific hard-coding;
- persistent Binder locked-card action context;
- reliable double-click/double-confirm equip/unequip;
- rounded/simplified Gacha result presentation with large icons and reveal sparkles;
- full large-panel ritual flash;
- English/Vietnamese localization consistency.

## Build
Use the versioned full Windows builder for the candidate and follow `BUILD.md`.

Do not call a candidate stable until it has both:
- compiled against real Stardew Valley + SMAPI assemblies;
- passed relevant in-game regression tests.

## Story / future progression
The agreed MiMi / ChaCha / 20-40-60-80 boss / airship direction is documented in `docs/STORY_GAMEPLAY_BIBLE.md`, which explicitly separates LOCKED decisions from TBD ideas.

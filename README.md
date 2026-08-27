# Cardcha! / Cardcha-Shardbound

Cardcha! is a Stardew Valley SMAPI mod project centered on an 80-card collection, gacha pulls, combat cards, MiMi/ChaCha story progression, and the Binder UI/system.

## Current canonical candidate
**v0.3.0-alpha.25 — Gacha Interior Flash**

The canonical repository baseline is now on **`main`**. The development branch `binder-v0.3-alpha1` has been reconciled with this baseline and can continue future v0.3 work from the same history.

Verified alpha.25 source anchor:
- source commit: `a083e0a0cb1eb94852964a6f732a73fd7f506b04`
- exact `src/Cardcha` tree: `89cff25d67700762ed94399a5905bdf1a52e736f`
- promotion merge to `main`: `ef7b34bbd9aebdd53c2aae3c6ead60606a1c8d33`

The alpha.25 source tree matches `Cardcha_v0.3.0-alpha.25_SOURCE_SNAPSHOT.zip` byte-for-byte across all 69 source files.

## Start here
For a new developer, AI session, or account migration, read in this order:
1. `PROJECT_HANDOFF.md`
2. `NEXT_SESSION_START_HERE.md`
3. `docs/STORY_GAMEPLAY_BIBLE.md`
4. `BUILD.md`
5. `KNOWN_ISSUES.md`
6. `CHANGELOG.md`

## Current alpha.25 baseline
- semantic multi-controller support remains centralized through `ControllerProfileService`;
- Binder locked-card selection and quick equip/unequip behavior remain protected;
- GMCM integration uses a public API interface, fixing the alpha.23 Cinderbox/SMAPI mapping error;
- Gacha reveal/result cards remain rounded with large icons, localized NEW/DUPLICATE state, and reveal sparkles;
- ritual flash is now a rarity/white filter across the panel interior while the outer gold frame remains visually stable;
- English/Vietnamese card localization remains aligned.

The user has accepted alpha.25 as the current working baseline after in-game testing. Treat it as the project’s canonical working version, not as a final public stable release unless broader regression testing is completed.

## Build
Use the versioned full Windows builder for the candidate and follow `BUILD.md`.

## Story / future progression
The agreed MiMi / ChaCha / 20-40-60-80 boss / airship direction is documented in `docs/STORY_GAMEPLAY_BIBLE.md`, which explicitly separates LOCKED decisions from TBD ideas.

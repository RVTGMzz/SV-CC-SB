# Binder v0.3 alpha.1 — Candidate Validation

**Date:** 2026-08-26  
**Candidate branch:** `binder-v0.3-alpha1`

## Static checks completed

- 80 cards loaded from `assets/cards.json`.
- Card IDs: 80 unique.
- Base IDs: 80 unique, continuous 1–80.
- Icon indexes: 80 unique, continuous 0–79.
- Every card satisfies `IconIndex = BaseId - 1`.
- Rarity distribution: 27 Common / 23 Rare / 16 Epic / 10 Legendary / 4 Mythic.
- Every card has `StarRules`; Binder uses these for per-star display when available.
- English and Vietnamese i18n both contain name + description keys for all 80 cards.
- Every literal translation key referenced by the new Binder exists in both English and Vietnamese i18n.
- Save schema 12 persists `FavoriteCardIds` by stable string card ID and includes favorites in the persistence fingerprint.
- Controller A is explicitly consumed as an in-book action; B handles return/close.
- Locked cards keep the real rarity border and use a cached **true grayscale atlas**, not a black tint/silhouette.
- C# delimiter sanity checks passed for all changed source files.

## Not yet verified

This environment does not have the .NET/Stardew/SMAPI build toolchain, so these still require the Windows/Stardew builder:

1. compile against the real Stardew + SMAPI references;
2. open Binder from Machine and inventory Book tab;
3. inspect UI scale/readability and controller traversal in game;
4. save/reload Favorite persistence;
5. regression-test MiMi, portable machine, gacha and combat HUD.

Do not merge/promote this candidate as a tested release until the real Windows build passes.

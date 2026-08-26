# NEXT SESSION — Cardcha v0.3.0-alpha.1 Binder UI

## Start here first

Read:

1. `design/BINDER_V0_3_CURRENT.md` — authoritative Binder/UI decisions and the exact last approved chat state.
2. `design/CARDCHA_DESIGN_CURRENT.md` — Base Set/Boss Slot/progression design.
3. `CARDCHA_PROJECT_STATE.json` — story/gameplay state inherited from the 11.45 source line.

## Latest preserved implementation work — 2026-08-26

A complete source snapshot of the current v0.3 Binder work is preserved at:

`snapshots/Cardcha_v0.3.0-alpha.1_BinderUI_SOURCE_SNAPSHOT.zip`

The snapshot has been advanced from the old 10-card/11.45 Binder source toward `0.3.0-alpha.1`:

- synchronized the approved **80-card visual/data snapshot** from `Cardcha_v0.2.0-beta.2_80CardVisuals_TEST`;
- Base IDs are 1–80 and IconIndex is 0–79;
- synchronized the 80-card atlas and bilingual i18n snapshot;
- added Binder v0.3 favorite persistence (`SaveData.SchemaVersion = 12`);
- rebuilt Binder around a near-full-screen two-page collection-book layout;
- collection is icon-only with Base ID + Lv + rarity border;
- locked cards retain their real rarity border and render as dark silhouette/grayscale;
- equipped cards receive an in-cell `IN USE / ĐANG DÙNG` overlay;
- rarity bookmarks filter the collection while preserving Base-ID order;
- Favorites is a separate bottom bookmark and persists by string card ID;
- five active slots are circular and the future Boss Slot is shown as a separate locked circle;
- right page contains readable selected-card details and actions;
- controller A is explicitly consumed as an in-book action and cannot close the Binder;
- the center seam is intentionally thin; no `assets/binder_book_frame.png` is required by the new Binder class.

## Mandatory first test on Windows/Stardew

This source snapshot was prepared without a local Stardew/SMAPI build environment, so the first next action is a real build/test with `BUILD_CARDCHA.bat` before treating it as a playable release.

Check in this order:

1. project compiles after the Binder class replacement;
2. open Binder from Machine and inventory Book tab;
3. verify 80 cards are visible across four All pages;
4. verify locked card = real rarity border + silhouette;
5. verify Favorite add/remove survives save/reload;
6. verify rarity/favorite bookmarks filter correctly and preserve Base-ID order;
7. verify equipped overlay appears on the matching Collection cell;
8. verify A never exits the book; B/back still returns correctly;
9. verify text is readable at the user's normal UI scale;
10. verify no missing `binder_book_frame.png` warning occurs from Binder;
11. regression-test MiMi, portable machine, gacha and combat HUD.

## Critical caveat: 80-card data vs runtime effects

The 80-card visual snapshot contains many effect keys that are newer than the old 10-card source baseline. Treat the preserved snapshot as authoritative for the **collection data/art/UI work**, but audit actual Combat/Drop/Gacha implementation before claiming all 80 card effects are active.

Do not silently reduce the registry back to the old 10-card `cards.json`.

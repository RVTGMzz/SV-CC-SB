# NEXT SESSION — Cardcha v0.3.0-alpha.1 Binder UI

## Start here first

Read:

1. `design/BINDER_V0_3_CURRENT.md` — authoritative Binder/UI decisions and the exact last approved chat state.
2. `design/CARDCHA_DESIGN_CURRENT.md` — Base Set/Boss Slot/progression design.
3. `CARDCHA_PROJECT_STATE.json` — story/gameplay state inherited from the 11.45 source line.
4. Branch `binder-v0.3-alpha1` — current r2 candidate handoff and validation notes.

## Latest preserved implementation work — 2026-08-26

Safe `main` still preserves the first v0.3 snapshot at:

`snapshots/Cardcha_v0.3.0-alpha.1_BinderUI_SOURCE_SNAPSHOT.zip`

The newer r2 candidate is tracked on branch `binder-v0.3-alpha1`. Read:

- `handoff/BINDER_V03_ALPHA1_CANDIDATE_STATUS.md`
- `handoff/BINDER_V03_ALPHA1_R2_CORRECTIONS.patch`
- `design/BINDER_V0_3_VALIDATION.md`

Latest Binder direction:

- synchronized the approved **80-card visual/data snapshot** from `Cardcha_v0.2.0-beta.2_80CardVisuals_TEST`;
- Base IDs are 1–80 and IconIndex is 0–79;
- synchronized the 80-card atlas and bilingual i18n snapshot;
- added Binder v0.3 favorite persistence (`SaveData.SchemaVersion = 12`);
- rebuilt Binder around a near-full-screen two-page collection-book layout;
- collection is icon-only with Base ID + Lv + rarity border;
- locked cards retain their real rarity border and use **true grayscale artwork**, not a black silhouette tint;
- equipped cards receive an in-cell `IN USE / ĐANG DÙNG` overlay;
- rarity bookmarks filter the collection while preserving Base-ID order;
- Favorites is a separate bottom bookmark and persists by string card ID;
- five active slots are circular and the future Boss Slot is shown as a separate locked circle;
- right page contains readable selected-card details and actions;
- r2 uses the 80-card `StarRules` for per-star Binder display when available;
- controller A is explicitly consumed as an in-book action and cannot close the Binder;
- the center seam is intentionally thin; no `assets/binder_book_frame.png` is required by the new Binder class.

## Mandatory next action: Windows/Stardew build

Static data/source validation passed, but the ChatGPT environment does not have the .NET/Stardew/SMAPI build toolchain. Do **not** treat v0.3 alpha.1 as compiled/tested yet.

Check in this order:

1. compile the r2 candidate against the real Stardew + SMAPI install;
2. open Binder from Machine and inventory Book tab;
3. verify 80 cards are visible across four All pages;
4. verify locked card = real rarity border + true grayscale icon;
5. verify Favorite add/remove survives save/reload;
6. verify rarity/favorite bookmarks filter correctly and preserve Base-ID order;
7. verify equipped overlay appears on the matching Collection cell;
8. verify A never exits the book; B/back still returns correctly;
9. verify text is readable at the user's normal UI scale;
10. verify no missing `binder_book_frame.png` warning occurs from Binder;
11. regression-test MiMi, portable machine, gacha and combat HUD.

If compile fails, preserve `build-v03-alpha1-log.txt` and continue from that error log instead of redesigning the Binder again.

## Critical caveat: 80-card data vs runtime effects

The 80-card visual snapshot contains many effect keys that are newer than the old 10-card source baseline. Treat the preserved data/art/UI snapshot as authoritative for the **collection**, but audit actual Combat/Drop/Gacha implementation before claiming all 80 card effects are active.

Do not silently reduce the registry back to the old 10-card `cards.json`.

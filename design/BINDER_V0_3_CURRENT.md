# Cardcha Binder v0.3 — Current Approved State

**Snapshot:** 2026-08-26  
**Target implementation:** `0.3.0-alpha.1`  
**Source of truth:** this repository + the preserved 80-card data/atlas synchronized from `Cardcha_v0.2.0-beta.2_80CardVisuals_TEST.zip`.

Preserved build snapshot checksum (SHA-256): `85c40046206bc6fdf11f7cd8aeb100f59ebca3be4d97724e4256835edf47a953`.

## Why this file exists

This handoff is intentionally detailed so a future ChatGPT/session can continue from GitHub without reconstructing decisions from old chat threads.

## Visual direction

The Binder is a custom Cardcha UI. Do **not** add Parchment as a dependency.

Reference direction from the approved book examples:

- open two-page fantasy collector notebook;
- near-full-screen so Stardew text is readable;
- very thin center seam/shadow, **not** a thick brown spine and **not** a large black spiral binding;
- collection page inspired by icon-grid journals: icons first, text only after selecting a card;
- detail page inspired by readable recipe/journal layouts: clear blocks, generous spacing, larger text;
- soft/rounded outer book, page panels, cells and buttons; equipped slots are circular.

## Left page — Equipped + Collection

### Equipped area

- Show five normal active-card slots as circles.
- Empty/unlocked slot = quiet circular inset.
- Locked normal slot = circular lock state.
- Boss Slot is one separate circular slot and remains locked until the future Boss system is implemented.
- The equipped row is only a quick loadout overview; detailed state is visible in Collection.

### Collection cells

Collection is icon-only. Do not render card names in the grid.

Every cell shows:

- stable Base ID (`01`–`80`);
- `Lv`;
- real rarity border;
- card icon;
- favorite marker when applicable;
- `ĐANG DÙNG` / `IN USE` overlay directly on the cell when equipped.

Approved locked-card rule:

> **A card that is not unlocked still keeps its real rarity border, but its icon is grayscale/silhouette.**

Locked cells stay in their fixed Base-ID positions. Do not reorder the main collection by unlock date, rarity, level or name.

## Stable numbering

The 80-card visual snapshot defines:

- `BaseId` 1–80;
- `IconIndex` 0–79;
- convention: `IconIndex = BaseId - 1`.

The code may fall back to `IconIndex + 1` only when older prototype data has no explicit `BaseId`.

## Bookmarks / filters

Main rarity bookmark cluster at the left edge:

1. Tất Cả / All
2. Thường / Common
3. Hiếm / Rare
4. Sử Thi / Epic
5. Huyền Thoại / Legendary
6. Thần Thoại / Mythic

`♥/★ Yêu thích / Favorites` is **separate near the bottom of the book**, with a visible gap from the rarity cluster. It is a personal shortcut, not a rarity.

Filtering never changes Base-ID order inside the result.

## Favorite system

Save favorites by stable string card ID, not grid index.

- Only unlocked/owned cards may be favorited.
- Detail page has Favorite / Unfavorite action.
- Favorite cards show a small marker in Collection.
- Favorites bookmark only displays owned cards that are currently favorited.
- Favorites remain sorted by Base ID.
- Invalid/unowned favorite IDs are pruned safely.

Save schema for this implementation: **12**.

## Pagination

Target page size: `5 × 4 = 20` collection cells.

With the Base Set 80 and no filter this gives four pages:

- 01–20
- 21–40
- 41–60
- 61–80

Filtered views compute page count dynamically while retaining the card's real Base ID.

## Right page — Detail

When no card is selected, show a clean selection hint.

When an owned card is selected, show:

- large icon;
- stable `#ID`;
- name;
- rarity;
- current level/stars;
- current effect;
- star-level effect rows;
- upgrade-copy requirement;
- actions: Favorite/Unfavorite, Equip/Unequip, Upgrade.

A locked card may show its ID/rarity and locked state, but should not expose full effect information as if owned.

## Controller rules

- A while inside Binder performs the focused Binder action. **A must never close the book.**
- B closes/returns.
- Controller traversal should flow approximately `Equipped → Collection → Detail actions`.
- Changing a page/filter must clamp focus to a valid component.

## Scope of v0.3 alpha.1

Included:

- Binder layout refactor;
- near-full-screen book;
- thin center seam;
- 80-card Base-ID data/atlas sync;
- rarity bookmarks;
- separate Favorites bookmark;
- favorite persistence;
- icon-only collection;
- rarity borders;
- locked silhouettes;
- ID + Lv;
- equipped overlay;
- circular equipped slots;
- readable right-side details;
- A-button regression guard.

Not part of this UI pass:

- Boss Card implementation;
- ChaCha Boss transformation;
- balance redesign;
- implementing every one of the 80 card effect keys;
- new MiMi story chapters.

## Important implementation caveat

The synchronized `0.2.0-beta.2_80CardVisuals_TEST` data contains 80 cards and many effect keys beyond the old 10-card prototype source. The visual/data sync is intentional so the repository no longer loses the approved Base Set snapshot, but **do not assume every one of those 80 runtime effects is implemented merely because its card data exists**. Runtime effect implementation must be audited separately against Combat/Drop/Gacha services.

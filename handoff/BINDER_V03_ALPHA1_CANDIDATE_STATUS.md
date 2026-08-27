# Binder v0.3.0-alpha.1 — Candidate Status

Branch: `binder-v0.3-alpha1`
Baseline: main commit `8d23d0ef63c7eae70041e46fe77111c5e7250b4f`
Date: 2026-08-26

This branch preserves the first Windows-build candidate for the approved Binder v0.3 redesign. Keep main as the safe baseline until a real Stardew/SMAPI compile and in-game regression pass succeeds.

Approved rules:
- custom open-book UI, no Parchment dependency;
- near-full-screen layout with thin center seam;
- icon-only collection ordered by stable Base ID;
- 20 cards/page, so Base Set 80 gives four All pages;
- cells show Base ID, Lv, rarity border and Favorite marker;
- equipped cells get IN USE / ĐANG DÙNG overlay;
- locked cells keep the real rarity border and use true grayscale artwork;
- five circular normal slots plus one separate future locked Boss Slot;
- rarity bookmarks are grouped left; Favorite is separate near the bottom;
- Favorites persist by stable string card ID;
- controller A acts inside Binder and must not close it; B returns/closes.

Data baseline: 80 unique cards, BaseId 1-80, IconIndex 0-79, IconIndex = BaseId - 1, rarity counts 27/23/16/10/4 for Common/Rare/Epic/Legendary/Mythic, 64x64 cells in a 320x1024 atlas, English + Vietnamese card text.

This does not claim all 80 runtime combat effects are implemented. This pass is Binder UI + collection data/visual integration + Favorite persistence.

r2 correction: the earlier alpha.1 snapshot used a black tint for locked artwork. r2 instead builds a cached grayscale atlas at runtime and keeps the original rarity frame separate. r2 also uses 80-card StarRules for per-star Binder display when available. Exact r1 -> r2 changes are in `handoff/BINDER_V03_ALPHA1_R2_CORRECTIONS.patch`.

Real Windows/Stardew build is still required before merge to main. On failure, preserve `build-v03-alpha1-log.txt`.

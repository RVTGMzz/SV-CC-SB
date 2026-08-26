# NEXT SESSION — Cardcha v0.3.0-alpha.18 Binder Lock + Typography

## Current candidate
- Version: `0.3.0-alpha.18`
- Build label: `Cardcha! v0.3.0-alpha.18 BINDER LOCK + TYPOGRAPHY`
- Baseline: alpha.17 Mythic + Minimap.

## Binder lock rewrite
1. Binder now separates free preview state (`PreviewCard`) from explicit action lock (`LockedCard`).
2. A or mouse click on a collection card creates/replaces `LockedCard`.
3. Ordinary controller movement across the grid does not mutate `LockedCard` and does not clear it.
4. Forced RIGHT/DOWN interception was removed; the normal clickable-neighbor graph lets the player move naturally across the grid and into the action buttons.
5. Favorite/Equip/Upgrade restore `LockedCard` immediately before acting.
6. Only `BỎ CHỌN / DESELECT` clears `LockedCard`; after that free preview follows the focused card again.
7. Locked card gets an explicit cyan + white double-border indicator so the player can see which card remains pinned even while focus moves elsewhere.

## UI fixes
- Prev/Next page controls are now pixel-drawn chevrons instead of font glyphs, preventing the left button from rendering as a heart or star.
- `Đã khám phá / Discovered`, current filter caption (`Tất cả`, rarity names), and not-owned/status text were enlarged to the same visual tier as `Trang x/y` across the shared Binder renderer.
- Vietnamese discovery footer shortened to `Đã khám phá: X/80` to keep the larger text readable.

## Inherited alpha.17 behavior
- Binder heading is just `BỘ SƯU TẬP / COLLECTION`.
- User-facing Boss slot wording is `Kỹ năng Thần Thoại / Mythic Skill`.
- MiMi/??? NPC Map Locations marker crop uses the dedicated full-face 16x15 marker and corrected Vanilla MugShotSourceRect.

## Test first
1. Free browse without A: right page previews each focused card.
2. A-select #34: #34 gets the lock border and right page stays on #34.
3. Move over #35/#40 and navigate into Favorite/Equip/Upgrade: all actions must still target #34.
4. Change page/filter while locked: #34 remains the action target until `BỎ CHỌN`.
5. Press `BỎ CHỌN`: free preview resumes.
6. Footer page controls must visibly be `<` and `>`-shaped pixel arrows, never a heart/star.
7. `Đã khám phá`, `Tất cả`, and `Chưa sở hữu lá này...` should visually match `Trang x/y` size.

## Artifacts
- `Cardcha_v0.3.0-alpha.18_BinderLockTypography_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.18_SOURCE_SNAPSHOT.zip`

Targeted static validation: 21/21 PASS. Real Windows compile with Stardew/SMAPI references is still required.
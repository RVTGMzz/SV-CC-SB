# NEXT SESSION — Cardcha v0.3.0-alpha.20 Control Hints

## Current candidate
- Version: `0.3.0-alpha.20`
- Build label: `Cardcha! v0.3.0-alpha.20 CONTROL HINTS`
- Baseline: alpha.19 Controller Remap.

## Exact alpha.20 behavior
1. A compact hint bar renders outside and immediately below the Binder.
2. Controller mode shows: `B Chọn/Xác nhận`, `A Yêu thích`, `Y Bỏ chọn`, `X Thoát`.
3. Keyboard mode shows: `Enter/Space Chọn/Xác nhận`, `F Yêu thích`, `Backspace Bỏ chọn`, `Esc Thoát`.
4. The bar follows whichever input family was used most recently.
5. Favorite and Deselect hints are dim until a LockedCard exists.
6. `F` toggles Favorite only for LockedCard; `Backspace` releases the LockedCard.
7. The book height reserves a narrow strip so the hint bar never covers page content.

## Regression requirements
- B still activates focused Equip/Unequip/Upgrade controls.
- A still Favorites only the locked card.
- Y still deselects.
- X/Esc still closes Binder + visual parent and returns to gameplay.
- PreviewCard/LockedCard separation from alpha.18 must remain.

## Artifacts
- `Cardcha_v0.3.0-alpha.20_ControlHints_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.20_SOURCE_SNAPSHOT.zip`

Static validation passed in the container; real Windows compile with Stardew/SMAPI references is still required.
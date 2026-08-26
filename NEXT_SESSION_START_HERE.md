# NEXT SESSION — Cardcha v0.3.0-alpha.16 Binder Deselect + Browse

## Current candidate
- Version: `0.3.0-alpha.16`
- Build label: `Cardcha! v0.3.0-alpha.16 BINDER DESELECT + BROWSE`
- Baseline: alpha.15 Gacha + Controller + Minimap.

## Exact controller/Binder behavior
1. When no card is locked, moving controller/keyboard focus across collection cells previews the newly focused card immediately; A is not required just to inspect cards.
2. Pressing A on a card locks that card as the action context. Moving focus elsewhere does not change the selected card.
3. New `DESELECT / BỎ CHỌN` button releases that lock.
4. With controller, Deselect returns focus to the currently selected card cell when it is visible, then free-preview mode resumes.
5. After deselect, moving to #04/#05/etc updates right-page information live; pressing A on a card locks that card again.
6. Double-A quick equip/unequip remains available.

## Inherited behavior that must remain
- alpha.15 fresh-runtime gacha entropy, literal `<` / `>` page arrows, larger Scrap count text, one-frame MiMi arrival-flash fix, NPC Map Locations integration.
- alpha.14 larger MiMi/???/ChaCha shadows and Binder X button.
- alpha.13 MiMi reveal/shop quantity/off-screen broom/portable feedback and compile hotfix.
- Binder 80-card collection, Favorite persistence, rarity filters, resource rail, 5 normal + Boss + ChaCha layout.

## Test first
1. Move across cards without A: right page must preview each focused card immediately.
2. A-select #03, move around several cells/buttons, then Equip/Favorite/Upgrade: action still targets #03.
3. Activate `BỎ CHỌN`: lock clears and controller returns to #03 cell.
4. Move to #04/#05 without A: preview changes live.
5. A-select #05: #05 becomes the new locked action target.

## Artifacts
- `Cardcha_v0.3.0-alpha.16_BinderDeselect_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.16_SOURCE_SNAPSHOT.zip`

Static validation passed in the container; real Windows compile with Stardew/SMAPI refs is still required.
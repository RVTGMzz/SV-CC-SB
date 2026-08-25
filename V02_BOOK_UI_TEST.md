# Cardcha v0.2 — Book Visual Pass Test

Build/install with Stardew Valley + SMAPI closed, then run `cardcha_open_binder`.

## Visual
- Open Binder is a balanced two-page leather/parchment book with a real central spine.
- Five rarity bookmarks sit outside the left edge: Common, Rare, Epic, Legendary, Mythic.
- Clicking a rarity filters only the collection grid; clicking the active rarity again clears the filter.
- Collection shows at most 10 cards per page (5 x 2) with working previous/next page controls.
- Locked normal loadout slots show a visible keyhole/lock badge instead of plain empty text.
- Dedicated circular Boss Slot is visually separate from the five normal slots.
- Boss Slot is locked below 20/80 discovered Base Cards and shows a keyhole.
- The external Stardew inventory Book tab uses the approved closed leather Cardcha cover icon.

## Regression
- Select card -> detail page updates.
- Equip / unequip still works.
- Normal card upgrades still work.
- Existing Suspicious Dust normal-slot unlock still works for this visual pass.
- Controller can browse cards, enter the right detail panel, scroll it, then reach action buttons.
- `B` closes the Binder normally.

## Scope note
The runtime registry currently still contains the implemented playable cards in `assets/cards.json`. The new Binder is layout-ready for the approved Base Set target of 80 cards and the five-rarity distribution. Boss-card combat/transformation mechanics are **not** activated by this visual pass; only the dedicated Boss Slot UI/progression placeholder is introduced.

# NEXT SESSION — Cardcha v0.3.0-alpha.13 MiMi Shop + Full Flight

## Current candidate

- **Version:** `v0.3.0-alpha.13`
- **Build label:** `Cardcha! v0.3.0-alpha.13 MIMI SHOP + FULL FLIGHT`
- **Baseline:** alpha.12 Binder Select + Resource Rail
- **Official broom asset:** user `mimi_broom.zip` -> `src/Cardcha/assets/mimi_broom.png`

## Alpha.13 changes

1. Pre-handoff mystery phase may show `???`; after `MimiMeetupCompleted` or `MachineDelivered`, MiMi's display/portrait dialogue name is forced to `MiMi`.
2. Portable Machine purchase button is only disabled after ownership; being short on money no longer makes it look broken/gray.
3. Clicking/confirming Normal or Shiny Scrap buy/sell opens a quantity panel with `−`, `+`, Confirm, Cancel.
4. All active broom arrival/departure paths use off-screen viewport points: MiMi/??? fly in from beyond the screen and fly fully beyond the screen before being hidden.
5. Official user-supplied broom sheet is copied byte-for-byte. It is 128x192 with 32x48 cells.
6. Standing MiMi/??? remains `0.575f`; broom presentation uses `0.575 * 1.10 = 0.6325f` runtime scale to compensate the smaller body in the revised art without resizing/blurring the PNG.
7. Builder cleans old `bin/obj`, then verifies the manifest inside the produced ZIP equals `0.3.0-alpha.13`; a mismatch stops packaging.
8. Installation rule: delete the old `Mods\Cardcha` folder before installing this test build. Do not merge over alpha.11/alpha.12.

## Inherited alpha.12 behavior that must remain

- Single confirm selects a card only; explicit selection + RIGHT enters detail actions for the same card.
- Double-confirm quick equip/unequip remains available.
- Normal/Shiny counters remain on the Binder left rail with hover/controller tooltip.
- 5 normal + Boss grouped; ChaCha separated; Boss Mythic border; ChaCha pink.
- Binder book icon remains restored.
- Gacha full-panel flash remains.
- Current compatibility portable milestone text remains 20 unique cards until the quest/Boss flow replaces the direct gift bridge.

## Approved next progression (not implemented here)

- 20 unique cards -> ChaCha info begins unlocking -> quest -> Boss encounter -> Portable Machine reward.
- 40 unique cards -> quest/encounter -> ChaCha absorbs/fuses stationary + portable machines -> Cardcha directly from Binder.

## Test priority

1. Open `manifest.json` from the built test ZIP/install and verify `0.3.0-alpha.13`.
2. After handoff/machine delivery, MiMi portrait label is `MiMi`, never `???`.
3. Portable buy button is clickable when unowned, including when money is insufficient.
4. Buy/sell Normal and Shiny Scrap: quantity panel works with mouse and controller.
5. Watch mystery/merchant/story broom entry and exit: actor begins/finishes beyond visible screen, no mid-screen pop/disappear.
6. Compare standing vs broom MiMi/??? body size; +10% broom compensation should look consistent.
7. Regression: Binder selection/actions/resources/book icon, stationary/portable gacha, Favorite, save/reload, ChaCha follower.

## Source preservation

Conversation artifacts prepared for this candidate:
- `Cardcha_v0.3.0-alpha.13_MimiShopFlight_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.13_SOURCE_SNAPSHOT.zip`

Static validation passed, but a real Windows compile with Stardew Valley + SMAPI references is still required before calling alpha.13 playable.
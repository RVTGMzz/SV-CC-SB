# Cardcha: Shardbound v0.1.17-alpha.11.36

This Windows builder focuses on four gameplay corrections: MiMi actor cleanup, Scrap pickup feedback after the Binder handoff, Shiny Scrap pricing, and stationary Machine placement rules.

## Alpha 11.36

- MiMi can no longer be left standing at the player's farm by a stale story exit state.
- Scrap sent directly to the Binder wallet now shows Stardew's normal item-gained HUD toast.
- MiMi prices: **Normal** — buy 1,000g / sell 100g; **Shiny** — buy 10,000g / sell 1,000g. (From MiMi's perspective: she buys Shiny for 1,000g and resells it for 10,000g.)
- The stationary Cardcha Machine may only stay inside the **main FarmHouse**. Old misplaced copies are returned to the player on load.
- Official art assets remain locked and unchanged.

### Future direction (not activated in 11.36)

Portable Cardcha Machine: MiMi sells it for 50,000g early; if the player reaches 50 unique Binder cards without buying it, she gives one free. At 80 unique cards, a hidden Binder-direct Cardcha function is planned, requiring the stationary Machine + portable Machine + a third story item/condition to be designed later.

Run `BUILD_CARDCHA.bat`, then verify with `cardcha_version`.

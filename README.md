# Cardcha: Shardbound — v0.1.17-alpha.11.6

Current development handoff for the MiMi merchant + Scrap wallet story branch.

## Gameplay changes in alpha.11.6
- Wizard meetup MiMi renders at a player-readable 2x scale.
- MiMi walks toward the exit after the Wizard meetup.
- ChaCha follower renders at 2x with extra front-facing separation from the player.
- After the meetup, MiMi acts as a merchant from 11:00–17:00.
  - Clear weather: Farm near the farmhouse.
  - Rain: WizardHouse.
- MiMi buys Scrap from the player for 100g and sells Scrap for 1,000g.
- Regular and Shiny Scrap are stored in a Binder wallet instead of backpack slots.
- Existing physical Scrap items migrate into the wallet when loading a save.
- The Binder shows both Scrap balances.
- Vietnamese MiMi dialogue uses neutral `bạn/mình` wording.

## Windows builder installer hotfix
`BUILD_CARDCHA.bat` now treats a loaded `Cardcha.dll` as an **install pending** state, not a build failure.

If Stardew Valley / SMAPI is still running:
1. The build ZIP is kept in `_READY_TO_INSTALL`.
2. The builder lets you close the game and retry installation **without rebuilding**.
3. You can exit and later run `INSTALL_CARDCHA_ONLY.bat` to install the already-built package.

Windows cannot replace a DLL that SMAPI currently has loaded, so the installer intentionally does **not** force-kill the game process.

The `CS9057` message produced by .NET SDK 6.0.428 is a compiler/analyzer warning only. The logged build shown for alpha.11.6 completed with `0 Error(s)` and produced `Cardcha.dll` successfully.

## Handoff
Continue development from:
- `NEXT_SESSION_START_HERE.md`
- `BUILD_HISTORY.md`
- `CARDCHA_PROJECT_STATE.json`

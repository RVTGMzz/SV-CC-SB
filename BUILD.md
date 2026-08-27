# Cardcha! — Build & Test Guide

This file is the canonical build handoff for the current Cardcha candidate.

## Current candidate
- Version: `0.3.0-alpha.23`
- Builder: `BUILD_ALPHA23_TEST.bat`
- Expected output: `_READY_TO_TEST/Cardcha_v0.3.0-alpha.23_MultiControllerGachaPolish_TEST.zip`

## Requirements
- Windows
- Stardew Valley install containing `Stardew Valley.dll`
- SMAPI install containing `StardewModdingAPI.dll`
- .NET SDK capable of building `net6.0`
- PowerShell

The project currently targets `net6.0` and uses:
- `Pathoschild.Stardew.ModBuildConfig` 4.4.0
- `Newtonsoft.Json` 13.0.3

SMAPI manifest minimum API version in the alpha.23 candidate is `4.1.10`.

## Preferred build workflow
1. Extract the full Windows builder ZIP into its own fresh folder.
2. Do not merge it into an older builder/source folder.
3. Run `BUILD_ALPHA23_TEST.bat`.
4. The script searches common Stardew install paths. If it does not find the game, provide the Stardew Valley folder manually.
5. The script removes old `bin/` and `obj/` folders.
6. It runs `dotnet restore` and `dotnet build` against the detected game path.
7. It asks ModBuildConfig to create a mod ZIP.
8. It extracts the generated ZIP and verifies that `manifest.json` contains exactly `0.3.0-alpha.23`.
9. Only after the version guard passes does it copy the package into `_READY_TO_TEST`.

## Known user game path
The builder currently checks, among others:
`E:\SteamLibrary\steamapps\common\Stardew Valley`

Do not hard-code this as universal; let the user provide another path when needed.

## Install test build
Before installing a new test candidate:
1. delete the old `Mods/Cardcha` folder;
2. install/extract only the new test ZIP;
3. do not merge over an old alpha folder because stale manifests/assets have caused confusing regressions before.

## If build fails
Send the generated build log to the coding assistant.

Note: the alpha.23 builder currently names its log `build-alpha22-log.txt` even though it builds alpha.23. This is a cosmetic script defect and should be cleaned up in a future builder revision.

## Do not claim success early
Static source validation is not a real compile.
A candidate is compile-passed only after the Windows builder completes against actual Stardew/SMAPI assemblies and the version guard succeeds.
A candidate is stable only after relevant in-game regression tests are also confirmed.

## Minimum alpha.23 in-game test matrix
- Binder free preview vs locked-card action context.
- Double-click equipped card with mouse => unequip.
- Double-confirm equipped card with controller => unequip.
- Xbox/Standard semantic mapping.
- Nintendo override semantic mapping.
- Favorite / Deselect / Exit / Confirm each trigger only their intended action.
- Gacha reveal/result: rounded cards, large icon, Name + NEW/DUPLICATE only.
- Sparkles appear during reveal.
- Resonance flash covers the full large gold-bordered panel; no small inner rectangular aura.
- EN and VI card details are semantically aligned, especially damage-variance wording.
- MiMi and ChaCha older story/shop/world-actor behavior does not regress.

## Artifact naming discipline
Keep builder, source snapshot, and test ZIP names versioned outside the actual installed mod folder. The installed mod folder itself should remain stable rather than carrying the alpha number in its internal folder identity.

# Cardcha! — Build & Test Guide

This file is the canonical build handoff for the current Cardcha candidate.

## Current candidate
- Version: `0.3.0-alpha.25`
- Builder: `BUILD_ALPHA25_TEST.bat`
- Expected output: `_READY_TO_TEST/Cardcha_v0.3.0-alpha.25_GachaInteriorFlash_TEST.zip`
- Full builder artifact: `Cardcha_v0.3.0-alpha.25_GachaInteriorFlash_WindowsBuilder_FULL.zip`

## Requirements
- Windows
- Stardew Valley install containing `Stardew Valley.dll`
- SMAPI install containing `StardewModdingAPI.dll`
- .NET SDK capable of building `net6.0`
- PowerShell

Project dependencies:
- `Pathoschild.Stardew.ModBuildConfig` 4.4.0
- `Newtonsoft.Json` 13.0.3
- manifest minimum SMAPI API version: `4.1.10`

## Preferred build workflow
1. Extract the alpha.25 full Windows builder ZIP into a fresh folder.
2. Do not merge it over an older builder/source folder.
3. Run `BUILD_ALPHA25_TEST.bat`.
4. Let the script detect Stardew Valley or provide the game folder manually.
5. Let it clean old `bin/` and `obj/`, restore/build, generate the mod ZIP, and run its version guard.
6. Install only the generated `_READY_TO_TEST` ZIP.

## Install rule
Before installing a new test candidate:
1. delete the old `Mods/Cardcha` folder;
2. install/extract only the new test ZIP;
3. do not merge over an older alpha folder.

This matters on both desktop and Cinderbox/Android because stale DLLs/manifests can make logs misleading.

## Current alpha.25 regression matrix
- `manifest.json`, project version, startup log and `cardcha_version` all report alpha.25.
- GMCM loads without the old `non-public interface` Cardcha error.
- Controller semantics remain South=Confirm, East=Favorite, West=Deselect, North=Exit.
- Binder free-preview and locked-card action context remain separate.
- Double-click/double-confirm can unequip an equipped card.
- Gacha results remain rounded with large icon, localized Name + NEW/DUPLICATE only.
- Reveal sparkles still appear.
- Stationary and Portable ritual flash covers the panel interior but does **not** pulse the outer gold frame.
- EN/VI card details remain aligned.
- MiMi/ChaCha story/shop/world actor behavior does not regress.

## Validation language
The alpha.25 source tree is verified against its source snapshot and the user has accepted it as the current working baseline after in-game testing. Do not turn that into a claim of exhaustive release QA unless the wider regression matrix is actually completed.

## Artifact naming discipline
Keep builder, source snapshot and test ZIP names versioned outside the installed mod folder. The installed mod folder itself remains `Cardcha`.

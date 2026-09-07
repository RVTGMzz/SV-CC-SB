from pathlib import Path
import base64
import json

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.21"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.22"

# Same 16x64 ladder art as before, but every painted pixel is shifted one source pixel right.
# Stardew renders map tiles at 4x, so this is a 4-screen-pixel visual nudge without moving
# the interaction/collision anchor into the right-wall tile.
SHIFTED_STAIR_B64 = "iVBORw0KGgoAAAANSUhEUgAAABAAAABACAYAAAATffeWAAAAnUlEQVR4nGNgoBAwwhi6kuL/sSm4/PwlIz55JkpdQD0DYE7NcRRmWFCmhSKGLi/PxwIXo9gFjMgcXAGFC1x+/pKRBZsEzAu4QELXNTgbqwFnTr8k2hUUewEjENFjARnD5GGxwMAwGBLSaDSORuNoNELAaDSORiNVDBiNxtFoHI1GCBiNxtFopIoBo9FIhWjE6wLkfiMu+YFPBxQbAAA/0vNyMDNuxQAAAABJRU5ErkJggg=="


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"0655 {label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def set_version() -> None:
    manifest = CARDCHA / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("Version") != OLD_VERSION:
        raise RuntimeError(f"0655 expected manifest {OLD_VERSION}, got {data.get('Version')}")
    data["Version"] = NEW_VERSION
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for rel in ["Cardcha.csproj", "Directory.Build.targets"]:
        path = CARDCHA / rel
        text = path.read_text(encoding="utf-8")
        if OLD_VERSION not in text:
            raise RuntimeError(f"0655 version anchor missing in {rel}")
        path.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")

    mod_entry = CARDCHA / "ModEntry.cs"
    text = mod_entry.read_text(encoding="utf-8")
    text = text.replace(
        f"Cardcha! {OLD_VERSION} MIMI STAIR + PROFILE FIT TEST",
        f"Cardcha! {NEW_VERSION} MIMI NATIVE PROFILE + STAIR ANCHOR TEST",
        1,
    )
    mod_entry.write_text(text, encoding="utf-8")


def restore_stair_anchor_and_shift_art() -> None:
    home = CARDCHA / "Services" / "MimiHomeService.cs"
    text = home.read_text(encoding="utf-8")
    old = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // 0654 in-game acceptance adjustment: keep the same stair route and vertical anchor,\n        // but move the ladder exactly one tile right so it sits snug against the right wall\n        // instead of floating over the stove/log nook. Do not move farther right into the wall.\n        return new Point(16, 15);\n    }'''
    new = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // 0655: x16 proved to be the right-wall/foreign-content column in-game. Keep the known-good\n        // solid/interaction anchor at x15, then nudge the ladder artwork itself four screen pixels\n        // to the right (one source pixel) so it sits closer to the wall without entering it.\n        return new Point(15, 15);\n    }'''
    text = replace_once(text, old, new, "Wizard stair anchor")
    home.write_text(text, encoding="utf-8")

    stair = CARDCHA / "assets" / "mimi_attic_stairs.png"
    raw = base64.b64decode(SHIFTED_STAIR_B64)
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("0655 shifted stair payload is not PNG")
    stair.write_bytes(raw)


def switch_profile_to_native_npc_sheet() -> None:
    world = CARDCHA / "Services" / "WorldActorService.cs"
    text = world.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '    private const string MimiProfileSheetPath = "assets/mimi_walk.png";',
        '    private const string MimiProfileSheetPath = "assets/mimi_npc.png";',
        "native profile sheet path",
    )
    world.write_text(text, encoding="utf-8")


def write_profile_patch() -> None:
    path = CARDCHA / "Patches" / "MimiProfileMenuPatch.cs"
    path.write_text(r'''using Cardcha.Services;
using HarmonyLib;
using StardewValley;
using StardewValley.Menus;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// 0655 removes all ProfileMenu draw scaling for MiMi. Instead, after vanilla selects MiMi,
/// replace only ProfileMenu._animatedSprite with Cardcha's existing native-size 16x32 NPC sheet.
/// From that point onward ProfileMenu uses its untouched vanilla 4x draw path exactly like Martin.
/// </summary>
internal static class MimiProfileMenuPatch
{
    private static readonly FieldInfo? AnimatedSpriteField = AccessTools.Field(typeof(ProfileMenu), "_animatedSprite");
    private static int NativeSpriteSubstitutions;
    private static string LastFrame = "<none>";

    public static void Apply(Harmony harmony)
    {
        MethodInfo? setCharacter = AccessTools.Method(
            typeof(ProfileMenu),
            "_SetCharacter",
            new[] { typeof(SocialPage.SocialEntry) }
        );

        if (setCharacter is null || AnimatedSpriteField is null)
        {
            ModEntry.StaticMonitor?.Log(
                "Could not install MiMi native-size ProfileMenu sprite substitution.",
                StardewModdingAPI.LogLevel.Error
            );
            return;
        }

        harmony.Patch(
            setCharacter,
            postfix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(SetCharacterPostfix))
        );
    }

    private static void SetCharacterPostfix(ProfileMenu __instance, SocialPage.SocialEntry entry)
    {
        if (entry.Character is not NPC npc || !IsMimiName(npc.Name))
            return;

        try
        {
            // mimi_npc.png is already a conventional 4x4 Stardew NPC sheet: 64x128 total,
            // 16x32 per frame. No custom draw hook, no 2x scale, no texture-name guessing.
            AnimatedSprite sprite = new(WorldActorService.MimiProfileCharacterAsset, 0, 16, 32);
            sprite.faceDirection(2);
            AnimatedSpriteField.SetValue(__instance, sprite);
            NativeSpriteSubstitutions++;
            LastFrame = $"{sprite.SpriteWidth}x{sprite.SpriteHeight}";
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.Log(
                $"MiMi native ProfileMenu sprite substitution failed safely: {ex.Message}",
                StardewModdingAPI.LogLevel.Warn
            );
        }
    }

    internal static string Describe()
        => $"MiMiProfileNativeSubstitutions={NativeSpriteSubstitutions} | LastFrame={LastFrame} | Expected=16x32 | DrawScale=vanilla-4x";

    private static bool IsMimiName(string? value)
        => string.Equals(value, WorldActorService.MimiNpcId, StringComparison.OrdinalIgnoreCase)
           || string.Equals(value, "MiMi", StringComparison.OrdinalIgnoreCase);
}
''', encoding="utf-8")


def write_handoff() -> None:
    handoff = ROOT / "handoff" / "ALPHA28_0655_MIMI_NATIVE_PROFILE_STAIR_ANCHOR_FIX.md"
    handoff.write_text(f'''# Alpha28 0655 - MiMi native profile + stair anchor fix

Branch: `cardcha-alpha28-0655-mimi-native-profile-stair-anchor-fix`

Build target: `{NEW_VERSION}`

## Why 0654 was rejected
- Moving the WizardHouse stair anchor from x15 to x16 did not produce the requested slight visual nudge; x16 is the right-side wall/foreign-content column in the tested map and the ladder presentation regressed.
- MiMi remained oversized in Gift Log/Profile despite draw-scale interception, proving that continuing to patch AnimatedSprite.draw is the wrong abstraction.

## 0655 strategy reset
### Wizard stair
- Restore the known-good gameplay/collision/interaction anchor to `(15,15)`.
- Keep up/down on the same stair route.
- Shift only the pixels inside `mimi_attic_stairs.png` one source pixel right, which equals roughly four screen pixels at Stardew's map scale.
- Do not use x16 and do not move the stair into the wall.

### MiMi Gift Log/Profile
- Reuse Cardcha's existing `assets/mimi_npc.png`, already a native Stardew-style 64x128 sheet with 16x32 frames.
- `Characters/Ronvotri.Cardcha_MiMi_Profile` now loads that native sheet instead of the 32x48 `mimi_walk.png` sheet.
- `ProfileMenu._SetCharacter` substitutes a 16x32 AnimatedSprite for MiMi.
- Remove all MiMi AnimatedSprite.draw scaling/interception. Vanilla ProfileMenu now renders MiMi at its normal 4x path, matching ordinary NPC layout behavior such as Martin.
- `cardcha_mimi_profile_status` now reports native sprite substitutions instead of scale-hook hits.

## Regression guard
- 0653 strict TMX runtime compatibility fix retained.
- No attic furniture/layout, MiMi HOME/TV/LATE routine, story/friendship, Save schema 19, Boss I, Hunt Run, Airship, card canon, or controller profile changes.

## In-game acceptance pending
- Ladder should appear in the previous working column, visually nudged right but not inside the wall.
- Returning from the attic should use that same ladder route.
- MiMi Gift Log should render at a normal NPC-sized 16x32-frame/4x presentation, comfortably inside the portrait background.
''', encoding="utf-8")

    latest = ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md"
    latest.write_text(f'''# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0655-mimi-native-profile-stair-anchor-fix`

Current build target:
`{NEW_VERSION}`

Read first:
- `handoff/ALPHA28_0655_MIMI_NATIVE_PROFILE_STAIR_ANCHOR_FIX.md`
- `handoff/ALPHA28_0654_MIMI_STAIR_PROFILE_FIT_FIX.md`
- `handoff/ALPHA28_0653_TMX_RUNTIME_COMPAT_FIX.md`
- `handoff/ALPHA28_0652_VERDANT_VISUAL_PROTOTYPE.md`
- `handoff/BOSS_CONCEPT_CANON.md`

## Current acceptance state
- 0655 resets the two rejected 0654 approaches: stair anchor back to x15 with sub-tile art nudge, and MiMi Gift Log switched to native 16x32 NPC frames with vanilla draw scaling. Fresh in-game acceptance pending.
- 0653 TMX runtime compatibility repair remains included; Hunt Run/Boss arena acceptance still depends on user test.
- Verdant Guardian gameplay + first custom visual overlay remain implemented; visual acceptance pending.

## Locked regression guard
Save schema 19; Boss Form 10 sec; Boss Energy 1/3; 76/76 active cards; Forest Arcane Gate/collision; Airship route/visual; MiMi HOME/TV/LATE and attic furniture/layout; card canon.
''', encoding="utf-8")


set_version()
restore_stair_anchor_and_shift_art()
switch_profile_to_native_npc_sheet()
write_profile_patch()
write_handoff()
print("0655 MiMi native profile/stair anchor generator complete", NEW_VERSION)

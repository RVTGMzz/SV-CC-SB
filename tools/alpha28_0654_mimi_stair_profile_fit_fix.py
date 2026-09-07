from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.20"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.21"


def set_version() -> None:
    manifest = CARDCHA / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("Version") != OLD_VERSION:
        raise RuntimeError(f"0654 expected manifest {OLD_VERSION}, got {data.get('Version')}")
    data["Version"] = NEW_VERSION
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for rel in ["Cardcha.csproj", "Directory.Build.targets"]:
        path = CARDCHA / rel
        text = path.read_text(encoding="utf-8")
        if OLD_VERSION not in text:
            raise RuntimeError(f"0654 version anchor missing in {rel}")
        path.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")

    mod_entry = CARDCHA / "ModEntry.cs"
    text = mod_entry.read_text(encoding="utf-8")
    old_log = "Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.19 VERDANT GUARDIAN VISUAL PROTOTYPE TEST"
    if old_log in text:
        text = text.replace(old_log, f"Cardcha! {NEW_VERSION} MIMI STAIR + PROFILE FIT TEST", 1)
    mod_entry.write_text(text, encoding="utf-8")


def move_wizard_stair_one_tile_right() -> None:
    path = CARDCHA / "Services" / "MimiHomeService.cs"
    text = path.read_text(encoding="utf-8")
    old = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // SVE WizardHouse exact acceptance tile: upper recessed niche between the two plants.\n        // Fixed absolute tile only. No percentages, map-size math, search, or dynamic relocation.\n        return new Point(15, 15);\n    }'''
    new = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // 0654 in-game acceptance adjustment: keep the same stair route and vertical anchor,\n        // but move the ladder exactly one tile right so it sits snug against the right wall\n        // instead of floating over the stove/log nook. Do not move farther right into the wall.\n        return new Point(16, 15);\n    }'''
    if old not in text:
        raise RuntimeError("0654 Wizard stair anchor missing")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def write_profile_patch() -> None:
    path = CARDCHA / "Patches" / "MimiProfileMenuPatch.cs"
    path.write_text(r'''using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;
using StardewValley.Menus;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// Keeps MiMi's Gift Log/Profile preview inside the same visual envelope as vanilla NPCs.
/// 0654 adds a caller-context guard around ProfileMenu.draw so the scale correction no longer
/// depends on AnimatedSprite.loadedTexture string identity, which proved unreliable in-game.
/// </summary>
internal static class MimiProfileMenuPatch
{
    private const float VanillaProfileSpriteScale = 4f;
    private const float MimiProfileSpriteScale = 2f;
    private const float MimiTargetRenderedWidth = 64f;
    private const float MimiTargetRenderedHeight = 112f;
    private static readonly FieldInfo? AnimatedSpriteField = AccessTools.Field(typeof(ProfileMenu), "_animatedSprite");

    [ThreadStatic]
    private static bool DrawingMimiProfile;

    private static int ProfileGuardHits;
    private static int ScaledDrawHits;

    public static void Apply(Harmony harmony)
    {
        MethodInfo? setCharacter = AccessTools.Method(
            typeof(ProfileMenu),
            "_SetCharacter",
            new[] { typeof(SocialPage.SocialEntry) }
        );
        MethodInfo? profileDraw = AccessTools.Method(
            typeof(ProfileMenu),
            nameof(ProfileMenu.draw),
            new[] { typeof(SpriteBatch) }
        );
        MethodInfo? threeArgDraw = AccessTools.Method(
            typeof(AnimatedSprite),
            "draw",
            new[] { typeof(SpriteBatch), typeof(Vector2), typeof(float) }
        );

        if (setCharacter is not null && AnimatedSpriteField is not null)
        {
            harmony.Patch(
                setCharacter,
                postfix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(SetCharacterPostfix))
            );
        }
        else
        {
            ModEntry.StaticMonitor?.Log(
                "MiMi ProfileMenu sprite substitution hook was not found; caller-context scale hook remains active.",
                StardewModdingAPI.LogLevel.Warn
            );
        }

        if (profileDraw is not null)
        {
            harmony.Patch(
                profileDraw,
                prefix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(ProfileDrawPrefix)),
                postfix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(ProfileDrawPostfix))
            );
        }
        else
        {
            ModEntry.StaticMonitor?.Log(
                "Could not install MiMi ProfileMenu caller-context guard.",
                StardewModdingAPI.LogLevel.Error
            );
        }

        if (threeArgDraw is null)
        {
            ModEntry.StaticMonitor?.Log(
                "Could not install MiMi ProfileMenu fitted AnimatedSprite draw hook.",
                StardewModdingAPI.LogLevel.Error
            );
            return;
        }

        harmony.Patch(
            threeArgDraw,
            prefix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(ThreeArgDrawPrefix))
        );
    }

    private static void ProfileDrawPrefix(ProfileMenu __instance)
    {
        DrawingMimiProfile = IsMimiCurrent(__instance);
        if (DrawingMimiProfile)
            ProfileGuardHits++;
    }

    private static void ProfileDrawPostfix()
    {
        DrawingMimiProfile = false;
    }

    private static void SetCharacterPostfix(ProfileMenu __instance, SocialPage.SocialEntry entry)
    {
        if (entry.Character is not NPC npc || !IsMimiName(npc.Name))
            return;

        try
        {
            // A dedicated 32x48 profile sprite prevents the world actor's runtime Scale value from
            // leaking into menu presentation. Drawing size itself is still normalized below.
            AnimatedSprite sprite = new(WorldActorService.MimiProfileCharacterAsset, 0, 32, 48);
            sprite.faceDirection(2);
            AnimatedSpriteField?.SetValue(__instance, sprite);
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.Log(
                $"MiMi ProfileMenu sprite substitution failed safely: {ex.Message}",
                StardewModdingAPI.LogLevel.Trace
            );
        }
    }

    private static bool ThreeArgDrawPrefix(AnimatedSprite __instance, SpriteBatch b, Vector2 screenPosition, float layerDepth)
    {
        // Primary rule: when ProfileMenu itself says the selected character is MiMi, normalize the
        // one AnimatedSprite portrait draw regardless of how SMAPI normalized its texture name.
        // Texture ownership is retained only as a safe fallback for older menu call paths.
        if (!DrawingMimiProfile && !IsMimiProfileTexture(__instance))
            return true;

        Texture2D texture = __instance.Texture;
        if (texture is null)
            return false;

        Rectangle source = __instance.SourceRect;
        if (source.Width <= 0 || source.Height <= 0)
            return false;

        // Fit to a vanilla-NPC-sized envelope rather than blindly multiplying the custom 32x48
        // frame. For MiMi's canonical 32x48 frame this resolves to 2x: 64x96 rendered pixels.
        float fitScale = Math.Min(
            MimiProfileSpriteScale,
            Math.Min(MimiTargetRenderedWidth / source.Width, MimiTargetRenderedHeight / source.Height)
        );

        // ProfileMenu computes screenPosition as if every NPC were drawn at vanilla 4x. Recenter
        // against that original envelope, both horizontally and vertically, so MiMi is not pinned
        // to the upper-left after being reduced.
        float centerOffsetX = source.Width * (VanillaProfileSpriteScale - fitScale) / 2f;
        float centerOffsetY = source.Height * (VanillaProfileSpriteScale - fitScale) / 2f;
        Vector2 centeredPosition = screenPosition + new Vector2(centerOffsetX, centerOffsetY);

        SpriteEffects effects = SpriteEffects.None;
        var animation = __instance.CurrentAnimation;
        if (animation is not null
            && __instance.currentAnimationIndex >= 0
            && __instance.currentAnimationIndex < animation.Count
            && animation[__instance.currentAnimationIndex].flip)
        {
            effects = SpriteEffects.FlipHorizontally;
        }

        b.Draw(
            texture,
            centeredPosition,
            source,
            Color.White,
            0f,
            Vector2.Zero,
            fitScale,
            effects,
            layerDepth
        );
        ScaledDrawHits++;
        return false;
    }

    internal static string Describe()
        => $"MiMiProfileGuardHits={ProfileGuardHits} | ScaledDrawHits={ScaledDrawHits} | Active={DrawingMimiProfile} | Target={MimiTargetRenderedWidth:0}x{MimiTargetRenderedHeight:0} | MaxScale={MimiProfileSpriteScale:0.##}";

    private static bool IsMimiCurrent(ProfileMenu menu)
        => menu.Current?.Character is NPC npc && IsMimiName(npc.Name);

    private static bool IsMimiProfileTexture(AnimatedSprite sprite)
    {
        string? loaded = sprite.loadedTexture;
        string? requested = sprite.textureName.Value;
        return IsMimiTextureName(loaded) || IsMimiTextureName(requested);
    }

    private static bool IsMimiTextureName(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
            return false;

        string normalized = value.Replace('\\', '/').Trim();
        string profile = WorldActorService.MimiProfileCharacterAsset.Replace('\\', '/');
        string world = WorldActorService.MimiCharacterAsset.Replace('\\', '/');
        return normalized.Equals(profile, StringComparison.OrdinalIgnoreCase)
            || normalized.Equals(world, StringComparison.OrdinalIgnoreCase)
            || normalized.EndsWith("/Ronvotri.Cardcha_MiMi_Profile", StringComparison.OrdinalIgnoreCase)
            || normalized.EndsWith("/Ronvotri.Cardcha_MiMi", StringComparison.OrdinalIgnoreCase);
    }

    private static bool IsMimiName(string? value)
        => string.Equals(value, WorldActorService.MimiNpcId, StringComparison.OrdinalIgnoreCase)
           || string.Equals(value, "MiMi", StringComparison.OrdinalIgnoreCase);
}
''', encoding="utf-8")


def add_profile_status_command() -> None:
    path = CARDCHA / "ModEntry.cs"
    text = path.read_text(encoding="utf-8")
    anchor = '        helper.ConsoleCommands.Add("cardcha_story_status", "Show MiMi/Cardcha Chapter 1 story state.", this.CommandStoryStatus);\n'
    line = '        helper.ConsoleCommands.Add("cardcha_mimi_profile_status", "Show MiMi Gift Log/Profile scaling hook diagnostics.", (_, _) => this.Monitor.Log(MimiProfileMenuPatch.Describe(), LogLevel.Alert));\n'
    if line not in text:
        if anchor not in text:
            raise RuntimeError("0654 profile status command anchor missing")
        text = text.replace(anchor, anchor + line, 1)
    path.write_text(text, encoding="utf-8")


def write_handoff() -> None:
    handoff = ROOT / "handoff" / "ALPHA28_0654_MIMI_STAIR_PROFILE_FIT_FIX.md"
    handoff.write_text(f'''# Alpha28 0654 - MiMi stair + Gift Log profile fit fix

Branch: `cardcha-alpha28-0654-mimi-stair-profile-fit-fix`

Build target: `{NEW_VERSION}`

## In-game evidence driving this patch
- WizardHouse ladder was almost correctly placed but needed one tile right, snug against the right wall without entering the wall.
- Returning from MiMi's attic must still land at the same stair route; no separate invisible exit relocation is introduced.
- MiMi remained oversized/clipped in ProfileMenu Gift Log while a vanilla NPC such as Martin fit normally inside the portrait background.

## Fix
- WizardHouse preferred stair anchor: `(15,15)` -> `(16,15)` only. Y, ladder height, route, attic landing logic, and solid Buildings-layer behavior stay unchanged.
- ProfileMenu now sets a caller-context flag when the currently selected character is MiMi. The AnimatedSprite draw correction therefore no longer relies on texture-name matching alone.
- MiMi's profile frame is fitted into a 64x112 maximum envelope with max scale 2x. Canonical 32x48 MiMi frames render 64x96 and are recentered against ProfileMenu's vanilla 4x positioning calculation.
- Added `cardcha_mimi_profile_status` diagnostics so real in-game tests can prove whether ProfileMenu guard and scaled draw hooks fire.

## Regression guard
- 0653 strict TMX runtime compatibility fix is retained.
- No attic layout/furniture, HOME/TV/LATE routine, friendship/story progression, Save schema 19, Cardcha progression, Airship, Boss I, cards, controller profile, or MiMi portrait-dialogue lifecycle is changed.

## Acceptance pending
- Stair must visually sit just left of the right wall, not overlap the wall and not float over the stove/log nook.
- Going up and returning down must use the same stair location.
- MiMi Gift Log sprite must fit comfortably inside the same portrait frame envelope as normal NPCs, with no clipping.
''', encoding="utf-8")

    latest = ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md"
    latest.write_text(f'''# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0654-mimi-stair-profile-fit-fix`

Current build target:
`{NEW_VERSION}`

Read first:
- `handoff/ALPHA28_0654_MIMI_STAIR_PROFILE_FIT_FIX.md`
- `handoff/ALPHA28_0653_TMX_RUNTIME_COMPAT_FIX.md`
- `handoff/ALPHA28_0652_VERDANT_VISUAL_PROTOTYPE.md`
- `handoff/VERDANT_GUARDIAN_ANIMATION_HOOK_SPEC.md`
- `handoff/BOSS_CONCEPT_CANON.md`

## Current acceptance state
- 0654 moves WizardHouse MiMi stair from x15 to x16 only and hardens Gift Log/Profile scaling by ProfileMenu caller context; fresh in-game acceptance pending.
- 0653 TMX runtime compatibility repair remains included; fresh Hunt Run/Boss arena acceptance still depends on user test.
- Verdant Guardian gameplay + first custom visual overlay remain implemented; visual acceptance pending.

## Locked regression guard
Save schema 19; Boss Form 10 sec; Boss Energy 1/3; 76/76 active cards; Forest Arcane Gate/collision; Airship route/visual; MiMi HOME/TV/LATE and attic furniture/layout; card canon.
''', encoding="utf-8")


set_version()
move_wizard_stair_one_tile_right()
write_profile_patch()
add_profile_status_command()
write_handoff()
print("0654 MiMi stair/profile fit generator complete", NEW_VERSION)

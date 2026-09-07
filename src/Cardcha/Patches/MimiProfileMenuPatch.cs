using Cardcha.Services;
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

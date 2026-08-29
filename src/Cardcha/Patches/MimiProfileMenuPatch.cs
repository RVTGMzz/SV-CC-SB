using Cardcha.Services;
using HarmonyLib;
using StardewValley;
using StardewValley.Menus;
using System.Reflection;

namespace Cardcha.Patches;

internal static class MimiProfileMenuPatch
{
    private static readonly FieldInfo? AnimatedSpriteField = AccessTools.Field(typeof(ProfileMenu), "_animatedSprite");

    public static void Apply(Harmony harmony)
    {
        MethodInfo? target = AccessTools.Method(
            typeof(ProfileMenu),
            "_SetCharacter",
            new[] { typeof(SocialPage.SocialEntry) }
        );

        if (target is null || AnimatedSpriteField is null)
        {
            ModEntry.StaticMonitor?.Log("Could not install MiMi ProfileMenu sprite-size patch.", StardewModdingAPI.LogLevel.Warn);
            return;
        }

        harmony.Patch(
            target,
            postfix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(Postfix))
        );
    }

    private static void Postfix(ProfileMenu __instance, SocialPage.SocialEntry entry)
    {
        if (entry.Character is not NPC npc
            || !string.Equals(npc.Name, WorldActorService.MimiNpcId, StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        try
        {
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
}

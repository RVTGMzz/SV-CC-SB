using Cardcha.Services;
using HarmonyLib;
using StardewValley;
using StardewValley.Menus;
using System.Reflection;

namespace Cardcha.Patches;

internal static class MimiProfileMenuPatch
{
    private const float MimiProfileScaleMultiplier = 0.5f;
    private static readonly FieldInfo? AnimatedSpriteField = AccessTools.Field(typeof(ProfileMenu), "_animatedSprite");
    private static bool MimiProfileActive;

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

        int scaledDrawOverloads = 0;
        foreach (MethodInfo drawMethod in typeof(AnimatedSprite)
                     .GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
                     .Where(method => string.Equals(method.Name, "draw", StringComparison.OrdinalIgnoreCase)
                         && method.GetParameters().Any(parameter => parameter.ParameterType == typeof(float)
                             && string.Equals(parameter.Name, "scale", StringComparison.OrdinalIgnoreCase))))
        {
            harmony.Patch(
                drawMethod,
                prefix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(ScaleDrawPrefix))
            );
            scaledDrawOverloads++;
        }

        if (scaledDrawOverloads == 0)
        {
            ModEntry.StaticMonitor?.Log(
                "MiMi ProfileMenu could not find an AnimatedSprite draw overload with a scale argument; vanilla scale will be used safely.",
                StardewModdingAPI.LogLevel.Warn
            );
        }
    }

    private static void Postfix(ProfileMenu __instance, SocialPage.SocialEntry entry)
    {
        bool isMimi = entry.Character is NPC npc
            && string.Equals(npc.Name, WorldActorService.MimiNpcId, StringComparison.OrdinalIgnoreCase);

        MimiProfileActive = isMimi;
        if (!isMimi)
            return;

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

    private static void ScaleDrawPrefix(AnimatedSprite __instance, MethodBase __originalMethod, object[] __args)
    {
        if (!MimiProfileActive
            || Game1.activeClickableMenu is not ProfileMenu profile
            || !ReferenceEquals(AnimatedSpriteField?.GetValue(profile), __instance))
        {
            return;
        }

        ParameterInfo[] parameters = __originalMethod.GetParameters();
        for (int i = 0; i < parameters.Length && i < __args.Length; i++)
        {
            ParameterInfo parameter = parameters[i];
            if (parameter.ParameterType != typeof(float)
                || !string.Equals(parameter.Name, "scale", StringComparison.OrdinalIgnoreCase)
                || __args[i] is not float scale)
            {
                continue;
            }

            __args[i] = scale * MimiProfileScaleMultiplier;
            return;
        }
    }
}

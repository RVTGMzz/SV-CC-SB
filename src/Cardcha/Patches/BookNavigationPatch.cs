using Cardcha.UI;
using HarmonyLib;
using StardewValley.Menus;

namespace Cardcha.Patches;

internal static class BookNavigationPatch
{
    private static CardchaBookTabService? Service;

    public static void Apply(
        Harmony harmony,
        CardchaBookTabService service)
    {
        Service = service;

        System.Reflection.MethodInfo? target =
            AccessTools.Method(
                typeof(IClickableMenu),
                nameof(IClickableMenu.applyMovementKey),
                new[] { typeof(int) }
            );

        if (target is null)
            throw new InvalidOperationException(
                "Could not find IClickableMenu.applyMovementKey(int)."
            );

        harmony.Patch(
            target,
            prefix: new HarmonyMethod(
                typeof(BookNavigationPatch),
                nameof(Prefix)
            )
        );
    }

    private static bool Prefix(
        IClickableMenu __instance,
        int direction)
    {
        try
        {
            if (Service?.TryHandleMovementKey(
                    __instance,
                    direction
                ) == true)
            {
                // Cardcha handled the navigation completely.
                // Skip Stardew's normal movement logic so it can't
                // redirect the hand to an automatic/outside neighbor.
                return false;
            }
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.LogOnce(
                $"Cardcha Book movement intercept failed safely: {ex}",
                StardewModdingAPI.LogLevel.Warn
            );
        }

        return true;
    }
}

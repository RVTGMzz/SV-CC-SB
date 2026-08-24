using Cardcha.Services;
using HarmonyLib;
using StardewModdingAPI;
using StardewValley;
using SObject = StardewValley.Object;
using System.Reflection;

namespace Cardcha.Patches;

internal static class MachineInteractionPatch
{
    private static Action? OpenMachineMenu;

    public static void Apply(Harmony harmony, Action openMachineMenu)
    {
        OpenMachineMenu = openMachineMenu;

        MethodInfo? target = AccessTools.Method(
            typeof(SObject),
            nameof(SObject.checkForAction),
            new[] { typeof(Farmer), typeof(bool) }
        );

        if (target is null)
            throw new MissingMethodException(
                "Could not find StardewValley.Object.checkForAction(Farmer, bool)."
            );

        HarmonyMethod prefix = new(
            typeof(MachineInteractionPatch),
            nameof(Prefix)
        )
        {
            priority = Priority.First
        };

        harmony.Patch(target, prefix: prefix);
    }

    private static bool Prefix(
        SObject __instance,
        Farmer who,
        bool justCheckingForActivity,
        ref bool __result
    )
    {
        try
        {
            if (!IsCardchaMachine(__instance))
                return true;

            __result = true;

            if (!justCheckingForActivity
                && ReferenceEquals(who, Game1.player)
                && Game1.activeClickableMenu is null)
            {
                Game1.playSound("bigSelect");
                OpenMachineMenu?.Invoke();
            }

            // Cardcha handles its own interaction; skip vanilla machine logic.
            return false;
        }
        catch (Exception ex)
        {
            // NEVER let Cardcha break Stardew's base action loop.
            ModEntry.LogOnce(
                "machine-interaction-prefix",
                $"Cardcha machine interaction prefix failed safely: {ex}"
            );

            return true;
        }
    }

    public static bool IsCardchaMachine(SObject? obj)
    {
        if (obj is null)
            return false;

        try
        {
            if (string.Equals(
                    obj.QualifiedItemId,
                    $"(BC){ItemAssetService.CardchaMachineId}",
                    StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }

            if (string.Equals(
                    obj.ItemId,
                    ItemAssetService.CardchaMachineId,
                    StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }

            if (obj.modData is not null
                && obj.modData.ContainsKey(ItemAssetService.MachineMarkerKey))
            {
                return true;
            }

            return string.Equals(
                obj.Name,
                "Cardcha! Machine",
                StringComparison.OrdinalIgnoreCase
            );
        }
        catch
        {
            // A companion/other mod may temporarily hand us a partially reconstructed object.
            return false;
        }
    }
}

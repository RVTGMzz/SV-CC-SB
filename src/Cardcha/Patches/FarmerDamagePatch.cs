using Cardcha.Services;
using HarmonyLib;
using StardewValley;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>Lets Phoenix Heart intervene after vanilla and vanilla revive effects finish resolving damage.</summary>
internal static class FarmerDamagePatch
{
    private static CombatService? Combat;

    public static void Apply(Harmony harmony, CombatService combat)
    {
        Combat = combat;

        MethodInfo? target = AccessTools.Method(
            typeof(Farmer),
            nameof(Farmer.takeDamage),
            new[] { typeof(int), typeof(bool), typeof(Monster) }
        );

        if (target is null)
            throw new MissingMethodException("Could not find Farmer.takeDamage(int,bool,Monster).");

        harmony.Patch(target, postfix: new HarmonyMethod(typeof(FarmerDamagePatch), nameof(Postfix)));
    }

    private static void Postfix(Farmer __instance)
    {
        try
        {
            Combat?.AfterFarmerTakesDamage(__instance);
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("farmer-damage-patch", $"Cardcha farmer damage hook failed: {ex}");
        }
    }
}

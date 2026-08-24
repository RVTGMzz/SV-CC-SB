using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using StardewValley;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>Adds Keen Eye before vanilla rolls weapon critical hits.</summary>
internal static class CriticalChancePatch
{
    private static CombatService? Combat;

    public static void Apply(Harmony harmony, CombatService combat)
    {
        Combat = combat;

        MethodInfo? target = AccessTools.Method(
            typeof(GameLocation),
            nameof(GameLocation.damageMonster),
            new[]
            {
                typeof(Rectangle), typeof(int), typeof(int), typeof(bool), typeof(float), typeof(int),
                typeof(float), typeof(float), typeof(bool), typeof(Farmer), typeof(bool)
            }
        );

        if (target is null)
            throw new MissingMethodException("Could not find the full GameLocation.damageMonster overload.");

        harmony.Patch(target, prefix: new HarmonyMethod(typeof(CriticalChancePatch), nameof(Prefix)));
    }

    private static void Prefix(bool isBomb, ref float critChance, Farmer? who)
    {
        try
        {
            if (Combat is not null)
                critChance = Combat.ModifyCriticalChance(critChance, isBomb, who);
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("crit-chance-patch", $"Cardcha critical chance hook failed: {ex}");
        }
    }
}

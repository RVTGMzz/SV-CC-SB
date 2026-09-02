using Cardcha.Services;
using HarmonyLib;
using StardewValley;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>Applies Cardcha incoming-damage rules, then lets post-hit/revive effects resolve.</summary>
internal static class FarmerDamagePatch
{
    private static CombatService? Combat;
    private static CardTestArenaService? TestArena;

    public static void Apply(Harmony harmony, CombatService combat, CardTestArenaService? testArena = null)
    {
        Combat = combat;
        TestArena = testArena;
        MethodInfo? target = AccessTools.Method(
            typeof(Farmer),
            nameof(Farmer.takeDamage),
            new[] { typeof(int), typeof(bool), typeof(Monster) }
        );
        if (target is null)
            throw new MissingMethodException("Could not find Farmer.takeDamage(int,bool,Monster).");

        harmony.Patch(
            target,
            prefix: new HarmonyMethod(typeof(FarmerDamagePatch), nameof(Prefix)),
            postfix: new HarmonyMethod(typeof(FarmerDamagePatch), nameof(Postfix))
        );
    }

    private static void Prefix(Farmer __instance, ref int damage, Monster? damager, out int __state)
    {
        __state = __instance.health;
        try
        {
            TestArena?.TryOverrideIncomingDamage(ref damage, damager);
            if (Combat is not null)
                damage = Combat.ModifyFarmerDamage(damage, __instance, damager);
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("farmer-damage-prefix", $"Cardcha incoming damage hook failed: {ex}");
        }
    }

    private static void Postfix(Farmer __instance, int __state)
    {
        try
        {
            Combat?.AfterFarmerTakesDamage(__instance, __state);
            TestArena?.AfterFarmerDamage(__instance);
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("farmer-damage-patch", $"Cardcha farmer damage post hook failed: {ex}");
        }
    }
}

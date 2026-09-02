using Cardcha.Services;
using HarmonyLib;
using StardewValley;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// Applies target-aware Cardcha damage bonuses and detects actual deaths at Monster.takeDamage.
/// Card Test Arena may normalize the raw pre-card hit so percentage effects are easy to verify.
/// </summary>
internal static class MonsterDamagePatch
{
    private static CombatService? Combat;
    private static MonsterDeathService? Deaths;
    private static CardTestArenaService? TestArena;

    public static void Apply(Harmony harmony, CombatService combat, MonsterDeathService deaths, CardTestArenaService? testArena = null)
    {
        Combat = combat;
        Deaths = deaths;
        TestArena = testArena;

        MethodInfo? target = AccessTools.Method(
            typeof(Monster),
            nameof(Monster.takeDamage),
            new[] { typeof(int), typeof(int), typeof(int), typeof(bool), typeof(double), typeof(Farmer) }
        );

        if (target is null)
            throw new MissingMethodException("Could not find Monster.takeDamage(int,int,int,bool,double,Farmer).");

        harmony.Patch(
            target,
            prefix: new HarmonyMethod(typeof(MonsterDamagePatch), nameof(Prefix)),
            postfix: new HarmonyMethod(typeof(MonsterDamagePatch), nameof(Postfix))
        );
    }

    private static void Prefix(Monster __instance, ref int damage, ref int xTrajectory, ref int yTrajectory, bool isBomb, Farmer? who, out int __state)
    {
        __state = __instance.Health;

        try
        {
            TestArena?.TryOverrideOutgoingDamage(__instance, ref damage, isBomb, who);

            if (Combat is not null)
            {
                damage = Combat.ModifyMonsterDamage(__instance, damage, isBomb, who);
                TestArena?.ClampMainDummyDamage(__instance, ref damage);
                Combat.ModifyMonsterTrajectory(ref xTrajectory, ref yTrajectory, isBomb, who);
            }
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("monster-damage-patch", $"Cardcha monster damage hook failed: {ex}");
        }
    }

    private static void Postfix(Monster __instance, Farmer? who, int __state)
    {
        try
        {
            Combat?.AfterMonsterTakesDamage(__instance, who, __state);
            if (__state > 0 && __instance.Health <= 0)
                Deaths?.HandleDeath(__instance, who, __instance.currentLocation);
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("monster-death-from-damage", $"Cardcha takeDamage death hook failed: {ex}");
        }
    }
}

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
    private static VerdantGuardianBossService? VerdantBoss;
    private const double VerdantGuardianKnockbackScale = 0.08d;
    private const int VerdantGuardianKnockbackCap = 12;

    public static void Apply(Harmony harmony, CombatService combat, MonsterDeathService deaths, CardTestArenaService? testArena, VerdantGuardianBossService verdantBoss)
    {
        Combat = combat;
        Deaths = deaths;
        TestArena = testArena;
        VerdantBoss = verdantBoss;

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

            bool isVerdantGuardian = __instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey);
            bool isVerdantTotem = __instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey);
            bool isMilestoneBoss = __instance.modData.ContainsKey(MilestoneBossService.BossMarkerKey);

            if (Combat is not null)
            {
                damage = Combat.ModifyMonsterDamage(__instance, damage, isBomb, who);
                TestArena?.ClampMainDummyDamage(__instance, ref damage);
                Combat.ModifyMonsterTrajectory(ref xTrajectory, ref yTrajectory, isBomb, who);
            }

            if (isVerdantGuardian && VerdantBoss is not null)
                damage = VerdantBoss.ModifyBossIncomingDamage(damage);

            if (isVerdantTotem || isMilestoneBoss) { xTrajectory = 0; yTrajectory = 0; }

            // 0665: receive 8% of final trajectory, then hard-cap it. The boss service recenters
            // toward HeavyAnchor, so repeated party hits cannot walk the Guardian into a wall.
            if (isVerdantGuardian)
            {
                xTrajectory = Math.Clamp((int)Math.Round(xTrajectory * VerdantGuardianKnockbackScale), -VerdantGuardianKnockbackCap, VerdantGuardianKnockbackCap);
                yTrajectory = Math.Clamp((int)Math.Round(yTrajectory * VerdantGuardianKnockbackScale), -VerdantGuardianKnockbackCap, VerdantGuardianKnockbackCap);
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
            VerdantBoss?.NotifyTotemHit(__instance, __state);
            if (__state > 0 && __instance.Health <= 0
                && !__instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey)
                && !__instance.modData.ContainsKey(MilestoneBossService.BossMarkerKey))
                Deaths?.HandleDeath(__instance, who, __instance.currentLocation);
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("monster-death-from-damage", $"Cardcha takeDamage death hook failed: {ex}");
        }
    }
}

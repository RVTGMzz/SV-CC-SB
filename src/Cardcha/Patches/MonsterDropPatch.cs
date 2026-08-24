using Cardcha.Services;
using HarmonyLib;
using StardewValley;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// Fallback death hook for unusual/modded flows which reach vanilla monsterDrop
/// without Cardcha observing the lethal takeDamage call.
/// MonsterDeathService deduplicates rewards when both hooks fire.
/// </summary>
internal static class MonsterDropPatch
{
    private static MonsterDeathService? Deaths;

    public static void Apply(Harmony harmony, MonsterDeathService deaths)
    {
        Deaths = deaths;

        MethodInfo? target = AccessTools.Method(
            typeof(GameLocation),
            nameof(GameLocation.monsterDrop),
            new[] { typeof(Monster), typeof(int), typeof(int), typeof(Farmer) }
        );

        if (target is null)
            throw new MissingMethodException("Could not find GameLocation.monsterDrop(Monster,int,int,Farmer).");

        harmony.Patch(target, postfix: new HarmonyMethod(typeof(MonsterDropPatch), nameof(Postfix)));
    }

    private static void Postfix(GameLocation __instance, Monster monster, Farmer who)
    {
        try
        {
            Deaths?.HandleDeath(monster, who, __instance);
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("monster-drop-fallback", $"Cardcha monsterDrop fallback failed: {ex}");
        }
    }
}

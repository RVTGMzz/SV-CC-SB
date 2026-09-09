using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>0675: expedition monsters keep real AI/hitboxes while Cardcha owns their visible authored art.</summary>
internal static class RegionExpeditionProxyDrawPatch
{
    public static void Apply(Harmony harmony)
    {
        HashSet<MethodInfo> targets = new();
        foreach (Type type in new[] { typeof(GreenSlime), typeof(Bat), typeof(Bug) })
        {
            MethodInfo? target = AccessTools.Method(type, "draw", new[] { typeof(SpriteBatch) });
            if (target is not null)
                targets.Add(target);
        }
        if (targets.Count == 0)
            throw new MissingMethodException("Could not resolve expedition monster draw methods.");
        HarmonyMethod prefix = new(typeof(RegionExpeditionProxyDrawPatch), nameof(Prefix));
        foreach (MethodInfo target in targets)
            harmony.Patch(target, prefix: prefix);
    }

    private static bool Prefix(Monster __instance)
        => !__instance.modData.ContainsKey(RegionExpeditionService.EnemyMarkerKey);
}

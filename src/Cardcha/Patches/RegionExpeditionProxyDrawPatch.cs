using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// 0676A runtime hotfix: patch the draw implementation declared by Monster exactly once.
/// Expedition GreenSlime/Bat/Bug proxies inherit this implementation; Harmony must not be asked
/// to patch an inherited MethodInfo as though it were declared on each subclass.
/// </summary>
internal static class RegionExpeditionProxyDrawPatch
{
    public static void Apply(Harmony harmony)
    {
        MethodInfo? target = AccessTools.DeclaredMethod(typeof(Monster), "draw", new[] { typeof(SpriteBatch) });
        if (target is null)
            throw new MissingMethodException("Could not resolve declared Monster.draw(SpriteBatch) for expedition proxy suppression.");

        HarmonyMethod prefix = new(typeof(RegionExpeditionProxyDrawPatch), nameof(Prefix));
        harmony.Patch(target, prefix: prefix);
    }

    private static bool Prefix(Monster __instance)
        => !__instance.modData.ContainsKey(RegionExpeditionService.EnemyMarkerKey);
}

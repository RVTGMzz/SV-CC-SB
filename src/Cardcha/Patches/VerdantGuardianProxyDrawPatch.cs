using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>0660: keep the Green Slime as a gameplay proxy but never render it for Boss I.</summary>
internal static class VerdantGuardianProxyDrawPatch
{
    public static void Apply(Harmony harmony)
    {
        MethodInfo? target = AccessTools.Method(typeof(GreenSlime), "draw", new[] { typeof(SpriteBatch) });
        if (target is null)
            throw new MissingMethodException("Could not find GreenSlime.draw(SpriteBatch) for Verdant Guardian proxy suppression.");
        harmony.Patch(target, prefix: new HarmonyMethod(typeof(VerdantGuardianProxyDrawPatch), nameof(Prefix)));
    }

    private static bool Prefix(GreenSlime __instance)
        => !__instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey)
           && !__instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey);
}

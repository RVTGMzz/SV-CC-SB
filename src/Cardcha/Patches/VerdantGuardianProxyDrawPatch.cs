using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// Suppress vanilla proxy art for Cardcha-owned Boss I / Totem / summon / milestone actors.
///
/// Important Harmony rule: GreenSlime does not own every draw implementation we depend on.
/// Patch the method declared by Monster once, then filter by Cardcha modData. This avoids the
/// runtime 'patch the declared Monster.draw method instead' failure seen in the expedition path.
/// </summary>
internal static class VerdantGuardianProxyDrawPatch
{
    public static void Apply(Harmony harmony)
    {
        MethodInfo? target = AccessTools.DeclaredMethod(typeof(Monster), "draw", new[] { typeof(SpriteBatch) });
        if (target is null || target.DeclaringType != typeof(Monster))
            throw new MissingMethodException("Could not resolve Monster.draw(SpriteBatch) for Cardcha proxy suppression.");

        harmony.Patch(target, prefix: new HarmonyMethod(typeof(VerdantGuardianProxyDrawPatch), nameof(Prefix)));
    }

    private static bool Prefix(Monster __instance)
        => !__instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey)
           && !__instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey)
           && !__instance.modData.ContainsKey(VerdantGuardianBossService.BossAddMarkerKey);
}

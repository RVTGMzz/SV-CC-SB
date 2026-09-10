using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// 0678 physical actor-depth owner for Boss II, III and IV.
/// The gameplay proxy remains a live Monster for hitbox/HP/combat, while Cardcha authored art
/// replaces only its vanilla body at the exact Monster.draw slot. No boss body is allowed to
/// return to Display.RenderedWorld.
/// </summary>
internal static class MilestoneBossActorDrawPatch
{
    private static MilestoneBossService? Service;
    private static IMonitor? Monitor;

    internal static void Apply(Harmony harmony, MilestoneBossService service, IMonitor monitor)
    {
        Service = service;
        Monitor = monitor;

        MethodInfo? target = AccessTools.DeclaredMethod(typeof(Monster), "draw", new[] { typeof(SpriteBatch) });
        if (target is null || target.DeclaringType != typeof(Monster))
            throw new MissingMethodException("0678 could not resolve the draw(SpriteBatch) implementation declared by Monster.");

        HarmonyMethod prefix = new(typeof(MilestoneBossActorDrawPatch), nameof(Prefix))
        {
            priority = Priority.First,
        };
        harmony.Patch(target, prefix: prefix);
    }

    private static bool Prefix(Monster __instance, SpriteBatch b)
    {
        if (!__instance.modData.ContainsKey(MilestoneBossService.BossMarkerKey))
            return true;

        try
        {
            Service?.DrawActorAtMonsterDepth(b, __instance);
        }
        catch (Exception ex)
        {
            Monitor?.Log($"0678 milestone boss actor draw failed safely: {ex.GetType().Name}: {ex.Message}", LogLevel.Error);
        }

        // Never reveal the GreenSlime proxy body for milestone bosses.
        return false;
    }
}

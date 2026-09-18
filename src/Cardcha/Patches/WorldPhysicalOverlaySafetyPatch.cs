using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// Repository-wide static-world depth safety hotfix.
///
/// These methods were confirmed to render solid physical art from Display.RenderedWorld,
/// after Stardew had already drawn Farmer/NPC actors. No layerDepth value inside those methods
/// can restore the completed world sort. Until each visual is migrated into TMX/Furniture/native
/// world ownership, suppressing the fake physical overlay is safer than letting it cover actors.
///
/// 0696D3-H keeps the three known unsafe legacy physical painters suppressed. The bridge Window
/// shell and transparent console body are now TMX-owned; AirshipGateDepthPatch owns only a narrow
/// pre-Farmer transient/presentation pass for Window/radar ambience, upgrade stations and TRAVEL.
/// It never replays the full DrawDeckMarkers physical room pass.
/// </summary>
internal static class WorldPhysicalOverlaySafetyPatch
{
    internal static void Apply(Harmony harmony, IMonitor monitor)
    {
        int patched = 0;

        patched += PatchSkip(
            harmony,
            typeof(AirshipFoundationService),
            "DrawRegion1Details",
            new[] { typeof(SpriteBatch), typeof(GameLocation) },
            monitor
        );

        // These legacy decor painters still have no native world ownership. Keep them disabled.
        patched += PatchSkip(
            harmony,
            typeof(AirshipInteriorStardewRenderer),
            "DrawDeckStardewDecor",
            new[] { typeof(SpriteBatch) },
            monitor
        );
        patched += PatchSkip(
            harmony,
            typeof(AirshipInteriorStardewRenderer),
            "DrawDockStardewDecor",
            new[] { typeof(SpriteBatch) },
            monitor
        );

        monitor.Log(
            $"0696D3-H world-depth safety active: suppressed {patched}/3 unsafe legacy physical renderer(s). Bridge shell/console depth is TMX-owned; the narrow pre-Farmer pass preserves stations/TRAVEL.",
            patched == 3 ? LogLevel.Info : LogLevel.Warn
        );
    }

    private static int PatchSkip(
        Harmony harmony,
        Type owner,
        string methodName,
        Type[] args,
        IMonitor monitor)
    {
        MethodInfo? target = AccessTools.DeclaredMethod(owner, methodName, args);
        if (target is null)
        {
            monitor.Log(
                $"0696D3-H depth safety couldn't resolve {owner.Name}.{methodName}; refusing to invent a fallback post-world renderer.",
                LogLevel.Error
            );
            return 0;
        }

        harmony.Patch(
            target,
            prefix: new HarmonyMethod(typeof(WorldPhysicalOverlaySafetyPatch), nameof(SkipPhysicalOverlay))
        );
        return 1;
    }

    private static bool SkipPhysicalOverlay()
        => false;
}

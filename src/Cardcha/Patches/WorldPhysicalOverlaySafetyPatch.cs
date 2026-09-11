using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// 0676B repository-wide static-world depth safety hotfix.
///
/// These methods were confirmed to render solid physical art from Display.RenderedWorld,
/// after Stardew had already drawn Farmer/NPC actors. No layerDepth value inside those methods
/// can restore the completed world sort. Until each visual is migrated into TMX/Furniture/native
/// world ownership, suppressing the fake physical overlay is safer than letting it cover actors.
///
/// VFX-only methods remain untouched.
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

        // Keep the Airship interior's lightweight magical cues, but remove fake solid props
        // and machine bodies which were being painted after Farmer/NPC draw order.
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
        patched += PatchSkip(
            harmony,
            typeof(AirshipInteriorStardewRenderer),
            "DrawUpgradeStations",
            new[] { typeof(SpriteBatch), typeof(SaveService), typeof(float) },
            monitor
        );

        monitor.Log(
            $"0695 world-depth safety active: suppressed {patched}/4 remaining post-world physical renderer(s). Region I Hunt Run environment art is now TMX-owned; remaining static props must migrate before their safety hooks are retired.",
            patched == 4 ? LogLevel.Info : LogLevel.Warn
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
                $"0676B depth safety couldn't resolve {owner.Name}.{methodName}; refusing to invent a fallback post-world renderer.",
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

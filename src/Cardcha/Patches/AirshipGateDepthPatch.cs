using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// 0676B Airship gate depth contract.
///
/// The Forest gate must never be painted by AirshipFoundationService.DrawSkyDock from
/// Display.RenderedWorld. That path runs after Farmer/NPC rendering and can cover the player.
///
/// Instead the gate is injected around the local Farmer's own draw call. The Airship service
/// remains the single authority for the gameplay tile and decides whether the gate belongs
/// before or after the Farmer at the current Y position. The old post-world DrawSkyDock call is
/// suppressed completely, so there is no duplicate gate and no layerDepth placebo.
/// </summary>
internal static class AirshipGateDepthPatch
{
    private static AirshipFoundationService? Service;

    internal static void Apply(Harmony harmony, AirshipFoundationService service, IMonitor monitor)
    {
        Service = service;

        MethodInfo? farmerDraw = AccessTools.Method(typeof(Farmer), "draw", new[] { typeof(SpriteBatch) });
        if (farmerDraw is null)
        {
            monitor.Log(
                "0676B couldn't find Farmer.draw(SpriteBatch). Forest gate rendering is disabled rather than falling back to a player-covering RenderedWorld overlay.",
                LogLevel.Error
            );
        }
        else
        {
            harmony.Patch(
                farmerDraw,
                prefix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(BeforeFarmerDraw)),
                postfix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(AfterFarmerDraw))
            );
        }

        MethodInfo? legacyPostWorldGate = AccessTools.DeclaredMethod(
            typeof(AirshipFoundationService),
            "DrawSkyDock",
            new[] { typeof(SpriteBatch), typeof(Point) }
        );
        if (legacyPostWorldGate is null)
        {
            monitor.Log(
                "0676B couldn't resolve AirshipFoundationService.DrawSkyDock; no legacy gate suppression was installed.",
                LogLevel.Error
            );
        }
        else
        {
            harmony.Patch(
                legacyPostWorldGate,
                prefix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(SkipLegacyPostWorldGate))
            );
        }
    }

    private static void BeforeFarmerDraw(Farmer __instance, SpriteBatch b)
    {
        AirshipFoundationService? service = Service;
        if (service is null || __instance != Game1.player || !service.CanDrawForestGateForLocalPlayer())
            return;

        if (!service.ShouldDrawForestGateAfterPlayer(__instance))
            service.DrawForestGateAtFarmerDepth(b);
    }

    private static void AfterFarmerDraw(Farmer __instance, SpriteBatch b)
    {
        AirshipFoundationService? service = Service;
        if (service is null || __instance != Game1.player || !service.CanDrawForestGateForLocalPlayer())
            return;

        if (service.ShouldDrawForestGateAfterPlayer(__instance))
            service.DrawForestGateAtFarmerDepth(b);
    }

    private static bool SkipLegacyPostWorldGate()
        => false;
}

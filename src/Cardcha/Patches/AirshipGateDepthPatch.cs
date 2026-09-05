using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using Cardcha.Services;

namespace Cardcha.Patches;

internal static class AirshipGateDepthPatch
{
    private static AirshipFoundationService? Service;

    internal static void Apply(Harmony harmony, AirshipFoundationService service, IMonitor monitor)
    {
        Service = service;
        var draw = AccessTools.Method(typeof(Farmer), "draw", new[] { typeof(SpriteBatch) });
        if (draw is null)
        {
            monitor.Log("Airship gate depth patch couldn't find Farmer.draw(SpriteBatch); gate rendering was disabled instead of falling back to player-covering RenderedWorld drawing.", LogLevel.Error);
            return;
        }
        harmony.Patch(
            draw,
            prefix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(BeforeFarmerDraw)),
            postfix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(AfterFarmerDraw))
        );
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
}

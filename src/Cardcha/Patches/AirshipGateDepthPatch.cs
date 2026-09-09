using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// Keeps the Forest Airship gate in Stardew's Farmer depth order and, as of 0676B,
/// also guarantees that the authored gate art is centered on the exact gameplay anchor.
///
/// The old 0669 renderer used Y + 70, an origin 10 px above the sprite's feet and 1.48x scale.
/// In-game that made the visible arch drift away from the route/interaction tile. 0676B renders
/// the 128x128 authored asset at native 1.0 scale with its bottom-center pinned to the center-bottom
/// of the authoritative dock tile. Visual, interaction and landing logic therefore share one anchor.
/// </summary>
internal static class AirshipGateDepthPatch
{
    private const string GateAssetPath = "assets/airship_gate_auth.png";

    private static AirshipFoundationService? Service;
    private static IMonitor? Monitor;
    private static Texture2D? GateTexture;
    private static bool GateTextureFailed;

    internal static void Apply(Harmony harmony, AirshipFoundationService service, IMonitor monitor)
    {
        Service = service;
        Monitor = monitor;

        MethodInfo? farmerDraw = AccessTools.Method(typeof(Farmer), "draw", new[] { typeof(SpriteBatch) });
        if (farmerDraw is null)
        {
            monitor.Log("Airship gate depth patch couldn't find Farmer.draw(SpriteBatch); gate rendering was disabled instead of falling back to player-covering RenderedWorld drawing.", LogLevel.Error);
            return;
        }
        harmony.Patch(
            farmerDraw,
            prefix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(BeforeFarmerDraw)),
            postfix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(AfterFarmerDraw))
        );

        MethodInfo? gateDraw = AccessTools.DeclaredMethod(
            typeof(AirshipFoundationService),
            "DrawSkyDock",
            new[] { typeof(SpriteBatch), typeof(Point) }
        );
        if (gateDraw is null)
        {
            monitor.Log("0676B couldn't resolve AirshipFoundationService.DrawSkyDock(SpriteBatch, Point); gate alignment override was not installed.", LogLevel.Error);
            return;
        }

        harmony.Patch(
            gateDraw,
            prefix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(DrawAlignedGatePrefix))
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

    private static bool DrawAlignedGatePrefix(SpriteBatch batch, Point tile)
    {
        Texture2D? gate = GetGateTexture();
        if (gate is null)
            return false;

        // The exact gameplay anchor is the dock tile itself. Bottom-center the authored 128px
        // sprite on that tile and keep native scale so its two-tile footprint reads naturally.
        Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 64f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        float pulse = 0.995f + 0.010f * (float)Math.Sin(Environment.TickCount64 / 420d);
        float layer = Math.Clamp((world.Y + 8f) / 10000f, 0f, 0.94f);

        batch.Draw(
            gate,
            local,
            null,
            Color.White,
            0f,
            new Vector2(gate.Width / 2f, gate.Height),
            pulse,
            SpriteEffects.None,
            layer
        );

        return false;
    }

    private static Texture2D? GetGateTexture()
    {
        if (GateTexture is not null && !GateTexture.IsDisposed)
            return GateTexture;
        if (GateTextureFailed)
            return null;

        try
        {
            GateTexture = ModEntry.StaticHelper?.ModContent.Load<Texture2D>(GateAssetPath);
            if (GateTexture is null)
                throw new InvalidOperationException("Cardcha StaticHelper wasn't available while loading the Airship gate.");
            return GateTexture;
        }
        catch (Exception ex)
        {
            GateTextureFailed = true;
            Monitor?.Log($"0676B Airship gate asset unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            return null;
        }
    }
}

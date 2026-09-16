using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// Airship draw-order and interaction bridge.
///
/// 0676B moved the Forest gate around Farmer.draw so a RenderedWorld overlay could no longer
/// cover the player. 0696D3-E extends that same ownership rule to the Airship deck itself:
/// DrawDeckMarkers is suppressed from Display.RenderedWorld and replayed immediately before the
/// local Farmer draw. This deliberately prefers the player over runtime deck overlays until each
/// solid prop is fully TMX/native-owned.
///
/// D3-E also normalizes action tiles to the real interaction footprints. This keeps the existing
/// AirshipFoundationService gameplay handlers authoritative while making the radar, travel gate,
/// upgrade stations and Sky Dock stations usable from their visible footprint rather than one
/// fragile anchor tile.
/// </summary>
internal static class AirshipGateDepthPatch
{
    private const string DeckLocationName = "Cardcha_AirshipDeck";
    private const string SkyDockInteriorLocationName = "Cardcha_SkyDockInterior";

    private static AirshipFoundationService? Service;
    private static MethodInfo? DeckMarkersMethod;
    private static bool AllowDeckMarkerPass;

    internal static void Apply(Harmony harmony, AirshipFoundationService service, IMonitor monitor)
    {
        Service = service;

        MethodInfo? farmerDraw = AccessTools.Method(typeof(Farmer), "draw", new[] { typeof(SpriteBatch) });
        if (farmerDraw is null)
        {
            monitor.Log(
                "0696D3-E couldn't find Farmer.draw(SpriteBatch). Airship deck post-world overlays remain disabled rather than covering the player.",
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

        DeckMarkersMethod = AccessTools.DeclaredMethod(
            typeof(AirshipFoundationService),
            "DrawDeckMarkers",
            new[] { typeof(SpriteBatch), typeof(GameLocation) }
        );
        if (DeckMarkersMethod is null)
        {
            monitor.Log(
                "0696D3-E couldn't resolve AirshipFoundationService.DrawDeckMarkers; refusing to leave deck overlays in RenderedWorld.",
                LogLevel.Error
            );
        }
        else
        {
            harmony.Patch(
                DeckMarkersMethod,
                prefix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(AllowOnlyFarmerDepthDeckMarkers))
            );
        }

        MethodInfo? getActionTile = AccessTools.DeclaredMethod(typeof(AirshipFoundationService), "GetActionTile", Type.EmptyTypes);
        if (getActionTile is null)
        {
            monitor.Log(
                "0696D3-E couldn't resolve AirshipFoundationService.GetActionTile; Airship footprint normalization is unavailable.",
                LogLevel.Error
            );
        }
        else
        {
            harmony.Patch(
                getActionTile,
                postfix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(NormalizeAirshipActionTile))
            );
        }

        monitor.Log(
            "0696D3-E active: deck runtime overlays draw before the local Farmer; radar/gate/station actions use visible footprints.",
            LogLevel.Info
        );
    }

    private static void BeforeFarmerDraw(Farmer __instance, SpriteBatch b)
    {
        AirshipFoundationService? service = Service;
        if (service is null || __instance != Game1.player)
            return;

        DrawDeckMarkersBeforePlayer(service, b);

        if (!service.CanDrawForestGateForLocalPlayer())
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

    private static void DrawDeckMarkersBeforePlayer(AirshipFoundationService service, SpriteBatch batch)
    {
        GameLocation? location = Game1.currentLocation;
        if (DeckMarkersMethod is null
            || location is null
            || !location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        AllowDeckMarkerPass = true;
        try
        {
            DeckMarkersMethod.Invoke(service, new object[] { batch, location });
        }
        catch (TargetInvocationException ex)
        {
            ModEntry.StaticMonitor?.Log(
                $"0696D3-E deck pre-player render failed: {ex.InnerException?.Message ?? ex.Message}",
                LogLevel.Error
            );
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.Log($"0696D3-E deck pre-player render failed: {ex.Message}", LogLevel.Error);
        }
        finally
        {
            AllowDeckMarkerPass = false;
        }
    }

    private static bool AllowOnlyFarmerDepthDeckMarkers()
        => AllowDeckMarkerPass;

    private static void NormalizeAirshipActionTile(ref Point __result)
    {
        GameLocation? location = Game1.currentLocation;
        Farmer? player = Game1.player;
        if (location is null || player is null)
            return;

        Point action = __result;
        Point playerTile = player.TilePoint;

        if (location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
        {
            Point travelGate = ResolvePoint("ResolveDeckTravelGateTile", location, new Point(4, 5));
            Point helm = ResolvePoint("ResolveDeckHelmTile", location, new Point(12, 6));
            Point exit = ResolvePoint("ResolveDeckExitTile", location, new Point(12, 12));

            // Runtime authority D3-E: the visible radar is also a travel control. Reuse the
            // existing gate handler by normalizing a radar press to the resolved travel-gate tile.
            if (NearEither(action, playerTile, helm, 2, 2))
            {
                __result = travelGate;
                return;
            }

            if (NearEither(action, playerTile, travelGate, 2, 2))
            {
                __result = travelGate;
                return;
            }

            // D3-A canonical upgrade sockets. Normalizing to the exact socket keeps the existing
            // AirshipUpgradeMenu path unchanged while making the full machine body interactive.
            foreach (Point station in new[]
            {
                new Point(4, 8),
                new Point(19, 8),
                new Point(7, 11),
                new Point(16, 11),
            })
            {
                if (!NearEither(action, playerTile, station, 2, 2))
                    continue;
                __result = station;
                return;
            }

            if (NearEither(action, playerTile, exit, 1, 2))
                __result = exit;
            return;
        }

        if (!location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))
            return;

        // Floor 1 had exact-tile comparisons for route/bay/exit. Snap a press anywhere on the
        // visible footprint to the resolver's canonical tile, so the original handlers fire.
        foreach ((string resolver, Point fallback, int radiusX, int radiusY) in new[]
        {
            ("ResolveSkyDockInteriorRouteTile", new Point(6, 3), 2, 2),
            ("ResolveSkyDockInteriorBayTile", new Point(8, 8), 2, 2),
            ("ResolveSkyDockLostFoundTile", new Point(4, 9), 2, 2),
            ("ResolveSkyDockInteriorExitTile", new Point(6, 12), 2, 2),
        })
        {
            Point target = ResolvePoint(resolver, location, fallback);
            if (!NearEither(action, playerTile, target, radiusX, radiusY))
                continue;
            __result = target;
            return;
        }
    }

    private static Point ResolvePoint(string methodName, GameLocation location, Point fallback)
    {
        try
        {
            MethodInfo? method = AccessTools.DeclaredMethod(
                typeof(AirshipFoundationService),
                methodName,
                new[] { typeof(GameLocation) }
            );
            if (method is null)
                return fallback;

            object? value = method.Invoke(method.IsStatic ? null : Service, new object[] { location });
            return value is Point point ? point : fallback;
        }
        catch
        {
            return fallback;
        }
    }

    private static bool NearEither(Point action, Point player, Point target, int radiusX, int radiusY)
        => Near(action, target, radiusX, radiusY) || Near(player, target, radiusX, radiusY);

    private static bool Near(Point a, Point b, int radiusX, int radiusY)
        => Math.Abs(a.X - b.X) <= radiusX && Math.Abs(a.Y - b.Y) <= radiusY;

    private static bool SkipLegacyPostWorldGate()
        => false;
}

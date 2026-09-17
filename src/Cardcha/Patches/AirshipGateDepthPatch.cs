using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// 0696D3-F physical blocking, travel affordance and deck-depth recovery.
///
/// Runtime authority is Ron's 2026-09-17 in-game screenshots:
/// - Forest/Sky Dock props need real no-enter footprints so the farmer cannot stand inside art.
/// - The bridge console and floor-2 machines must not behave like one blanket floating overlay.
/// - The four upgrade stations must always remain visible.
/// - Boarding/travel must have an obvious visible pad, while the radar remains an alternate travel control.
/// - The rejected yellow/static navigation-console base must not survive in the live deck map.
///
/// D3-F therefore does NOT replay the legacy DrawDeckMarkers pass. It owns a narrow pre-Farmer
/// presentation pass containing only ambient Window/radar slices, the dedicated travel gate/pad,
/// and four explicit upgrade stations. Physical footprints are guarded before the local Farmer is
/// rendered, so the player cannot visually enter large props even when their source art spans many tiles.
/// </summary>
internal static class AirshipGateDepthPatch
{
    private const string DeckLocationName = "Cardcha_AirshipDeck";
    private const string SkyDockInteriorLocationName = "Cardcha_SkyDockInterior";
    private const string ForestLocationName = "Forest";

    private const string UpgradeAtlasPath = "assets/airship_upgrade_visuals.png";
    private const string TravelGatePath = "assets/airship_props/set01_redux/boarding_gate_arch.png";
    private const int UpgradeCellSize = 96;

    private static AirshipFoundationService? Service;
    private static MethodInfo? DeckMarkersMethod;
    private static GameLocation? PreparedDeckLocation;

    private static Texture2D? UpgradeAtlas;
    private static bool UpgradeAtlasLoadFailed;
    private static Texture2D? TravelGateTexture;
    private static bool TravelGateLoadFailed;

    private static string LastSafeLocationName = string.Empty;
    private static Vector2 LastSafePlayerPosition;
    private static bool HasLastSafePlayerPosition;

    internal static void Apply(Harmony harmony, AirshipFoundationService service, IMonitor monitor)
    {
        Service = service;

        MethodInfo? farmerDraw = AccessTools.Method(typeof(Farmer), "draw", new[] { typeof(SpriteBatch) });
        if (farmerDraw is null)
        {
            monitor.Log(
                "0696D3-F couldn't find Farmer.draw(SpriteBatch). Physical deck overlays remain suppressed rather than covering the player.",
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
        if (legacyPostWorldGate is not null)
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
                "0696D3-F couldn't resolve AirshipFoundationService.DrawDeckMarkers; no legacy deck suppression was installed.",
                LogLevel.Error
            );
        }
        else
        {
            harmony.Patch(
                DeckMarkersMethod,
                prefix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(SuppressLegacyDeckMarkers))
            );
        }

        MethodInfo? getActionTile = AccessTools.DeclaredMethod(typeof(AirshipFoundationService), "GetActionTile", Type.EmptyTypes);
        if (getActionTile is null)
        {
            monitor.Log(
                "0696D3-F couldn't resolve AirshipFoundationService.GetActionTile; footprint interaction normalization is unavailable.",
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
            "0696D3-F active: legacy deck overlay disabled; physical no-enter footprints, explicit upgrade stations and visible travel pads are authoritative.",
            LogLevel.Info
        );
    }

    private static void BeforeFarmerDraw(Farmer __instance, SpriteBatch b)
    {
        AirshipFoundationService? service = Service;
        if (service is null || __instance != Game1.player)
            return;

        GameLocation? location = Game1.currentLocation;
        if (location is not null)
        {
            EnforceD3FPhysicalFootprints(__instance, location, service);

            if (location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
            {
                PrepareD3FDeckMap(location);
                DrawD3FDeckPass(b);
            }
            else if (location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))
            {
                DrawD3FBoardingPad(b, new Point(23, 8), "BOARD AIRSHIP");
            }
        }

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

    private static bool SuppressLegacyDeckMarkers()
        => false;

    /// <summary>
    /// Removes only the 7x5 map-native navigation-console base. That base contains the rejected
    /// yellow/static backing. The transparent runtime frame + sweep/pings/glow own the live console.
    /// </summary>
    private static void PrepareD3FDeckMap(GameLocation deck)
    {
        if (ReferenceEquals(PreparedDeckLocation, deck))
            return;

        PreparedDeckLocation = deck;
        try
        {
            var layer = deck.Map?.GetLayer("Buildings2");
            if (layer is null)
                return;

            for (int y = 5; y <= 9; y++)
            {
                for (int x = 9; x <= 15; x++)
                {
                    if (x >= 0 && y >= 0 && x < layer.LayerWidth && y < layer.LayerHeight)
                        layer.Tiles[x, y] = null;
                }
            }

            ModEntry.StaticMonitor?.Log(
                "0696D3-F removed the live 7x5 yellow navigation-console base; transparent runtime frame is authoritative.",
                LogLevel.Trace
            );
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.Log($"0696D3-F console-base cleanup failed: {ex.Message}", LogLevel.Warn);
        }
    }

    private static void DrawD3FDeckPass(SpriteBatch batch)
    {
        AirshipAmbientAnimationService.DrawDeckAmbient(batch);
        DrawD3FTravelGate(batch);
        DrawD3FUpgradeStations(batch);
    }

    private static void DrawD3FTravelGate(SpriteBatch batch)
    {
        Point tile = new(4, 5);
        Vector2 floor = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 58f);
        Texture2D? gate = GetTravelGateTexture();
        if (gate is not null && gate.Width > 0 && gate.Height > 0)
        {
            const int width = 244;
            int height = Math.Max(128, (int)MathF.Round(gate.Height * (width / (float)gate.Width)));
            Rectangle dst = new((int)floor.X - width / 2, (int)floor.Y - height + 32, width, height);
            batch.Draw(gate, dst, Color.White);
        }

        DrawD3FBoardingPad(batch, tile, "TRAVEL");
    }

    private static void DrawD3FBoardingPad(SpriteBatch batch, Point tile, string label)
    {
        Vector2 floor = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 58f);
        float pulse = 0.72f + 0.12f * MathF.Sin(Environment.TickCount64 / 180f);
        Color cyan = new Color(95, 224, 218) * pulse;
        Color gold = new Color(229, 177, 84) * 0.78f;

        DrawRect(batch, new Rectangle((int)floor.X - 48, (int)floor.Y + 7, 96, 5), gold);
        DrawRect(batch, new Rectangle((int)floor.X - 38, (int)floor.Y + 1, 76, 3), cyan * 0.72f);
        DrawDiamond(batch, new Vector2(floor.X, floor.Y - 11f), 7, cyan);

        Vector2 size = Game1.smallFont.MeasureString(label);
        Vector2 text = new(floor.X - size.X / 2f, floor.Y + 18f);
        batch.DrawString(Game1.smallFont, label, text + new Vector2(2f, 2f), Color.Black * 0.76f);
        batch.DrawString(Game1.smallFont, label, text, Color.White);
    }

    private static void DrawD3FUpgradeStations(SpriteBatch batch)
    {
        Texture2D? atlas = GetUpgradeAtlas();
        int[] levels = ResolveUpgradeLevels();
        (Point Tile, int Column, Color Accent)[] stations =
        {
            (new Point(4, 8), 0, new Color(104, 205, 200)),
            (new Point(19, 8), 1, new Color(98, 166, 211)),
            (new Point(7, 11), 2, new Color(151, 151, 210)),
            (new Point(16, 11), 3, new Color(190, 133, 207)),
        };

        for (int i = 0; i < stations.Length; i++)
        {
            (Point tile, int column, Color accent) = stations[i];
            Vector2 center = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 52f);
            float pulse = 0.72f + 0.10f * MathF.Sin(Environment.TickCount64 / 220f + i);

            // Ground first: even if the atlas fails, the station remains visible and readable.
            DrawRect(batch, new Rectangle((int)center.X - 48, (int)center.Y + 10, 96, 16), new Color(47, 32, 29) * 0.95f);
            DrawRect(batch, new Rectangle((int)center.X - 41, (int)center.Y + 7, 82, 6), new Color(180, 120, 58) * 0.86f);

            if (atlas is not null && atlas.Width >= (column + 1) * UpgradeCellSize)
            {
                int rows = Math.Max(1, atlas.Height / UpgradeCellSize);
                int level = Math.Clamp(levels[i], 0, rows - 1);
                Rectangle src = new(column * UpgradeCellSize, level * UpgradeCellSize, UpgradeCellSize, UpgradeCellSize);
                Rectangle dst = new((int)center.X - 48, (int)center.Y - 64, 96, 96);
                batch.Draw(atlas, dst, src, Color.White);
            }
            else
            {
                DrawRect(batch, new Rectangle((int)center.X - 34, (int)center.Y - 49, 68, 58), new Color(41, 47, 57) * 0.96f);
                DrawRect(batch, new Rectangle((int)center.X - 25, (int)center.Y - 38, 50, 30), accent * 0.42f);
            }

            DrawRect(batch, new Rectangle((int)center.X - 22, (int)center.Y - 26, 44, 4), accent * pulse);
            DrawDiamond(batch, new Vector2(center.X, center.Y - 44), 5, accent * pulse);

            const string label = "UPGRADE";
            Vector2 size = Game1.smallFont.MeasureString(label);
            Vector2 text = new(center.X - size.X / 2f, center.Y + 28f);
            batch.DrawString(Game1.smallFont, label, text + new Vector2(2f, 2f), Color.Black * 0.72f);
            batch.DrawString(Game1.smallFont, label, text, Color.White * 0.92f);
        }
    }

    private static int[] ResolveUpgradeLevels()
    {
        int[] result = { 0, 0, 0, 0 };
        AirshipFoundationService? service = Service;
        if (service is null)
            return result;

        try
        {
            FieldInfo? saveField = typeof(AirshipFoundationService).GetField("Save", BindingFlags.Instance | BindingFlags.NonPublic);
            if (saveField?.GetValue(service) is not SaveService save)
                return result;

            result[0] = Math.Clamp(save.Data.AirshipEngineLevel, 0, 3);
            result[1] = Math.Clamp(save.Data.AirshipNavigationLevel, 0, 3);
            result[2] = Math.Clamp(save.Data.AirshipHullLevel, 0, 3);
            result[3] = Math.Clamp(save.Data.AirshipReactorLevel, 0, 3);
        }
        catch
        {
            // Level 0 art is a safe visual fallback; gameplay values remain owned by SaveService.
        }
        return result;
    }

    private static Texture2D? GetUpgradeAtlas()
    {
        if (UpgradeAtlas is not null && !UpgradeAtlas.IsDisposed)
            return UpgradeAtlas;
        UpgradeAtlas = null;
        if (UpgradeAtlasLoadFailed || ModEntry.StaticHelper is null)
            return null;
        try
        {
            UpgradeAtlas = ModEntry.StaticHelper.ModContent.Load<Texture2D>(UpgradeAtlasPath);
            return UpgradeAtlas;
        }
        catch (Exception ex)
        {
            UpgradeAtlasLoadFailed = true;
            ModEntry.StaticMonitor?.Log($"0696D3-F upgrade atlas unavailable; visible fallback stations will be used. {ex.Message}", LogLevel.Warn);
            return null;
        }
    }

    private static Texture2D? GetTravelGateTexture()
    {
        if (TravelGateTexture is not null && !TravelGateTexture.IsDisposed)
            return TravelGateTexture;
        TravelGateTexture = null;
        if (TravelGateLoadFailed || ModEntry.StaticHelper is null)
            return null;
        try
        {
            TravelGateTexture = ModEntry.StaticHelper.ModContent.Load<Texture2D>(TravelGatePath);
            return TravelGateTexture;
        }
        catch (Exception ex)
        {
            TravelGateLoadFailed = true;
            ModEntry.StaticMonitor?.Log($"0696D3-F travel gate art unavailable; travel pad remains visible. {ex.Message}", LogLevel.Warn);
            return null;
        }
    }

    /// <summary>
    /// D3-F no-enter guard. This intentionally changes only the local Farmer position, never the
    /// base Forest map, so other map mods keep ownership of their tiles. The last valid position is
    /// restored before draw whenever movement enters a Cardcha physical footprint.
    /// </summary>
    private static void EnforceD3FPhysicalFootprints(Farmer player, GameLocation location, AirshipFoundationService service)
    {
        List<Rectangle> blocked = BuildD3FBlockedRects(location, service);
        string locationName = location.NameOrUniqueName;
        if (blocked.Count == 0)
        {
            LastSafeLocationName = locationName;
            LastSafePlayerPosition = player.Position;
            HasLastSafePlayerPosition = true;
            return;
        }

        Rectangle bounds = player.GetBoundingBox();
        bool inside = blocked.Any(rect => rect.Intersects(bounds));
        bool sameLocation = string.Equals(LastSafeLocationName, locationName, StringComparison.OrdinalIgnoreCase);

        if (!sameLocation)
        {
            LastSafeLocationName = locationName;
            HasLastSafePlayerPosition = false;
        }

        if (!inside)
        {
            LastSafePlayerPosition = player.Position;
            HasLastSafePlayerPosition = true;
            return;
        }

        if (HasLastSafePlayerPosition)
        {
            player.Position = LastSafePlayerPosition;
            player.Halt();
            return;
        }

        Point origin = player.TilePoint;
        for (int radius = 1; radius <= 5; radius++)
        {
            for (int y = origin.Y - radius; y <= origin.Y + radius; y++)
            {
                for (int x = origin.X - radius; x <= origin.X + radius; x++)
                {
                    if (Math.Abs(x - origin.X) != radius && Math.Abs(y - origin.Y) != radius)
                        continue;
                    if (x < 0 || y < 0)
                        continue;

                    Rectangle candidate = new(x * 64 + 10, y * 64 + 30, 44, 28);
                    if (blocked.Any(rect => rect.Intersects(candidate)))
                        continue;
                    try
                    {
                        if (location.IsTileBlockedBy(new Vector2(x, y)))
                            continue;
                    }
                    catch
                    {
                        continue;
                    }

                    player.Position = new Vector2(x * 64f, y * 64f);
                    player.Halt();
                    LastSafePlayerPosition = player.Position;
                    HasLastSafePlayerPosition = true;
                    return;
                }
            }
        }
    }

    private static List<Rectangle> BuildD3FBlockedRects(GameLocation location, AirshipFoundationService service)
    {
        List<Rectangle> result = new();
        string name = location.NameOrUniqueName;

        if (name.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
        {
            // Large navigation desk: keep the farmer in front of it, never inside its lower body.
            result.Add(TileRect(9, 8, 7, 3));

            // Four upgrade stations. Top pair needs two physical rows; lower pair keeps one row
            // so the bottom doorway/walking spine remains open.
            result.Add(TileRect(3, 8, 3, 2));
            result.Add(TileRect(18, 8, 3, 2));
            result.Add(TileRect(6, 11, 3, 1));
            result.Add(TileRect(15, 11, 3, 1));

            // Dedicated travel gate: solid posts, open center/pad.
            result.Add(TileRect(2, 4, 2, 3));
            result.Add(TileRect(5, 4, 2, 3));
            return result;
        }

        if (name.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))
        {
            // Wall-board cluster and waiting bench.
            result.Add(TileRect(2, 4, 12, 2));
            result.Add(TileRect(2, 9, 6, 2));

            // Boarding gate has solid side posts but an open center leading to bay (23,8).
            result.Add(TileRect(21, 4, 2, 4));
            result.Add(TileRect(26, 4, 2, 4));

            // Cargo/service cluster on the far right.
            result.Add(TileRect(22, 10, 4, 3));
            return result;
        }

        if (name.Equals(ForestLocationName, StringComparison.OrdinalIgnoreCase)
            && service.CanDrawForestGateForLocalPlayer())
        {
            Point? dock = TryResolveServicePointNoArgs("ResolveSkyDockTile");
            if (dock is Point p)
            {
                // Do not alter Forest tiles. Only the two gate posts are no-enter; the center
                // opening and approach lane stay walkable/actionable.
                result.Add(TileRect(p.X - 2, p.Y - 2, 1, 4));
                result.Add(TileRect(p.X + 2, p.Y - 2, 1, 4));
            }
        }

        return result;
    }

    private static Rectangle TileRect(int x, int y, int width, int height)
        => new(x * 64, y * 64, width * 64, height * 64);

    private static Point? TryResolveServicePointNoArgs(string methodName)
    {
        try
        {
            MethodInfo? method = AccessTools.DeclaredMethod(typeof(AirshipFoundationService), methodName, Type.EmptyTypes);
            object? value = method?.Invoke(Service, Array.Empty<object>());
            return value is Point point ? point : null;
        }
        catch
        {
            return null;
        }
    }

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

            // Radar remains a valid alternate travel control, but the dedicated gate/pad is now
            // visually obvious and is the primary affordance.
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

        foreach ((string resolver, Point fallback, int radiusX, int radiusY) in new[]
        {
            ("ResolveSkyDockInteriorRouteTile", new Point(7, 7), 2, 2),
            ("ResolveSkyDockInteriorBayTile", new Point(23, 8), 2, 2),
            ("ResolveSkyDockLostFoundTile", new Point(5, 11), 2, 2),
            ("ResolveSkyDockInteriorExitTile", new Point(15, 16), 2, 2),
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

    private static Vector2 WorldToScreen(float worldX, float worldY)
        => Game1.GlobalToLocal(Game1.viewport, new Vector2(worldX, worldY));

    private static void DrawDiamond(SpriteBatch batch, Vector2 center, int radius, Color color)
    {
        for (int y = -radius; y <= radius; y++)
        {
            int half = radius - Math.Abs(y);
            DrawRect(batch, new Rectangle((int)center.X - half, (int)center.Y + y, half * 2 + 1, 1), color);
        }
    }

    private static void DrawRect(SpriteBatch batch, Rectangle rect, Color color)
    {
        if (rect.Width <= 0 || rect.Height <= 0 || color.A == 0)
            return;
        batch.Draw(Game1.staminaRect, rect, color);
    }

    private static bool SkipLegacyPostWorldGate()
        => false;
}

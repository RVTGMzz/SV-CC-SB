using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// 0696D3-L asset separation, native collision and bridge-depth recovery.
///
/// Runtime authority is Ron's 2026-09-18 post-D3-G 12-image retest:
/// - never correct Farmer.Position to fake collision;
/// - Room 1 / Room 2 physical footprints belong to native map collision wherever possible;
/// - the Forest gate uses the game's collision query for segmented solid posts/wood only;
/// - the map owns the transparent console body and observation-window shell depth;
/// - four upgrade stations and the visible TRAVEL affordance remain preserved.
///
/// This patch now owns only the narrow pre-Farmer transient/presentation pass plus interaction
/// normalization and the Forest gate's native collision answer. It never teleports, pins, or
/// rewinds the Farmer as a collision response.
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
    private static Texture2D? UpgradeAtlas;
    private static bool UpgradeAtlasLoadFailed;
    private static Texture2D? TravelGateTexture;
    private static bool TravelGateLoadFailed;

    internal static void Apply(Harmony harmony, AirshipFoundationService service, IMonitor monitor)
    {
        Service = service;

        MethodInfo? farmerDraw = AccessTools.Method(typeof(Farmer), "draw", new[] { typeof(SpriteBatch) });
        if (farmerDraw is null)
        {
            monitor.Log(
                "0696D3-L couldn't find Farmer.draw(SpriteBatch). Physical deck overlays remain suppressed rather than covering the player.",
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
                "0696D3-L couldn't resolve AirshipFoundationService.DrawDeckMarkers; no legacy deck suppression was installed.",
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


        // 0696D3-L load-safety correction:
        // D3-K proved three runtime overloads exist, but installing a generic object[]/MethodBase
        // postfix on every collision overload caused Ron's save load to stall before world entry.
        // Do not Harmony-patch this hot path in D3-L. Probe signatures once at startup instead,
        // preserve the authored TMX collision in Room 1/2, and use the runtime evidence to choose
        // one lightweight hook in the next incremental patch if the Forest gate still needs it.
        int collisionCandidateCount = 0;
        foreach (MethodInfo candidate in AccessTools.GetDeclaredMethods(typeof(GameLocation)))
        {
            if (!candidate.Name.Equals("isCollidingPosition", StringComparison.Ordinal)
                || candidate.ReturnType != typeof(bool))
            {
                continue;
            }

            ParameterInfo[] parameters = candidate.GetParameters();
            if (parameters.Length == 0 || parameters[0].ParameterType != typeof(Rectangle))
                continue;

            collisionCandidateCount++;
            string signature = string.Join(
                ", ",
                parameters.Select(parameter =>
                    $"{parameter.ParameterType.FullName ?? parameter.ParameterType.Name} {parameter.Name}")
            );
            monitor.Log(
                $"0696D3-L collision signature probe [{collisionCandidateCount}]: bool GameLocation.isCollidingPosition({signature})",
                LogLevel.Info
            );
        }

        if (collisionCandidateCount == 0)
        {
            monitor.Log(
                "0696D3-L couldn't discover a compatible GameLocation.isCollidingPosition signature. No runtime collision Harmony hook is installed.",
                LogLevel.Warn
            );
        }
        else
        {
            monitor.Log(
                $"0696D3-L load-safe mode: observed {collisionCandidateCount} compatible GameLocation.isCollidingPosition overload(s); runtime collision Harmony postfix is intentionally disabled.",
                LogLevel.Info
            );
        }

        MethodInfo? getActionTile = AccessTools.DeclaredMethod(typeof(AirshipFoundationService), "GetActionTile", Type.EmptyTypes);
        if (getActionTile is null)
        {
            monitor.Log(
                "0696D3-L couldn't resolve AirshipFoundationService.GetActionTile; footprint interaction normalization is unavailable.",
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
            "0696D3-L active: forced-position blocking removed; TMX/native collision, transparent console layering, explicit upgrade stations and travel affordances are authoritative.",
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
            if (location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
            {
                DrawD3KDeckPass(b);
            }
            else if (location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))
            {
                Point bay = ResolvePoint("ResolveSkyDockInteriorBayTile", location, new Point(17, 7));
                DrawD3KBoardingPad(b, bay, "BOARD AIRSHIP");
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

    private static void DrawD3KDeckPass(SpriteBatch batch)
    {
        AirshipAmbientAnimationService.DrawDeckAmbient(batch);
        DrawD3KTravelGate(batch);
        DrawD3KUpgradeStations(batch);
    }

    private static void DrawD3KTravelGate(SpriteBatch batch)
    {
        Point tile = new(4, 5);
        Vector2 floor = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 58f);
        Texture2D? gate = GetTravelGateTexture();
        if (gate is not null && gate.Width > 0 && gate.Height > 0)
        {
            const int width = 366;
            int height = Math.Max(128, (int)MathF.Round(gate.Height * (width / (float)gate.Width)));
            Rectangle dst = new((int)floor.X - width / 2, (int)floor.Y - height + 32, width, height);
            batch.Draw(gate, dst, Color.White);
        }

        DrawD3KBoardingPad(batch, tile, "TRAVEL");
    }

    private static void DrawD3KBoardingPad(SpriteBatch batch, Point tile, string label)
    {
        Vector2 floor = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 58f);
        float pulse = 0.72f + 0.12f * MathF.Sin(Environment.TickCount64 / 180f);
        Color cyan = new Color(95, 224, 218) * pulse;
        Color gold = new Color(229, 177, 84) * 0.78f;

        // D3-K: the map-authored rug owns the physical path; runtime only gives the
        // destination rune a restrained pixel glow so the carpet never becomes a flat LED panel.
        DrawRect(batch, new Rectangle((int)floor.X - 45, (int)floor.Y + 7, 90, 3), gold * 0.72f);
        DrawRect(batch, new Rectangle((int)floor.X - 28, (int)floor.Y - 1, 56, 3), cyan * 0.58f);
        DrawRect(batch, new Rectangle((int)floor.X - 18, (int)floor.Y - 8, 36, 16), cyan * (0.07f + pulse * 0.035f));
        DrawDiamond(batch, new Vector2(floor.X, floor.Y - 11f), 8, cyan);
        DrawDiamond(batch, new Vector2(floor.X, floor.Y - 11f), 3, Color.White * (0.55f + pulse * 0.18f));

        Vector2 size = Game1.smallFont.MeasureString(label);
        Vector2 text = new(floor.X - size.X / 2f, floor.Y + 18f);
        batch.DrawString(Game1.smallFont, label, text + new Vector2(2f, 2f), Color.Black * 0.76f);
        batch.DrawString(Game1.smallFont, label, text, Color.White);
    }

    private static void DrawD3KUpgradeStations(SpriteBatch batch)
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

            const int presentationSize = 96;
            const int halfPresentation = presentationSize / 2;
            const int topOffset = 64;

            // D3-K: all four UPGRADE stations return to the same native-scale presentation. The separate
            // ChaCha Resonance station is the machine Ron requested at 2x.
            DrawRect(batch,
                new Rectangle((int)center.X - Math.Max(42, halfPresentation - 8), (int)center.Y - 52,
                    Math.Max(84, presentationSize - 16), 58),
                accent * (0.055f + pulse * 0.025f));
            DrawRect(batch,
                new Rectangle((int)center.X - 32, (int)center.Y - 35, 64, 38),
                accent * (0.070f + pulse * 0.040f));

            if (atlas is not null && atlas.Width >= (column + 1) * UpgradeCellSize)
            {
                int rows = Math.Max(1, atlas.Height / UpgradeCellSize);
                int level = Math.Clamp(levels[i], 0, rows - 1);
                Rectangle src = new(column * UpgradeCellSize, level * UpgradeCellSize, UpgradeCellSize, UpgradeCellSize);
                Rectangle dst = new((int)center.X - halfPresentation, (int)center.Y - topOffset, presentationSize, presentationSize);
                batch.Draw(atlas, dst, src, Color.White);
            }
            else
            {
                const int fallbackWidth = 68;
                const int fallbackHeight = 58;
                DrawRect(batch, new Rectangle((int)center.X - fallbackWidth / 2, (int)center.Y - fallbackHeight + 9, fallbackWidth, fallbackHeight), new Color(41, 47, 57) * 0.96f);
                DrawRect(batch, new Rectangle((int)center.X - fallbackWidth / 2 + 9, (int)center.Y - fallbackHeight + 20, fallbackWidth - 18, Math.Max(30, fallbackHeight / 2)), accent * 0.42f);
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
            ModEntry.StaticMonitor?.Log($"0696D3-L upgrade atlas unavailable; visible fallback stations will be used. {ex.Message}", LogLevel.Warn);
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
            ModEntry.StaticMonitor?.Log($"0696D3-L travel gate art unavailable; travel pad remains visible. {ex.Message}", LogLevel.Warn);
            return null;
        }
    }

    private static void AfterCollisionCheck(
        GameLocation __instance,
        MethodBase __originalMethod,
        object[] __args,
        ref bool __result)
    {
        AirshipFoundationService? service = Service;
        if (__result || service is null || __args.Length == 0 || __args[0] is not Rectangle position)
            return;

        bool isFarmer = false;
        Character? character = null;
        ParameterInfo[] parameters = __originalMethod.GetParameters();

        for (int i = 0; i < parameters.Length && i < __args.Length; i++)
        {
            ParameterInfo parameter = parameters[i];

            if (parameter.Name?.Equals("isFarmer", StringComparison.OrdinalIgnoreCase) == true
                && __args[i] is bool farmerFlag)
            {
                isFarmer = farmerFlag;
            }

            if (character is null
                && typeof(Character).IsAssignableFrom(parameter.ParameterType)
                && __args[i] is Character candidateCharacter)
            {
                character = candidateCharacter;
            }
        }

        if (!isFarmer || !ReferenceEquals(character, Game1.player))
            return;

        string locationName = __instance.NameOrUniqueName;

        // 0696D3-L: collision-query enforcement mirrors the TMX Buildings footprints.
        // This is a normal collision answer only; it never moves, rewinds, pins, or teleports Farmer.
        if (locationName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
        {
            if (IntersectsAny(position, BuildD3KDeckSolidSegments()))
                __result = true;
            return;
        }

        if (locationName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))
        {
            if (IntersectsAny(position, BuildD3KSkyDockSolidSegments()))
                __result = true;
            return;
        }

        if (!locationName.Equals(ForestLocationName, StringComparison.OrdinalIgnoreCase)
            || !service.CanDrawForestGateForLocalPlayer())
        {
            return;
        }

        Point? anchor = TryResolveForestGateAnchor();
        if (anchor is not Point gate)
            return;

        if (IntersectsAny(position, BuildForestGateSolidSegments(gate)))
            __result = true;
    }

    private static bool IntersectsAny(Rectangle position, IEnumerable<Rectangle> solids)
    {
        foreach (Rectangle solid in solids)
        {
            if (solid.Intersects(position))
                return true;
        }
        return false;
    }

    private static Rectangle TileRect(int x, int y, int widthTiles, int heightTiles)
    {
        const int tile = 64;
        return new Rectangle(x * tile, y * tile, widthTiles * tile, heightTiles * tile);
    }

    private static IEnumerable<Rectangle> BuildD3KSkyDockSolidSegments()
    {
        // Wall furniture: leave exactly the row below each prop open as the interaction lane.
        yield return TileRect(2, 5, 5, 3);   // notice board
        yield return TileRect(8, 5, 6, 2);   // Lost & Found
        yield return TileRect(2, 9, 6, 3);   // waiting bench
        yield return TileRect(8, 9, 4, 4);   // luggage cart
        yield return TileRect(20, 9, 3, 3);  // cargo

        // Boarding architecture: side furnishings/posts are solid; x17 remains the center throat.
        yield return TileRect(14, 5, 3, 4);
        yield return TileRect(18, 5, 3, 4);

        // Wall lamp.
        yield return TileRect(21, 5, 2, 2);
    }

    private static IEnumerable<Rectangle> BuildD3KDeckSolidSegments()
    {
        // Dedicated TRAVEL gate: segmented sides, center x4 open.
        yield return TileRect(2, 4, 2, 3);
        yield return TileRect(5, 4, 2, 3);

        // Navigation console full visible body. y10 is the front interaction lane.
        yield return TileRect(9, 5, 7, 5);

        // Four UPGRADE physical bases. These block crossing through the machines while retaining
        // natural Stardew-style walk-behind/front lanes around their upper sprite portions.
        yield return TileRect(3, 8, 3, 1);
        yield return TileRect(18, 8, 3, 1);
        yield return TileRect(6, 11, 3, 1);
        yield return TileRect(15, 11, 3, 1);

        // Signal lamp and the actual 2x ChaCha Resonance machine.
        yield return TileRect(18, 6, 2, 1);
        yield return TileRect(20, 5, 3, 2);
    }

    private static IEnumerable<Rectangle> BuildForestGateSolidSegments(Point gate)
    {
        const int tile = 64;

        // Tall outer posts: always solid.
        yield return new Rectangle((gate.X - 2) * tile, (gate.Y - 2) * tile, tile, tile * 4);
        yield return new Rectangle((gate.X + 2) * tile, (gate.Y - 2) * tile, tile, tile * 4);

        // Upper wooden shoulders: solid only above the entrance. The center/lower lane stays open.
        yield return new Rectangle((gate.X - 1) * tile, (gate.Y - 2) * tile, tile, tile * 2);
        yield return new Rectangle((gate.X + 1) * tile, (gate.Y - 2) * tile, tile, tile * 2);
    }

    private static Point? TryResolveForestGateAnchor()
    {
        try
        {
            MethodInfo? method = AccessTools.DeclaredMethod(
                typeof(AirshipFoundationService),
                "ResolveSkyDockTile",
                Type.EmptyTypes
            );
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
            ("ResolveSkyDockInteriorRouteTile", new Point(4, 7), 2, 2),
            ("ResolveSkyDockInteriorBayTile", new Point(17, 7), 2, 2),
            ("ResolveSkyDockLostFoundTile", new Point(10, 6), 3, 2),
            ("ResolveSkyDockWaitingBenchTile", new Point(4, 11), 3, 2),
            ("ResolveSkyDockLuggageCartTile", new Point(9, 12), 2, 2),
            ("ResolveSkyDockCargoTile", new Point(21, 11), 2, 2),
            ("ResolveSkyDockInteriorExitTile", new Point(12, 13), 2, 2),
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

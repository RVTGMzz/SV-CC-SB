using System.Runtime.CompilerServices;
using HarmonyLib;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Patches;

/// <summary>
/// Runtime correction for the Forest Arcane Gate placement policy.
///
/// The original alpha.28 resolver searched a growing radius around the Farm entrance and paired
/// that with a 320px action bubble. On heavily edited Forest maps this could leave the gate visually
/// wedged into a dense pocket while still being activatable from oddly far away.
///
/// This patch keeps the Buildings/Front safety rejection, but changes what happens when the local
/// pocket is bad: search a few compact, clearly separate Forest zones instead. The interaction reach
/// is then clamped back to a normal nearby distance, so relocation is visible and physical rather
/// than being hidden behind a giant invisible activation radius.
/// </summary>
internal static class AirshipGateRelocationPatch
{
    private const float LegacyWideGateUseDistance = 320f;
    private const float RelocatedGateUseDistance = 160f;
    private const int LocalSearchRadius = 3;
    private const int AlternateZoneSearchRadius = 3;
    private const int MinAlternateZoneDistanceTiles = 8;
    private const int SectorSpacingTiles = 8;

    private static bool LoggedRelocation;
    private static bool LoggedFallback;

    [ModuleInitializer]
    internal static void Initialize()
    {
        Harmony harmony = new("Ronvotri.Cardcha.AirshipGateRelocation");

        var resolveGate = AccessTools.Method(typeof(AirshipFoundationService), "ResolveSkyDockTile");
        var resolvePrefix = AccessTools.Method(typeof(AirshipGateRelocationPatch), nameof(ResolveSkyDockTilePrefix));
        if (resolveGate is not null && resolvePrefix is not null)
            harmony.Patch(resolveGate, prefix: new HarmonyMethod(resolvePrefix));

        var playerIsNear = AccessTools.Method(
            typeof(AirshipFoundationService),
            "PlayerIsNear",
            new[] { typeof(Point), typeof(float) }
        );
        var nearPrefix = AccessTools.Method(typeof(AirshipGateRelocationPatch), nameof(PlayerIsNearPrefix));
        if (playerIsNear is not null && nearPrefix is not null)
            harmony.Patch(playerIsNear, prefix: new HarmonyMethod(nearPrefix));
    }

    private static void PlayerIsNearPrefix(ref float useDistance)
    {
        // Only replace the old Forest-gate reach. Leave all ordinary 128px Airship interactions alone.
        if (Math.Abs(useDistance - LegacyWideGateUseDistance) < 0.01f)
            useDistance = RelocatedGateUseDistance;
    }

    private static bool ResolveSkyDockTilePrefix(
        ref Point __result,
        ref Point? ___CachedSkyDockTile,
        ref Point? ___CachedForestFarmWarpTile
    )
    {
        if (___CachedSkyDockTile is Point cached)
        {
            __result = cached;
            return false;
        }

        GameLocation? forest = Game1.getLocationFromName(AirshipFoundationService.SkyDockLocationName);
        if (forest is null)
        {
            ___CachedSkyDockTile = new Point(6, 6);
            __result = ___CachedSkyDockTile.Value;
            return false;
        }

        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        int height = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;
        Point farmWarp = ___CachedForestFarmWarpTile ?? ResolveForestFarmWarpTile(forest, width);
        ___CachedForestFarmWarpTile = farmWarp;

        Point preferred = ClampInsideMap(
            new Point(farmWarp.X - 7, farmWarp.Y + 2),
            width,
            height
        );

        Point? local = FindSafeInZone(forest, preferred, farmWarp, LocalSearchRadius, width, height);
        if (local is Point localSafe)
        {
            ___CachedSkyDockTile = localSafe;
            __result = localSafe;
            return false;
        }

        foreach (Point zone in BuildAlternateZones(width, height, farmWarp, preferred))
        {
            Point? alternate = FindSafeInZone(
                forest,
                zone,
                farmWarp,
                AlternateZoneSearchRadius,
                width,
                height
            );
            if (alternate is not Point alternateSafe)
                continue;

            ___CachedSkyDockTile = alternateSafe;
            __result = alternateSafe;

            if (!LoggedRelocation)
            {
                LoggedRelocation = true;
                ModEntry.StaticMonitor?.Log(
                    $"Arcane Gate local Forest pocket is blocked; relocated to ({alternateSafe.X},{alternateSafe.Y}) instead of widening its interaction radius.",
                    LogLevel.Info
                );
            }
            return false;
        }

        // Last resort: hop sector-by-sector through the map. Each sector still gets only a tiny
        // local search. This is relocation, not one enormous expanding circle around the old spot.
        foreach (Point sector in BuildSectorSweep(width, height, farmWarp, preferred))
        {
            Point? alternate = FindSafeInZone(forest, sector, farmWarp, 2, width, height);
            if (alternate is not Point alternateSafe)
                continue;

            ___CachedSkyDockTile = alternateSafe;
            __result = alternateSafe;

            if (!LoggedRelocation)
            {
                LoggedRelocation = true;
                ModEntry.StaticMonitor?.Log(
                    $"Arcane Gate required a distant Forest relocation; using safe sector ({alternateSafe.X},{alternateSafe.Y}) with normal interaction reach.",
                    LogLevel.Info
                );
            }
            return false;
        }

        // Extremely hostile/fully blocked maps may expose no valid 3x3 footprint at all. Keep the
        // deterministic preferred anchor, but do NOT restore the old 320px invisible activation bubble.
        ___CachedSkyDockTile = preferred;
        __result = preferred;
        if (!LoggedFallback)
        {
            LoggedFallback = true;
            ModEntry.StaticMonitor?.Log(
                "Arcane Gate could not find any fully clear Forest sector. Keeping the preferred anchor with normal interaction reach; no wide-radius fallback was enabled.",
                LogLevel.Warn
            );
        }
        return false;
    }

    private static Point ResolveForestFarmWarpTile(GameLocation forest, int width)
    {
        try
        {
            foreach (Warp warp in forest.warps)
            {
                if (!string.IsNullOrWhiteSpace(warp.TargetName)
                    && warp.TargetName.Contains("Farm", StringComparison.OrdinalIgnoreCase))
                {
                    return new Point(warp.X, warp.Y);
                }
            }
        }
        catch
        {
            // A map overhaul may expose warp metadata differently. Use the same deterministic fallback
            // shape as the foundation service instead of guessing a vanilla-only coordinate.
        }

        return new Point(Math.Clamp(width / 2, 3, Math.Max(3, width - 4)), 2);
    }

    private static IEnumerable<Point> BuildAlternateZones(int width, int height, Point farmWarp, Point preferred)
    {
        Point[] raw =
        {
            new(farmWarp.X + 9, farmWarp.Y + 3),
            new(farmWarp.X - 11, farmWarp.Y + 11),
            new(width / 4, height / 3),
            new((width * 3) / 4, height / 3),
            new(width / 4, (height * 2) / 3),
            new((width * 3) / 4, (height * 2) / 3),
            new(width / 2, height / 2),
        };

        HashSet<Point> seen = new();
        int minDistanceSquared = MinAlternateZoneDistanceTiles * MinAlternateZoneDistanceTiles;

        foreach (Point point in raw)
        {
            Point clamped = ClampInsideMap(point, width, height);
            if (TileDistanceSquared(clamped, preferred) < minDistanceSquared || !seen.Add(clamped))
                continue;
            yield return clamped;
        }
    }

    private static IEnumerable<Point> BuildSectorSweep(int width, int height, Point farmWarp, Point preferred)
    {
        int minDistanceSquared = MinAlternateZoneDistanceTiles * MinAlternateZoneDistanceTiles;
        List<Point> sectors = new();

        for (int y = 4; y <= Math.Max(4, height - 5); y += SectorSpacingTiles)
        {
            for (int x = 4; x <= Math.Max(4, width - 5); x += SectorSpacingTiles)
            {
                Point point = ClampInsideMap(new Point(x, y), width, height);
                if (TileDistanceSquared(point, preferred) < minDistanceSquared)
                    continue;
                sectors.Add(point);
            }
        }

        return sectors
            .Distinct()
            .OrderBy(point => TileDistanceSquared(point, farmWarp))
            .ThenBy(point => point.Y)
            .ThenBy(point => point.X);
    }

    private static Point? FindSafeInZone(
        GameLocation forest,
        Point center,
        Point farmWarp,
        int radius,
        int width,
        int height
    )
    {
        for (int ring = 0; ring <= radius; ring++)
        {
            for (int y = center.Y - ring; y <= center.Y + ring; y++)
            {
                for (int x = center.X - ring; x <= center.X + ring; x++)
                {
                    if (Math.Max(Math.Abs(x - center.X), Math.Abs(y - center.Y)) != ring)
                        continue;

                    Point candidate = ClampInsideMap(new Point(x, y), width, height);
                    if (IsDockFootprintSafe(forest, candidate, farmWarp, width, height))
                        return candidate;
                }
            }
        }

        return null;
    }

    private static bool IsDockFootprintSafe(
        GameLocation location,
        Point anchor,
        Point farmWarp,
        int width,
        int height
    )
    {
        Point[] footprint =
        {
            new(anchor.X - 1, anchor.Y),
            anchor,
            new(anchor.X + 1, anchor.Y),
            new(anchor.X - 1, anchor.Y + 1),
            new(anchor.X, anchor.Y + 1),
            new(anchor.X + 1, anchor.Y + 1),
            new(anchor.X - 1, anchor.Y + 2),
            new(anchor.X, anchor.Y + 2),
            new(anchor.X + 1, anchor.Y + 2),
        };

        foreach (Point tile in footprint)
        {
            if (!IsMapTileClear(location, tile, farmWarp, width, height))
                return false;
        }

        // A clear visual footprint is not enough if the player still cannot stand in front of it.
        // Require at least one clear approach tile immediately below the 3x3 gate footprint.
        Point[] approach =
        {
            new(anchor.X - 1, anchor.Y + 3),
            new(anchor.X, anchor.Y + 3),
            new(anchor.X + 1, anchor.Y + 3),
        };
        return approach.Any(tile => IsMapTileClear(location, tile, farmWarp, width, height));
    }

    private static bool IsMapTileClear(
        GameLocation location,
        Point tilePoint,
        Point farmWarp,
        int width,
        int height
    )
    {
        if (tilePoint.X < 1 || tilePoint.Y < 1 || tilePoint.X >= width - 1 || tilePoint.Y >= height - 1)
            return false;

        if (Math.Abs(tilePoint.X - farmWarp.X) <= 3 && Math.Abs(tilePoint.Y - farmWarp.Y) <= 3)
            return false;

        try
        {
            // Static fences, trunks, buildings and canopy from map overhauls may exist only on these
            // map layers. Reject them as placement geometry, then relocate elsewhere if the zone fails.
            var buildings = location.Map?.GetLayer("Buildings");
            var front = location.Map?.GetLayer("Front");
            if (buildings?.Tiles[tilePoint.X, tilePoint.Y] is not null
                || front?.Tiles[tilePoint.X, tilePoint.Y] is not null)
            {
                return false;
            }

            Vector2 tile = new(tilePoint.X, tilePoint.Y);
            if (location.IsTileBlockedBy(tile)
                || location.Objects.ContainsKey(tile)
                || location.terrainFeatures.ContainsKey(tile))
            {
                return false;
            }

            Rectangle tileBounds = new(tilePoint.X * 64, tilePoint.Y * 64, 64, 64);
            foreach (var feature in location.largeTerrainFeatures)
            {
                if (feature.getBoundingBox().Intersects(tileBounds))
                    return false;
            }
        }
        catch
        {
            return false;
        }

        try
        {
            foreach (Warp warp in location.warps)
            {
                if (Math.Abs(warp.X - tilePoint.X) <= 2 && Math.Abs(warp.Y - tilePoint.Y) <= 2)
                    return false;
            }
        }
        catch
        {
            // Hidden warp metadata should not by itself make a visually clear sector unusable.
        }

        return true;
    }

    private static Point ClampInsideMap(Point point, int width, int height)
        => new(
            Math.Clamp(point.X, 2, Math.Max(2, width - 3)),
            Math.Clamp(point.Y, 2, Math.Max(2, height - 5))
        );

    private static int TileDistanceSquared(Point a, Point b)
    {
        int dx = a.X - b.X;
        int dy = a.Y - b.Y;
        return (dx * dx) + (dy * dy);
    }
}

using System.Runtime.CompilerServices;
using HarmonyLib;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Patches;

/// <summary>
/// .5.6.1.2 canonical Forest Arcane Gate placement: lower Wizard-side meadow.
/// The gate now belongs to the lower Wizard-side meadow instead of the blocked upper pocket. We anchor from
/// the live WizardHouse warp, search only a tiny local pocket, and keep normal 160px interaction.
/// No Forest collision/path tiles are ever edited.
/// </summary>
internal static class AirshipGateRelocationPatch
{
    private const float LegacyWideGateUseDistance = 320f;
    private const float CanonicalGateUseDistance = 160f;
    private const int LocalSearchRadius = 2;
    private static readonly Point WizardGateOffset = new(-4, 0);
    private static readonly Point[] WizardGateAlternates =
    {
        new(-5, 1),
        new(-4, 2),
        new(-6, 0),
    };

    private static bool LoggedPlacement;
    private static bool LoggedFallback;

    [ModuleInitializer]
    internal static void Initialize()
    {
        Harmony harmony = new("Ronvotri.Cardcha.AirshipGateCanonicalWizardMeadow");

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
        if (Math.Abs(useDistance - LegacyWideGateUseDistance) < 0.01f)
            useDistance = CanonicalGateUseDistance;
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
        Point farmWarp = ___CachedForestFarmWarpTile ?? ResolveWarpTile(forest, "Farm")
            ?? new Point(Math.Clamp(width / 2, 3, Math.Max(3, width - 4)), 2);
        ___CachedForestFarmWarpTile = farmWarp;

        Point? wizardWarp = ResolveWarpTile(forest, "WizardHouse") ?? ResolveWarpTile(forest, "Wizard");
        if (wizardWarp is Point wizard)
        {
            Point preferred = ClampInsideMap(wizard + WizardGateOffset, width, height);
            Point? safe = FindSafeInPocket(forest, preferred, farmWarp, width, height);
            if (safe is Point exact)
                return Use(exact, ref __result, ref ___CachedSkyDockTile, "Wizard-side meadow");

            foreach (Point offset in WizardGateAlternates)
            {
                Point alternate = ClampInsideMap(wizard + offset, width, height);
                safe = FindSafeInPocket(forest, alternate, farmWarp, width, height);
                if (safe is Point local)
                    return Use(local, ref __result, ref ___CachedSkyDockTile, "Wizard-side meadow fallback");
            }

            // Do not wander to unrelated Forest sectors. Keep the requested landmark area even on
            // hostile map overhauls; interaction stays short and collision remains untouched.
            ___CachedSkyDockTile = preferred;
            __result = preferred;
            if (!LoggedFallback)
            {
                LoggedFallback = true;
                ModEntry.StaticMonitor?.Log(
                    $"Arcane Gate Wizard meadow footprint was not fully clear; retaining canonical anchor ({preferred.X},{preferred.Y}) without map-wide relocation or wide interaction radius.",
                    LogLevel.Warn
                );
            }
            return false;
        }

        // Compatibility fallback only when the map exposes no Wizard warp at all.
        Point legacy = ClampInsideMap(new Point(farmWarp.X - 7, farmWarp.Y + 2), width, height);
        Point? legacySafe = FindSafeInPocket(forest, legacy, farmWarp, width, height);
        Point chosen = legacySafe ?? legacy;
        ___CachedSkyDockTile = chosen;
        __result = chosen;
        if (!LoggedFallback)
        {
            LoggedFallback = true;
            ModEntry.StaticMonitor?.Log(
                $"Arcane Gate couldn't resolve a WizardHouse warp; using compact compatibility anchor ({chosen.X},{chosen.Y}).",
                LogLevel.Warn
            );
        }
        return false;
    }

    private static bool Use(Point point, ref Point result, ref Point? cache, string reason)
    {
        cache = point;
        result = point;
        if (!LoggedPlacement)
        {
            LoggedPlacement = true;
            ModEntry.StaticMonitor?.Log(
                $"Arcane Gate canonical placement: {reason} at ({point.X},{point.Y}); interaction=160px; CollisionEdits=NONE.",
                LogLevel.Info
            );
        }
        return false;
    }

    private static Point? ResolveWarpTile(GameLocation location, string targetToken)
    {
        try
        {
            foreach (Warp warp in location.warps)
            {
                if (!string.IsNullOrWhiteSpace(warp.TargetName)
                    && warp.TargetName.Contains(targetToken, StringComparison.OrdinalIgnoreCase))
                {
                    return new Point(warp.X, warp.Y);
                }
            }
        }
        catch
        {
            // A map overhaul can hide/replace warp metadata. Caller owns fallback policy.
        }
        return null;
    }

    private static Point? FindSafeInPocket(
        GameLocation forest,
        Point center,
        Point farmWarp,
        int width,
        int height
    )
    {
        for (int ring = 0; ring <= LocalSearchRadius; ring++)
        {
            for (int y = center.Y - ring; y <= center.Y + ring; y++)
            {
                for (int x = center.X - ring; x <= center.X + ring; x++)
                {
                    if (Math.Max(Math.Abs(x - center.X), Math.Abs(y - center.Y)) != ring)
                        continue;
                    Point candidate = ClampInsideMap(new Point(x, y), width, height);
                    if (IsFootprintSafe(forest, candidate, farmWarp, width, height))
                        return candidate;
                }
            }
        }
        return null;
    }

    private static bool IsFootprintSafe(GameLocation location, Point anchor, Point farmWarp, int width, int height)
    {
        Point[] footprint =
        {
            new(anchor.X - 1, anchor.Y), anchor, new(anchor.X + 1, anchor.Y),
            new(anchor.X - 1, anchor.Y + 1), new(anchor.X, anchor.Y + 1), new(anchor.X + 1, anchor.Y + 1),
            new(anchor.X - 1, anchor.Y + 2), new(anchor.X, anchor.Y + 2), new(anchor.X + 1, anchor.Y + 2),
        };
        if (footprint.Any(p => !IsTileClear(location, p, farmWarp, width, height)))
            return false;

        // Action-driven portal: player must have a clean approach strip below it.
        Point[] approach =
        {
            new(anchor.X - 1, anchor.Y + 3),
            new(anchor.X, anchor.Y + 3),
            new(anchor.X + 1, anchor.Y + 3),
        };
        return approach.Any(p => IsTileClear(location, p, farmWarp, width, height));
    }

    private static bool IsTileClear(GameLocation location, Point p, Point farmWarp, int width, int height)
    {
        if (p.X < 1 || p.Y < 1 || p.X >= width - 1 || p.Y >= height - 1)
            return false;
        if (Math.Abs(p.X - farmWarp.X) <= 3 && Math.Abs(p.Y - farmWarp.Y) <= 3)
            return false;

        try
        {
            var buildings = location.Map?.GetLayer("Buildings");
            var front = location.Map?.GetLayer("Front");
            if (buildings?.Tiles[p.X, p.Y] is not null || front?.Tiles[p.X, p.Y] is not null)
                return false;

            Vector2 tile = new(p.X, p.Y);
            if (location.IsTileBlockedBy(tile)
                || location.Objects.ContainsKey(tile)
                || location.terrainFeatures.ContainsKey(tile))
                return false;

            Rectangle tileBounds = new(p.X * 64, p.Y * 64, 64, 64);
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
                if (Math.Abs(warp.X - p.X) <= 2 && Math.Abs(warp.Y - p.Y) <= 2)
                    return false;
            }
        }
        catch { }
        return true;
    }

    private static Point ClampInsideMap(Point point, int width, int height)
        => new(
            Math.Clamp(point.X, 2, Math.Max(2, width - 3)),
            Math.Clamp(point.Y, 2, Math.Max(2, height - 5))
        );
}

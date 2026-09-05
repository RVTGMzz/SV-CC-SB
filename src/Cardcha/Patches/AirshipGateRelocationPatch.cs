using System.Runtime.CompilerServices;
using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Patches;

/// <summary>
/// .5.11.2 reachable relocation pass for the Forest Arcane Gate.
///
/// The previous prefix-based resolver depended on private-field injection and could leave the
/// gate at its old visual position on heavily modded Forest maps. This pass deliberately keeps
/// Cardcha's original resolver authoritative, then shifts its resolved point by a fixed visual
/// delta matching the requested lower-left meadow. The same resolved point is used for drawing
/// and interaction, so the clickable area can never remain behind at the old gate.
///
/// CollisionEdits=NONE remains locked.
/// </summary>
internal static class AirshipGateRelocationPatch
{
    private const float LegacyWideGateUseDistance = 320f;
    private const float CanonicalGateUseDistance = 160f;

    // Move from the previous fenced placement toward the open meadow immediately right of the pink blossom tree.
    private const int GateShiftX = -16;
    private const int GateShiftY = 8;

    private static bool LoggedPlacement;

    [ModuleInitializer]
    internal static void Initialize()
    {
        Harmony harmony = new("Ronvotri.Cardcha.AirshipGateHardRelocate05613");

        var resolveGate = AccessTools.Method(typeof(AirshipFoundationService), "ResolveSkyDockTile");
        var resolvePostfix = AccessTools.Method(typeof(AirshipGateRelocationPatch), nameof(AfterResolveSkyDockTile));
        if (resolveGate is not null && resolvePostfix is not null)
            harmony.Patch(resolveGate, postfix: new HarmonyMethod(resolvePostfix));

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

    private static void AfterResolveSkyDockTile(ref Point __result)
    {
        GameLocation? forest = Game1.getLocationFromName(AirshipFoundationService.SkyDockLocationName);
        if (forest is null)
            return;

        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        int height = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;
        Point original = __result;
        Point desired = new(
            Math.Clamp(original.X + GateShiftX, 2, Math.Max(2, width - 3)),
            Math.Clamp(original.Y + GateShiftY, 2, Math.Max(2, height - 4))
        );

        Point seed = FindFarmSideSeed(forest, original);
        HashSet<Point> reachable = FloodWalkable(forest, seed);
        Point final = FindReachableGateAnchor(forest, desired, reachable) ?? original;
        __result = final;

        if (!LoggedPlacement)
        {
            LoggedPlacement = true;
            ModEntry.StaticMonitor?.Log(
                $"Arcane Gate reachable relocation: base=({original.X},{original.Y}) desired=({desired.X},{desired.Y}) final=({final.X},{final.Y}); interaction=160px; CollisionEdits=NONE.",
                LogLevel.Alert
            );
        }
    }

    private static Point FindFarmSideSeed(GameLocation forest, Point fallback)
    {
        try
        {
            foreach (Warp warp in forest.warps)
            {
                if (!string.IsNullOrWhiteSpace(warp.TargetName) && warp.TargetName.Contains("Farm", StringComparison.OrdinalIgnoreCase))
                {
                    for (int r = 0; r <= 5; r++)
                        for (int y = warp.Y - r; y <= warp.Y + r; y++)
                            for (int x = warp.X - r; x <= warp.X + r; x++)
                            {
                                Point p = new(x, y);
                                if (IsWalkable(forest, p))
                                    return p;
                            }
                }
            }
        }
        catch { }
        return IsWalkable(forest, fallback) ? fallback : new Point(Math.Max(2, fallback.X), Math.Max(2, fallback.Y));
    }

    private static HashSet<Point> FloodWalkable(GameLocation forest, Point seed)
    {
        HashSet<Point> seen = new();
        if (!IsWalkable(forest, seed))
            return seen;
        Queue<Point> q = new();
        q.Enqueue(seed); seen.Add(seed);
        Point[] dirs = { new(1,0), new(-1,0), new(0,1), new(0,-1) };
        while (q.Count > 0)
        {
            Point p = q.Dequeue();
            foreach (Point d in dirs)
            {
                Point n = new(p.X + d.X, p.Y + d.Y);
                if (seen.Contains(n) || !IsWalkable(forest, n))
                    continue;
                seen.Add(n); q.Enqueue(n);
            }
        }
        return seen;
    }

    private static Point? FindReachableGateAnchor(GameLocation forest, Point desired, HashSet<Point> reachable)
    {
        for (int r = 0; r <= 14; r++)
        {
            for (int y = desired.Y - r; y <= desired.Y + r; y++)
            for (int x = desired.X - r; x <= desired.X + r; x++)
            {
                if (Math.Abs(x - desired.X) != r && Math.Abs(y - desired.Y) != r)
                    continue;
                Point a = new(x, y);
                if (!GateFootprintClear(forest, a))
                    continue;
                Point[] action = { new(a.X, a.Y + 2), new(a.X - 1, a.Y + 2), new(a.X + 1, a.Y + 2), new(a.X, a.Y + 3) };
                if (action.Any(reachable.Contains))
                    return a;
            }
        }
        return null;
    }

    private static bool GateFootprintClear(GameLocation forest, Point a)
    {
        for (int y = a.Y; y <= a.Y + 2; y++)
            for (int x = a.X - 1; x <= a.X + 1; x++)
                if (!IsWalkable(forest, new Point(x, y)))
                    return false;
        return true;
    }

    private static bool IsWalkable(GameLocation forest, Point p)
    {
        int w = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        int h = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;
        if (p.X < 1 || p.Y < 1 || p.X >= w - 1 || p.Y >= h - 1)
            return false;
        try
        {
            Vector2 v = new(p.X, p.Y);
            if (forest.Map?.GetLayer("Buildings")?.Tiles[p.X, p.Y] is not null || forest.Map?.GetLayer("Front")?.Tiles[p.X, p.Y] is not null)
                return false;
            if (forest.IsTileBlockedBy(v) || forest.Objects.ContainsKey(v) || forest.terrainFeatures.ContainsKey(v))
                return false;
            Rectangle box = new(p.X * 64, p.Y * 64, 64, 64);
            foreach (var f in forest.largeTerrainFeatures)
                if (f.getBoundingBox().Intersects(box))
                    return false;
            return true;
        }
        catch { return false; }
    }

}}

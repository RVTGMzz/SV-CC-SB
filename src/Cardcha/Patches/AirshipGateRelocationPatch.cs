using System.Runtime.CompilerServices;
using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Patches;

/// <summary>
/// .5.6.1.3 hard relocation pass for the Forest Arcane Gate.
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

    // User-accepted screenshot target: about 11 tiles left and 4 tiles down from the old portal.
    private const int GateShiftX = -11;
    private const int GateShiftY = 4;

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
        int width = forest?.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        int height = forest?.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;

        Point original = __result;
        Point shifted = new(
            Math.Clamp(original.X + GateShiftX, 2, Math.Max(2, width - 3)),
            Math.Clamp(original.Y + GateShiftY, 2, Math.Max(2, height - 5))
        );

        __result = shifted;

        if (!LoggedPlacement)
        {
            LoggedPlacement = true;
            ModEntry.StaticMonitor?.Log(
                $"Arcane Gate HARD relocation active: ({original.X},{original.Y}) -> ({shifted.X},{shifted.Y}); delta=({GateShiftX},{GateShiftY}); interaction=160px; CollisionEdits=NONE.",
                LogLevel.Alert
            );
        }
    }
}

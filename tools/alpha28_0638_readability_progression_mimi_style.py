from pathlib import Path
import json
import re
import hashlib
from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
ASSETS = SRC / "assets"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.6.1"
LOCKED_AIRSHIP_SHA = "1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132"


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def replace_once(text, old, new, label):
    require(old in text, f"Missing patch anchor: {label}")
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# 1) Remove the persistent ChaCha Energy rectangle without changing energy logic.
#    Mouse activation is also removed so there is no invisible clickable hotspot.
# -----------------------------------------------------------------------------
boss_path = SRC / "Services" / "ChaChaBossFormService.cs"
boss = boss_path.read_text(encoding="utf-8")
mouse_pattern = re.compile(
    r'''        if \(e\.Button == SButton\.MouseLeft\)\n        \{.*?\n        \}\n\n        SButton confirm''',
    re.S,
)
boss, n = mouse_pattern.subn(
    '''        // .5.6.1: the persistent ChaCha Energy panel was removed from gameplay HUD.\n        // Do not leave its former rectangle as an invisible mouse activation hotspot.\n        if (e.Button == SButton.MouseLeft)\n            return;\n\n        SButton confirm''',
    boss,
    count=1,
)
require(n == 1, "Couldn't remove ChaCha Energy mouse hotspot")

hud_pattern = re.compile(
    r'''    public void OnRenderedHud\(object\? sender, RenderedHudEventArgs e\)\n    \{.*?\n    \}\n\n    public void OnRenderedWorld''',
    re.S,
)
boss, n = hud_pattern.subn(
    '''    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)\n    {\n        // .5.6.1: user-approved HUD cleanup. Boss Energy continues charging internally and\n        // READY still announces through sound/ChaCha emote; activation remains controller chord\n        // or Left Shift+A. The old always-on rectangular meter is intentionally not drawn.\n    }\n\n    public void OnRenderedWorld''',
    boss,
    count=1,
)
require(n == 1, "Couldn't replace ChaCha Energy HUD renderer")
boss_path.write_text(boss, encoding="utf-8")


# -----------------------------------------------------------------------------
# 2) Tighten early-game Wizard-house Cardcha bypass to the actual appointment day.
#    Picking up Scrap/cardboard alone can never open the Wizard door or start MiMi meetup.
# -----------------------------------------------------------------------------
story_path = SRC / "Services" / "CardchaStoryService.cs"
story = story_path.read_text(encoding="utf-8")
button_anchor = '''        {\n            return;\n        }\n\n        GameLocation? location = Game1.currentLocation;'''
# Use the unique guard that contains ShouldStartMimiMeetup.
button_guard = '''            || Game1.eventUp\n            || !this.Progression.ShouldStartMimiMeetup())\n        {\n            return;\n        }\n\n        GameLocation? location = Game1.currentLocation;'''
button_repl = '''            || Game1.eventUp\n            || !this.Progression.ShouldStartMimiMeetup())\n        {\n            return;\n        }\n\n        // Cardcha may bypass the vanilla Wizard lock only on MiMi's explicitly offered\n        // appointment day. Merely finding/picking a Scrap never satisfies this gate.\n        if (this.Save.Data.MimiMeetupOfferedDay != Game1.Date.TotalDays)\n            return;\n\n        GameLocation? location = Game1.currentLocation;'''
story = replace_once(story, button_guard, button_repl, "Wizard door appointment-day guard")

meetup_anchor = '''        if (!this.Progression.ShouldStartMimiMeetup())\n            return;\n\n        if (Game1.currentLocation?.NameOrUniqueName.Equals('''
meetup_repl = '''        if (!this.Progression.ShouldStartMimiMeetup())\n            return;\n\n        // A stale pending quest must not turn WizardHouse into an evergreen Cardcha bypass.\n        // The missed-appointment fallback remains the separate forced doorstep handoff.\n        if (this.Save.Data.MimiMeetupOfferedDay != Game1.Date.TotalDays)\n            return;\n\n        if (Game1.currentLocation?.NameOrUniqueName.Equals('''
story = replace_once(story, meetup_anchor, meetup_repl, "Wizard meetup appointment-day guard")
story_path.write_text(story, encoding="utf-8")


# -----------------------------------------------------------------------------
# 3) Canonical Forest Gate placement near Wizard Tower instead of map-wide roaming.
#    Resolve from WizardHouse warp so SVE/forest overhauls can move the whole landmark together.
# -----------------------------------------------------------------------------
gate_path = SRC / "Patches" / "AirshipGateRelocationPatch.cs"
gate_source = r'''using System.Runtime.CompilerServices;
using HarmonyLib;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Patches;

/// <summary>
/// .5.6.1 canonical Forest Arcane Gate placement.
/// The gate now belongs to the Wizard-side meadow instead of roaming the Forest. We anchor from
/// the live WizardHouse warp, search only a tiny local pocket, and keep normal 160px interaction.
/// No Forest collision/path tiles are ever edited.
/// </summary>
internal static class AirshipGateRelocationPatch
{
    private const float LegacyWideGateUseDistance = 320f;
    private const float CanonicalGateUseDistance = 160f;
    private const int LocalSearchRadius = 2;
    private static readonly Point WizardGateOffset = new(8, -4);
    private static readonly Point[] WizardGateAlternates =
    {
        new(10, -3),
        new(7, -2),
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
'''
gate_path.write_text(gate_source, encoding="utf-8")


# -----------------------------------------------------------------------------
# 4) Airship readability: move gate art upward from the interaction tile, remove lines/sigils
#    drawn through the player's central walking lanes, clarify the route board.
# -----------------------------------------------------------------------------
airship_path = SRC / "Services" / "AirshipFoundationService.cs"
airship = airship_path.read_text(encoding="utf-8")
airship = replace_once(
    airship,
    'new Vector2(tile.X * 64f + 32f, tile.Y * 64f + 30f)',
    'new Vector2(tile.X * 64f + 32f, tile.Y * 64f - 34f)',
    "raise Forest Gate visual above approach tile",
)
airship = replace_once(
    airship,
    'Point landing = FindClearTileNear(forest, new Point(dock.X + 1, dock.Y + 1));',
    'Point landing = FindClearTileNear(forest, new Point(dock.X, dock.Y + 2));',
    "return in front of Forest Gate",
)

old_dock_lanes = '''        DrawManaLane(batch, arrivalCenter, routeCenter, violet * 0.40f, phase);\n        DrawManaLane(batch, arrivalCenter, bayCenter, cyan * 0.46f, -phase * 0.82f);\n        DrawArcaneSigil(batch, arrivalCenter, 72f, violet, phase);\n        DrawArcaneSigil(batch, arrivalCenter, 48f, cyan, -phase * 0.67f);\n        DrawDiamondRune(batch, arrivalCenter, 18f, gold * 0.78f);'''
new_dock_lanes = '''        // .5.6.1 readability: no post-world energy lines or large sigils through the farmer.\n        // Keep magical identification attached to the actual destinations instead.\n        DrawArcaneSigil(batch, routeCenter, 31f, violet * 0.52f, phase * 0.55f);\n        DrawDiamondRune(batch, routeCenter, 10f, cyan * 0.68f);\n        DrawArcaneSigil(batch, bayCenter, 29f, cyan * 0.48f, -phase * 0.48f);'''
airship = replace_once(airship, old_dock_lanes, new_dock_lanes, "remove Sky Dock player-crossing mana lanes")

airship = replace_once(
    airship,
    '        DrawManaLane(batch, exitCenter, helmCenter, cyan * 0.38f, phase);',
    '        // .5.6.1: removed post-world mana line through the central player lane.',
    "remove Bridge player-crossing mana lane",
)
airship = airship.replace('new Color(78, 45, 83) * 0.34f', 'new Color(78, 45, 83) * 0.18f')
airship = airship.replace('gold * 0.38f', 'gold * 0.26f', 2)
airship = airship.replace('gold * 0.30f', 'gold * 0.19f', 1)

board_anchor = '''        DrawRect(batch, new Rectangle((int)board.X + 124, (int)board.Y + 74, 10, 38), brass);\n        DrawBrassLamp(batch, new Vector2(board.X - 26f, board.Y + 78f), phase, gold, violet);'''
board_repl = '''        DrawRect(batch, new Rectangle((int)board.X + 124, (int)board.Y + 74, 10, 38), brass);\n        string routeBoardLabel = ModEntry.T("airship.arcane.route_board.label");\n        Vector2 routeBoardSize = Game1.smallFont.MeasureString(routeBoardLabel);\n        float routeBoardScale = Math.Min(0.56f, 116f / Math.Max(1f, routeBoardSize.X));\n        batch.DrawString(Game1.smallFont, routeBoardLabel,\n            new Vector2(board.X + 78f - routeBoardSize.X * routeBoardScale / 2f, board.Y + 53f),\n            new Color(236, 211, 151) * 0.84f, 0f, Vector2.Zero, routeBoardScale, SpriteEffects.None, 1f);\n        DrawBrassLamp(batch, new Vector2(board.X - 26f, board.Y + 78f), phase, gold, violet);'''
airship = replace_once(airship, board_anchor, board_repl, "label route board")
airship_path.write_text(airship, encoding="utf-8")


# -----------------------------------------------------------------------------
# 5) Remove post-world foreground bars/ropes that visually slice through the farmer. Fill the
#    boarding room only at safe side-wall pockets with outlined crates / service lamps.
# -----------------------------------------------------------------------------
depth_path = SRC / "Patches" / "AirshipVisualDepthPatch.cs"
depth = depth_path.read_text(encoding="utf-8")

dock_method = re.compile(
    r'''    private static void AfterSkyDockInterior\(SpriteBatch batch, GameLocation interior\)\n    \{.*?\n    \}\n\n    private static void AfterBridge''',
    re.S,
)
new_dock_method = '''    private static void AfterSkyDockInterior(SpriteBatch batch, GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        float phase = (float)(Environment.TickCount64 / 980.0);\n        Color outline = new Color(45, 29, 31) * 0.96f;\n        Color wood = new Color(119, 73, 47) * 0.92f;\n        Color brass = new Color(195, 132, 62) * 0.90f;\n        Color cyan = new Color(88, 211, 230) * 0.34f;\n        Color violet = new Color(163, 98, 220) * 0.30f;\n\n        // Side-wall service props fill the formerly empty room but deliberately stay out of\n        // the center boarding lane, so a post-world overlay never slices across the farmer.\n        Vector2 left = Game1.GlobalToLocal(Game1.viewport, new Vector2(3.2f * 64f, (height - 4.0f) * 64f));\n        Vector2 leftBack = Game1.GlobalToLocal(Game1.viewport, new Vector2(4.4f * 64f, (height - 6.1f) * 64f));\n        Vector2 right = Game1.GlobalToLocal(Game1.viewport, new Vector2((width - 3.4f) * 64f, (height - 4.0f) * 64f));\n        DrawDockCrate(batch, left, outline, wood, brass);\n        DrawDockCrate(batch, leftBack, outline, wood * 0.88f, brass * 0.82f);\n        DrawDockCrate(batch, right, outline, wood, brass);\n\n        Vector2 lampLeft = Game1.GlobalToLocal(Game1.viewport, new Vector2(2.4f * 64f, (height - 7.0f) * 64f));\n        Vector2 lampRight = Game1.GlobalToLocal(Game1.viewport, new Vector2((width - 2.4f) * 64f, (height - 7.0f) * 64f));\n        DrawServiceLamp(batch, lampLeft, phase, outline, brass, violet);\n        DrawServiceLamp(batch, lampRight, -phase, outline, brass, cyan);\n    }\n\n    private static void AfterBridge'''
depth, n = dock_method.subn(new_dock_method, depth, count=1)
require(n == 1, "Couldn't replace Sky Dock foreground depth pass")

bridge_method = re.compile(
    r'''    private static void AfterBridge\(SpriteBatch batch, GameLocation deck\)\n    \{.*?\n    \}\n\n    private static Texture2D\? GetAirshipTexture''',
    re.S,
)
new_bridge_method = '''    private static void AfterBridge(SpriteBatch batch, GameLocation deck)\n    {\n        // .5.6.1: intentionally no post-world foreground ribs, rails or hanging cables.\n        // Those lines looked like transparent UI drawn over the farmer. Structural depth now\n        // comes from the map/window/station masses while the playable center remains clean.\n    }\n\n    private static void DrawDockCrate(SpriteBatch batch, Vector2 p, Color outline, Color wood, Color brass)\n    {\n        Rectangle outer = new((int)p.X - 34, (int)p.Y - 34, 68, 52);\n        DrawRect(batch, outer, outline);\n        DrawRect(batch, new Rectangle(outer.X + 4, outer.Y + 4, outer.Width - 8, outer.Height - 8), wood);\n        DrawRect(batch, new Rectangle(outer.X + 9, outer.Y + 9, outer.Width - 18, 5), brass * 0.72f);\n        DrawLine(batch, new Vector2(outer.X + 8, outer.Bottom - 8), new Vector2(outer.Right - 8, outer.Y + 8), 3f, outline * 0.68f);\n        DrawLine(batch, new Vector2(outer.Right - 8, outer.Bottom - 8), new Vector2(outer.X + 8, outer.Y + 8), 3f, outline * 0.68f);\n    }\n\n    private static void DrawServiceLamp(SpriteBatch batch, Vector2 p, float phase, Color outline, Color brass, Color glow)\n    {\n        DrawRect(batch, new Rectangle((int)p.X - 5, (int)p.Y - 52, 10, 52), outline);\n        DrawRect(batch, new Rectangle((int)p.X - 2, (int)p.Y - 49, 4, 49), brass);\n        DrawRect(batch, new Rectangle((int)p.X - 13, (int)p.Y - 68, 26, 18), outline);\n        float pulse = 0.58f + 0.14f * MathF.Sin(phase * 2.2f);\n        DrawRect(batch, new Rectangle((int)p.X - 8, (int)p.Y - 64, 16, 10), glow * pulse);\n    }\n\n    private static Texture2D? GetAirshipTexture'''
depth, n = bridge_method.subn(new_bridge_method, depth, count=1)
require(n == 1, "Couldn't disable Bridge post-world foreground bars")
depth_path.write_text(depth, encoding="utf-8")


# -----------------------------------------------------------------------------
# 6) Stardewization pass for MiMi portrait family. Preserve dimensions/expressions and NEVER touch
#    user-locked mimi_walk.png. The pass reduces smooth anime gradients and adds a readable dark
#    silhouette stroke while keeping lavender hair + red bow identity.
# -----------------------------------------------------------------------------
def stardewize_portrait(path: Path):
    im = Image.open(path).convert("RGBA")
    original_size = im.size
    alpha = im.getchannel("A")

    # Reduce smooth high-resolution gradients using nearest-neighbour pixel clusters on portrait-size
    # assets. Tiny mugshots stay at native detail so they don't collapse.
    working = im
    if min(im.size) >= 64:
        small = (max(1, im.width // 2), max(1, im.height // 2))
        working = im.resize(small, Image.Resampling.NEAREST).resize(im.size, Image.Resampling.NEAREST)

    # Palette discipline closer to Stardew portraits. Quantize RGB while restoring original alpha.
    rgb = Image.new("RGB", working.size, (0, 0, 0))
    rgb.paste(working.convert("RGB"), mask=working.getchannel("A"))
    q = rgb.quantize(colors=56, method=Image.Quantize.FASTOCTREE).convert("RGB")
    body = q.convert("RGBA")
    body.putalpha(alpha)

    # One-pixel dark plum/brown outline around non-transparent portrait silhouettes.
    dilated = alpha.filter(ImageFilter.MaxFilter(3))
    ring = ImageChops.subtract(dilated, alpha)
    outline = Image.new("RGBA", im.size, (51, 35, 49, 0))
    outline.putalpha(ring.point(lambda a: min(230, int(a * 0.92))))
    out = Image.alpha_composite(outline, body)
    require(out.size == original_size, f"Portrait size changed: {path.name}")
    out.save(path, format="PNG", optimize=False)


portrait_names = [
    "mimi_portraits.png",
    "mimi_portraits_runtime64.png",
    "mimi_npc_portraits.png",
    "mimi_profile.png",
    "mimi_social_mugshot.png",
]
for name in portrait_names:
    path = ASSETS / name
    require(path.is_file(), f"Missing MiMi portrait asset: {name}")
    stardewize_portrait(path)

# Upgrade hardware gets the same strong silhouette principle instead of soft concept-overlay edges.
atlas_path = ASSETS / "airship_upgrade_visuals.png"
require(atlas_path.is_file(), "Missing .5.6 airship upgrade atlas")
atlas = Image.open(atlas_path).convert("RGBA")
a = atlas.getchannel("A")
ring2 = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(5)), a)
outline2 = Image.new("RGBA", atlas.size, (42, 29, 34, 0))
outline2.putalpha(ring2.point(lambda value: min(235, int(value * 0.95))))
atlas = Image.alpha_composite(outline2, atlas)
atlas.save(atlas_path, format="PNG", optimize=False)


# -----------------------------------------------------------------------------
# 7) Clarify the informational route board in both languages.
# -----------------------------------------------------------------------------
for lang, label, text in [
    ("default.json", "ROUTE STATUS", "Route Status Board: {{cards}} Cardcha cards registered. This board only shows route readiness; use the helm inside the Airship Bridge to depart."),
    ("vi.json", "BẢNG TUYẾN BAY", "Bảng Trạng Thái Tuyến Bay: đã ghi nhận {{cards}} lá Cardcha. Bảng này chỉ để xem tình trạng tuyến; hãy dùng bánh lái trong Buồng Lái Tàu Bay để khởi hành."),
]:
    path = SRC / "i18n" / lang
    data = json.loads(path.read_text(encoding="utf-8"))
    data["airship.arcane.route_board.label"] = label
    data["airship.arcane.route_console"] = text
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# -----------------------------------------------------------------------------
# 8) Version metadata and milestone note.
# -----------------------------------------------------------------------------
manifest_path = SRC / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["Version"] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

csproj_path = SRC / "Cardcha.csproj"
csproj = csproj_path.read_text(encoding="utf-8")
csproj = re.sub(r"<Version>[^<]+</Version>", f"<Version>{VERSION}</Version>", csproj, count=1)
csproj_path.write_text(csproj, encoding="utf-8")

(SRC / "Directory.Build.targets").write_text(f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .5.6.1 Airship readability + progression + MiMi Stardew portrait pass. -->\n  <Target Name="CardchaAlpha2804144561Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n''', encoding="utf-8")

mod_path = SRC / "ModEntry.cs"
mod = mod_path.read_text(encoding="utf-8")
mod = re.sub(
    r'Cardcha! v?0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.\d+(?:\.\d+)?[^\"]*TEST with',
    f'Cardcha! {VERSION} READABILITY + PROGRESSION + MIMI STYLE TEST with',
    mod,
    count=1,
)
mod_path.write_text(mod, encoding="utf-8")

require(hashlib.sha256((ASSETS / "airship_visual.png").read_bytes()).hexdigest() == LOCKED_AIRSHIP_SHA,
        "Locked airship_visual.png changed")

print(f"Prepared {VERSION}")
print("Gate=Wizard-side canonical pocket | Interaction=160px | CollisionEdits=NONE")
print("ChaChaEnergyHUD=HIDDEN | Energy mechanics preserved")
for name in portrait_names:
    with Image.open(ASSETS / name) as im:
        print(name, im.size)

using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Objects;

namespace Cardcha.Services;

/// <summary>
/// Alpha28 .5.11 MiMi Attic living-lore + real 17:30 secret-TV routine support.
/// The TMX provides the vanilla townInterior shell; this service adds real vanilla
/// Furniture instances for the five locked zones with no room-sized visual overlay. Inspect points now reveal
/// layered character/environmental lore by friendship, time, and repeat inspection; the 17:30 / 6-heart TV hook is now a real home routine.
/// </summary>
internal sealed class MimiAtticVisualService
{
    public const string AtticMapAssetName = "Maps/Cardcha_MiMiAttic";

    private const int SecretTvHeartRequirement = 6;
    private const int SecretTvTime = 1730;
    private const int SecretTvEndTime = 2200;
    private const string DecorMarkerKey = "Ronvotri.Cardcha/MiMiAtticDecor";
    private const string StairSpritePath = "assets/mimi_attic_stairs.png";
    private const string DecorVersion = "alpha.28.0.4.14.4.5.9";

    private readonly IModHelper Helper;
    private readonly SaveService Save;
    private bool TestAccessActive;
    private GameLocation? DecorAppliedLocation;
    private readonly Dictionary<string, int> InspectCountsToday = new(StringComparer.OrdinalIgnoreCase);
    private int InspectMemoryDay = -1;

    public MimiAtticVisualService(IModHelper helper, SaveService save)
    {
        this.Helper = helper;
        this.Save = save;
    }

    /// <summary>Enable or disable runtime-only attic testing without touching save progression.</summary>
    public void SetTestAccess(bool enabled)
    {
        this.TestAccessActive = enabled;
    }

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (!e.NameWithoutLocale.IsEquivalentTo(AtticMapAssetName))
            return;

        e.LoadFromModFile<xTile.Map>(
            "assets/mimi_attic.tmx",
            AssetLoadPriority.Exclusive
        );
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        GameLocation? location = Game1.currentLocation;
        if (location is null)
            return;

        if (location.NameOrUniqueName.Equals(MimiHomeService.AtticLocationName, StringComparison.OrdinalIgnoreCase))
        {
            if (this.Save.Data.MimiMeetupCompleted || this.TestAccessActive)
                EnsureVanillaFurniture(location);
            return;
        }

        if (!this.Save.Data.MimiMeetupCompleted)
            return;

        if (location.NameOrUniqueName.Equals("WizardHouse", StringComparison.OrdinalIgnoreCase))
        {
            Point stair = MimiHomeService.ResolvePreferredWizardStairTile(location);
            this.DrawStairMarker(e.SpriteBatch, stair);
        }
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady
            || (!this.Save.Data.MimiMeetupCompleted && !this.TestAccessActive)
            || !e.Button.IsActionButton()
            || Game1.activeClickableMenu is not null
            || Game1.dialogueUp
            || Game1.eventUp
            || Game1.currentLocation is null
            || !Game1.currentLocation.NameOrUniqueName.Equals(MimiHomeService.AtticLocationName, StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        AtticLayout layout = GetLayout(Game1.currentLocation);
        Point actionTile = GetActionTile();

        string? target = null;
        if (Touches(actionTile, layout.DeskLeft) || Touches(actionTile, layout.DeskRight) || Touches(actionTile, layout.Notes))
            target = "desk";
        else if (Touches(actionTile, layout.Television) || Touches(actionTile, layout.TvChair))
            target = "tv";
        else if (Touches(actionTile, layout.ChaChaCushion) || Touches(actionTile, layout.Prototype))
            target = "chacha";
        else if (Touches(actionTile, layout.Bed) || Touches(actionTile, layout.Bedside) || Touches(actionTile, layout.Dresser))
            target = "personal";

        if (target is null)
            return;

        string key = this.ResolveInspectKey(target);
        this.Helper.Input.Suppress(e.Button);
        Game1.drawObjectDialogue(this.Helper.Translation.Get(key).ToString());
    }

    private string ResolveInspectKey(string target)
    {
        this.ResetInspectMemoryIfNeeded();

        int hearts = GetMimiHeartLevel();
        int seen = this.InspectCountsToday.TryGetValue(target, out int count) ? count : 0;
        this.InspectCountsToday[target] = seen + 1;

        return target switch
        {
            "desk" when hearts >= 8 && seen >= 1 => "mimi.attic.inspect.desk.deep",
            "desk" when hearts >= 4 && seen >= 1 => "mimi.attic.inspect.desk.personal",
            "desk" when seen == 0 => "mimi.attic.inspect.desk.first",
            "desk" => "mimi.attic.inspect.desk.repeat",

            "tv" when this.IsSecretTvRoutineEligible() => "mimi.attic.inspect.tv.routine",
            "tv" when hearts >= SecretTvHeartRequirement && Game1.timeOfDay >= SecretTvEndTime => "mimi.attic.inspect.tv.after",
            "tv" when hearts >= SecretTvHeartRequirement && seen >= 1 => "mimi.attic.inspect.tv.secret",
            "tv" when seen == 0 => "mimi.attic.inspect.tv.first",
            "tv" => "mimi.attic.inspect.tv.repeat",

            "chacha" when hearts >= 8 && seen >= 1 => "mimi.attic.inspect.chacha.prototype",
            "chacha" when this.Save.Data.ChaChaLoaned => "mimi.attic.inspect.chacha.away",
            "chacha" when seen == 0 => "mimi.attic.inspect.chacha.first",
            "chacha" => "mimi.attic.inspect.chacha.repeat",

            "personal" when Game1.timeOfDay >= 2200 => "mimi.attic.inspect.personal.late",
            "personal" when seen == 0 => "mimi.attic.inspect.personal.first",
            "personal" => "mimi.attic.inspect.personal.repeat",

            _ => "mimi.attic.inspect.desk.repeat",
        };
    }

    private void ResetInspectMemoryIfNeeded()
    {
        int day = (int)Game1.stats.DaysPlayed;
        if (this.InspectMemoryDay == day)
            return;

        this.InspectMemoryDay = day;
        this.InspectCountsToday.Clear();
    }

    private static int GetMimiHeartLevel()
    {
        if (!Game1.player.friendshipData.TryGetValue(MimiMysteryTownService.NpcId, out Friendship? friendship) || friendship is null)
            return 0;

        return Math.Clamp(friendship.Points / 250, 0, 10);
    }

    /// <summary>
    /// Shared eligibility rule for the real .5.11 private-TV routine window.
    /// MimiHomeService owns physical placement; this service mirrors the gate for inspect text.
    /// </summary>
    public bool IsSecretTvRoutineEligible()
    {
        if (!Context.IsWorldReady
            || Game1.timeOfDay < SecretTvTime
            || Game1.timeOfDay >= SecretTvEndTime)
        {
            return false;
        }

        if (!Game1.player.friendshipData.TryGetValue(MimiMysteryTownService.NpcId, out Friendship? friendship) || friendship is null)
            return false;

        return friendship.Points >= SecretTvHeartRequirement * 250;
    }

    /// <summary>
    /// Populate the room with actual Stardew furniture rather than a room-sized custom PNG.
    /// This keeps vanilla sprite proportions, shadows, draw ordering, and furniture collision.
    /// </summary>
    private void EnsureVanillaFurniture(GameLocation attic)
    {
        if (ReferenceEquals(this.DecorAppliedLocation, attic))
            return;

        this.DecorAppliedLocation = attic;

        // A decor-version change must replace our old runtime furniture instead of stacking a
        // second copy on the same tiles. Stacked furniture was the source of the visible chair
        // flicker in the 0.7.4 acceptance screenshot.
        foreach (Furniture old in attic.furniture
                     .Where(f => f.modData.ContainsKey(DecorMarkerKey))
                     .ToList())
        {
            attic.furniture.Remove(old);
        }

        // Rugs first so Stardew naturally draws the furniture on top of them.
        TryAddFurniture(attic, "(F)1456", 16, 9, pixelOffsetX: -40);  // Final left nudge: rug visual center under the prototype table.
        TryAddFurniture(attic, "(F)1623", 3, 9);   // Green Cottage Rug aligned with the couch.
        TryAddFurniture(attic, "(F)1461", 14, 4);  // Large dark rug under the bed.

        // Research desk — deliberately domestic, not a full workshop.
        TryAddFurniture(attic, "(F)1289", 2, 4);                 // Dark Bookcase.
        TryAddFurniture(attic, "(F)1120", 4, 4, heldId: "(F)1362"); // Oak Table against the wall + Small Plant.
        TryAddFurniture(attic, "(F)1443", 9, 4);                 // Country Lamp tucked beside the raised window.

        // Personal / bed corner.
        TryAddFurniture(attic, "(F)2058", 15, 4);                // Starry Double Bed.
        TryAddFurniture(attic, "(F)704", 19, 4);                 // Oak Dresser.
        TryAddFurniture(attic, "(F)1399", 14, 5, heldId: "(F)1369"); // Modern End Table + lantern.

        // TV secret nook — cozy, clearly separate from the research side.
        TryAddFurniture(attic, "(F)1466", 4, 7, pixelOffsetX: -32); // Another 8px left after in-game acceptance screenshot.
        TryAddFurniture(attic, "(F)432", 3, 11, rotation: 2);    // Couch shifted right to visually center beneath the TV.

        // ChaCha / future-upgrade corner — a small tinkering area, not a machine shop.
        TryAddFurniture(attic, "(F)1132", 16, 9, heldId: "(F)1368"); // Modern Table + crystal prototype.
        TryAddFurniture(attic, "(F)1390", 19, 9);                // House Plant.

        // Wall details make the shell read like a real Stardew bedroom rather than an empty shed.
        TryAddFurniture(attic, "(F)1614", 10, 1);                // Basic Window raised to mid-wall height.
        TryAddFurniture(attic, "(F)1541", 6, 1);                 // A Night On Eco-Hill, hung higher on the wall.

        attic.modData[DecorMarkerKey] = DecorVersion;
    }

    private static void TryAddFurniture(
        GameLocation attic,
        string itemId,
        int x,
        int y,
        int rotation = 0,
        string? heldId = null,
        int pixelOffsetX = 0)
    {
        try
        {
            Furniture item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);
            if (pixelOffsetX != 0)
            {
                Rectangle box = item.boundingBox.Value;
                box.X += pixelOffsetX;
                item.boundingBox.Value = box;
                item.updateDrawPosition();
            }
            item.modData[DecorMarkerKey] = DecorVersion;

            if (heldId is not null)
            {
                Furniture held = ItemRegistry.Create<Furniture>(heldId);
                item.SetHeldObject(held);
            }

            attic.furniture.Add(item);
        }
        catch
        {
            // A missing/changed vanilla furniture entry should never make the whole attic unloadable.
        }
    }

    private static void PrepareWizardStairArea(GameLocation location, Point tile)
    {
        // The old marker sat beside decorative plant/wall tiles and could visually/collision-wise
        // pinch the player into the wall. Reserve a clean 2x3 opening for the real stair graphic.
        foreach (string layerName in new[] { "Buildings", "Front" })
        {
            var layer = location.Map?.GetLayer(layerName);
            if (layer is null)
                continue;

            int x = tile.X;
            for (int y = tile.Y - 3; y <= tile.Y; y++)
            {
                if (x >= 0 && y >= 0 && x < layer.LayerWidth && y < layer.LayerHeight)
                    layer.Tiles[x, y] = null;
            }
        }
    }

    private void DrawStairMarker(SpriteBatch batch, Point tile)
    {
        try
        {
            Texture2D staircase = this.Helper.ModContent.Load<Texture2D>(StairSpritePath);
            Vector2 world = new(tile.X * 64f, (tile.Y - 4) * 64f);
            Vector2 screen = Game1.GlobalToLocal(Game1.viewport, world);
            batch.Draw(staircase, screen, null, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, 0.995f);
        }
        catch
        {
            // The actual warp still works if the visual asset can't be loaded.
        }
    }

    private static AtticLayout GetLayout(GameLocation location)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 22;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        int maxX = Math.Max(1, width - 2);
        int maxY = Math.Max(1, height - 2);

        Point P(int x, int y) => new(Math.Clamp(x, 1, maxX), Math.Clamp(y, 1, maxY));

        return new AtticLayout(
            Landing: P(width / 2, height - 3),

            // Research desk / notes on the upper-left.
            Notes: P(3, 4),
            DeskLeft: P(4, 4),
            DeskRight: P(6, 4),

            // TV secret nook on the lower-left.
            Television: P(4, 7),
            TvChair: P(3, 10),

            // ChaCha / future upgrade corner on the lower-right.
            ChaChaCushion: P(17, 10),
            Prototype: P(16, 9),

            // Personal corner. These are environmental-storytelling inspect anchors only.
            Bed: P(15, 4),
            Bedside: P(14, 5),
            Dresser: P(19, 4)
        );
    }

    private static Point GetActionTile()
    {
        Point p = new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));
        return Game1.player.FacingDirection switch
        {
            0 => new Point(p.X, p.Y - 1),
            1 => new Point(p.X + 1, p.Y),
            2 => new Point(p.X, p.Y + 1),
            3 => new Point(p.X - 1, p.Y),
            _ => p
        };
    }

    private static bool Touches(Point actionTile, Point propTile)
        => Math.Abs(actionTile.X - propTile.X) <= 1 && Math.Abs(actionTile.Y - propTile.Y) <= 1;

    private static Point FindClearTileNear(GameLocation location, bool preferUpperHalf)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 12;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 10;
        int centerX = Math.Clamp(width / 2, 2, Math.Max(2, width - 3));
        int centerY = preferUpperHalf
            ? Math.Clamp(height / 3, 2, Math.Max(2, height - 3))
            : Math.Clamp(height / 2, 2, Math.Max(2, height - 3));

        for (int radius = 0; radius < Math.Max(width, height); radius++)
        {
            for (int y = Math.Max(1, centerY - radius); y <= Math.Min(height - 2, centerY + radius); y++)
            {
                for (int x = Math.Max(1, centerX - radius); x <= Math.Min(width - 2, centerX + radius); x++)
                {
                    if (Math.Abs(x - centerX) != radius && Math.Abs(y - centerY) != radius)
                        continue;

                    Point p = new(x, y);
                    try
                    {
                        Vector2 v = new(p.X, p.Y);
                        if (!location.IsTileBlockedBy(v) && !location.Objects.ContainsKey(v))
                            return p;
                    }
                    catch
                    {
                        return p;
                    }
                }
            }
        }

        return new Point(centerX, centerY);
    }

    private readonly record struct AtticLayout(
        Point Landing,
        Point Notes,
        Point DeskLeft,
        Point DeskRight,
        Point Television,
        Point TvChair,
        Point ChaChaCushion,
        Point Prototype,
        Point Bed,
        Point Bedside,
        Point Dresser
    );
}

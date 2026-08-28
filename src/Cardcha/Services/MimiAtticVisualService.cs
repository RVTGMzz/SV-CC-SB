using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Objects;

namespace Cardcha.Services;

/// <summary>
/// Alpha.27.0.7.1 true-Stardew visual layer with test access for MiMi's attic.
/// The TMX now provides a tile-based vanilla townInterior shell; this service adds real vanilla
/// Furniture instances for the five locked room zones, keeps inspect points, and preserves the
/// future 17:30 / 6-heart TV eligibility hook.
/// </summary>
internal sealed class MimiAtticVisualService
{
    public const string AtticMapAssetName = "Maps/Cardcha_MiMiAttic";

    private const int SecretTvHeartRequirement = 6;
    private const int SecretTvTime = 1730;
    private const string DecorMarkerKey = "Ronvotri.Cardcha/MiMiAtticDecor";
    private const string DecorVersion = "alpha.27.0.7.5";

    private readonly IModHelper Helper;
    private readonly SaveService Save;
    private bool TestAccessActive;

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
            DrawStairMarker(e.SpriteBatch, FindClearTileNear(location, preferUpperHalf: true));
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

        string? key = null;
        if (Touches(actionTile, layout.DeskLeft) || Touches(actionTile, layout.DeskRight) || Touches(actionTile, layout.Notes))
            key = "mimi.attic.inspect.desk";
        else if (Touches(actionTile, layout.Television) || Touches(actionTile, layout.TvChair) || Touches(actionTile, layout.TvTable))
            key = "mimi.attic.inspect.tv";
        else if (Touches(actionTile, layout.ChaChaCushion) || Touches(actionTile, layout.Prototype))
            key = "mimi.attic.inspect.chacha";

        if (key is null)
            return;

        this.Helper.Input.Suppress(e.Button);
        Game1.drawObjectDialogue(this.Helper.Translation.Get(key).ToString());
    }

    /// <summary>
    /// Still only an eligibility hook in alpha.27.0.7.1. The actual private TV routine remains
    /// intentionally out of scope until the true Stardew attic passes in-game layout acceptance.
    /// </summary>
    public bool IsSecretTvRoutineEligible()
    {
        if (!Context.IsWorldReady || Game1.timeOfDay < SecretTvTime)
            return false;

        if (!Game1.player.friendshipData.TryGetValue(MimiMysteryTownService.NpcId, out Friendship? friendship) || friendship is null)
            return false;

        return friendship.Points >= SecretTvHeartRequirement * 250;
    }

    /// <summary>
    /// Populate the room with actual Stardew furniture rather than a room-sized custom PNG.
    /// This keeps vanilla sprite proportions, shadows, draw ordering, and furniture collision.
    /// </summary>
    private static void EnsureVanillaFurniture(GameLocation attic)
    {
        if (attic.modData.TryGetValue(DecorMarkerKey, out string? version)
            && string.Equals(version, DecorVersion, StringComparison.Ordinal))
        {
            return;
        }

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
        TryAddFurniture(attic, "(F)1456", 3, 5);   // Patchwork Rug — research zone.
        TryAddFurniture(attic, "(F)1623", 2, 9);   // Green Cottage Rug — TV nook.
        TryAddFurniture(attic, "(F)1461", 9, 8);   // Dark central rug — concept anchor / open circulation.

        // Research desk — deliberately domestic, not a full workshop.
        TryAddFurniture(attic, "(F)1289", 2, 4);                 // Dark Bookcase.
        TryAddFurniture(attic, "(F)1120", 4, 5, heldId: "(F)1368"); // Oak Table + Small Crystal.
        TryAddFurniture(attic, "(F)1443", 8, 5);                 // Country Lamp.
        TryAddFurniture(attic, "(F)1362", 9, 5);                 // Small Plant.

        // Personal / bed corner.
        TryAddFurniture(attic, "(F)2058", 15, 4);                // Starry Double Bed.
        TryAddFurniture(attic, "(F)704", 19, 4);                 // Oak Dresser.
        TryAddFurniture(attic, "(F)1399", 14, 5, heldId: "(F)1369"); // Modern End Table + lantern.

        // TV secret nook — cozy, clearly separate from the research side.
        TryAddFurniture(attic, "(F)1466", 3, 8);                 // Budget TV.
        TryAddFurniture(attic, "(F)432", 3, 10);                 // Green Couch.
        TryAddFurniture(attic, "(F)724", 6, 9, heldId: "(F)1364");  // Coffee Table + bowl/snacks stand-in.

        // ChaCha / future-upgrade corner — a small tinkering area, not a machine shop.
        TryAddFurniture(attic, "(F)1132", 16, 9, heldId: "(F)1368"); // Modern Table + crystal prototype.
        TryAddFurniture(attic, "(F)1390", 19, 9);                // House Plant.

        // Wall details make the shell read like a real Stardew bedroom rather than an empty shed.
        TryAddFurniture(attic, "(F)1614", 10, 2);                // Basic Window.
        TryAddFurniture(attic, "(F)1541", 6, 2);                 // A Night On Eco-Hill.
        TryAddFurniture(attic, "(F)1600", 17, 2);                // Skull Poster.

        attic.modData[DecorMarkerKey] = DecorVersion;
    }

    private static void TryAddFurniture(
        GameLocation attic,
        string itemId,
        int x,
        int y,
        int rotation = 0,
        string? heldId = null)
    {
        try
        {
            Furniture item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);
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

    private static void DrawStairMarker(SpriteBatch batch, Point tile)
    {
        try
        {
            Item staircase = ItemRegistry.Create("(BC)71");
            Vector2 world = new(tile.X * 64f, tile.Y * 64f - 64f);
            Vector2 screen = Game1.GlobalToLocal(Game1.viewport, world);
            staircase.drawInMenu(batch, screen, 1f, 0.96f, 0.995f, StackDrawType.Hide);
        }
        catch
        {
            // Access remains functional if another mod replaces/removes the vanilla decorative icon.
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
            DeskLeft: P(4, 5),
            DeskRight: P(6, 5),

            // TV secret nook on the lower-left.
            Television: P(3, 8),
            TvChair: P(3, 10),
            TvTable: P(6, 9),

            // ChaCha / future upgrade corner on the lower-right.
            ChaChaCushion: P(17, 10),
            Prototype: P(16, 9)
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
        Point TvTable,
        Point ChaChaCushion,
        Point Prototype
    );
}

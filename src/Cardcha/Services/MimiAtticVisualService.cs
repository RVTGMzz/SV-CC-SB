using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Alpha.27.0.5 custom interior layer for MiMi's attic.
/// The room now loads from a dedicated TMX + PNG asset while this service keeps the stable
/// inspect points, staircase marker, and the future 17:30 / 6-heart TV eligibility hook.
/// </summary>
internal sealed class MimiAtticVisualService
{
    public const string AtticMapAssetName = "Maps/Cardcha_MiMiAttic";

    private const int SecretTvHeartRequirement = 6;
    private const int SecretTvTime = 1730;

    private readonly IModHelper Helper;
    private readonly SaveService Save;

    public MimiAtticVisualService(IModHelper helper, SaveService save)
    {
        this.Helper = helper;
        this.Save = save;
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
        if (!Context.IsWorldReady || !this.Save.Data.MimiMeetupCompleted)
            return;

        GameLocation? location = Game1.currentLocation;
        if (location is null)
            return;

        if (location.NameOrUniqueName.Equals("WizardHouse", StringComparison.OrdinalIgnoreCase))
        {
            DrawStairMarker(e.SpriteBatch, FindClearTileNear(location, preferUpperHalf: true));
            return;
        }

        if (!location.NameOrUniqueName.Equals(MimiHomeService.AtticLocationName, StringComparison.OrdinalIgnoreCase))
            return;

        DrawStairMarker(e.SpriteBatch, GetLayout(location).Landing);
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady
            || !this.Save.Data.MimiMeetupCompleted
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
    /// Still only an eligibility hook in alpha.27.0.5. The actual private TV routine remains
    /// intentionally out of scope until the custom attic passes in-game layout acceptance.
    /// </summary>
    public bool IsSecretTvRoutineEligible()
    {
        if (!Context.IsWorldReady || Game1.timeOfDay < SecretTvTime)
            return false;

        if (!Game1.player.friendshipData.TryGetValue(MimiMysteryTownService.NpcId, out Friendship? friendship) || friendship is null)
            return false;

        return friendship.Points >= SecretTvHeartRequirement * 250;
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

            // Research desk / notes on the left half.
            Notes: P(3, 8),
            DeskLeft: P(2, 9),
            DeskRight: P(5, 9),

            // TV secret corner on the upper-right.
            Television: P(width - 4, 5),
            TvChair: P(width - 6, 8),
            TvTable: P(width - 3, 8),

            // ChaCha / future upgrade corner on the lower-right.
            ChaChaCushion: P(width - 6, height - 3),
            Prototype: P(width - 3, height - 3)
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

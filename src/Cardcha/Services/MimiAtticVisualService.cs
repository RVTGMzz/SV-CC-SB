using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Alpha.27.0.4 visual/environment layer for MiMi's attic.
/// Keeps the stable runtime location and safe vanilla Shed base, then overlays a Cardcha-specific
/// lived-in room layout plus inspectable lore points without turning the attic into a second shop.
/// </summary>
internal sealed class MimiAtticVisualService
{
    private const int SpriteSize = 16;
    private const float WorldScale = 4f;
    private const int SecretTvHeartRequirement = 6;
    private const int SecretTvTime = 1730;

    private readonly IModHelper Helper;
    private readonly SaveService Save;
    private Texture2D? PropsTexture;

    public MimiAtticVisualService(IModHelper helper, SaveService save)
    {
        this.Helper = helper;
        this.Save = save;
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

        AtticLayout layout = GetLayout(location);
        this.DrawAtticFoundation(e.SpriteBatch, layout);
        DrawStairMarker(e.SpriteBatch, layout.Landing);
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
    /// Intentionally unused by alpha.27.0.4. This is the stable eligibility hook for the later
    /// private 17:30 TV routine; the event itself remains out of scope for this milestone.
    /// </summary>
    public bool IsSecretTvRoutineEligible()
    {
        if (!Context.IsWorldReady || Game1.timeOfDay < SecretTvTime)
            return false;

        if (!Game1.player.friendshipData.TryGetValue(MimiMysteryTownService.NpcId, out Friendship? friendship) || friendship is null)
            return false;

        return friendship.Points >= SecretTvHeartRequirement * 250;
    }

    private void DrawAtticFoundation(SpriteBatch batch, AtticLayout l)
    {
        Texture2D texture = this.PropsTexture ??= this.Helper.ModContent.Load<Texture2D>("assets/mimi_attic_props.png");

        // Entrance / stair landing.
        DrawTile(batch, texture, 15, l.Landing, -0.020f);

        // Research desk: deliberately busy, but still reads as a personal desk instead of a lab.
        DrawTile(batch, texture, 13, l.Bookcase, 0f);
        DrawTile(batch, texture, 12, l.Clutter, 0f);
        DrawTile(batch, texture, 3, l.Notes, 0f);
        DrawTile(batch, texture, 1, l.DeskLeft, 0f);
        DrawTile(batch, texture, 2, l.DeskRight, 0f);

        // Bed / personal corner.
        DrawTile(batch, texture, 6, l.Bedside, 0f);
        DrawTile(batch, texture, 4, l.BedHead, 0f);
        DrawTile(batch, texture, 5, l.BedFoot, 0f);

        // TV secret zone. The divider makes this corner feel tucked away even on the compact Shed map.
        DrawTile(batch, texture, 14, l.TvDivider, 0f);
        DrawTile(batch, texture, 7, l.Television, 0f);
        DrawTile(batch, texture, 8, l.TvChair, 0f);
        DrawTile(batch, texture, 9, l.TvTable, 0f);

        // ChaCha / future upgrade corner.
        DrawTile(batch, texture, 0, l.ChaChaRug, -0.020f);
        DrawTile(batch, texture, 10, l.ChaChaCushion, 0f);
        DrawTile(batch, texture, 11, l.Prototype, 0f);
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

    private static void DrawTile(SpriteBatch batch, Texture2D texture, int frame, Point tile, float depthBias)
    {
        Rectangle source = new(frame * SpriteSize, 0, SpriteSize, SpriteSize);
        Vector2 world = new(tile.X * 64f, tile.Y * 64f);
        Vector2 screen = Game1.GlobalToLocal(Game1.viewport, world);
        float depth = Math.Clamp(((tile.Y + 1) * 64f) / 10000f + depthBias, 0.001f, 0.999f);
        batch.Draw(texture, screen, source, Color.White, 0f, Vector2.Zero, WorldScale, SpriteEffects.None, depth);
    }

    private static AtticLayout GetLayout(GameLocation location)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 12;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 10;
        int maxX = Math.Max(1, width - 2);
        int maxY = Math.Max(1, height - 2);

        Point P(int x, int y) => new(Math.Clamp(x, 1, maxX), Math.Clamp(y, 1, maxY));

        int leftX = Math.Clamp(2, 1, maxX);
        int deskY = Math.Clamp(3, 1, maxY);
        int rightX = Math.Clamp(width - 3, 1, maxX);
        int tvX = Math.Clamp(width - 4, 1, maxX);
        int tvY = 1;
        int chachaY = Math.Clamp(height - 4, 1, maxY);

        return new AtticLayout(
            Landing: P(width / 2, height - 3),
            Bookcase: P(1, 2),
            Clutter: P(1, 4),
            Notes: P(leftX, deskY - 1),
            DeskLeft: P(leftX, deskY),
            DeskRight: P(leftX + 1, deskY),
            Bedside: P(rightX - 1, 3),
            BedHead: P(rightX, 3),
            BedFoot: P(rightX, 4),
            TvDivider: P(tvX - 1, tvY),
            Television: P(tvX, tvY),
            TvChair: P(tvX, tvY + 1),
            TvTable: P(tvX + 1, tvY + 1),
            ChaChaRug: P(leftX, chachaY),
            ChaChaCushion: P(leftX, chachaY),
            Prototype: P(leftX + 1, chachaY)
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
        Point Bookcase,
        Point Clutter,
        Point Notes,
        Point DeskLeft,
        Point DeskRight,
        Point Bedside,
        Point BedHead,
        Point BedFoot,
        Point TvDivider,
        Point Television,
        Point TvChair,
        Point TvTable,
        Point ChaChaRug,
        Point ChaChaCushion,
        Point Prototype
    );
}

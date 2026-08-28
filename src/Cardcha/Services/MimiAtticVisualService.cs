using Microsoft.Xna.Framework;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>Draws a vanilla staircase marker over the runtime attic access tiles.</summary>
internal sealed class MimiAtticVisualService
{
    private readonly SaveService Save;
    private Item? StaircaseIcon;

    public MimiAtticVisualService(SaveService save)
    {
        this.Save = save;
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Save.Data.MimiMeetupCompleted)
            return;

        GameLocation? location = Game1.currentLocation;
        if (location is null)
            return;

        Point? tile = null;
        if (location.NameOrUniqueName.Equals("WizardHouse", StringComparison.OrdinalIgnoreCase))
            tile = FindClearTileNear(location, preferUpperHalf: true);
        else if (location.NameOrUniqueName.Equals(MimiHomeService.AtticLocationName, StringComparison.OrdinalIgnoreCase))
            tile = FindAtticExitTile(location);

        if (tile is null)
            return;

        try
        {
            this.StaircaseIcon ??= ItemRegistry.Create("(BC)71");
            Vector2 world = new(tile.Value.X * 64f, tile.Value.Y * 64f - 64f);
            Vector2 screen = Game1.GlobalToLocal(Game1.viewport, world);
            this.StaircaseIcon.drawInMenu(e.SpriteBatch, screen, 1f, 0.96f, 0.995f, StackDrawType.Hide);
        }
        catch
        {
            // The stairs are still interactable if a texture replacement mod makes the vanilla
            // decorative staircase unavailable. Never let a visual hint break the location.
        }
    }

    private static Point FindAtticExitTile(GameLocation location)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 12;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 10;
        int x = Math.Clamp(width / 2, 1, Math.Max(1, width - 2));
        int startY = Math.Max(1, height - 3);
        for (int y = startY; y >= 1; y--)
        {
            Point p = new(x, y);
            if (IsTileClear(location, p))
                return p;
        }
        return new Point(x, startY);
    }

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
                    if (IsTileClear(location, p))
                        return p;
                }
            }
        }
        return new Point(centerX, centerY);
    }

    private static bool IsTileClear(GameLocation location, Point tile)
    {
        try
        {
            Vector2 v = new(tile.X, tile.Y);
            return !location.IsTileBlockedBy(v) && !location.Objects.ContainsKey(v);
        }
        catch
        {
            return true;
        }
    }
}

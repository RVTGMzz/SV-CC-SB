using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// .5.8 visual runtime for the rebuilt Airship Bridge + Sky Dock.
/// The heavy room architecture lives in TMX/backdrop PNGs so it participates in normal map depth.
/// This renderer is intentionally lightweight: only animated lights, upgrade stations, and small
/// interaction accents are drawn after the map. It never paints foreground beams over the farmer.
/// </summary>
internal static class AirshipInteriorStardewRenderer
{
    private const string UpgradeAtlasPath = "assets/airship_upgrade_visuals.png";
    private const int CellSize = 96;

    private static Texture2D? UpgradeAtlas;
    private static bool AtlasLoadFailed;

    public static bool TryDrawDeck(SpriteBatch batch, GameLocation deck, SaveService save)
    {
        if (batch is null || deck is null || save is null)
            return false;

        float phase = (float)(Environment.TickCount64 / 1000.0);
        DrawDeckWindowLife(batch, phase);
        DrawHelmAccent(batch, phase);
        DrawUpgradeStations(batch, save, phase);
        DrawChaChaPedestalAccent(batch, phase);
        DrawFloorMarker(batch, new Point(12, 12), new Color(89, 210, 226) * 0.48f, phase * 0.7f);
        return true;
    }

    public static bool TryDrawSkyDock(SpriteBatch batch, GameLocation dock)
    {
        if (batch is null || dock is null)
            return false;

        float phase = (float)(Environment.TickCount64 / 1000.0);

        // Route console, boarding arch, and return tile get tiny pixel-like accents only.
        DrawConsoleLamp(batch, new Point(10, 7), new Color(194, 132, 70), new Color(170, 105, 223), phase);
        DrawConsoleLamp(batch, new Point(24, 7), new Color(194, 132, 70), new Color(78, 193, 211), -phase);
        DrawFloorMarker(batch, new Point(15, 16), new Color(88, 208, 224) * 0.48f, phase * 0.7f);
        return true;
    }

    private static void DrawDeckWindowLife(SpriteBatch batch, float phase)
    {
        // Window sits in the top five map rows. These tiny lights read as pixel stars/reflections,
        // not a translucent UI sheet covering the room.
        Color star = new Color(238, 225, 194) * 0.58f;
        Color cyan = new Color(92, 214, 228) * 0.36f;
        for (int i = 0; i < 13; i++)
        {
            int tx = 3 + ((i * 7 + 2) % 18);
            int ty = 1 + ((i * 5 + 1) % 3);
            Vector2 p = WorldToScreen(tx * 64f + 13f + (i % 3) * 12f, ty * 64f + 9f + (i % 2) * 13f);
            float pulse = 0.46f + 0.18f * MathF.Sin(phase * 1.5f + i * 0.9f);
            DrawRect(batch, new Rectangle((int)p.X, (int)p.Y, 3, 3), (i % 4 == 0 ? cyan : star) * pulse);
        }
    }

    private static void DrawHelmAccent(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(12f * 64f + 32f, 4f * 64f + 18f);
        Color dark = new Color(42, 29, 38) * 0.88f;
        Color brass = new Color(204, 144, 70) * 0.78f;
        Color cyan = new Color(82, 215, 228) * 0.66f;
        Color violet = new Color(165, 100, 216) * 0.52f;

        // Small hard-edged astrolabe. Backdrop carries the actual dais and console mass.
        DrawPixelRing(batch, c, 22, dark);
        DrawPixelRing(batch, c, 18, brass);
        DrawPixelRing(batch, c, 12, violet);
        int needle = (int)(MathF.Sin(phase * 1.2f) * 8f);
        DrawRect(batch, new Rectangle((int)c.X - 2, (int)c.Y - 14 + needle / 4, 4, 28), cyan);
        DrawRect(batch, new Rectangle((int)c.X - 13, (int)c.Y - 2, 26, 4), brass * 0.74f);
        DrawDiamond(batch, c, 7, cyan);
    }

    private static void DrawUpgradeStations(SpriteBatch batch, SaveService save, float phase)
    {
        Texture2D? atlas = GetUpgradeAtlas();
        if (atlas is null)
            return;

        (Point Tile, int Column, int Level, Color Accent)[] stations =
        {
            (new Point(5, 9), 0, Math.Clamp(save.Data.AirshipEngineLevel, 0, 3), new Color(89, 205, 218)),
            (new Point(18, 9), 1, Math.Clamp(save.Data.AirshipNavigationLevel, 0, 3), new Color(103, 215, 231)),
            (new Point(8, 10), 2, Math.Clamp(save.Data.AirshipHullLevel, 0, 3), new Color(151, 139, 213)),
            (new Point(15, 10), 3, Math.Clamp(save.Data.AirshipReactorLevel, 0, 3), new Color(183, 101, 224)),
        };

        foreach ((Point tile, int column, int level, Color accent) in stations)
        {
            Vector2 center = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 34f);
            Rectangle src = new(column * CellSize, level * CellSize, CellSize, CellSize);
            Rectangle shadow = new((int)center.X - 48, (int)center.Y + 26, 96, 14);
            DrawRect(batch, shadow, new Color(28, 21, 28) * 0.42f);

            Rectangle dst = new((int)center.X - 48, (int)center.Y - 61, 96, 96);
            batch.Draw(atlas, dst, src, Color.White);

            if (level > 0)
            {
                float pulse = 0.55f + 0.20f * MathF.Sin(phase * 2.0f + column * 1.3f);
                DrawRect(batch, new Rectangle((int)center.X - 16, (int)center.Y + 28, 32, 3), accent * pulse);
                if (level >= 3)
                {
                    DrawRect(batch, new Rectangle((int)center.X - 2, (int)center.Y - 54, 4, 7), accent * (pulse + 0.12f));
                    DrawRect(batch, new Rectangle((int)center.X - 13, (int)center.Y - 46, 3, 3), accent * pulse);
                    DrawRect(batch, new Rectangle((int)center.X + 10, (int)center.Y - 40, 3, 3), accent * pulse);
                }
            }
        }
    }

    private static void DrawChaChaPedestalAccent(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(19f * 64f + 32f, 5f * 64f + 34f);
        Color violet = new Color(177, 106, 225) * (0.44f + 0.13f * MathF.Sin(phase * 2.2f));
        Color cyan = new Color(89, 211, 224) * (0.42f + 0.12f * MathF.Sin(phase * 1.8f + 1f));
        DrawRect(batch, new Rectangle((int)c.X - 22, (int)c.Y + 19, 16, 3), violet);
        DrawRect(batch, new Rectangle((int)c.X + 6, (int)c.Y + 19, 16, 3), cyan);
        DrawDiamond(batch, c + new Vector2(-19f, 9f), 4, violet);
        DrawDiamond(batch, c + new Vector2(19f, 9f), 4, cyan);
    }

    private static void DrawConsoleLamp(SpriteBatch batch, Point tile, Color brass, Color glow, float phase)
    {
        Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 20f);
        DrawRect(batch, new Rectangle((int)c.X - 9, (int)c.Y - 3, 18, 6), new Color(43, 31, 35) * 0.85f);
        DrawRect(batch, new Rectangle((int)c.X - 6, (int)c.Y - 1, 12, 2), brass * 0.82f);
        float pulse = 0.55f + 0.18f * MathF.Sin(phase * 2.1f + tile.X * 0.2f);
        DrawRect(batch, new Rectangle((int)c.X - 2, (int)c.Y - 10, 4, 4), glow * pulse);
    }

    private static void DrawFloorMarker(SpriteBatch batch, Point tile, Color color, float phase)
    {
        Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 43f);
        int s = 7 + (int)MathF.Round((MathF.Sin(phase * 2f) + 1f) * 1.5f);
        DrawDiamond(batch, c, s, color);
    }

    private static Texture2D? GetUpgradeAtlas()
    {
        if (UpgradeAtlas is not null)
            return UpgradeAtlas;
        if (AtlasLoadFailed || ModEntry.StaticHelper is null)
            return null;

        try
        {
            UpgradeAtlas = ModEntry.StaticHelper.ModContent.Load<Texture2D>(UpgradeAtlasPath);
            return UpgradeAtlas;
        }
        catch
        {
            AtlasLoadFailed = true;
            return null;
        }
    }

    private static Vector2 WorldToScreen(float x, float y)
        => Game1.GlobalToLocal(Game1.viewport, new Vector2(x, y));

    private static void DrawPixelRing(SpriteBatch batch, Vector2 center, int radius, Color color)
    {
        int x = (int)center.X;
        int y = (int)center.Y;
        DrawRect(batch, new Rectangle(x - radius, y - 2, radius * 2 + 1, 4), color);
        DrawRect(batch, new Rectangle(x - 2, y - radius, 4, radius * 2 + 1), color);
        int d = Math.Max(2, radius / 2);
        DrawRect(batch, new Rectangle(x - radius + 3, y - d, 3, d * 2), color * 0.78f);
        DrawRect(batch, new Rectangle(x + radius - 5, y - d, 3, d * 2), color * 0.78f);
        DrawRect(batch, new Rectangle(x - d, y - radius + 3, d * 2, 3), color * 0.78f);
        DrawRect(batch, new Rectangle(x - d, y + radius - 5, d * 2, 3), color * 0.78f);
    }

    private static void DrawDiamond(SpriteBatch batch, Vector2 center, int radius, Color color)
    {
        radius = Math.Max(2, radius);
        for (int y = -radius; y <= radius; y++)
        {
            int half = radius - Math.Abs(y);
            DrawRect(batch, new Rectangle((int)center.X - half, (int)center.Y + y, half * 2 + 1, 1), color);
        }
    }

    private static void DrawRect(SpriteBatch batch, Rectangle rect, Color color)
    {
        if (rect.Width <= 0 || rect.Height <= 0)
            return;
        batch.Draw(Game1.staminaRect, rect, color);
    }
}

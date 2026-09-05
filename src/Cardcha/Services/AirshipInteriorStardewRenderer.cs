using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// 0648 Stardew Visual Pass 1.
/// Heavy architecture lives in TMX/backdrop assets with real Buildings collision.
/// This renderer owns only small animated accents and the four level-aware upgrade machines.
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
        DrawWarmDeckAmbient(batch, phase);
        DrawHelmAccent(batch, phase);
        DrawSideConsoleAccent(batch, new Point(5, 7), new Color(100, 174, 176), phase);
        DrawSideConsoleAccent(batch, new Point(18, 7), new Color(101, 139, 164), -phase);
        DrawUpgradeStations(batch, save, phase);
        DrawChaChaPedestalAccent(batch, phase);
        DrawDoorwayThreshold(batch, new Point(12, 12), new Color(173, 133, 72) * 0.48f);
        return true;
    }

    public static bool TryDrawSkyDock(SpriteBatch batch, GameLocation dock)
    {
        if (batch is null || dock is null)
            return false;

        float phase = (float)(Environment.TickCount64 / 1000.0);
        DrawRouteBoardAccent(batch, phase);
        DrawBoardingGantryAccent(batch, phase);
        DrawServiceCornerAccent(batch, phase);
        DrawConsoleLamp(batch, new Point(10, 6), new Color(188, 132, 70), new Color(145, 112, 156), phase);
        DrawConsoleLamp(batch, new Point(24, 6), new Color(188, 132, 70), new Color(96, 168, 174), -phase);
        DrawDoorwayThreshold(batch, new Point(15, 16), new Color(173, 133, 72) * 0.46f);
        return true;
    }

    private static void DrawDeckWindowLife(SpriteBatch batch, float phase)
    {
        Color star = new Color(238, 225, 194) * 0.48f;
        Color blue = new Color(103, 158, 181) * 0.28f;
        for (int i = 0; i < 12; i++)
        {
            int tx = 3 + ((i * 7 + 2) % 18);
            int ty = 1 + ((i * 5 + 1) % 3);
            Vector2 p = WorldToScreen(tx * 64f + 13f + (i % 3) * 12f, ty * 64f + 9f + (i % 2) * 13f);
            float pulse = 0.38f + 0.12f * MathF.Sin(phase * 1.35f + i * 0.9f);
            DrawRect(batch, new Rectangle((int)p.X, (int)p.Y, 3, 3), (i % 4 == 0 ? blue : star) * pulse);
        }
    }

    private static void DrawWarmDeckAmbient(SpriteBatch batch, float phase)
    {
        Color brass = new Color(199, 148, 78) * 0.54f;
        Color warm = new Color(230, 196, 126) * (0.34f + 0.05f * MathF.Sin(phase * 1.6f));
        foreach (Point tile in new[] { new Point(2, 4), new Point(21, 4) })
        {
            Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 18f);
            DrawRect(batch, new Rectangle((int)c.X - 8, (int)c.Y - 3, 16, 3), brass);
            DrawRect(batch, new Rectangle((int)c.X - 3, (int)c.Y - 8, 6, 5), warm);
        }
    }

    private static void DrawHelmAccent(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(12f * 64f + 32f, 4f * 64f + 18f);
        Color dark = new Color(48, 33, 34) * 0.90f;
        Color brass = new Color(199, 148, 78) * 0.82f;
        Color teal = new Color(100, 174, 176) * 0.58f;
        Color violet = new Color(145, 112, 156) * 0.42f;

        DrawPixelRing(batch, c, 22, dark);
        DrawPixelRing(batch, c, 18, brass);
        DrawPixelRing(batch, c, 12, violet);
        int needle = (int)(MathF.Sin(phase * 1.1f) * 7f);
        DrawRect(batch, new Rectangle((int)c.X - 2, (int)c.Y - 14 + needle / 4, 4, 28), teal);
        DrawRect(batch, new Rectangle((int)c.X - 13, (int)c.Y - 2, 26, 4), brass * 0.70f);
        DrawDiamond(batch, c, 7, teal);
    }

    private static void DrawSideConsoleAccent(SpriteBatch batch, Point tile, Color accent, float phase)
    {
        Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 24f);
        Color brass = new Color(197, 145, 76) * 0.58f;
        float blink = 0.36f + 0.10f * MathF.Sin(phase * 1.9f + tile.X * 0.3f);
        DrawRect(batch, new Rectangle((int)c.X - 18, (int)c.Y - 5, 9, 4), accent * blink);
        DrawRect(batch, new Rectangle((int)c.X - 4, (int)c.Y - 5, 8, 4), brass);
        DrawRect(batch, new Rectangle((int)c.X + 9, (int)c.Y - 5, 9, 4), accent * (blink * 0.85f));
    }

    private static void DrawUpgradeStations(SpriteBatch batch, SaveService save, float phase)
    {
        Texture2D? atlas = GetUpgradeAtlas();
        if (atlas is null)
            return;

        (Point Tile, int Column, int Level, Color Accent)[] stations =
        {
            (new Point(5, 9), 0, Math.Clamp(save.Data.AirshipEngineLevel, 0, 3), new Color(98, 171, 174)),
            (new Point(18, 9), 1, Math.Clamp(save.Data.AirshipNavigationLevel, 0, 3), new Color(94, 145, 171)),
            (new Point(8, 10), 2, Math.Clamp(save.Data.AirshipHullLevel, 0, 3), new Color(132, 126, 169)),
            (new Point(15, 10), 3, Math.Clamp(save.Data.AirshipReactorLevel, 0, 3), new Color(151, 111, 157)),
        };

        foreach ((Point tile, int column, int level, Color accent) in stations)
        {
            Vector2 center = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 34f);
            Rectangle src = new(column * CellSize, level * CellSize, CellSize, CellSize);
            Rectangle shadow = new((int)center.X - 55, (int)center.Y + 30, 110, 13);
            DrawRect(batch, shadow, new Color(34, 25, 25) * 0.34f);

            Rectangle dst = new((int)center.X - 56, (int)center.Y - 76, 112, 112);
            batch.Draw(atlas, dst, src, Color.White);

            float pulse = 0.40f + 0.12f * MathF.Sin(phase * 1.7f + column * 1.2f);
            DrawRect(batch, new Rectangle((int)center.X - 15, (int)center.Y + 28, 30, 3), new Color(199, 148, 78) * 0.48f);
            if (level > 0)
                DrawRect(batch, new Rectangle((int)center.X - 9, (int)center.Y + 24, 18, 2), accent * pulse);
            if (level >= 3)
            {
                DrawRect(batch, new Rectangle((int)center.X - 2, (int)center.Y - 54, 4, 6), accent * (pulse + 0.08f));
                DrawRect(batch, new Rectangle((int)center.X - 12, (int)center.Y - 45, 3, 3), accent * pulse);
                DrawRect(batch, new Rectangle((int)center.X + 9, (int)center.Y - 40, 3, 3), accent * pulse);
            }
        }
    }

    private static void DrawChaChaPedestalAccent(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(19f * 64f + 32f, 5f * 64f + 34f);
        Color violet = new Color(145, 112, 156) * (0.34f + 0.08f * MathF.Sin(phase * 1.8f));
        Color teal = new Color(99, 173, 175) * (0.32f + 0.08f * MathF.Sin(phase * 1.5f + 1f));
        Color brass = new Color(197, 145, 76) * 0.48f;
        DrawRect(batch, new Rectangle((int)c.X - 23, (int)c.Y + 19, 17, 3), brass);
        DrawRect(batch, new Rectangle((int)c.X + 6, (int)c.Y + 19, 17, 3), brass);
        DrawDiamond(batch, c + new Vector2(-19f, 9f), 4, violet);
        DrawDiamond(batch, c + new Vector2(19f, 9f), 4, teal);
    }

    private static void DrawRouteBoardAccent(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(10f * 64f + 32f, 6f * 64f + 16f);
        Color brass = new Color(198, 145, 76) * 0.56f;
        Color[] chips =
        {
            new Color(98, 171, 174),
            new Color(210, 158, 83),
            new Color(145, 112, 156),
            new Color(94, 145, 171),
        };
        for (int i = 0; i < chips.Length; i++)
        {
            float pulse = 0.32f + 0.07f * MathF.Sin(phase * 1.4f + i * 0.8f);
            DrawRect(batch, new Rectangle((int)c.X - 26 + i * 17, (int)c.Y - 5, 9, 4), chips[i] * pulse);
        }
        DrawRect(batch, new Rectangle((int)c.X - 30, (int)c.Y + 4, 60, 2), brass);
    }

    private static void DrawBoardingGantryAccent(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(24f * 64f + 32f, 6f * 64f + 24f);
        Color brass = new Color(198, 145, 76) * 0.54f;
        Color teal = new Color(99, 173, 175) * (0.30f + 0.08f * MathF.Sin(phase * 1.6f));
        DrawRect(batch, new Rectangle((int)c.X - 34, (int)c.Y - 12, 68, 3), brass);
        DrawDiamond(batch, c + new Vector2(-28f, -15f), 3, teal);
        DrawDiamond(batch, c + new Vector2(28f, -15f), 3, teal);
    }

    private static void DrawServiceCornerAccent(SpriteBatch batch, float phase)
    {
        Color warm = new Color(220, 184, 111) * (0.28f + 0.05f * MathF.Sin(phase * 1.3f));
        foreach (Point tile in new[] { new Point(4, 10), new Point(26, 10) })
        {
            Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 22f);
            DrawRect(batch, new Rectangle((int)c.X - 3, (int)c.Y - 8, 6, 5), warm);
        }
    }

    private static void DrawConsoleLamp(SpriteBatch batch, Point tile, Color brass, Color glow, float phase)
    {
        Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 20f);
        DrawRect(batch, new Rectangle((int)c.X - 9, (int)c.Y - 3, 18, 6), new Color(48, 34, 34) * 0.78f);
        DrawRect(batch, new Rectangle((int)c.X - 6, (int)c.Y - 1, 12, 2), brass * 0.72f);
        float pulse = 0.38f + 0.10f * MathF.Sin(phase * 1.8f + tile.X * 0.2f);
        DrawRect(batch, new Rectangle((int)c.X - 2, (int)c.Y - 10, 4, 4), glow * pulse);
    }

    private static void DrawDoorwayThreshold(SpriteBatch batch, Point tile, Color color)
    {
        Vector2 c = WorldToScreen(tile.X * 64f, tile.Y * 64f + 54f);
        DrawRect(batch, new Rectangle((int)c.X - 58, (int)c.Y, 116, 3), color);
        DrawDiamond(batch, new Vector2(c.X - 50f, c.Y + 1f), 3, color * 0.72f);
        DrawDiamond(batch, new Vector2(c.X + 50f, c.Y + 1f), 3, color * 0.72f);
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

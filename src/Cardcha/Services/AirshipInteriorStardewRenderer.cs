using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// 0648B. Vanilla townInterior owns the room shell. This renderer only adds magical light,
/// weather-aware glass ambience and four independent level-aware machine sprites.
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
        DrawWindowMagic(batch, phase);
        DrawAmbientLamps(batch, phase);
        DrawHelmMagic(batch, phase);
        DrawUpgradeStations(batch, save, phase);
        DrawChaChaMagic(batch, phase);
        DrawDoorwayThreshold(batch, new Point(12, 12), new Color(210, 161, 79) * 0.60f);
        return true;
    }

    public static bool TryDrawSkyDock(SpriteBatch batch, GameLocation dock)
    {
        if (batch is null || dock is null)
            return false;
        float phase = (float)(Environment.TickCount64 / 1000.0);
        DrawDockMagic(batch, phase);
        DrawDoorwayThreshold(batch, new Point(15, 16), new Color(210, 161, 79) * 0.54f);
        return true;
    }

    private static void DrawWindowMagic(SpriteBatch batch, float phase)
    {
        bool night = Game1.timeOfDay >= 2000 || Game1.timeOfDay < 600;
        Color warm = new Color(244, 209, 138) * 0.35f;
        Color teal = new Color(103, 205, 207) * 0.30f;
        for (int i = 0; i < 14; i++)
        {
            int x = 2 + ((i * 7) % 20);
            Vector2 p = WorldToScreen(x * 64f + 26f, 2f * 64f + 24f + (i % 3) * 13f);
            float pulse = 0.45f + 0.18f * MathF.Sin(phase * 1.4f + i * 0.85f);
            DrawRect(batch, new Rectangle((int)p.X, (int)p.Y, night ? 4 : 3, night ? 4 : 3), (i % 4 == 0 ? teal : warm) * pulse);
        }
    }

    private static void DrawAmbientLamps(SpriteBatch batch, float phase)
    {
        foreach ((Point tile, Color glow) in new[]
        {
            (new Point(2,6), new Color(248, 211, 132)),
            (new Point(21,6), new Color(248, 211, 132)),
            (new Point(10,7), new Color(116, 219, 215)),
            (new Point(14,7), new Color(179, 132, 211)),
        })
        {
            Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 25f);
            float pulse = 0.58f + 0.08f * MathF.Sin(phase * 1.55f + tile.X);
            // Pixel halo, intentionally chunky instead of smooth neon.
            DrawRect(batch, new Rectangle((int)c.X - 30, (int)c.Y - 20, 60, 40), glow * (0.055f * pulse));
            DrawRect(batch, new Rectangle((int)c.X - 18, (int)c.Y - 12, 36, 24), glow * (0.085f * pulse));
            DrawDiamond(batch, c, 5, glow * (0.52f + pulse * 0.12f));
            DrawRect(batch, new Rectangle((int)c.X - 2, (int)c.Y + 7, 4, 6), new Color(190, 135, 60) * 0.82f);
        }
    }

    private static void DrawHelmMagic(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(12f * 64f + 32f, 6f * 64f + 10f);
        Color brass = new Color(218, 163, 79) * 0.82f;
        Color teal = new Color(109, 220, 216) * 0.72f;
        Color violet = new Color(184, 133, 216) * 0.58f;
        float pulse = 0.58f + 0.10f * MathF.Sin(phase * 1.8f);
        DrawRect(batch, new Rectangle((int)c.X - 46, (int)c.Y - 32, 92, 64), teal * (0.045f + pulse * 0.035f));
        DrawPixelRing(batch, c, 23, brass);
        DrawPixelRing(batch, c, 16, violet);
        DrawDiamond(batch, c, 7, teal * pulse);
        int needle = (int)(MathF.Sin(phase * 0.9f) * 7f);
        DrawRect(batch, new Rectangle((int)c.X + needle - 1, (int)c.Y - 14, 3, 28), teal * 0.62f);
        for (int i = 0; i < 4; i++)
        {
            float a = phase * 0.45f + i * MathHelper.PiOver2;
            Vector2 s = c + new Vector2(MathF.Cos(a) * 35f, MathF.Sin(a) * 22f);
            DrawRect(batch, new Rectangle((int)s.X, (int)s.Y, 3, 3), (i % 2 == 0 ? teal : violet) * 0.60f);
        }
    }

    private static void DrawUpgradeStations(SpriteBatch batch, SaveService save, float phase)
    {
        Texture2D? atlas = GetUpgradeAtlas();
        if (atlas is null)
            return;
        (Point Tile, int Column, int Level, Color Accent)[] stations =
        {
            (new Point(4,8), 0, Math.Clamp(save.Data.AirshipEngineLevel,0,3), new Color(104,205,200)),
            (new Point(19,8), 1, Math.Clamp(save.Data.AirshipNavigationLevel,0,3), new Color(98,166,211)),
            (new Point(7,11), 2, Math.Clamp(save.Data.AirshipHullLevel,0,3), new Color(151,151,210)),
            (new Point(16,11), 3, Math.Clamp(save.Data.AirshipReactorLevel,0,3), new Color(190,133,207)),
        };
        foreach ((Point tile, int column, int level, Color accent) in stations)
        {
            Vector2 center = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 52f);
            Rectangle src = new(column * CellSize, level * CellSize, CellSize, CellSize);
            float pulse = 0.62f + 0.16f * MathF.Sin(phase * 2.05f + column * 1.1f);
            DrawRect(batch, new Rectangle((int)center.X - 54, (int)center.Y - 55, 108, 72), accent * (0.075f + pulse * 0.045f));
            DrawRect(batch, new Rectangle((int)center.X - 38, (int)center.Y - 42, 76, 52), accent * (0.085f + pulse * 0.055f));
            Rectangle dst = new((int)center.X - 56, (int)center.Y - 76, 112, 112);
            batch.Draw(atlas, dst, src, Color.White);
            DrawRect(batch, new Rectangle((int)center.X - 19, (int)center.Y - 26, 38, 4), accent * (0.42f + pulse * 0.22f));
            DrawDiamond(batch, new Vector2(center.X, center.Y - 44), 4 + level, accent * (0.58f + pulse * 0.22f));
            for (int i = 0; i < 3 + level; i++)
            {
                float a = phase * (0.5f + column * 0.05f) + i * 2.1f;
                Vector2 s = center + new Vector2(MathF.Cos(a) * 31f, -31f + MathF.Sin(a) * 17f);
                DrawRect(batch, new Rectangle((int)s.X, (int)s.Y, 3, 3), accent * 0.56f);
            }
        }
    }

    private static void DrawChaChaMagic(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(21f * 64f + 32f, 5f * 64f + 34f);
        Color violet = new Color(190, 132, 218) * (0.50f + 0.10f * MathF.Sin(phase * 1.8f));
        Color teal = new Color(111, 218, 209) * (0.46f + 0.10f * MathF.Sin(phase * 1.5f + 1f));
        DrawRect(batch, new Rectangle((int)c.X - 38, (int)c.Y - 30, 76, 60), violet * 0.055f);
        DrawDiamond(batch, c + new Vector2(-18f, 4f), 5, violet);
        DrawDiamond(batch, c + new Vector2(18f, 4f), 5, teal);
        DrawDiamond(batch, c + new Vector2(0f, -15f), 4, Color.White * 0.46f);
    }

    private static void DrawDockMagic(SpriteBatch batch, float phase)
    {
        // Route board indicator.
        Vector2 route = WorldToScreen(7f * 64f + 32f, 7f * 64f + 10f);
        DrawDiamond(batch, route, 5, new Color(109,210,204) * (0.58f + 0.10f*MathF.Sin(phase*1.6f)));
        // Boarding pad is deliberately bright so the warp trigger is never invisible.
        Vector2 bay = WorldToScreen(23f * 64f + 32f, 8f * 64f + 34f);
        Color teal = new Color(103,221,214);
        DrawRect(batch, new Rectangle((int)bay.X - 38, (int)bay.Y - 18, 76, 36), teal * 0.08f);
        DrawPixelRing(batch, bay, 20, teal * 0.56f);
        DrawDiamond(batch, bay, 8, teal * 0.70f);
        for (int i=0;i<5;i++)
        {
            float a=phase*0.55f+i*MathHelper.TwoPi/5f;
            Vector2 s=bay+new Vector2(MathF.Cos(a)*31f,MathF.Sin(a)*14f);
            DrawRect(batch,new Rectangle((int)s.X,(int)s.Y,3,3),Color.White*0.52f);
        }
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
        if (UpgradeAtlas is not null && !UpgradeAtlas.IsDisposed)
            return UpgradeAtlas;
        UpgradeAtlas = null;
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
        => Game1.GlobalToLocal(Game1.viewport, new Vector2(x,y));

    private static void DrawPixelRing(SpriteBatch batch, Vector2 c, int r, Color color)
    {
        DrawRect(batch,new Rectangle((int)c.X-r,(int)c.Y-r,r*2+1,3),color);
        DrawRect(batch,new Rectangle((int)c.X-r,(int)c.Y+r-2,r*2+1,3),color);
        DrawRect(batch,new Rectangle((int)c.X-r,(int)c.Y-r,3,r*2+1),color);
        DrawRect(batch,new Rectangle((int)c.X+r-2,(int)c.Y-r,3,r*2+1),color);
    }

    private static void DrawDiamond(SpriteBatch batch, Vector2 c, int r, Color color)
    {
        for (int y=-r;y<=r;y++)
        {
            int half=r-Math.Abs(y);
            DrawRect(batch,new Rectangle((int)c.X-half,(int)c.Y+y,half*2+1,1),color);
        }
    }

    private static void DrawRect(SpriteBatch batch, Rectangle rect, Color color)
    {
        if (rect.Width<=0 || rect.Height<=0 || color.A==0) return;
        batch.Draw(Game1.staminaRect,rect,color);
    }
}

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
    private const string HubDecorAtlasPath = "assets/airship_hub_decor.png";
    private const string PropRoot0690 = "assets/airship_props/set01_redux";
    private const string TravelGateVisualPath0696D3A = PropRoot0690 + "/boarding_gate_arch.png";
    private static readonly string[] WindowOverlayPaths0690 =
    {
        PropRoot0690 + "/observation_window_overlay_1.png",
        PropRoot0690 + "/observation_window_overlay_2.png",
        PropRoot0690 + "/observation_window_overlay_3.png",
        PropRoot0690 + "/observation_window_overlay_4.png",
    };
    private static readonly string[] ConsoleOverlayPaths0690 =
    {
        PropRoot0690 + "/navigation_console_overlay_1.png",
        PropRoot0690 + "/navigation_console_overlay_2.png",
        PropRoot0690 + "/navigation_console_overlay_3.png",
        PropRoot0690 + "/navigation_console_overlay_4.png",
    };
    private static readonly Texture2D?[] WindowOverlays0690 = new Texture2D?[4];
    private static readonly Texture2D?[] ConsoleOverlays0690 = new Texture2D?[4];
    private const int CellSize = 96;
    private static Texture2D? UpgradeAtlas;
    private static bool AtlasLoadFailed;
    private static Texture2D? HubDecorAtlas;
    private static bool HubDecorLoadFailed;
    private static Texture2D? TravelGateVisual0696D3A;
    private static bool TravelGateVisualLoadFailed0696D3A;

    public static bool TryDrawDeck(SpriteBatch batch, GameLocation deck, SaveService save)
    {
        if (batch is null || deck is null || save is null)
            return false;

        float phase = (float)(Environment.TickCount64 / 1000.0);
        AirshipAmbientAnimationService.DrawDeckAmbient(batch);
        DrawWindowMagic(batch, phase);
        DrawAmbientLamps(batch, phase);
        DrawTravelGate0696D3A(batch, phase);
        // 0696D3-A: all four upgrade stations stay present and share a grounded physical footprint.
        DrawUpgradeStations(batch, save, phase);
        DrawHelmMagic(batch, phase);
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

    private static void DrawDeckStardewDecor(SpriteBatch batch)
    {
        Texture2D? atlas = GetHubDecorAtlas();
        if (atlas is null) return;

        // 0669 foundation: grouped by purpose instead of scattered test props.
        // Navigation/work cluster.
        DrawDecor(batch, atlas, 2, 0, new Point(4, 6), 1.75f);
        DrawDecor(batch, atlas, 0, 1, new Point(7, 6), 1.75f);
        DrawDecor(batch, atlas, 1, 2, new Point(5, 9), 1.65f);

        // Central communal/helm cluster.
        DrawDecor(batch, atlas, 1, 1, new Point(12, 8), 2.35f, 92, 56);
        DrawDecor(batch, atlas, 3, 0, new Point(10, 10), 1.70f);

        // Maintenance/storage cluster.
        DrawDecor(batch, atlas, 3, 2, new Point(18, 8), 1.75f);
        DrawDecor(batch, atlas, 0, 0, new Point(20, 10), 1.65f);
        DrawDecor(batch, atlas, 2, 2, new Point(19, 5), 1.65f);
    }

    private static void DrawDockStardewDecor(SpriteBatch batch)
    {
        Texture2D? atlas = GetHubDecorAtlas();
        if (atlas is null) return;

        // Waiting/storage side.
        DrawDecor(batch, atlas, 0, 0, new Point(4, 10), 1.70f);
        DrawDecor(batch, atlas, 2, 1, new Point(6, 10), 1.65f);
        DrawDecor(batch, atlas, 0, 2, new Point(6, 12), 1.60f);

        // Route desk in one readable cluster.
        DrawDecor(batch, atlas, 3, 1, new Point(8, 6), 1.70f);
        DrawDecor(batch, atlas, 1, 2, new Point(9, 8), 1.60f);

        // Boarding side, kept visually open.
        DrawDecor(batch, atlas, 2, 2, new Point(22, 10), 1.65f);
        DrawDecor(batch, atlas, 1, 0, new Point(24, 11), 1.65f);
    }

    private static void DrawDecor(SpriteBatch batch, Texture2D atlas, int col, int row, Point tile, float scale, int destW = 0, int destH = 0)
    {
        Rectangle src = new(col * 32, row * 32, 32, 32); Vector2 local = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 58f);
        if (destW > 0 && destH > 0) { batch.Draw(atlas, new Rectangle((int)local.X - destW/2, (int)local.Y - destH, destW, destH), src, Color.White); return; }
        batch.Draw(atlas, local, src, Color.White, 0f, new Vector2(16f, 31f), scale, SpriteEffects.None, 0.92f);
    }

    private static Texture2D? GetHubDecorAtlas()
    {
        if (HubDecorAtlas is not null && !HubDecorAtlas.IsDisposed) return HubDecorAtlas; HubDecorAtlas = null; if (HubDecorLoadFailed || ModEntry.StaticHelper is null) return null;
        try { HubDecorAtlas = ModEntry.StaticHelper.ModContent.Load<Texture2D>(HubDecorAtlasPath); return HubDecorAtlas; } catch { HubDecorLoadFailed = true; return null; }
    }

    private static Texture2D? Get0690Overlay(Texture2D?[] cache, string[] paths, int index)
    {
        if (index < 0 || index >= cache.Length || ModEntry.StaticHelper is null)
            return null;
        Texture2D? current = cache[index];
        if (current is not null && !current.IsDisposed)
            return current;
        try
        {
            cache[index] = ModEntry.StaticHelper.ModContent.Load<Texture2D>(paths[index]);
            return cache[index];
        }
        catch
        {
            return null;
        }
    }

    private static void Draw0690WindowOverlay(SpriteBatch batch)
    {
        int frame = (int)((Environment.TickCount64 / 900L) % 4L);
        Texture2D? texture = Get0690Overlay(WindowOverlays0690, WindowOverlayPaths0690, frame);
        if (texture is null)
            return;
        Vector2 topLeft = WorldToScreen(7f * 64f, 1f * 64f);
        batch.Draw(texture,
            new Rectangle((int)topLeft.X, (int)topLeft.Y, texture.Width * 4, texture.Height * 4),
            null, Color.White, 0f, Vector2.Zero, SpriteEffects.None, 0.885f);
    }

    private static void Draw0690ConsoleOverlay(SpriteBatch batch)
    {
        int frame = (int)((Environment.TickCount64 / 1150L) % 4L);
        Texture2D? texture = Get0690Overlay(ConsoleOverlays0690, ConsoleOverlayPaths0690, frame);
        if (texture is null)
            return;
        Vector2 topLeft = WorldToScreen(9f * 64f, 5f * 64f);
        batch.Draw(texture,
            new Rectangle((int)topLeft.X, (int)topLeft.Y, texture.Width * 4, texture.Height * 4),
            null, Color.White, 0f, Vector2.Zero, SpriteEffects.None, 0.886f);
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

    private static Texture2D? GetTravelGateVisual0696D3A()
    {
        if (TravelGateVisual0696D3A is not null && !TravelGateVisual0696D3A.IsDisposed)
            return TravelGateVisual0696D3A;
        TravelGateVisual0696D3A = null;
        if (TravelGateVisualLoadFailed0696D3A || ModEntry.StaticHelper is null)
            return null;
        try
        {
            TravelGateVisual0696D3A = ModEntry.StaticHelper.ModContent.Load<Texture2D>(TravelGateVisualPath0696D3A);
            return TravelGateVisual0696D3A;
        }
        catch
        {
            TravelGateVisualLoadFailed0696D3A = true;
            return null;
        }
    }

    private static void DrawTravelGate0696D3A(SpriteBatch batch, float phase)
    {
        Texture2D? gate = GetTravelGateVisual0696D3A();
        if (gate is null || gate.Width <= 0 || gate.Height <= 0)
            return;

        Point tile = new(4, 5);
        Vector2 floor = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 58f);
        const int width = 244;
        int height = Math.Max(128, (int)MathF.Round(gate.Height * (width / (float)gate.Width)));
        Rectangle dst = new((int)floor.X - width / 2, (int)floor.Y - height + 32, width, height);
        batch.Draw(gate, dst, null, Color.White, 0f, Vector2.Zero, SpriteEffects.None, 0.883f);

        float pulse = 0.56f + 0.12f * MathF.Sin(phase * 2.1f);
        Color gold = new Color(228, 176, 84) * (0.52f + pulse * 0.20f);
        Color cyan = new Color(96, 211, 224) * (0.34f + pulse * 0.18f);
        DrawRect(batch, new Rectangle((int)floor.X - 48, (int)floor.Y - 4, 96, 5), gold);
        DrawDiamond(batch, new Vector2(floor.X, floor.Y - 18), 7, cyan);
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
            // 0696D3-A: a dark/brass plinth anchors the machine to the room instead of floating over the floor.
            // 0696D3-B: keep the D3-A grounded footprint but pull visual mass closer to native Stardew scale.
            DrawRect(batch, new Rectangle((int)center.X - 48, (int)center.Y + 9, 96, 16), new Color(49, 34, 31) * 0.92f);
            DrawRect(batch, new Rectangle((int)center.X - 41, (int)center.Y + 7, 82, 6), new Color(177, 118, 57) * 0.78f);
            DrawRect(batch, new Rectangle((int)center.X - 48, (int)center.Y - 49, 96, 64), accent * (0.050f + pulse * 0.032f));
            DrawRect(batch, new Rectangle((int)center.X - 34, (int)center.Y - 38, 68, 47), accent * (0.060f + pulse * 0.040f));
            Rectangle dst = new((int)center.X - 48, (int)center.Y - 64, 96, 96);
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
        // 0696D3-I: map AmbientLight owns general daylight. These are small pixel light pools
        // only at functional anchors, so Room 1 stays readable without a screen-sized wash.
        foreach ((Point tile, Color glow) in new[]
        {
            (new Point(4, 7), new Color(238, 188, 96)),
            (new Point(10, 6), new Color(151, 121, 218)),
            (new Point(17, 8), new Color(91, 220, 211)),
        })
        {
            Vector2 light = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 30f);
            float lightPulse = 0.62f + 0.08f * MathF.Sin(phase * 1.35f + tile.X);
            DrawRect(batch, new Rectangle((int)light.X - 28, (int)light.Y - 16, 56, 32), glow * (0.045f * lightPulse));
            DrawRect(batch, new Rectangle((int)light.X - 13, (int)light.Y - 8, 26, 16), glow * (0.070f * lightPulse));
            DrawDiamond(batch, light, 3, glow * (0.42f + lightPulse * 0.10f));
        }

        // Route board indicator.
        Vector2 route = WorldToScreen(4f * 64f + 32f, 7f * 64f + 10f);
        DrawDiamond(batch, route, 5, new Color(109,210,204) * (0.58f + 0.10f*MathF.Sin(phase*1.6f)));
        // Boarding pad is deliberately bright so the warp trigger is never invisible.
        Vector2 bay = WorldToScreen(17f * 64f + 32f, 7f * 64f + 34f);
        Color teal = new Color(103,221,214);
        DrawRect(batch, new Rectangle((int)bay.X - 30, (int)bay.Y - 7, 60, 3), teal * 0.28f);
        DrawDiamond(batch, bay + new Vector2(0f, -5f), 5, teal * 0.58f);
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

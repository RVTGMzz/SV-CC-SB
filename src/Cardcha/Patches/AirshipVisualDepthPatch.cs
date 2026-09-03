using System.Runtime.CompilerServices;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using Cardcha.Services;

namespace Cardcha.Patches;

/// <summary>
/// Alpha.28.0.4.14.4.5.4 visual-depth pass for the Airship.
///
/// Goals:
/// - keep the locked 384x256 exterior sprite unchanged;
/// - add a rear shadow / ambient silhouette before the real sprite;
/// - add foreground rigging, porthole glow, hull edge shade and small crystal highlights after it;
/// - add real foreground mooring ropes / gangplank framing in Sky Dock;
/// - add side ribs / foreground rail depth inside the Airship Bridge;
/// - preserve all existing gameplay, collisions, warps and the 0634 relocated-gate resolver.
/// </summary>
internal static class AirshipVisualDepthPatch
{
    private const string AirshipVisualPath = "assets/airship_visual.png";
    private static Texture2D? AirshipTexture;
    private static bool TextureLoadFailed;
    private static bool LoggedApply;

    [ModuleInitializer]
    internal static void Initialize()
    {
        Harmony harmony = new("Ronvotri.Cardcha.AirshipVisualDepthPass1");

        var spriteMethod = AccessTools.DeclaredMethod(
            typeof(AirshipFoundationService),
            "TryDrawAirshipSprite",
            new[]
            {
                typeof(SpriteBatch), typeof(Vector2), typeof(float), typeof(Color), typeof(SpriteEffects),
                typeof(float), typeof(float)
            }
        );
        var skyDockMethod = AccessTools.DeclaredMethod(
            typeof(AirshipFoundationService),
            "DrawSkyDockInteriorDetails",
            new[] { typeof(SpriteBatch), typeof(GameLocation) }
        );
        var bridgeMethod = AccessTools.DeclaredMethod(
            typeof(AirshipFoundationService),
            "DrawDeckMarkers",
            new[] { typeof(SpriteBatch), typeof(GameLocation) }
        );

        if (spriteMethod is not null)
        {
            harmony.Patch(
                spriteMethod,
                prefix: new HarmonyMethod(typeof(AirshipVisualDepthPatch), nameof(BeforeAirshipSprite)),
                postfix: new HarmonyMethod(typeof(AirshipVisualDepthPatch), nameof(AfterAirshipSprite))
            );
        }

        if (skyDockMethod is not null)
        {
            harmony.Patch(
                skyDockMethod,
                postfix: new HarmonyMethod(typeof(AirshipVisualDepthPatch), nameof(AfterSkyDockInterior))
            );
        }

        if (bridgeMethod is not null)
        {
            harmony.Patch(
                bridgeMethod,
                postfix: new HarmonyMethod(typeof(AirshipVisualDepthPatch), nameof(AfterBridge))
            );
        }
    }

    private static void BeforeAirshipSprite(
        SpriteBatch batch,
        Vector2 center,
        float targetWidth,
        Color tint,
        SpriteEffects effects,
        float rotation,
        float verticalScale)
    {
        if (AirshipLayeredRenderer.HasLayerAssets())
            return;

        Texture2D? sprite = GetAirshipTexture();
        if (sprite is null || targetWidth <= 0f)
            return;

        LogAppliedOnce();

        float scale = targetWidth / sprite.Width;
        Vector2 origin = new(sprite.Width / 2f, sprite.Height / 2f);
        Vector2 offset = TransformOffset(new Vector2(0f, 8.5f * scale), rotation, verticalScale, effects);

        // Broad rear silhouette. It is deliberately offset down and widened a hair so the real
        // sprite sits visibly in front instead of reading as one flat card pasted onto the sky.
        batch.Draw(
            sprite,
            center + offset,
            null,
            new Color(22, 16, 29) * 0.30f,
            rotation,
            origin,
            new Vector2(scale * 1.022f, scale * Math.Max(0.01f, verticalScale) * 1.018f),
            effects,
            1f
        );

        // Soft balloon backlight. This stays subtle and uses only the vanilla 1px texture.
        Vector2 balloon = center + TransformOffset(new Vector2(18f * scale, -40f * scale), rotation, verticalScale, effects);
        DrawSoftGlow(batch, balloon, Math.Max(10, (int)(58f * scale)), Math.Max(5, (int)(17f * scale)), new Color(102, 212, 238) * 0.075f);
    }

    private static void AfterAirshipSprite(
        bool __result,
        SpriteBatch batch,
        Vector2 center,
        float targetWidth,
        Color tint,
        SpriteEffects effects,
        float rotation,
        float verticalScale)
    {
        if (AirshipLayeredRenderer.HasLayerAssets())
            return;

        Texture2D? sprite = GetAirshipTexture();
        if (!__result || sprite is null || targetWidth <= 0f)
            return;

        float scale = targetWidth / sprite.Width;
        Color ropeShadow = new Color(31, 22, 24) * 0.62f;
        Color rope = new Color(145, 97, 54) * 0.48f;
        Color brass = new Color(224, 170, 80) * 0.47f;
        Color cyan = new Color(92, 224, 246) * 0.70f;
        Color violet = new Color(183, 112, 247) * 0.60f;

        // Foreground rigging. Draw a dark under-stroke then a thinner brass stroke so ropes read as
        // a separate front plane rather than detail baked into the same silhouette.
        (Vector2 A, Vector2 B)[] rigging =
        {
            (new(-83f, -14f), new(-68f, 57f)),
            (new(-43f, -10f), new(-38f, 65f)),
            (new(0f, -7f), new(5f, 66f)),
            (new(43f, -10f), new(47f, 62f)),
            (new(82f, -15f), new(72f, 57f)),
        };
        foreach ((Vector2 a, Vector2 b) in rigging)
        {
            Vector2 start = center + TransformOffset(a * scale, rotation, verticalScale, effects);
            Vector2 end = center + TransformOffset(b * scale, rotation, verticalScale, effects);
            DrawLine(batch, start, end, Math.Max(2f, 2.8f * scale), ropeShadow);
            DrawLine(batch, start, end, Math.Max(1f, 1.15f * scale), rope);
        }

        // Hull keel shadow and brass lip. This is a tiny foreground strip, not a replacement sprite.
        Vector2 keelLeft = center + TransformOffset(new Vector2(-104f, 93f) * scale, rotation, verticalScale, effects);
        Vector2 keelRight = center + TransformOffset(new Vector2(93f, 93f) * scale, rotation, verticalScale, effects);
        DrawLine(batch, keelLeft, keelRight, Math.Max(2f, 4.4f * scale), new Color(25, 18, 22) * 0.50f);
        DrawLine(batch, keelLeft, keelRight, Math.Max(1f, 1.25f * scale), brass);

        // Existing portholes/crystals get independent light, which makes the gondola read forward of
        // the balloon instead of sharing one uniform lighting layer.
        float[] ports = { -104f, -58f, -10f, 38f, 84f };
        foreach (float x in ports)
        {
            Vector2 p = center + TransformOffset(new Vector2(x, 72f) * scale, rotation, verticalScale, effects);
            DrawSoftGlow(batch, p, Math.Max(2, (int)(7f * scale)), Math.Max(1, (int)(3f * scale)), cyan * 0.55f);
        }

        Vector2 cabinGlow = center + TransformOffset(new Vector2(-103f, 46f) * scale, rotation, verticalScale, effects);
        Vector2 coreGlow = center + TransformOffset(new Vector2(13f, 40f) * scale, rotation, verticalScale, effects);
        Vector2 bannerCrystal = center + TransformOffset(new Vector2(34f, 83f) * scale, rotation, verticalScale, effects);
        DrawSoftGlow(batch, cabinGlow, Math.Max(3, (int)(9f * scale)), Math.Max(2, (int)(5f * scale)), cyan * 0.58f);
        DrawSoftGlow(batch, coreGlow, Math.Max(3, (int)(10f * scale)), Math.Max(2, (int)(6f * scale)), cyan * 0.74f);
        DrawDiamond(batch, bannerCrystal, Math.Max(2f, 4f * scale), violet);
    }

    private static void AfterSkyDockInterior(SpriteBatch batch, GameLocation interior)
    {
        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;
        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;
        float phase = (float)(Environment.TickCount64 / 980.0);
        Color outline = new Color(45, 29, 31) * 0.96f;
        Color wood = new Color(119, 73, 47) * 0.92f;
        Color brass = new Color(195, 132, 62) * 0.90f;
        Color cyan = new Color(88, 211, 230) * 0.34f;
        Color violet = new Color(163, 98, 220) * 0.30f;

        // Side-wall service props fill the formerly empty room but deliberately stay out of
        // the center boarding lane, so a post-world overlay never slices across the farmer.
        Vector2 left = Game1.GlobalToLocal(Game1.viewport, new Vector2(3.2f * 64f, (height - 4.0f) * 64f));
        Vector2 leftBack = Game1.GlobalToLocal(Game1.viewport, new Vector2(4.4f * 64f, (height - 6.1f) * 64f));
        Vector2 right = Game1.GlobalToLocal(Game1.viewport, new Vector2((width - 3.4f) * 64f, (height - 4.0f) * 64f));
        DrawDockCrate(batch, left, outline, wood, brass);
        DrawDockCrate(batch, leftBack, outline, wood * 0.88f, brass * 0.82f);
        DrawDockCrate(batch, right, outline, wood, brass);

        Vector2 lampLeft = Game1.GlobalToLocal(Game1.viewport, new Vector2(2.4f * 64f, (height - 7.0f) * 64f));
        Vector2 lampRight = Game1.GlobalToLocal(Game1.viewport, new Vector2((width - 2.4f) * 64f, (height - 7.0f) * 64f));
        DrawServiceLamp(batch, lampLeft, phase, outline, brass, violet);
        DrawServiceLamp(batch, lampRight, -phase, outline, brass, cyan);
    }

    private static void AfterBridge(SpriteBatch batch, GameLocation deck)
    {
        // .5.6.1: intentionally no post-world foreground ribs, rails or hanging cables.
        // Those lines looked like transparent UI drawn over the farmer. Structural depth now
        // comes from the map/window/station masses while the playable center remains clean.
    }

    private static void DrawDockCrate(SpriteBatch batch, Vector2 p, Color outline, Color wood, Color brass)
    {
        Rectangle outer = new((int)p.X - 34, (int)p.Y - 34, 68, 52);
        DrawRect(batch, outer, outline);
        DrawRect(batch, new Rectangle(outer.X + 4, outer.Y + 4, outer.Width - 8, outer.Height - 8), wood);
        DrawRect(batch, new Rectangle(outer.X + 9, outer.Y + 9, outer.Width - 18, 5), brass * 0.72f);
        DrawLine(batch, new Vector2(outer.X + 8, outer.Bottom - 8), new Vector2(outer.Right - 8, outer.Y + 8), 3f, outline * 0.68f);
        DrawLine(batch, new Vector2(outer.Right - 8, outer.Bottom - 8), new Vector2(outer.X + 8, outer.Y + 8), 3f, outline * 0.68f);
    }

    private static void DrawServiceLamp(SpriteBatch batch, Vector2 p, float phase, Color outline, Color brass, Color glow)
    {
        DrawRect(batch, new Rectangle((int)p.X - 5, (int)p.Y - 52, 10, 52), outline);
        DrawRect(batch, new Rectangle((int)p.X - 2, (int)p.Y - 49, 4, 49), brass);
        DrawRect(batch, new Rectangle((int)p.X - 13, (int)p.Y - 68, 26, 18), outline);
        float pulse = 0.58f + 0.14f * MathF.Sin(phase * 2.2f);
        DrawRect(batch, new Rectangle((int)p.X - 8, (int)p.Y - 64, 16, 10), glow * pulse);
    }

    private static Texture2D? GetAirshipTexture()
    {
        if (AirshipTexture is not null)
            return AirshipTexture;
        if (TextureLoadFailed || ModEntry.StaticHelper is null)
            return null;

        try
        {
            AirshipTexture = ModEntry.StaticHelper.ModContent.Load<Texture2D>(AirshipVisualPath);
            return AirshipTexture;
        }
        catch (Exception ex)
        {
            TextureLoadFailed = true;
            ModEntry.StaticMonitor?.Log($"Airship Visual Depth couldn't load locked exterior texture: {ex.Message}", LogLevel.Warn);
            return null;
        }
    }

    private static void LogAppliedOnce()
    {
        if (LoggedApply)
            return;
        LoggedApply = true;
        ModEntry.StaticMonitor?.Log(
            "Airship Visual Depth Pass 1 active: rear silhouette + foreground rigging + dock mooring + bridge ribs.",
            LogLevel.Info
        );
    }

    private static Vector2 TransformOffset(Vector2 offset, float rotation, float verticalScale, SpriteEffects effects)
    {
        if ((effects & SpriteEffects.FlipHorizontally) != SpriteEffects.None)
            offset.X = -offset.X;
        offset.Y *= Math.Max(0.01f, verticalScale);
        float cos = MathF.Cos(rotation);
        float sin = MathF.Sin(rotation);
        return new Vector2(offset.X * cos - offset.Y * sin, offset.X * sin + offset.Y * cos);
    }

    private static void DrawSoftGlow(SpriteBatch batch, Vector2 center, int radiusX, int radiusY, Color color)
    {
        radiusX = Math.Max(2, radiusX);
        radiusY = Math.Max(1, radiusY);
        for (int i = 3; i >= 1; i--)
        {
            float f = i / 3f;
            int rx = Math.Max(1, (int)(radiusX * f));
            int ry = Math.Max(1, (int)(radiusY * f));
            Color c = color * (0.20f + (1f - f) * 0.22f);
            DrawRect(batch, new Rectangle((int)center.X - rx, (int)center.Y - ry, rx * 2 + 1, ry * 2 + 1), c);
        }
    }

    private static void DrawRail(SpriteBatch batch, Vector2 start, Vector2 end, Color dark, Color brass, Color accent)
    {
        DrawLine(batch, start, end, 8f, dark);
        DrawLine(batch, start, end, 3f, brass);
        Vector2 delta = end - start;
        float length = delta.Length();
        if (length < 1f)
            return;
        Vector2 dir = delta / length;
        for (float d = 0; d <= length; d += 62f)
        {
            Vector2 p = start + dir * d;
            DrawRect(batch, new Rectangle((int)p.X - 4, (int)p.Y - 34, 8, 36), dark);
            DrawRect(batch, new Rectangle((int)p.X - 1, (int)p.Y - 31, 3, 31), brass * 0.84f);
            DrawDiamond(batch, p + new Vector2(0f, -36f), 5f, accent);
        }
    }

    private static void DrawDiamond(SpriteBatch batch, Vector2 center, float radius, Color color)
    {
        float r = Math.Max(2f, radius);
        DrawLine(batch, center + new Vector2(0f, -r), center + new Vector2(r, 0f), 2f, color);
        DrawLine(batch, center + new Vector2(r, 0f), center + new Vector2(0f, r), 2f, color);
        DrawLine(batch, center + new Vector2(0f, r), center + new Vector2(-r, 0f), 2f, color);
        DrawLine(batch, center + new Vector2(-r, 0f), center + new Vector2(0f, -r), 2f, color);
    }

    private static void DrawLine(SpriteBatch batch, Vector2 start, Vector2 end, float width, Color color)
    {
        Vector2 delta = end - start;
        float length = delta.Length();
        if (length < 0.5f)
            return;
        batch.Draw(
            Game1.staminaRect,
            start,
            null,
            color,
            MathF.Atan2(delta.Y, delta.X),
            new Vector2(0f, 0.5f),
            new Vector2(length, Math.Max(1f, width)),
            SpriteEffects.None,
            1f
        );
    }

    private static void DrawRect(SpriteBatch batch, Rectangle rect, Color color)
    {
        if (rect.Width > 0 && rect.Height > 0)
            batch.Draw(Game1.staminaRect, rect, color);
    }

    private static Point FindSimpleClear(GameLocation location, Point preferred)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;
        int cx = Math.Clamp(preferred.X, 1, Math.Max(1, width - 2));
        int cy = Math.Clamp(preferred.Y, 1, Math.Max(1, height - 2));
        for (int radius = 0; radius <= 4; radius++)
        {
            for (int y = Math.Max(1, cy - radius); y <= Math.Min(height - 2, cy + radius); y++)
            for (int x = Math.Max(1, cx - radius); x <= Math.Min(width - 2, cx + radius); x++)
            {
                try
                {
                    Vector2 tile = new(x, y);
                    if (!location.IsTileBlockedBy(tile) && !location.Objects.ContainsKey(tile))
                        return new Point(x, y);
                }
                catch
                {
                    return new Point(x, y);
                }
            }
        }
        return new Point(cx, cy);
    }
}

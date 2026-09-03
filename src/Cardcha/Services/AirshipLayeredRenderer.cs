using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Real multi-texture Airship renderer. Every layer is derived from the locked official exterior
/// sprite at build time, so the art stays canonical while runtime gains independent depth planes.
/// </summary>
internal static class AirshipLayeredRenderer
{
    private const string ShadowPath = "assets/airship_layer_shadow.png";
    private const string BalloonPath = "assets/airship_layer_balloon.png";
    private const string HullPath = "assets/airship_layer_hull.png";
    private const string RiggingPath = "assets/airship_layer_rigging.png";
    private const string GlowPath = "assets/airship_layer_glow.png";

    private static Texture2D? Shadow;
    private static Texture2D? Balloon;
    private static Texture2D? Hull;
    private static Texture2D? Rigging;
    private static Texture2D? Glow;
    private static bool LoadFailed;
    private static bool LoggedLoaded;

    public static bool HasLayerAssets()
        => EnsureLoaded();

    public static bool TryDraw(
        SpriteBatch batch,
        Vector2 center,
        float targetWidth,
        Color tint,
        SpriteEffects effects,
        float rotation,
        float verticalScale)
    {
        if (targetWidth <= 0f || !EnsureLoaded() || Balloon is null || Hull is null || Shadow is null || Rigging is null || Glow is null)
            return false;

        float scale = targetWidth / Balloon.Width;
        Vector2 origin = new(Balloon.Width / 2f, Balloon.Height / 2f);
        Vector2 drawScale = new(scale, scale * Math.Max(0.01f, verticalScale));
        float phase = (float)(Environment.TickCount64 / 1000.0);
        float breathe = MathF.Sin(phase * 1.35f) * 1.15f * scale;

        Vector2 shadowOffset = TransformOffset(new Vector2(0f, 8.0f * scale), rotation, verticalScale, effects);
        Vector2 balloonOffset = TransformOffset(new Vector2(0f, -breathe), rotation, verticalScale, effects);
        Vector2 hullOffset = TransformOffset(new Vector2(0f, breathe * 0.45f), rotation, verticalScale, effects);
        Vector2 rigOffset = TransformOffset(new Vector2(0f, breathe * 0.18f), rotation, verticalScale, effects);

        batch.Draw(
            Shadow,
            center + shadowOffset,
            null,
            Color.White * 0.82f,
            rotation,
            origin,
            new Vector2(drawScale.X * 1.018f, drawScale.Y * 1.012f),
            effects,
            1f
        );

        batch.Draw(Balloon, center + balloonOffset, null, tint * 0.99f, rotation, origin, drawScale, effects, 1f);
        batch.Draw(Hull, center + hullOffset, null, tint, rotation, origin, drawScale, effects, 1f);
        batch.Draw(Rigging, center + rigOffset, null, tint * 0.94f, rotation, origin, drawScale, effects, 1f);

        float glowPulse = 0.58f + 0.18f * MathF.Sin(phase * 2.2f);
        batch.Draw(
            Glow,
            center + hullOffset,
            null,
            tint * glowPulse,
            rotation,
            origin,
            drawScale * (1f + 0.003f * MathF.Sin(phase * 1.8f)),
            effects,
            1f
        );
        return true;
    }

    private static bool EnsureLoaded()
    {
        if (Balloon is not null && Hull is not null && Shadow is not null && Rigging is not null && Glow is not null)
            return true;
        if (LoadFailed || ModEntry.StaticHelper is null)
            return false;

        try
        {
            Shadow = ModEntry.StaticHelper.ModContent.Load<Texture2D>(ShadowPath);
            Balloon = ModEntry.StaticHelper.ModContent.Load<Texture2D>(BalloonPath);
            Hull = ModEntry.StaticHelper.ModContent.Load<Texture2D>(HullPath);
            Rigging = ModEntry.StaticHelper.ModContent.Load<Texture2D>(RiggingPath);
            Glow = ModEntry.StaticHelper.ModContent.Load<Texture2D>(GlowPath);
            if (!LoggedLoaded)
            {
                LoggedLoaded = true;
                ModEntry.StaticMonitor?.Log(
                    "Airship layered assets loaded: shadow + balloon + hull + rigging + glow.",
                    LogLevel.Info
                );
            }
            return true;
        }
        catch (Exception ex)
        {
            LoadFailed = true;
            ModEntry.StaticMonitor?.Log(
                $"Airship layered assets unavailable; falling back to locked single sprite. {ex.GetType().Name}: {ex.Message}",
                LogLevel.Warn
            );
            return false;
        }
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
}

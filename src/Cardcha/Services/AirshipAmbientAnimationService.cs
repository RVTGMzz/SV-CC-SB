using Cardcha.Models;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// 0696D1R isolated Window recovery plus existing Console ambient renderer.
/// Window returns to the approved 0690 ownership contract: static physical body in TMX,
/// four independent transparent moving-sky overlays at runtime. D2 will rebuild the
/// season/time/weather matrix only after Ron accepts this bounded source repair.
/// </summary>
internal static class AirshipAmbientAnimationService
{
    private static AirshipAmbientResolver? Resolver;
    private static readonly Dictionary<string, Texture2D?> TextureCache = new(StringComparer.OrdinalIgnoreCase);
    private static readonly HashSet<string> FailedTextureLoads = new(StringComparer.OrdinalIgnoreCase);
    private static long NextLightningAtMs;
    private static long LightningUntilMs;
    private static int LightningVariant;

    // 0696D1R: preserve the approved 0690 contract. The physical Window body is map-native;
    // runtime cycles four independent transparent 160x80 moving-sky overlays. D2 will later
    // rebuild season/time/weather behavior from this accepted clean source.
    private static readonly string[] D1RWindowOverlayPaths =
    {
        "assets/airship_props/set01_redux/observation_window_overlay_1.png",
        "assets/airship_props/set01_redux/observation_window_overlay_2.png",
        "assets/airship_props/set01_redux/observation_window_overlay_3.png",
        "assets/airship_props/set01_redux/observation_window_overlay_4.png",
    };
    private const long D1RWindowFrameDurationMs = 450L;

    public static bool DrawDeckAmbient(SpriteBatch batch)
    {
        if (batch is null || ModEntry.StaticHelper is null || ModEntry.StaticMonitor is null)
            return false;

        Resolver ??= new AirshipAmbientResolver(ModEntry.StaticHelper, ModEntry.StaticMonitor);
        long clockMs = Environment.TickCount64;

        bool window = DrawObservationWindow(batch, clockMs);
        bool console = DrawNavigationConsole(batch, clockMs);
        return window || console;
    }

    private static bool DrawObservationWindow(SpriteBatch batch, long clockMs)
    {
        if (Resolver is null)
            return false;

        AirshipAmbientManifest? manifest = Resolver.Manifest;
        if (manifest is null)
            return false;

        AirshipObservationWindowConfig config = manifest.ObservationWindow;
        Vector2 propTopLeft = WorldToScreen(config.WorldAnchor.TileX * 64f, config.WorldAnchor.TileY * 64f);

        int frameIndex = (int)((clockMs / D1RWindowFrameDurationMs) % D1RWindowOverlayPaths.Length);
        string overlayPath = D1RWindowOverlayPaths[frameIndex];

        // The TMX already owns the full physical body. Draw only one repaired transparent
        // moving-sky overlay. Never crop, repack, shift or hollow the Window body here.
        return DrawLegacyFullOverlay(batch, overlayPath, propTopLeft, depth: 0.8845f);
    }

    private static bool DrawNavigationConsole(SpriteBatch batch, long clockMs)
    {
        if (Resolver is null)
            return false;

        AirshipResolvedConsoleState state = Resolver.ResolveConsole(clockMs);
        AirshipAmbientManifest? manifest = Resolver.Manifest;
        if (manifest is null)
            return false;

        AirshipNavigationConsoleConfig config = manifest.NavigationConsole;
        Vector2 propTopLeft = WorldToScreen(config.WorldAnchor.TileX * 64f, config.WorldAnchor.TileY * 64f);

        if (!state.AmbientAssetsReady)
            return DrawLegacyFullOverlay(batch, state.FallbackOverlayPath, propTopLeft, depth: 0.886f);

        Rectangle viewport = ScaleViewport(config.ViewportPx, propTopLeft);
        DrawConsoleLayer(batch, state.RadarBackground, clockMs, config.ViewportPx, viewport, 0.8848f);
        DrawConsoleLayer(batch, state.RadarGlow, clockMs, config.ViewportPx, viewport, 0.8850f);
        DrawConsoleLayer(batch, state.RadarSweep, clockMs, config.ViewportPx, viewport, 0.8852f);
        DrawConsoleLayer(batch, state.RadarPings, clockMs, config.ViewportPx, viewport, 0.8854f);

        if (Resolver.AssetExists(config.Frame.Path))
        {
            Texture2D? frame = GetTexture(config.Frame.Path);
            if (frame is not null)
            {
                batch.Draw(
                    frame,
                    new Rectangle((int)propTopLeft.X, (int)propTopLeft.Y, frame.Width * 4, frame.Height * 4),
                    null,
                    Color.White,
                    0f,
                    Vector2.Zero,
                    SpriteEffects.None,
                    0.8858f
                );
            }
        }
        return true;
    }

    private static void DrawConsoleLayer(
        SpriteBatch batch,
        AirshipAnimationAssetConfig? animation,
        long clockMs,
        AirshipViewportConfig sourceViewport,
        Rectangle destination,
        float depth
    )
    {
        if (Resolver is null || animation is null || !Resolver.AssetExists(animation.Path))
            return;

        Texture2D? texture = GetTexture(animation.Path);
        if (texture is null)
            return;

        int frame = AirshipAmbientResolver.ResolveAnimationFrame(animation, clockMs);
        DrawViewportStripFrame(batch, texture, Math.Max(1, animation.FrameCount), frame, sourceViewport, destination, depth);
    }

    private static void DrawLightningIfActive(
        SpriteBatch batch,
        AirshipObservationWindowConfig config,
        Vector2 propTopLeft,
        long clockMs
    )
    {
        if (Resolver is null || config.Lightning.Paths.Count == 0)
            return;

        if (NextLightningAtMs <= 0)
            NextLightningAtMs = clockMs + Math.Max(500, config.Lightning.MinIntervalMs);

        if (clockMs >= NextLightningAtMs && clockMs >= LightningUntilMs)
        {
            int min = Math.Max(500, config.Lightning.MinIntervalMs);
            int max = Math.Max(min + 1, config.Lightning.MaxIntervalMs);
            int interval = Random.Shared.Next(min, max);
            LightningVariant = Random.Shared.Next(config.Lightning.Paths.Count);
            LightningUntilMs = clockMs + Math.Max(40, config.Lightning.FlashDurationMs);
            NextLightningAtMs = clockMs + interval;
        }

        if (clockMs >= LightningUntilMs)
            return;

        string path = config.Lightning.Paths[Math.Clamp(LightningVariant, 0, config.Lightning.Paths.Count - 1)];
        if (!Resolver.AssetExists(path))
            return;
        Texture2D? flash = GetTexture(path);
        if (flash is null)
            return;

        batch.Draw(
            flash,
            new Rectangle((int)propTopLeft.X, (int)propTopLeft.Y, config.FootprintPx.Width * 4, config.FootprintPx.Height * 4),
            null,
            Color.White,
            0f,
            Vector2.Zero,
            SpriteEffects.None,
            0.8840f
        );
    }

    private static bool DrawLegacyFullOverlay(SpriteBatch batch, string? path, Vector2 propTopLeft, float depth)
    {
        Texture2D? texture = GetTexture(path);
        if (texture is null)
            return false;
        batch.Draw(
            texture,
            new Rectangle((int)propTopLeft.X, (int)propTopLeft.Y, texture.Width * 4, texture.Height * 4),
            null,
            Color.White,
            0f,
            Vector2.Zero,
            SpriteEffects.None,
            depth
        );
        return true;
    }

    private static Rectangle ScaleViewport(AirshipViewportConfig source, Vector2 propTopLeft)
    {
        return new Rectangle(
            (int)propTopLeft.X + source.X * 4,
            (int)propTopLeft.Y + source.Y * 4,
            source.Width * 4,
            source.Height * 4
        );
    }

    private static void DrawViewportTexture(
        SpriteBatch batch,
        Texture2D texture,
        AirshipViewportConfig viewport,
        Rectangle destination,
        float depth
    )
    {
        Rectangle? source = ResolveViewportSource(texture, viewport);
        batch.Draw(texture, destination, source, Color.White, 0f, Vector2.Zero, SpriteEffects.None, depth);
    }

    private static void DrawViewportStripFrame(
        SpriteBatch batch,
        Texture2D strip,
        int frameCount,
        int frameIndex,
        AirshipViewportConfig viewport,
        Rectangle destination,
        float depth
    )
    {
        frameCount = Math.Max(1, frameCount);
        frameIndex = Math.Clamp(frameIndex, 0, frameCount - 1);
        int frameWidth = strip.Width / frameCount;
        if (frameWidth <= 0)
            return;

        Rectangle frameRect = new(frameIndex * frameWidth, 0, frameWidth, strip.Height);
        Rectangle source;
        if (frameWidth == viewport.Width && strip.Height == viewport.Height)
        {
            source = frameRect;
        }
        else if (frameWidth >= viewport.X + viewport.Width && strip.Height >= viewport.Y + viewport.Height)
        {
            source = new Rectangle(frameRect.X + viewport.X, viewport.Y, viewport.Width, viewport.Height);
        }
        else
        {
            source = frameRect;
        }
        batch.Draw(strip, destination, source, Color.White, 0f, Vector2.Zero, SpriteEffects.None, depth);
    }

    private static Rectangle? ResolveViewportSource(Texture2D texture, AirshipViewportConfig viewport)
    {
        if (texture.Width == viewport.Width && texture.Height == viewport.Height)
            return null;
        if (texture.Width >= viewport.X + viewport.Width && texture.Height >= viewport.Y + viewport.Height)
            return new Rectangle(viewport.X, viewport.Y, viewport.Width, viewport.Height);
        return null;
    }

    private static Texture2D? GetTexture(string? path)
    {
        if (string.IsNullOrWhiteSpace(path) || ModEntry.StaticHelper is null)
            return null;

        if (TextureCache.TryGetValue(path, out Texture2D? cached))
        {
            if (cached is not null && !cached.IsDisposed)
                return cached;
            TextureCache.Remove(path);
        }
        if (FailedTextureLoads.Contains(path))
            return null;

        try
        {
            Texture2D texture = ModEntry.StaticHelper.ModContent.Load<Texture2D>(path);
            TextureCache[path] = texture;
            return texture;
        }
        catch
        {
            FailedTextureLoads.Add(path);
            return null;
        }
    }

    private static Vector2 WorldToScreen(float worldX, float worldY)
    {
        return new Vector2(worldX - Game1.viewport.X, worldY - Game1.viewport.Y);
    }
}

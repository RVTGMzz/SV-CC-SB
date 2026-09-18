using Cardcha.Models;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// 0696D3-G transient Window/radar ambience.
/// Physical Window and console bodies are map-native. Runtime owns only environment/motion slices:
/// the moving airship, approved Window environment, and radar glow/sweep/pings.
/// The console frame/body is never replayed as a runtime full-prop overlay.
/// </summary>
internal static class AirshipAmbientAnimationService
{
    private static AirshipAmbientResolver? Resolver;
    private static readonly Dictionary<string, Texture2D?> TextureCache = new(StringComparer.OrdinalIgnoreCase);
    private static readonly HashSet<string> FailedTextureLoads = new(StringComparer.OrdinalIgnoreCase);
    private static long NextLightningAtMs;
    private static long LightningUntilMs;
    private static int LightningVariant;

    // 0696D1S: the four legacy Window overlays are NOT four airship frames.
    // Only this extracted airship sprite moves. The Window frame/body stays map-native.
    private const string D1SAirshipPath =
        "assets/airship_props/set01_redux/window_runtime/observation_window_airship.png";
    private static readonly Point[] D1SAirshipPositions =
    {
        new(62, 33),
        new(71, 33),
        new(80, 33),
        new(89, 33),
    };
    private const long D1SAirshipFrameDurationMs = 550L;
    // 0696D3-H: exact TMX footprint. The old 4.25x overscan made the Window read detached from the wall
    // and could visually bleed beyond its architectural frame.
    private const float ObservationWindowPresentationScale = 4.0f;

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

        // 0696D2: resolve one approved clear 160x80 environment from Game1.timeOfDay.
        // The accepted .68 airship stays independent and is drawn above the environment.
        AirshipResolvedWindowState state = Resolver.ResolveWindow(clockMs);
        if (state.AmbientAssetsReady && !string.IsNullOrWhiteSpace(state.BackdropPath))
        {
            Texture2D? environment = GetTexture(state.BackdropPath);
            if (environment is not null && environment.Width == 160 && environment.Height == 80)
            {
                Rectangle environmentPresentation = ResolveObservationWindowPresentation(config, propTopLeft);
                batch.Draw(
                    environment,
                    environmentPresentation,
                    null,
                    Color.White,
                    0f,
                    Vector2.Zero,
                    SpriteEffects.None,
                    0.8840f
                );
            }
        }

        Texture2D? airship = GetTexture(D1SAirshipPath);
        if (airship is null)
            return state.AmbientAssetsReady;

        int frameIndex = (int)((clockMs / D1SAirshipFrameDurationMs) % D1SAirshipPositions.Length);
        Point pos = D1SAirshipPositions[frameIndex];
        Rectangle presentation = ResolveObservationWindowPresentation(config, propTopLeft);
        float presentationScale = presentation.Width / (float)Math.Max(1, config.FootprintPx.Width);
        batch.Draw(
            airship,
            new Rectangle(
                presentation.X + (int)MathF.Round(pos.X * presentationScale),
                presentation.Y + (int)MathF.Round(pos.Y * presentationScale),
                (int)MathF.Round(airship.Width * presentationScale),
                (int)MathF.Round(airship.Height * presentationScale)
            ),
            null,
            Color.White,
            0f,
            Vector2.Zero,
            SpriteEffects.None,
            0.8845f
        );
        return true;
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

        // 0696D3-G runtime authority: never resurrect a full console body here.
        // If ambient slices are unavailable, the transparent TMX console remains clean.
        if (!state.AmbientAssetsReady)
            return false;

        Rectangle viewport = ScaleViewport(config.ViewportPx, propTopLeft);
        // Keep only animated glow/sweep/pings over the map-native transparent console body.
        DrawConsoleLayer(batch, state.RadarGlow, clockMs, config.ViewportPx, viewport, 0.8850f);
        DrawConsoleLayer(batch, state.RadarSweep, clockMs, config.ViewportPx, viewport, 0.8852f);
        DrawConsoleLayer(batch, state.RadarPings, clockMs, config.ViewportPx, viewport, 0.8854f);

        // 0696D3-G: console frame/body is authored into TMX using the transparent
        // navigation_console_body_d3g.png asset. Runtime owns only radar animation.
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
            ResolveObservationWindowPresentation(config, propTopLeft),
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

    private static Rectangle ResolveObservationWindowPresentation(
        AirshipObservationWindowConfig config,
        Vector2 propTopLeft
    )
    {
        int baseWidth = config.FootprintPx.Width * 4;
        int baseHeight = config.FootprintPx.Height * 4;
        int width = (int)MathF.Round(config.FootprintPx.Width * ObservationWindowPresentationScale);
        int height = (int)MathF.Round(config.FootprintPx.Height * ObservationWindowPresentationScale);
        return new Rectangle(
            (int)propTopLeft.X - (width - baseWidth) / 2,
            (int)propTopLeft.Y - (height - baseHeight) / 2,
            width,
            height
        );
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

using Cardcha.Models;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Services;

internal sealed record AirshipResolvedWindowState(
    string Season,
    string TimeBucket,
    string Weather,
    string? BackdropPath,
    AirshipAnimationAssetConfig? WeatherFx,
    bool AmbientAssetsReady,
    string? FallbackOverlayPath
);

internal sealed record AirshipResolvedConsoleState(
    bool AmbientAssetsReady,
    AirshipAnimationAssetConfig? RadarBackground,
    AirshipAnimationAssetConfig? RadarSweep,
    AirshipAnimationAssetConfig? RadarPings,
    AirshipAnimationAssetConfig? RadarGlow,
    string? FallbackOverlayPath
);

/// <summary>
/// 0696D2 source-of-truth resolver for the clear-time Airship Window environments.
/// Observation Window D2 state resolves four approved clear environments by time bucket.
/// Drawing remains isolated in AirshipAmbientAnimationService.
/// </summary>
internal sealed class AirshipAmbientResolver
{
    internal const string ManifestPath = "assets/airship_props/set01_redux/airship_ambient_manifest.json";

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private AirshipAmbientManifest? CachedManifest;
    private bool ManifestLoadAttempted;
    private readonly HashSet<string> LoggedMissing = new(StringComparer.OrdinalIgnoreCase);

    public AirshipAmbientResolver(IModHelper helper, IMonitor monitor)
    {
        this.Helper = helper;
        this.Monitor = monitor;
    }

    public AirshipAmbientManifest? Manifest => this.GetManifest();

    public AirshipResolvedWindowState ResolveWindow(long clockMs)
    {
        AirshipAmbientManifest? manifest = this.GetManifest();
        if (manifest is null || !manifest.ObservationWindow.Enabled)
            return new("default", "noon", "clear", null, null, false, null);

        string season = NormalizeSeason(Game1.currentSeason);
        string timeBucket = ResolveTimeBucket(manifest.Global, Game1.timeOfDay);
        string weather = ResolveWeather();
        string? scene = this.ResolveScenePath(manifest.ObservationWindow.SceneMatrix, season, timeBucket, weather);

        // 0696B compatibility only. A schema-1 manifest can still resolve its old backdrop map.
        if (string.IsNullOrWhiteSpace(scene))
            scene = this.ResolveBackdropPath(manifest.ObservationWindow.Backdrops, season, timeBucket);

        manifest.ObservationWindow.WeatherFx.TryGetValue(weather, out AirshipAnimationAssetConfig? weatherFx);

        bool ambientReady =
            this.AssetExists(manifest.ObservationWindow.Frame.Path, required: manifest.ObservationWindow.Frame.RequiredForAmbientMode)
            && !string.IsNullOrWhiteSpace(scene)
            && this.AssetExists(scene, required: true);

        string? fallback = ResolveLegacyFrame(manifest.ObservationWindow.LegacyFallback, clockMs);
        return new(season, timeBucket, weather, scene, weatherFx, ambientReady, fallback);
    }

    public AirshipResolvedConsoleState ResolveConsole(long clockMs)
    {
        AirshipAmbientManifest? manifest = this.GetManifest();
        if (manifest is null || !manifest.NavigationConsole.Enabled)
            return new(false, null, null, null, null, null);

        Dictionary<string, AirshipAnimationAssetConfig> layers = manifest.NavigationConsole.Layers;
        layers.TryGetValue("radarBg", out AirshipAnimationAssetConfig? bg);
        layers.TryGetValue("radarSweep", out AirshipAnimationAssetConfig? sweep);
        layers.TryGetValue("radarPings", out AirshipAnimationAssetConfig? pings);
        layers.TryGetValue("radarGlow", out AirshipAnimationAssetConfig? glow);

        bool requiredSweepReady = sweep is not null && this.AssetExists(sweep.Path, required: !sweep.Optional);
        bool frameReady = !manifest.NavigationConsole.Frame.RequiredForAmbientMode
            || this.AssetExists(manifest.NavigationConsole.Frame.Path, required: true);
        bool ambientReady = requiredSweepReady && frameReady;

        string? fallback = ResolveLegacyFrame(manifest.NavigationConsole.LegacyFallback, clockMs);
        return new(ambientReady, bg, sweep, pings, glow, fallback);
    }

    public bool AssetExists(string? relativePath, bool required = false)
    {
        if (string.IsNullOrWhiteSpace(relativePath))
            return false;

        string normalized = relativePath.Replace('/', Path.DirectorySeparatorChar);
        string fullPath = Path.Combine(this.Helper.DirectoryPath, normalized);
        bool exists = File.Exists(fullPath);
        if (!exists && required && this.LoggedMissing.Add(relativePath))
            this.Monitor.Log($"0696C ambient asset pending: {relativePath}.", LogLevel.Trace);
        return exists;
    }

    public static string ResolveTimeBucket(AirshipAmbientGlobalConfig global, int timeOfDay)
    {
        int comparable = timeOfDay < 600 ? timeOfDay + 2400 : timeOfDay;
        foreach ((string key, AirshipTimeBucketConfig range) in global.TimeBuckets)
        {
            if (comparable >= range.Start && comparable <= range.End)
                return key.ToLowerInvariant();
        }
        return "night";
    }

    public static string ResolveWeather()
    {
        if (Game1.isLightning)
            return "storm";
        if (Game1.isSnowing)
            return "snow";
        if (Game1.isRaining)
            return "rain";
        return "clear";
    }

    public static int ResolveAnimationFrame(AirshipAnimationAssetConfig animation, long clockMs)
    {
        if (animation.FrameCount <= 1 || animation.FrameDurationMs <= 0)
            return 0;
        return (int)((clockMs / animation.FrameDurationMs) % animation.FrameCount);
    }

    private AirshipAmbientManifest? GetManifest()
    {
        if (this.CachedManifest is not null)
            return this.CachedManifest;
        if (this.ManifestLoadAttempted)
            return null;

        this.ManifestLoadAttempted = true;
        try
        {
            this.CachedManifest = this.Helper.Data.ReadJsonFile<AirshipAmbientManifest>(ManifestPath);
            if (this.CachedManifest is null)
            {
                this.Monitor.Log($"0696C ambient manifest returned null: {ManifestPath}", LogLevel.Warn);
                return null;
            }

            ValidateManifest(this.CachedManifest);
            this.Monitor.Log(
                $"0696C Airship ambient manifest loaded: schema={this.CachedManifest.SchemaVersion}, version={this.CachedManifest.Version}, acceptance={this.CachedManifest.VisualAcceptance}.",
                LogLevel.Trace
            );
            return this.CachedManifest;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"0696C ambient manifest load failed. Static TMX hero art remains visible. {ex.Message}", LogLevel.Warn);
            return null;
        }
    }

    private string? ResolveScenePath(AirshipWindowSceneMatrixConfig config, string season, string timeBucket, string weather)
    {
        // Exact authored state is always preferred.
        if (TryResolveScene(config.States, season, timeBucket, weather, out string? exact) && this.AssetExists(exact))
            return exact;

        // Same time+weather but default season keeps weather semantics intact.
        if (TryResolveScene(config.States, config.FallbackSeason, timeBucket, weather, out string? defaultSeason) && this.AssetExists(defaultSeason))
            return defaultSeason;

        // Same season+time, clear weather is safer than silently changing time of day.
        if (TryResolveScene(config.States, season, timeBucket, config.FallbackWeather, out string? seasonClear) && this.AssetExists(seasonClear))
            return seasonClear;

        if (TryResolveScene(config.States, config.FallbackSeason, timeBucket, config.FallbackWeather, out string? defaultClear) && this.AssetExists(defaultClear))
            return defaultClear;

        // Last-resort authored fallback, still explicit in the manifest.
        if (TryResolveScene(config.States, season, config.FallbackTime, config.FallbackWeather, out string? seasonFallback) && this.AssetExists(seasonFallback))
            return seasonFallback;

        if (TryResolveScene(config.States, config.FallbackSeason, config.FallbackTime, config.FallbackWeather, out string? finalFallback))
            return finalFallback;

        return null;
    }

    private static bool TryResolveScene(
        Dictionary<string, Dictionary<string, Dictionary<string, string>>> states,
        string season,
        string bucket,
        string weather,
        out string? path
    )
    {
        path = null;
        if (!states.TryGetValue(season, out Dictionary<string, Dictionary<string, string>>? seasonStates))
            return false;
        if (!seasonStates.TryGetValue(bucket, out Dictionary<string, string>? timeStates))
            return false;
        if (!timeStates.TryGetValue(weather, out string? value) || string.IsNullOrWhiteSpace(value))
            return false;
        path = value;
        return true;
    }

    private string? ResolveBackdropPath(AirshipBackdropConfig config, string season, string timeBucket)
    {
        if (TryResolveBackdrop(config.States, season, timeBucket, out string? exact) && this.AssetExists(exact))
            return exact;
        if (TryResolveBackdrop(config.States, config.FallbackSeason, timeBucket, out string? defaultTime) && this.AssetExists(defaultTime))
            return defaultTime;
        if (TryResolveBackdrop(config.States, season, config.FallbackTime, out string? seasonFallback) && this.AssetExists(seasonFallback))
            return seasonFallback;
        if (TryResolveBackdrop(config.States, config.FallbackSeason, config.FallbackTime, out string? finalFallback))
            return finalFallback;
        return null;
    }

    private static bool TryResolveBackdrop(
        Dictionary<string, Dictionary<string, string>> states,
        string season,
        string bucket,
        out string? path
    )
    {
        path = null;
        if (!states.TryGetValue(season, out Dictionary<string, string>? seasonStates))
            return false;
        if (!seasonStates.TryGetValue(bucket, out string? value) || string.IsNullOrWhiteSpace(value))
            return false;
        path = value;
        return true;
    }

    private static string? ResolveLegacyFrame(AirshipLegacyFallbackConfig fallback, long clockMs)
    {
        if (!fallback.Enabled || fallback.Paths.Count == 0)
            return null;
        int duration = Math.Max(1, fallback.FrameDurationMs);
        int index = (int)((clockMs / duration) % fallback.Paths.Count);
        return fallback.Paths[index];
    }

    private static string NormalizeSeason(string? season)
    {
        return season?.ToLowerInvariant() switch
        {
            "spring" => "spring",
            "summer" => "summer",
            "fall" => "fall",
            "winter" => "winter",
            _ => "default",
        };
    }

    private static void ValidateManifest(AirshipAmbientManifest manifest)
    {
        if (manifest.SchemaVersion is not (1 or 2))
            throw new InvalidOperationException($"Unsupported Airship ambient schema {manifest.SchemaVersion}.");
        if (manifest.Global.TileSize != 16)
            throw new InvalidOperationException("Airship ambient contract must preserve Stardew 16px source tiles.");
        if (manifest.ObservationWindow.FootprintPx.Width != 160 || manifest.ObservationWindow.FootprintPx.Height != 80)
            throw new InvalidOperationException("Observation Window footprint drifted from 160x80.");
        if (manifest.NavigationConsole.FootprintPx.Width != 112 || manifest.NavigationConsole.FootprintPx.Height != 80)
            throw new InvalidOperationException("Navigation Console footprint drifted from 112x80.");
        if (!string.Equals(manifest.Validation.CollisionOwnedBy, "Buildings", StringComparison.Ordinal))
            throw new InvalidOperationException("0696C collision must remain owned by base Buildings.");
        if (!manifest.Validation.ForbiddenLayers.Contains("BackDecor", StringComparer.OrdinalIgnoreCase))
            throw new InvalidOperationException("0696C contract must explicitly forbid BackDecor.");
        if (manifest.SchemaVersion >= 2 && manifest.ObservationWindow.SceneMatrix.States.Count == 0)
            throw new InvalidOperationException("0696C requires an explicit season/time/weather scene matrix.");
    }
}

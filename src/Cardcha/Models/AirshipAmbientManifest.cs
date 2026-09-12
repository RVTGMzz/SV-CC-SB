using Newtonsoft.Json;

namespace Cardcha.Models;

internal sealed class AirshipAmbientManifest
{
    [JsonProperty("schemaVersion")]
    public int SchemaVersion { get; set; }

    [JsonProperty("workstream")]
    public string Workstream { get; set; } = string.Empty;

    [JsonProperty("version")]
    public string Version { get; set; } = string.Empty;

    [JsonProperty("visualAcceptance")]
    public string VisualAcceptance { get; set; } = string.Empty;

    [JsonProperty("assetRoot")]
    public string AssetRoot { get; set; } = string.Empty;

    [JsonProperty("global")]
    public AirshipAmbientGlobalConfig Global { get; set; } = new();

    [JsonProperty("observationWindow")]
    public AirshipObservationWindowConfig ObservationWindow { get; set; } = new();

    [JsonProperty("navigationConsole")]
    public AirshipNavigationConsoleConfig NavigationConsole { get; set; } = new();

    [JsonProperty("validation")]
    public AirshipAmbientValidationConfig Validation { get; set; } = new();
}

internal sealed class AirshipAmbientGlobalConfig
{
    [JsonProperty("tileSize")]
    public int TileSize { get; set; } = 16;

    [JsonProperty("timeBuckets")]
    public Dictionary<string, AirshipTimeBucketConfig> TimeBuckets { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    [JsonProperty("weatherPriority")]
    public List<string> WeatherPriority { get; set; } = new();
}

internal sealed class AirshipTimeBucketConfig
{
    [JsonProperty("start")]
    public int Start { get; set; }

    [JsonProperty("end")]
    public int End { get; set; }
}

internal sealed class AirshipSizeConfig
{
    [JsonProperty("width")]
    public int Width { get; set; }

    [JsonProperty("height")]
    public int Height { get; set; }
}

internal sealed class AirshipAnchorConfig
{
    [JsonProperty("map")]
    public string Map { get; set; } = string.Empty;

    [JsonProperty("tileX")]
    public int TileX { get; set; }

    [JsonProperty("tileY")]
    public int TileY { get; set; }
}

internal sealed class AirshipViewportConfig
{
    [JsonProperty("x")]
    public int X { get; set; }

    [JsonProperty("y")]
    public int Y { get; set; }

    [JsonProperty("width")]
    public int Width { get; set; }

    [JsonProperty("height")]
    public int Height { get; set; }
}

internal sealed class AirshipStaticAssetConfig
{
    [JsonProperty("path")]
    public string Path { get; set; } = string.Empty;

    [JsonProperty("requiredForAmbientMode")]
    public bool RequiredForAmbientMode { get; set; }

    [JsonProperty("expectedWidth")]
    public int ExpectedWidth { get; set; }

    [JsonProperty("expectedHeight")]
    public int ExpectedHeight { get; set; }
}

internal sealed class AirshipAnimationAssetConfig
{
    [JsonProperty("path")]
    public string Path { get; set; } = string.Empty;

    [JsonProperty("frameCount")]
    public int FrameCount { get; set; } = 1;

    [JsonProperty("frameDurationMs")]
    public int FrameDurationMs { get; set; }

    [JsonProperty("optional")]
    public bool Optional { get; set; }
}

/// <summary>
/// 0696C: explicit outside-scene lookup. The scene key is no longer just season+time;
/// weather is part of the authored scene identity so rainy evening, stormy night, etc.
/// can have their own sky palette before moving FX are layered on top.
/// states[season][timeBucket][weather] = asset path.
/// </summary>
internal sealed class AirshipWindowSceneMatrixConfig
{
    [JsonProperty("fallbackSeason")]
    public string FallbackSeason { get; set; } = "default";

    [JsonProperty("fallbackTime")]
    public string FallbackTime { get; set; } = "noon";

    [JsonProperty("fallbackWeather")]
    public string FallbackWeather { get; set; } = "clear";

    [JsonProperty("states")]
    public Dictionary<string, Dictionary<string, Dictionary<string, string>>> States { get; set; }
        = new(StringComparer.OrdinalIgnoreCase);
}

/// <summary>0696B compatibility only. 0696C production resolves SceneMatrix first.</summary>
internal sealed class AirshipBackdropConfig
{
    [JsonProperty("fallbackSeason")]
    public string FallbackSeason { get; set; } = "default";

    [JsonProperty("fallbackTime")]
    public string FallbackTime { get; set; } = "noon";

    [JsonProperty("states")]
    public Dictionary<string, Dictionary<string, string>> States { get; set; } = new(StringComparer.OrdinalIgnoreCase);
}

internal sealed class AirshipLightningConfig
{
    [JsonProperty("paths")]
    public List<string> Paths { get; set; } = new();

    [JsonProperty("minIntervalMs")]
    public int MinIntervalMs { get; set; } = 2500;

    [JsonProperty("maxIntervalMs")]
    public int MaxIntervalMs { get; set; } = 7000;

    [JsonProperty("flashDurationMs")]
    public int FlashDurationMs { get; set; } = 120;

    [JsonProperty("optional")]
    public bool Optional { get; set; } = true;
}

internal sealed class AirshipLegacyFallbackConfig
{
    [JsonProperty("enabled")]
    public bool Enabled { get; set; } = true;

    [JsonProperty("frameDurationMs")]
    public int FrameDurationMs { get; set; } = 900;

    [JsonProperty("paths")]
    public List<string> Paths { get; set; } = new();
}

internal sealed class AirshipObservationWindowConfig
{
    [JsonProperty("id")]
    public string Id { get; set; } = string.Empty;

    [JsonProperty("enabled")]
    public bool Enabled { get; set; } = true;

    [JsonProperty("productionStatus")]
    public string ProductionStatus { get; set; } = string.Empty;

    [JsonProperty("footprintPx")]
    public AirshipSizeConfig FootprintPx { get; set; } = new();

    [JsonProperty("footprintTiles")]
    public AirshipSizeConfig FootprintTiles { get; set; } = new();

    [JsonProperty("worldAnchor")]
    public AirshipAnchorConfig WorldAnchor { get; set; } = new();

    [JsonProperty("viewportPx")]
    public AirshipViewportConfig ViewportPx { get; set; } = new();

    [JsonProperty("frame")]
    public AirshipStaticAssetConfig Frame { get; set; } = new();

    [JsonProperty("mask")]
    public AirshipStaticAssetConfig Mask { get; set; } = new();

    [JsonProperty("sceneMatrix")]
    public AirshipWindowSceneMatrixConfig SceneMatrix { get; set; } = new();

    [JsonProperty("backdrops")]
    public AirshipBackdropConfig Backdrops { get; set; } = new();

    [JsonProperty("weatherFx")]
    public Dictionary<string, AirshipAnimationAssetConfig> WeatherFx { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    [JsonProperty("lightning")]
    public AirshipLightningConfig Lightning { get; set; } = new();

    [JsonProperty("legacyFallback")]
    public AirshipLegacyFallbackConfig LegacyFallback { get; set; } = new();
}

internal sealed class AirshipNavigationConsoleConfig
{
    [JsonProperty("id")]
    public string Id { get; set; } = string.Empty;

    [JsonProperty("enabled")]
    public bool Enabled { get; set; } = true;

    [JsonProperty("productionStatus")]
    public string ProductionStatus { get; set; } = string.Empty;

    [JsonProperty("footprintPx")]
    public AirshipSizeConfig FootprintPx { get; set; } = new();

    [JsonProperty("footprintTiles")]
    public AirshipSizeConfig FootprintTiles { get; set; } = new();

    [JsonProperty("worldAnchor")]
    public AirshipAnchorConfig WorldAnchor { get; set; } = new();

    [JsonProperty("viewportPx")]
    public AirshipViewportConfig ViewportPx { get; set; } = new();

    [JsonProperty("frame")]
    public AirshipStaticAssetConfig Frame { get; set; } = new();

    [JsonProperty("layers")]
    public Dictionary<string, AirshipAnimationAssetConfig> Layers { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    [JsonProperty("legacyFallback")]
    public AirshipLegacyFallbackConfig LegacyFallback { get; set; } = new();
}

internal sealed class AirshipAmbientValidationConfig
{
    [JsonProperty("preserveFootprint")]
    public bool PreserveFootprint { get; set; } = true;

    [JsonProperty("preserveCollisionContract")]
    public bool PreserveCollisionContract { get; set; } = true;

    [JsonProperty("collisionOwnedBy")]
    public string CollisionOwnedBy { get; set; } = "Buildings";

    [JsonProperty("forbiddenLayers")]
    public List<string> ForbiddenLayers { get; set; } = new();

    [JsonProperty("requiredMapLayers")]
    public List<string> RequiredMapLayers { get; set; } = new();

    [JsonProperty("noSilentSubstitution")]
    public bool NoSilentSubstitution { get; set; } = true;
}

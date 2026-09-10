namespace Cardcha.Services;

/// <summary>
/// Runtime-only summary of a Region II Forgotten Archive run.
/// It is handed to Hollow Curator at the Archive Seal and deliberately is not persisted,
/// so the boss reflects the run the player just completed without changing save schema.
/// </summary>
internal sealed class CuratorRunRecord
{
    public string Tag { get; }
    public int Risk { get; }
    public int Precision { get; }
    public int Pressure { get; }
    public int Recovery { get; }
    public int Mirror { get; }
    public int NodesReached { get; }
    public bool DebugMode { get; }

    public CuratorRunRecord(string tag, int risk, int precision, int pressure, int recovery, int mirror, int nodesReached, bool debugMode = false)
    {
        this.Tag = NormalizeTag(tag);
        this.Risk = Math.Max(0, risk);
        this.Precision = Math.Max(0, precision);
        this.Pressure = Math.Max(0, pressure);
        this.Recovery = Math.Max(0, recovery);
        this.Mirror = Math.Max(0, mirror);
        this.NodesReached = Math.Max(0, nodesReached);
        this.DebugMode = debugMode;
    }

    public static CuratorRunRecord Neutral => new("neutral", 0, 0, 0, 0, 0, 0);

    public static CuratorRunRecord Debug(string? tag)
    {
        string normalized = NormalizeTag(tag);
        return normalized switch
        {
            "risk" => new(normalized, 4, 1, 1, 0, 0, 6, true),
            "precision" => new(normalized, 0, 4, 0, 0, 0, 6, true),
            "pressure" => new(normalized, 1, 0, 4, 0, 0, 6, true),
            "recovery" => new(normalized, 0, 0, 1, 4, 0, 6, true),
            "mirror" => new(normalized, 0, 1, 0, 0, 4, 6, true),
            _ => new("neutral", 0, 0, 0, 0, 0, 6, true),
        };
    }

    public string Describe()
        => $"tag={this.Tag}, nodes={this.NodesReached}, risk={this.Risk}, precision={this.Precision}, pressure={this.Pressure}, recovery={this.Recovery}, mirror={this.Mirror}, debug={this.DebugMode}";

    private static string NormalizeTag(string? tag)
    {
        string value = (tag ?? "neutral").Trim().ToLowerInvariant();
        return value is "risk" or "precision" or "pressure" or "recovery" or "mirror" ? value : "neutral";
    }
}

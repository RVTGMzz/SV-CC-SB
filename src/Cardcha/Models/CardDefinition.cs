namespace Cardcha.Models;

internal sealed class CardDefinition
{
    /// <summary>Stable public/wiki number for the Base Set. Zero means derive from IconIndex + 1.</summary>
    public int BaseId { get; set; }

    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public CardRarity Rarity { get; set; }
    public string Build { get; set; } = "";
    public string EffectKey { get; set; } = "";
    public double Value { get; set; }
    public string Description { get; set; } = "";

    /// <summary>
    /// Zero-based cell index in assets/card_icons.png.
    /// Base Set convention: IconIndex = BaseId - 1.
    /// </summary>
    public int IconIndex { get; set; } = -1;

    /// <summary>
    /// Visual-test metadata used by the 80-card atlas. When false, the atlas art should be preferred.
    /// </summary>
    public bool UseInitialFallback { get; set; } = true;

    /// <summary>Maximum upgrade level for this card (1-5).</summary>
    public int MaxLevel { get; set; } = 1;

    /// <summary>
    /// Multiplicative power gain per extra level for generic/prototype effects.
    /// </summary>
    public double LevelStep { get; set; } = 0.25;

    /// <summary>
    /// Human-readable per-star rules from the Base Set design snapshot. Gameplay services remain authoritative
    /// for effects which already have concrete runtime implementations.
    /// </summary>
    public List<string> StarRules { get; set; } = new();

    public int StableBaseId => this.BaseId > 0 ? this.BaseId : this.IconIndex >= 0 ? this.IconIndex + 1 : int.MaxValue;
}


namespace Cardcha.Models;

internal sealed class CardDefinition
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public CardRarity Rarity { get; set; }
    public string EffectKey { get; set; } = "";
    public double Value { get; set; }
    public string Description { get; set; } = "";

    /// <summary>
    /// Zero-based cell index in assets/card_icons.png. The atlas is optional during prototyping;
    /// CardRenderer falls back to a runtime-drawn initial when the atlas is absent.
    /// </summary>
    public int IconIndex { get; set; } = -1;

    /// <summary>Maximum upgrade level for this card (1-5).</summary>
    public int MaxLevel { get; set; } = 1;

    /// <summary>
    /// Multiplicative power gain per extra level. Example: 0.25 means Lv2 = 125% of base value.
    /// </summary>
    public double LevelStep { get; set; } = 0.25;
}

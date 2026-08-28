namespace Cardcha;

internal sealed class ModConfig
{
    public bool EnableMonsterDrops { get; set; } = true;
    public bool EnableCombatCards { get; set; } = true;
    public bool EnableCombatHud { get; set; } = true;
    public double CombatHudScale { get; set; } = 1.0;
    public double PrototypeDropMultiplier { get; set; } = 1.0;
    public int StandardPullCost { get; set; } = 10;
    public int PremiumPullCost { get; set; } = 10;
    public int StandardLegendaryPity { get; set; } = 70;
    public int PremiumLegendaryPity { get; set; } = 30;

    // v0.1.2 combat tuning. These are intentionally easy to tweak while testing.
    public int BloodFangCooldownMs { get; set; } = 1000;
    public int ChainHunterDurationMs { get; set; } = 6000;
    public int ChainHunterMaxStacks { get; set; } = 5;
    public int LastStandDefenseBonus { get; set; } = 2;
    public int PhoenixInvincibilityMs { get; set; } = 5000;

    // alpha.23 multi-controller profile. Layout controls user-facing labels; mapping controls
    // how the runtime reports the four face buttons. Auto is the recommended default.
    public string ControllerLayout { get; set; } = "Auto"; // Auto, Xbox, Nintendo, PlayStation, Generic
    public string ControllerMapping { get; set; } = "Auto"; // Auto, Standard, NintendoNative

    public bool VerboseLogging { get; set; } = false;
}

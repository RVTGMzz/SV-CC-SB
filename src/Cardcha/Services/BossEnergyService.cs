using Cardcha.Models;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Transient Cardcha combat resource used by Boss/Ultimate mechanics.
/// It deliberately does not persist to SaveData. Victory Charge modifies only kill-sourced
/// Energy, never damage or crit-like Energy.
/// </summary>
internal sealed class BossEnergyService
{
    public const double MaxEnergy = 100d;
    public const double RegularKillEnergy = 10d;
    public const double BossLikeKillEnergy = 20d;
    public const double CritLikeEnergy = 1d;
    public const double DamagePerEnergy = 100d;
    public const double MaxDamageEnergyPerHit = 2d;

    // User tuning: Boss Energy was reaching READY too quickly. Scale every real combat gain to
    // one third so the time/effort to fill the bar is approximately 3x longer without changing
    // the 100 Energy activation threshold or Victory Charge's relative bonus behavior.
    public const double EnergyGainScale = 1d / 3d;

    private readonly LoadoutService Loadout;
    private readonly CardRegistry Cards;
    private readonly CardUpgradeService Upgrades;

    private double Current;
    private bool GainSuppressed;

    public double CurrentEnergy => Math.Clamp(this.Current, 0d, MaxEnergy);
    public bool IsGainSuppressed => this.GainSuppressed;
    public double LastGain { get; private set; }
    public double LastBaseGain { get; private set; }
    public double LastVictoryChargeBonus { get; private set; }
    public string LastSource { get; private set; } = "none";
    public long GainEvents { get; private set; }

    public BossEnergyService(LoadoutService loadout, CardRegistry cards, CardUpgradeService upgrades)
    {
        this.Loadout = loadout;
        this.Cards = cards;
        this.Upgrades = upgrades;
    }

    public void OnDamageDealt(int actualDamage, bool critLike)
    {
        if (!this.Loadout.CardEffectsActive || actualDamage <= 0)
            return;

        double damageGain = Math.Min(MaxDamageEnergyPerHit, actualDamage / DamagePerEnergy);
        if (damageGain > 0d)
            this.Add(damageGain, damageGain, 0d, "damage");

        if (critLike)
            this.Add(CritLikeEnergy, CritLikeEnergy, 0d, "crit-like");
    }

    public void OnKill(bool bossLike, Farmer? who)
    {
        if (!this.Loadout.CardEffectsActive || who?.IsLocalPlayer != true)
            return;

        double baseGain = bossLike ? BossLikeKillEnergy : RegularKillEnergy;
        double bonusRate = 0d;

        if (this.Loadout.IsEquipped("victory_charge"))
        {
            CardDefinition? card = this.Cards.Get("victory_charge");
            bonusRate = Math.Max(0d, this.Upgrades.GetStats(card).Primary);
        }

        double victoryBonus = baseGain * bonusRate;
        this.Add(baseGain + victoryBonus, baseGain, victoryBonus, bossLike ? "boss kill" : "kill");
    }

    public void SetGainSuppressed(bool suppressed)
        => this.GainSuppressed = suppressed;

    public bool TrySpend(double amount)
    {
        amount = Math.Max(0d, amount);
        if (amount <= 0d)
            return true;
        if (this.CurrentEnergy + 0.0001d < amount)
            return false;

        this.Current = Math.Max(0d, this.Current - amount);
        return true;
    }

    public void Reset()
    {
        this.Current = 0d;
        this.LastGain = 0d;
        this.LastBaseGain = 0d;
        this.LastVictoryChargeBonus = 0d;
        this.LastSource = "none";
        this.GainEvents = 0;
        this.GainSuppressed = false;
    }

    public void OnDayStarted(object? sender, DayStartedEventArgs e)
        => this.Reset();

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
        => this.Reset();

    internal void DebugSetEnergy(double value)
        => this.Current = Math.Clamp(value, 0d, MaxEnergy);

    public string Describe()
        => $"BossEnergy={this.CurrentEnergy:0.##}/{MaxEnergy:0} | GainRate=x{EnergyGainScale:0.###} | Last={this.LastGain:0.##} from {this.LastSource} " +
           $"(base={this.LastBaseGain:0.##}, VictoryChargeBonus={this.LastVictoryChargeBonus:0.##}) | Events={this.GainEvents} | Suppressed={this.GainSuppressed}";

    private void Add(double amount, double baseGain, double victoryBonus, string source)
    {
        amount *= EnergyGainScale;
        baseGain *= EnergyGainScale;
        victoryBonus *= EnergyGainScale;

        if (amount <= 0d || this.GainSuppressed)
            return;

        double before = this.CurrentEnergy;
        this.Current = Math.Min(MaxEnergy, before + amount);
        this.LastGain = this.Current - before;
        this.LastBaseGain = Math.Max(0d, baseGain);
        this.LastVictoryChargeBonus = Math.Max(0d, victoryBonus);
        this.LastSource = source;
        this.GainEvents++;
    }
}

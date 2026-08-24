using Cardcha.Models;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Monsters;
using System.Text.RegularExpressions;

namespace Cardcha.Services;

internal enum EnemyLootScale
{
    Regular,
    BossLike
}

internal sealed class DropService
{
    public const string CardboardScrapId = "Ronvotri.Cardcha_CardboardScrap";
    public const string ShinyScrapId = "Ronvotri.Cardcha_ShinyScrap";

    private readonly ModConfig Config;
    private readonly LoadoutService Loadout;
    private readonly CardUpgradeService Upgrades;
    private readonly CardRegistry Cards;
    private readonly ResourceService Resources;
    private readonly Action OnFirstCardboardScrapDropped;
    private readonly Func<bool> HasFirstScrapTriggered;

    private int KillsSinceNormalScrap;

    public long EligibleDeaths { get; private set; }
    public long NormalDropEvents { get; private set; }
    public long ShinyDropEvents { get; private set; }
    public double LastNormalChance { get; private set; }
    public double LastShinyChance { get; private set; }
    public bool LastNormalForced { get; private set; }
    public string LastLootScale { get; private set; } = "none";
    public int LastNormalAmount { get; private set; }
    public int LastShinyAmount { get; private set; }
    public string LastEnemyName { get; private set; } = "none";
    public int LastRawMaxHealth { get; private set; }

    public DropService(
        ModConfig config,
        LoadoutService loadout,
        CardUpgradeService upgrades,
        CardRegistry cards,
        ResourceService resources,
        Action onFirstCardboardScrapDropped,
        Func<bool> hasFirstScrapTriggered
    )
    {
        this.Config = config;
        this.Loadout = loadout;
        this.Upgrades = upgrades;
        this.Cards = cards;
        this.Resources = resources;
        this.OnFirstCardboardScrapDropped = onFirstCardboardScrapDropped;
        this.HasFirstScrapTriggered = hasFirstScrapTriggered;
    }

    public void TryDrop(GameLocation location, Monster monster, Farmer? killer)
    {
        string name = string.IsNullOrWhiteSpace(monster.Name)
            ? monster.GetType().Name
            : monster.Name;

        string source = monster.GetType().FullName ?? monster.GetType().Name;

        // IMPORTANT:
        // Do NOT use monster assembly or MaxHealth to decide whether something is "vanilla".
        // Mods can spawn/reuse vanilla Monster classes with their own very large HP scale.
        EnemyLootScale scale = ClassifyEnemy(name, source, monster.modData?.Pairs);

        this.TryDrop(
            location,
            monster.Position,
            name,
            Math.Max(1, monster.MaxHealth),
            killer,
            scale
        );
    }

    public void TryDrop(
        GameLocation location,
        Microsoft.Xna.Framework.Vector2 position,
        string enemyName,
        int maxHealth,
        Farmer? killer,
        EnemyLootScale scale = EnemyLootScale.Regular
    )
    {
        if (!this.Config.EnableMonsterDrops)
            return;

        this.EligibleDeaths++;
        this.KillsSinceNormalScrap++;

        int hp = Math.Max(1, maxHealth);

        this.LastLootScale = scale.ToString();
        this.LastEnemyName = string.IsNullOrWhiteSpace(enemyName) ? "enemy" : enemyName;
        this.LastRawMaxHealth = hp;
        this.LastNormalAmount = 0;
        this.LastShinyAmount = 0;

        double normalChance;
        double shinyChance;
        int normalAmount;
        int shinyAmount;
        int dryStreakLimit;

        if (scale == EnemyLootScale.BossLike)
        {
            normalChance = 0.65;
            normalAmount = 2;

            shinyChance = 0.25;
            shinyAmount = 1;

            dryStreakLimit = 4;
        }
        else
        {
            // Conservative profile for ALL ordinary enemies, including ordinary mod Pokémon.
            // Raw HP is intentionally ignored.
            normalChance = 0.12;
            normalAmount = 1;

            // Premium currency should essentially come from elite/boss content.
            shinyChance = 0.03; // 3%
            shinyAmount = 1;

            dryStreakLimit = 8;
        }

        if (killer?.IsLocalPlayer == true && this.Loadout.IsEquipped("card_seeker"))
        {
            CardDefinition? seeker = this.Cards.Get("card_seeker");
            double bonus = Math.Max(0d, this.Upgrades.GetStats(seeker).Primary);

            // Card Seeker affects NORMAL Cardboard Scrap only.
            // It must never boost premium Shiny Scrap.
            normalChance *= 1d + bonus;
        }

        double multiplier = Math.Max(0, this.Config.PrototypeDropMultiplier);
        normalChance = Math.Min(0.95, normalChance * multiplier);

        // Premium currency has its own economy.
        // Regular enemies are fixed at 3% Shiny regardless of:
        // - Card Seeker;
        // - PrototypeDropMultiplier;
        // - enemy MaxHealth.
        // BossLike enemies retain their intentional 25% premium chance.
        shinyChance = scale == EnemyLootScale.Regular
            ? 0.03
            : Math.Min(1.00, shinyChance);

        bool forceFirst = !this.HasFirstScrapTriggered();
        bool forceDryStreak = this.KillsSinceNormalScrap >= dryStreakLimit;
        bool forceNormal = forceFirst || forceDryStreak;

        this.LastNormalChance = normalChance;
        this.LastShinyChance = shinyChance;
        this.LastNormalForced = forceNormal;

        Random rng = Game1.random;

        if (forceNormal || rng.NextDouble() < normalChance)
        {
            this.AwardToWallet(CardboardScrapId, normalAmount);
            this.NormalDropEvents++;
            this.LastNormalAmount = normalAmount;
            this.KillsSinceNormalScrap = 0;
            this.OnFirstCardboardScrapDropped();

            if (this.Config.VerboseLogging)
            {
                ModEntry.StaticMonitor?.Log(
                    $"Cardboard Scrap: {normalAmount} from {this.LastEnemyName} " +
                    $"(profile={scale}, rawMaxHP={hp}, chance={normalChance:P1}, forced={forceNormal}).",
                    LogLevel.Info
                );
            }
        }

        if (shinyChance > 0 && rng.NextDouble() < shinyChance)
        {
            this.AwardToWallet(ShinyScrapId, shinyAmount);
            this.ShinyDropEvents++;
            this.LastShinyAmount = shinyAmount;

            if (this.Config.VerboseLogging)
            {
                ModEntry.StaticMonitor?.Log(
                    $"Shiny Scrap: {shinyAmount} from {this.LastEnemyName} " +
                    $"(profile={scale}, rawMaxHP={hp}, chance={shinyChance:P2}).",
                    LogLevel.Info
                );
            }
        }
    }

    public static EnemyLootScale ClassifyEnemy(
        string enemyName,
        string sourceType,
        IEnumerable<KeyValuePair<string, string>>? modData = null
    )
    {
        // Do not use loose substring matching here.
        // A normal mod namespace/modData value can easily contain words like
        // "champion" as part of an unrelated identifier and accidentally turn
        // a regular enemy into the 25% Shiny boss profile.
        if (HasBossRankToken(enemyName) || HasBossRankToken(sourceType))
            return EnemyLootScale.BossLike;

        if (modData is not null)
        {
            foreach ((string key, string value) in modData)
            {
                // Only inspect modData that actually looks like rank/class metadata.
                bool rankLikeKey =
                    HasExactToken(key, "boss")
                    || HasExactToken(key, "elite")
                    || HasExactToken(key, "rank")
                    || HasExactToken(key, "tier")
                    || HasExactToken(key, "class")
                    || HasExactToken(key, "type");

                if (rankLikeKey && HasBossRankToken(value))
                    return EnemyLootScale.BossLike;
            }
        }

        return EnemyLootScale.Regular;
    }

    private static bool HasBossRankToken(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
            return false;

        string[] tokens = Regex.Split(
            value.ToLowerInvariant(),
            @"[^a-z0-9]+"
        );

        return tokens.Any(token =>
            token is "boss"
                or "elite"
                or "apex"
                or "champion"
                or "raid"
        );
    }

    private static bool HasExactToken(string? value, string expected)
    {
        if (string.IsNullOrWhiteSpace(value))
            return false;

        return Regex.Split(
                value.ToLowerInvariant(),
                @"[^a-z0-9]+"
            )
            .Any(token => token.Equals(expected, StringComparison.Ordinal));
    }

    public string Describe()
    {
        CardDefinition? seeker = this.Cards.Get("card_seeker");
        bool seekerOn = this.Loadout.IsEquipped("card_seeker");
        int seekerLevel = seekerOn ? this.Upgrades.GetLevel(seeker) : 0;
        double seekerBonus = seekerOn
            ? Math.Max(0d, this.Upgrades.GetStats(seeker).Primary)
            : 0d;

        string seekerText = seekerOn
            ? $"CardSeeker=ON Lv{seekerLevel} (+{seekerBonus:P0} NORMAL only)"
            : "CardSeeker=off";

        return
            $"EligibleDeaths={this.EligibleDeaths} | NormalDrops={this.NormalDropEvents} | ShinyDrops={this.ShinyDropEvents} | " +
            $"DryStreak={this.KillsSinceNormalScrap} | Profile={this.LastLootScale} | Enemy={this.LastEnemyName} | RawMaxHP={this.LastRawMaxHealth} | " +
            $"LastNormal={this.LastNormalAmount} @ {this.LastNormalChance:P1} forced={this.LastNormalForced} | " +
            $"LastShiny={this.LastShinyAmount} @ {this.LastShinyChance:P2} | {seekerText}";
    }

    private void AwardToWallet(string itemId, int amount)
    {
        this.Resources.Add(itemId, amount);
    }
}

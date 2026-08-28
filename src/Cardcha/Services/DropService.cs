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
    private readonly Func<int> GetNoHitKillStreak;

    private int KillsSinceNormalScrap;
    private int LuckyBreakFailStreak;

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
        Func<bool> hasFirstScrapTriggered,
        Func<int> getNoHitKillStreak
    )
    {
        this.Config = config;
        this.Loadout = loadout;
        this.Upgrades = upgrades;
        this.Cards = cards;
        this.Resources = resources;
        this.OnFirstCardboardScrapDropped = onFirstCardboardScrapDropped;
        this.HasFirstScrapTriggered = hasFirstScrapTriggered;
        this.GetNoHitKillStreak = getNoHitKillStreak;
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

        bool normalDropped = forceNormal || rng.NextDouble() < normalChance;
        if (normalDropped)
        {
            int awarded = normalAmount + this.RollEssenceFinderBonus(CardboardScrapId, rng);
            this.AwardScrap(location, position, CardboardScrapId, awarded);
            this.NormalDropEvents++;
            this.LastNormalAmount = awarded;
            this.KillsSinceNormalScrap = 0;
            this.OnFirstCardboardScrapDropped();

            if (this.Config.VerboseLogging)
            {
                ModEntry.StaticMonitor?.Log(
                    $"Cardboard Scrap: {awarded} from {this.LastEnemyName} " +
                    $"(profile={scale}, rawMaxHP={hp}, chance={normalChance:P1}, forced={forceNormal}).",
                    LogLevel.Info
                );
            }
        }

        bool shinyDropped = shinyChance > 0 && rng.NextDouble() < shinyChance;
        if (shinyDropped)
        {
            int awarded = shinyAmount + this.RollEssenceFinderBonus(ShinyScrapId, rng);
            this.AwardScrap(location, position, ShinyScrapId, awarded);
            this.ShinyDropEvents++;
            this.LastShinyAmount = awarded;

            if (this.Config.VerboseLogging)
            {
                ModEntry.StaticMonitor?.Log(
                    $"Shiny Scrap: {awarded} from {this.LastEnemyName} " +
                    $"(profile={scale}, rawMaxHP={hp}, chance={shinyChance:P2}).",
                    LogLevel.Info
                );
            }
        }

        // Smaller loot-oriented cards use independent bonus rolls so they don't distort
        // the core Scrap or Shiny pity/drop profile. These are deliberately additive.
        if (killer?.IsLocalPlayer == true)
        {
            if (this.Loadout.IsEquipped("scavenger")
                && rng.NextDouble() < this.LevelPercent("scavenger", 0.03, 0.04, 0.05, 0.06, 0.07))
            {
                this.AwardScrap(location, position, CardboardScrapId, 1);
                this.LastNormalAmount += 1;
            }

            if (this.Loadout.IsEquipped("treasure_eye")
                && rng.NextDouble() < this.LevelPercent("treasure_eye", 0.04, 0.05, 0.06, 0.07))
            {
                this.AwardScrap(location, position, CardboardScrapId, 1);
                this.LastNormalAmount += 1;
            }

            if (this.Loadout.IsEquipped("lucky_pocket")
                && rng.NextDouble() < this.LevelPercent("lucky_pocket", 0.02, 0.03, 0.04, 0.05, 0.06))
            {
                // Low-value money reward by design; this card should feel useful without
                // becoming a primary economy engine.
                killer.Money = checked(killer.Money + 25);
            }

            if (scale == EnemyLootScale.BossLike)
            {
                if (this.Loadout.IsEquipped("collectors_instinct")
                    && rng.NextDouble() < this.LevelPercent("collectors_instinct", 0.05, 0.07, 0.09, 0.11))
                {
                    this.AwardScrap(location, position, CardboardScrapId, 1);
                    this.LastNormalAmount += 1;
                }

                if (this.Loadout.IsEquipped("treasure_hunter")
                    && rng.NextDouble() < this.LevelPercent("treasure_hunter", 0.10, 0.13, 0.16))
                {
                    this.AwardScrap(location, position, CardboardScrapId, 1);
                    this.LastNormalAmount += 1;
                }

                if (this.Loadout.IsEquipped("kings_ransom"))
                {
                    int level = this.Upgrades.GetLevel(this.Cards.Get("kings_ransom"));
                    double upgradeChance = level switch { 2 => 0.20, >= 3 => 0.35, _ => 0d };
                    if (upgradeChance > 0 && rng.NextDouble() < upgradeChance)
                    {
                        this.AwardScrap(location, position, ShinyScrapId, 1);
                        this.LastShinyAmount += 1;
                    }
                    else
                    {
                        this.AwardScrap(location, position, CardboardScrapId, 1);
                        this.LastNormalAmount += 1;
                    }
                }
            }

            // Fortune Chain: once the player reaches five consecutive no-hit kills, each
            // following kill gets an independent bonus Cardboard Scrap roll until a hit
            // breaks the streak. It deliberately doesn't inflate the Shiny economy.
            if (this.Loadout.IsEquipped("fortune_chain")
                && this.GetNoHitKillStreak() >= 5
                && rng.NextDouble() < this.LevelPercent("fortune_chain", 0.05, 0.07, 0.09, 0.11))
            {
                this.AwardScrap(location, position, CardboardScrapId, 1);
                this.LastNormalAmount += 1;
            }

            // Lucky Break: failing its small bonus-loot roll builds a transient fail streak.
            // From the third failure onward the card's advertised bonus stays active until
            // one extra Scrap succeeds, then the streak resets.
            if (this.Loadout.IsEquipped("lucky_break"))
            {
                double luckyChance = this.LuckyBreakFailStreak >= 3
                    ? this.LevelPercent("lucky_break", 0.08, 0.12, 0.16)
                    : 0d;
                if (luckyChance > 0 && rng.NextDouble() < luckyChance)
                {
                    this.AwardScrap(location, position, CardboardScrapId, 1);
                    this.LastNormalAmount += 1;
                    this.LuckyBreakFailStreak = 0;
                }
                else
                {
                    this.LuckyBreakFailStreak = Math.Min(999, this.LuckyBreakFailStreak + 1);
                }
            }
            else
            {
                this.LuckyBreakFailStreak = 0;
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

    private int RollEssenceFinderBonus(string itemId, Random rng)
    {
        if (!this.Loadout.IsEquipped("essence_finder"))
            return 0;

        double chance = this.LevelPercent("essence_finder", 0.08, 0.10, 0.12, 0.14, 0.16);
        if (chance <= 0 || rng.NextDouble() >= chance)
            return 0;

        // The approved design explicitly applies to BOTH normal and Shiny Scrap.
        return itemId.Equals(CardboardScrapId, StringComparison.OrdinalIgnoreCase)
            || itemId.Equals(ShinyScrapId, StringComparison.OrdinalIgnoreCase)
            ? 1
            : 0;
    }

    private double LevelPercent(string cardId, params double[] values)
    {
        CardDefinition? card = this.Cards.Get(cardId);
        if (card is null || values.Length == 0)
            return 0;

        int level = Math.Clamp(this.Upgrades.GetLevel(card), 1, values.Length);
        return values[level - 1];
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

    private void AwardScrap(GameLocation location, Microsoft.Xna.Framework.Vector2 position, string itemId, int amount)
    {
        if (amount <= 0)
            return;

        // Before the Binder handoff, Scrap is a real world/backpack item so the player can
        // inspect and count the strange fragments they found. Once the Binder exists, drops
        // go directly into its wallet to avoid permanently consuming inventory slots.
        if (!this.Resources.IsBinderWalletActive)
        {
            Item item = ItemRegistry.Create($"(O){itemId}");
            item.Stack = amount;
            Game1.createItemDebris(item, position, -1, location);
            return;
        }

        this.Resources.Add(itemId, amount);

        // Once the Binder wallet is active there is no physical debris pickup for Stardew
        // to announce, so reproduce the vanilla item-gained toast explicitly. This keeps
        // feedback identical before/after the Wizard handoff.
        try
        {
            Item gained = ItemRegistry.Create($"(O){itemId}");
            Game1.addHUDMessage(HUDMessage.ForItemGained(gained, amount, $"Cardcha:{itemId}"));
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("scrap-wallet-toast", $"Couldn't show Scrap wallet pickup toast: {ex}");
        }
    }
}

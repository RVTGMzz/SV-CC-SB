using Cardcha.Models;

namespace Cardcha.Services;

internal sealed class CardLevelStats
{
    public double Primary { get; init; }
    public double Secondary { get; init; }
    public int DurationMs { get; init; }
    public double Threshold { get; init; }
}

internal sealed class CardUpgradeService
{
    public const int MaxActiveSlots = 5;
    public const int StartingActiveSlots = 2;

    private readonly SaveService Save;
    private readonly CardRegistry Cards;

    public CardUpgradeService(SaveService save, CardRegistry cards)
    {
        this.Save = save;
        this.Cards = cards;
    }

    public int GetUnlockedSlotCount()
        // Until milestone quests are implemented, every save uses the approved two-slot start.
        // This also repairs test saves temporarily promoted to 3-5 slots by alpha.4.
        => StartingActiveSlots;

    public int GetLevel(string cardId)
    {
        if (string.IsNullOrWhiteSpace(cardId))
            return 1;

        if (!this.Save.Data.CardLevels.TryGetValue(cardId, out int level) || level < 1)
        {
            this.Save.Data.CardLevels[cardId] = 1;
            return 1;
        }

        return Math.Clamp(level, 1, 5);
    }

    public int GetLevel(CardDefinition? card)
        => card is null ? 1 : this.GetLevel(card.Id);

    public int GetMaxLevel(CardDefinition? card)
        => Math.Clamp(card?.MaxLevel ?? 1, 1, 5);

    public bool IsMaxLevel(CardDefinition? card)
        => card is not null && this.GetLevel(card) >= this.GetMaxLevel(card);

    public int GetCopies(CardDefinition? card)
        => card is null ? 0 : this.GetCopies(card.Id);

    public int GetCopies(string cardId)
        => this.Save.Data.CardCopies.TryGetValue(cardId, out int count)
            ? Math.Max(0, count)
            : 0;

    public void AddDuplicateCopy(string cardId, int amount = 1)
    {
        if (string.IsNullOrWhiteSpace(cardId) || amount <= 0)
            return;

        this.Save.Data.CardCopies[cardId] = this.GetCopies(cardId) + amount;
        this.Save.Save();
    }

    /// <summary>
    /// Concrete per-level tuning. UI and gameplay both read this exact table,
    /// so the level descriptions in the Binder cannot drift away from combat values.
    /// </summary>
    public CardLevelStats GetStats(CardDefinition? card, int? levelOverride = null)
    {
        if (card is null)
            return new CardLevelStats();

        int level = Math.Clamp(
            levelOverride ?? this.GetLevel(card),
            1,
            this.GetMaxLevel(card)
        );

        return card.Id switch
        {
            "iron_edge" => new CardLevelStats
            {
                Primary = Pick(level, 0.04, 0.06, 0.08, 0.10, 0.12)
            },

            "thick_hide" => new CardLevelStats
            {
                Primary = Pick(level, 1, 1, 2, 2, 3)
            },

            "keen_eye" => new CardLevelStats
            {
                Primary = Pick(level, 0.02, 0.03, 0.04, 0.05, 0.06)
            },

            "swift_feet" => new CardLevelStats
            {
                Primary = Pick(level, 1, 1, 1, 1, 2),
                DurationMs = PickInt(level, 0, 1500, 3000, 4500, 6000)
            },

            "blood_fang" => new CardLevelStats
            {
                Primary = Pick(level, 0.020, 0.025, 0.030, 0.035, 0.040),
                DurationMs = PickInt(level, 1000, 900, 800, 700, 600)
            },

            "executioner" => new CardLevelStats
            {
                Primary = Pick(level, 0.20, 0.25, 0.30, 0.35, 0.40),
                Threshold = Pick(level, 0.20, 0.20, 0.25, 0.25, 0.30)
            },

            "card_seeker" => new CardLevelStats
            {
                Primary = Pick(level, 0.50, 0.60, 0.70, 0.85, 1.00)
            },

            "chain_hunter" => new CardLevelStats
            {
                Primary = Pick(level, 0.05, 0.06, 0.07, 0.08),
                DurationMs = PickInt(level, 6000, 7000, 8000, 9000)
            },

            "last_stand" => new CardLevelStats
            {
                Primary = Pick(level, 0.20, 0.25, 0.30, 0.35),
                Secondary = Pick(level, 2, 2, 3, 3),
                Threshold = 0.20
            },

            "phoenix_heart" => new CardLevelStats
            {
                DurationMs = PickInt(level, 5000, 7000, 9000)
            },

            _ => new CardLevelStats
            {
                Primary = card.Value
            }
        };
    }

    public string GetLevelEffectText(CardDefinition? card, int level)
    {
        if (card is null)
            return "";

        CardLevelStats s = this.GetStats(card, level);

        return card.Id switch
        {
            "iron_edge" => ModEntry.T(
                "binder.level-effect.iron-edge",
                new { damage = Percent(s.Primary) }
            ),

            "thick_hide" => ModEntry.T(
                "binder.level-effect.thick-hide",
                new { defense = (int)Math.Round(s.Primary) }
            ),

            "keen_eye" => ModEntry.T(
                "binder.level-effect.keen-eye",
                new { crit = Percent(s.Primary) }
            ),

            "swift_feet" => s.DurationMs <= 0
                ? ModEntry.T(
                    "binder.level-effect.swift-feet-base",
                    new { speed = (int)Math.Round(s.Primary) }
                )
                : ModEntry.T(
                    "binder.level-effect.swift-feet",
                    new
                    {
                        speed = (int)Math.Round(s.Primary),
                        duration = Seconds(s.DurationMs)
                    }
                ),

            "blood_fang" => ModEntry.T(
                "binder.level-effect.blood-fang",
                new
                {
                    heal = Percent(s.Primary),
                    cooldown = Seconds(s.DurationMs)
                }
            ),

            "executioner" => ModEntry.T(
                "binder.level-effect.executioner",
                new
                {
                    damage = Percent(s.Primary),
                    threshold = Percent(s.Threshold)
                }
            ),

            "card_seeker" => ModEntry.T(
                "binder.level-effect.card-seeker",
                new { drop = Percent(s.Primary) }
            ),

            "chain_hunter" => ModEntry.T(
                "binder.level-effect.chain-hunter",
                new
                {
                    damage = Percent(s.Primary),
                    duration = Seconds(s.DurationMs)
                }
            ),

            "last_stand" => ModEntry.T(
                "binder.level-effect.last-stand",
                new
                {
                    threshold = Percent(s.Threshold),
                    damage = Percent(s.Primary),
                    defense = (int)Math.Round(s.Secondary)
                }
            ),

            "phoenix_heart" => ModEntry.T(
                "binder.level-effect.phoenix-heart",
                new { duration = Seconds(s.DurationMs) }
            ),

            _ => card.Description
        };
    }

    /// <summary>
    /// Required SAME-CARD duplicate copies for the next star.
    /// Normal tiers: 1,2,3,4.
    /// Legendary/Mythic: 1,1,2,2.
    /// </summary>
    public int GetRequiredCopies(CardDefinition? card)
    {
        if (card is null)
            return 0;

        int level = this.GetLevel(card);
        if (level >= this.GetMaxLevel(card))
            return 0;

        bool topTier = card.Rarity is CardRarity.Legendary or CardRarity.Mythic;
        return topTier
            ? Math.Max(1, (level + 1) / 2)
            : Math.Max(1, level);
    }

    public bool TryUpgrade(CardDefinition card, out int newLevel, out int copiesSpent)
    {
        newLevel = this.GetLevel(card);
        copiesSpent = this.GetRequiredCopies(card);

        if (copiesSpent <= 0 || this.GetCopies(card) < copiesSpent)
            return false;

        this.Save.Data.CardCopies[card.Id] = this.GetCopies(card) - copiesSpent;
        newLevel = Math.Min(this.GetMaxLevel(card), newLevel + 1);
        this.Save.Data.CardLevels[card.Id] = newLevel;
        this.Save.Save();
        return true;
    }

    public int GetNextSlotUnlockCost()
    {
        int slots = this.GetUnlockedSlotCount();
        return slots switch
        {
            < 2 => 20,
            2 => 30,
            3 => 70,
            4 => 140,
            _ => 0,
        };
    }

    public bool TryUnlockNextSlot(out int newSlotCount, out int cost)
    {
        newSlotCount = this.GetUnlockedSlotCount();
        cost = this.GetNextSlotUnlockCost();
        if (cost <= 0 || this.Save.Data.SuspiciousDust < cost)
            return false;

        this.Save.Data.SuspiciousDust -= cost;
        newSlotCount = Math.Min(MaxActiveSlots, newSlotCount + 1);
        this.Save.Data.ActiveCardSlotCount = newSlotCount;
        this.Save.Save();
        return true;
    }

    private static double Pick(int level, params double[] values)
        => values[Math.Clamp(level, 1, values.Length) - 1];

    private static int PickInt(int level, params int[] values)
        => values[Math.Clamp(level, 1, values.Length) - 1];

    private static string Percent(double fraction)
        => (fraction * 100d).ToString("0.#");

    private static string Seconds(int ms)
        => (ms / 1000d).ToString("0.#");
}

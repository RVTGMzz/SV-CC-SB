using StardewValley;
using Cardcha.Models;

namespace Cardcha.Services;

internal sealed class GachaService
{
    private const int CollectionInsuranceDuplicates = 20;

    private readonly CardRegistry Registry;
    private readonly SaveService Save;
    private readonly ModConfig Config;

    public GachaService(CardRegistry registry, SaveService save, ModConfig config)
    {
        this.Registry = registry;
        this.Save = save;
        this.Config = config;
    }

    public PullResult Pull(PullType type)
    {
        SaveData data = this.Save.Data;
        long pullIndex = data.PullIndex;

        // Keep save-seed continuity while ensuring reloads don't replay the exact same result.
        ulong runtimeSalt = unchecked(
            (ulong)DateTime.UtcNow.Ticks
            ^ ((ulong)Environment.TickCount64 << 1)
            ^ ((ulong)(uint)Game1.random.Next() << 32)
            ^ (uint)Game1.random.Next()
        );
        ulong seed = SaveService.Mix(
            data.GachaSeed
            ^ ((ulong)pullIndex + 0x9E3779B97F4A7C15UL)
            ^ (type == PullType.Premium ? 0xCA4DCAUL : 0x51A4DUL)
            ^ runtimeSalt
        );
        var rng = new DeterministicRng(seed);

        // alpha.26.5 collection insurance. After 20 consecutive duplicate pulls, the next
        // pull is guaranteed NEW *within the selected machine's real pool*. Premium therefore
        // remains Rare/Epic/Legendary only; its approved rarity distribution is otherwise unchanged.
        List<CardDefinition> guaranteedNew = data.DuplicatePullStreak >= CollectionInsuranceDuplicates
            ? this.GetEligibleUnowned(type, data).ToList()
            : new List<CardDefinition>();

        CardDefinition card;
        if (guaranteedNew.Count > 0)
        {
            card = guaranteedNew[rng.Next(guaranteedNew.Count)];
        }
        else
        {
            CardRarity rarity = type == PullType.Standard
                ? RollStandardRarity(rng, data)
                : RollPremiumRarity(rng, data);

            List<CardDefinition> pool = this.Registry.ForRarity(rarity)
                .Where(IsActiveBaseSetCard)
                .ToList();
            if (pool.Count == 0)
            {
                rarity = FindNearestAvailableRarity(rarity, type);
                pool = this.Registry.ForRarity(rarity)
                    .Where(IsActiveBaseSetCard)
                    .ToList();
            }

            card = pool[rng.Next(pool.Count)];
        }

        bool isNew = data.OwnedCards.Add(card.Id);
        int duplicateCopies = 0;
        int dustAwarded = 0;

        if (isNew)
        {
            data.DuplicatePullStreak = 0;
            if (!data.CardLevels.ContainsKey(card.Id))
                data.CardLevels[card.Id] = 1;
        }
        else
        {
            data.DuplicatePullStreak = checked(data.DuplicatePullStreak + 1);

            int level = data.CardLevels.TryGetValue(card.Id, out int storedLevel)
                ? Math.Max(1, storedLevel)
                : 1;
            int maxLevel = Math.Clamp(card.MaxLevel <= 0 ? 1 : card.MaxLevel, 1, 5);

            // Once a card is already at max stars, further copies convert directly into Magic Dust.
            // The old save field name SuspiciousDust is intentionally retained for compatibility.
            if (level >= maxLevel)
            {
                dustAwarded = 1;

                // Dust Collector: +15/20/25/30% chance for one extra Magic Dust on a maxed duplicate.
                if (data.EquippedCards.Contains("dust_collector", StringComparer.OrdinalIgnoreCase))
                {
                    int dustLevel = data.CardLevels.TryGetValue("dust_collector", out int dl) ? Math.Clamp(dl, 1, 4) : 1;
                    double extraChance = dustLevel switch { 1 => 0.15, 2 => 0.20, 3 => 0.25, _ => 0.30 };
                    if (rng.NextDouble() < extraChance)
                        dustAwarded++;
                }

                data.SuspiciousDust = checked(Math.Max(0, data.SuspiciousDust) + dustAwarded);
            }
            else
            {
                duplicateCopies = 1;
                int current = data.CardCopies.TryGetValue(card.Id, out int stored)
                    ? Math.Max(0, stored)
                    : 0;
                data.CardCopies[card.Id] = current + duplicateCopies;
            }

            // Arcane Recycler (#61): Rare+ duplicates refund an expected 5/7.5/10%
            // of this pull's resource cost. Fractional refunds are resolved as a deterministic
            // extra-unit roll so the wallet remains integer-only and save-compatible.
            if (card.Rarity >= CardRarity.Rare
                && data.EquippedCards.Contains("arcane_recycler", StringComparer.OrdinalIgnoreCase))
            {
                int recyclerLevel = data.CardLevels.TryGetValue("arcane_recycler", out int rl)
                    ? Math.Clamp(rl, 1, 3)
                    : 1;
                double refundRate = recyclerLevel switch { 1 => 0.05, 2 => 0.075, _ => 0.10 };
                int pullCost = type == PullType.Standard
                    ? Math.Max(0, this.Config.StandardPullCost)
                    : Math.Max(0, this.Config.PremiumPullCost);
                double expectedRefund = pullCost * refundRate;
                int refund = (int)Math.Floor(expectedRefund);
                double fractional = expectedRefund - refund;
                if (fractional > 0 && rng.NextDouble() < fractional)
                    refund++;

                if (refund > 0)
                {
                    if (type == PullType.Standard)
                        data.CardboardScraps = checked(Math.Max(0, data.CardboardScraps) + refund);
                    else
                        data.ShinyScraps = checked(Math.Max(0, data.ShinyScraps) + refund);
                }
            }
        }

        data.PullIndex++;

        // Golden Hand (#60): a clean, deterministic every-10-pulls Magic Dust reward.
        if (data.EquippedCards.Contains("golden_hand", StringComparer.OrdinalIgnoreCase)
            && data.PullIndex > 0
            && data.PullIndex % 10 == 0)
        {
            int level = data.CardLevels.TryGetValue("golden_hand", out int gl) ? Math.Clamp(gl, 1, 3) : 1;
            int bonusDust = level switch { 1 => 5, 2 => 7, _ => 10 };
            data.SuspiciousDust = checked(Math.Max(0, data.SuspiciousDust) + bonusDust);
            dustAwarded += bonusDust;
        }

        // Cardmaster (#74): approved periodic Dust component. Its small Rare+ weighting bonus
        // is intentionally conservative and applied only to Standard by nudging the next roll
        // through the persisted duplicate insurance/pity systems rather than bypassing either.
        if (type == PullType.Standard
            && data.EquippedCards.Contains("cardmaster", StringComparer.OrdinalIgnoreCase)
            && data.PullIndex > 0
            && data.PullIndex % 10 == 0)
        {
            int level = data.CardLevels.TryGetValue("cardmaster", out int cl) ? Math.Clamp(cl, 1, 3) : 1;
            int bonusDust = level switch { 1 => 5, 2 => 7, _ => 10 };
            data.SuspiciousDust = checked(Math.Max(0, data.SuspiciousDust) + bonusDust);
            dustAwarded += bonusDust;
        }

        UpdatePity(type, card.Rarity, data);
        this.Save.Save();

        return new PullResult(card, isNew, duplicateCopies, dustAwarded, type, pullIndex);
    }

    private IEnumerable<CardDefinition> GetEligibleUnowned(PullType type, SaveData data)
    {
        foreach (CardDefinition card in this.Registry.All)
        {
            if (!IsActiveBaseSetCard(card) || data.OwnedCards.Contains(card.Id))
                continue;

            if (type == PullType.Premium && card.Rarity < CardRarity.Rare)
                continue;
            if (card.Rarity > CardRarity.Legendary)
                continue;

            yield return card;
        }
    }

    private static bool IsActiveBaseSetCard(CardDefinition card)
        => card.Rarity != CardRarity.Mythic && card.StableBaseId is >= 1 and <= CardRegistry.TargetBaseSetCount;

    private CardRarity RollStandardRarity(DeterministicRng rng, SaveData data)
    {
        if (data.StandardSinceLegendary + 1 >= this.Config.StandardLegendaryPity)
            return CardRarity.Legendary;
        if (data.StandardSinceEpic + 1 >= 30)
            return CardRarity.Epic;
        if (data.StandardSinceRare + 1 >= 10)
            return CardRarity.Rare;

        double roll = rng.NextDouble();
        if (roll < 0.03) return CardRarity.Legendary;
        if (roll < 0.15) return CardRarity.Epic;
        if (roll < 0.45) return CardRarity.Rare;
        return CardRarity.Common;
    }

    private CardRarity RollPremiumRarity(DeterministicRng rng, SaveData data)
    {
        if (data.PremiumSinceLegendary + 1 >= this.Config.PremiumLegendaryPity)
            return CardRarity.Legendary;
        if (data.PremiumSinceEpic + 1 >= 5)
            return CardRarity.Epic;

        // Approved Premium distribution remains unchanged: 55% Rare / 35% Epic / 10% Legendary.
        double roll = rng.NextDouble();
        if (roll < 0.10) return CardRarity.Legendary;
        if (roll < 0.45) return CardRarity.Epic;
        return CardRarity.Rare;
    }

    private CardRarity FindNearestAvailableRarity(CardRarity requested, PullType type)
    {
        for (int delta = 0; delta <= 4; delta++)
        {
            int down = (int)requested - delta;
            if (down >= 0)
            {
                CardRarity r = (CardRarity)down;
                if (!(type == PullType.Premium && r < CardRarity.Rare)
                    && r <= CardRarity.Legendary
                    && this.Registry.ForRarity(r).Any(IsActiveBaseSetCard))
                    return r;
            }

            int up = (int)requested + delta;
            if (up <= (int)CardRarity.Legendary)
            {
                CardRarity r = (CardRarity)up;
                if (!(type == PullType.Premium && r < CardRarity.Rare)
                    && this.Registry.ForRarity(r).Any(IsActiveBaseSetCard))
                    return r;
            }
        }
        throw new InvalidOperationException("Cardcha has no active cards registered for this machine.");
    }

    private static void UpdatePity(PullType type, CardRarity rarity, SaveData data)
    {
        if (type == PullType.Standard)
        {
            data.StandardSinceRare = rarity >= CardRarity.Rare ? 0 : data.StandardSinceRare + 1;
            data.StandardSinceEpic = rarity >= CardRarity.Epic ? 0 : data.StandardSinceEpic + 1;
            data.StandardSinceLegendary = rarity >= CardRarity.Legendary ? 0 : data.StandardSinceLegendary + 1;
        }
        else
        {
            data.PremiumSinceEpic = rarity >= CardRarity.Epic ? 0 : data.PremiumSinceEpic + 1;
            data.PremiumSinceLegendary = rarity >= CardRarity.Legendary ? 0 : data.PremiumSinceLegendary + 1;
        }
    }

    private sealed class DeterministicRng
    {
        private ulong State;
        public DeterministicRng(ulong seed) => this.State = seed == 0 ? 1UL : seed;
        private ulong NextU64()
        {
            ulong x = this.State;
            x ^= x >> 12;
            x ^= x << 25;
            x ^= x >> 27;
            this.State = x;
            return x * 2685821657736338717UL;
        }
        public double NextDouble() => (NextU64() >> 11) * (1.0 / (1UL << 53));
        public int Next(int maxExclusive) => maxExclusive <= 1 ? 0 : (int)(NextU64() % (uint)maxExclusive);
    }
}

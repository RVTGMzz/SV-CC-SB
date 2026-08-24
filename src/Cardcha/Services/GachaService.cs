using Cardcha.Models;

namespace Cardcha.Services;

internal sealed class GachaService
{
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
        ulong seed = SaveService.Mix(data.GachaSeed ^ ((ulong)pullIndex + 0x9E3779B97F4A7C15UL) ^ (type == PullType.Premium ? 0xCA4DCAUL : 0x51A4DUL));
        var rng = new DeterministicRng(seed);

        CardRarity rarity = type == PullType.Standard
            ? RollStandardRarity(rng, data)
            : RollPremiumRarity(rng, data);

        List<CardDefinition> pool = this.Registry.ForRarity(rarity).ToList();
        if (pool.Count == 0)
        {
            rarity = FindNearestAvailableRarity(rarity);
            pool = this.Registry.ForRarity(rarity).ToList();
        }

        CardDefinition card = pool[rng.Next(pool.Count)];
        bool isNew = data.OwnedCards.Add(card.Id);

        int duplicateCopies = 0;
        if (isNew)
        {
            if (!data.CardLevels.ContainsKey(card.Id))
                data.CardLevels[card.Id] = 1;
        }
        else
        {
            duplicateCopies = 1;
            int current = data.CardCopies.TryGetValue(card.Id, out int stored)
                ? Math.Max(0, stored)
                : 0;
            data.CardCopies[card.Id] = current + duplicateCopies;
        }

        data.PullIndex++;
        UpdatePity(type, card.Rarity, data);
        this.Save.Save(); // result + duplicate copy are persisted before reveal animation.

        return new PullResult(card, isNew, duplicateCopies, 0, type, pullIndex);
    }

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

        double roll = rng.NextDouble();
        if (roll < 0.10) return CardRarity.Legendary;
        if (roll < 0.45) return CardRarity.Epic;
        return CardRarity.Rare;
    }

    private CardRarity FindNearestAvailableRarity(CardRarity requested)
    {
        for (int delta = 0; delta <= 4; delta++)
        {
            int down = (int)requested - delta;
            if (down >= 0 && this.Registry.ForRarity((CardRarity)down).Any())
                return (CardRarity)down;
            int up = (int)requested + delta;
            if (up <= 4 && this.Registry.ForRarity((CardRarity)up).Any())
                return (CardRarity)up;
        }
        throw new InvalidOperationException("Cardcha has no cards registered.");
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

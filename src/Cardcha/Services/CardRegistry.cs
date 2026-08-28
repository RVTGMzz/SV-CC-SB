using Cardcha.Models;
using StardewModdingAPI;

namespace Cardcha.Services;

internal sealed class CardRegistry
{
    // The public-facing Base Set remains an 80-card collection target.
    // Legacy Mythic entries 77-80 are hidden from the Binder while their future replacements
    // are being designed, so active progression ignores those legacy IDs without deleting save data.
    public const int TargetBaseSetCount = 76;

    private static readonly HashSet<string> LegacyMythicCardIds = new(StringComparer.OrdinalIgnoreCase)
    {
        "endless_hunt",
        "fate_weaver",
        "immortal_echo",
        "worldbreaker"
    };

    private readonly IModHelper Helper;
    private Dictionary<string, CardDefinition> Cards = new(StringComparer.OrdinalIgnoreCase);

    public CardRegistry(IModHelper helper)
    {
        this.Helper = helper;
    }

    public IReadOnlyCollection<CardDefinition> All => this.Cards.Values;

    public void Load()
    {
        List<CardDefinition> cards =
            this.Helper.ModContent.Load<List<CardDefinition>>("assets/cards.json")
            ?? new List<CardDefinition>();

        this.Cards = cards.ToDictionary(p => p.Id, StringComparer.OrdinalIgnoreCase);
        this.RefreshTranslations();
    }

    public void RefreshTranslations()
    {
        foreach (CardDefinition card in this.Cards.Values)
        {
            string nameKey = $"card.{card.Id}.name";
            string descKey = $"card.{card.Id}.desc";

            string localizedName = this.Helper.Translation.Get(nameKey).ToString();
            string localizedDescription = this.Helper.Translation.Get(descKey).ToString();

            if (!string.IsNullOrWhiteSpace(localizedName) && localizedName != nameKey)
                card.Name = localizedName;

            if (!string.IsNullOrWhiteSpace(localizedDescription) && localizedDescription != descKey)
                card.Description = localizedDescription;

            if (card.Name == nameKey || card.Description == descKey)
            {
                ModEntry.StaticMonitor?.Log(
                    $"Missing localized Cardcha card text for '{card.Id}'. Expected keys: {nameKey}, {descKey}.",
                    LogLevel.Warn
                );
            }
        }
    }

    public CardDefinition? Get(string id)
        => this.Cards.TryGetValue(id, out CardDefinition? card) ? card : null;

    public static int CountActiveOwned(IEnumerable<string>? ownedCardIds)
    {
        if (ownedCardIds is null)
            return 0;

        return ownedCardIds.Count(id =>
            !string.IsNullOrWhiteSpace(id)
            && !LegacyMythicCardIds.Contains(id));
    }

    public IEnumerable<CardDefinition> ForRarity(CardRarity rarity)
        => this.Cards.Values.Where(p => p.Rarity == rarity);
}

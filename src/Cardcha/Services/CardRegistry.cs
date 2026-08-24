using Cardcha.Models;
using StardewModdingAPI;

namespace Cardcha.Services;

internal sealed class CardRegistry
{
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

    public IEnumerable<CardDefinition> ForRarity(CardRarity rarity)
        => this.Cards.Values.Where(p => p.Rarity == rarity);
}

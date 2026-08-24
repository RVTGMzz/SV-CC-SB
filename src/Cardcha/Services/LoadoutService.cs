
using Cardcha.Models;

namespace Cardcha.Services;

internal sealed class LoadoutService
{
    private readonly SaveService Save;
    private readonly CardRegistry Registry;
    private readonly CardUpgradeService Upgrades;

    public LoadoutService(SaveService save, CardRegistry registry, CardUpgradeService upgrades)
    {
        this.Save = save;
        this.Registry = registry;
        this.Upgrades = upgrades;
    }

    public bool CardEffectsActive
        => this.Save.Data.MachineDelivered
           && this.Save.Data.BinderUnlocked
           && this.Save.Data.MimiMeetupCompleted;

    public bool IsEquipped(string id)
        => this.CardEffectsActive
           && this.Save.Data.EquippedCards.Contains(id, StringComparer.OrdinalIgnoreCase);

    public bool Equip(string id)
    {
        if (!this.CardEffectsActive)
            return false;

        SaveData data = this.Save.Data;
        if (!data.OwnedCards.Contains(id) || this.Registry.Get(id) is null)
            return false;
        if (IsEquipped(id))
            return true;
        if (data.EquippedCards.Count >= this.Upgrades.GetUnlockedSlotCount())
            return false;

        data.EquippedCards.Add(id);
        this.Save.Save();
        return true;
    }

    public bool Unequip(string id)
    {
        int removed = this.Save.Data.EquippedCards.RemoveAll(p => p.Equals(id, StringComparison.OrdinalIgnoreCase));
        if (removed > 0)
            this.Save.Save();
        return removed > 0;
    }
}

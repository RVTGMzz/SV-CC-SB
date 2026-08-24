using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Cardcha Scrap has two deliberate storage phases:
/// 1) before the Wizard gives the Binder, Scrap is a normal physical backpack item;
/// 2) after the Binder handoff, all physical Scrap is absorbed into the Binder wallet.
/// This keeps the early-game discovery tangible without permanently consuming inventory slots.
/// </summary>
internal sealed class ResourceService
{
    private readonly SaveService Save;

    public ResourceService(SaveService save)
    {
        this.Save = save;
    }

    public bool IsBinderWalletActive => this.Save.Data.BinderUnlocked;

    public int Count(string unqualifiedObjectId)
    {
        int wallet = unqualifiedObjectId switch
        {
            DropService.CardboardScrapId => Math.Max(0, this.Save.Data.CardboardScraps),
            DropService.ShinyScrapId => Math.Max(0, this.Save.Data.ShinyScraps),
            _ => 0
        };

        // In normal play the inactive side should be zero, but counting both while the
        // Binder is locked makes old/prototype saves self-healing until SyncStorageModeOnLoad runs.
        return this.IsBinderWalletActive
            ? wallet
            : checked(wallet + CountPhysicalScraps(unqualifiedObjectId));
    }

    public void Add(string unqualifiedObjectId, int amount, bool persist = true)
    {
        if (amount <= 0 || !IsScrapId(unqualifiedObjectId))
            return;

        if (!this.IsBinderWalletActive)
        {
            AddPhysicalScrapsToPlayer(unqualifiedObjectId, amount);
            return;
        }

        if (unqualifiedObjectId.Equals(DropService.CardboardScrapId, StringComparison.OrdinalIgnoreCase))
            this.Save.Data.CardboardScraps = checked(Math.Max(0, this.Save.Data.CardboardScraps) + amount);
        else
            this.Save.Data.ShinyScraps = checked(Math.Max(0, this.Save.Data.ShinyScraps) + amount);

        if (persist)
            this.Save.Save();
    }

    public bool TryConsume(string unqualifiedObjectId, int amount)
    {
        if (amount <= 0)
            return true;

        if (!IsScrapId(unqualifiedObjectId))
            return false;

        if (!this.IsBinderWalletActive)
        {
            int physical = CountPhysicalScraps(unqualifiedObjectId);
            int wallet = GetWalletCount(unqualifiedObjectId);
            if (physical + wallet < amount)
                return false;

            int removedPhysical = RemovePhysicalScraps(unqualifiedObjectId, amount);
            int remaining = amount - removedPhysical;
            if (remaining > 0)
                SetWalletCount(unqualifiedObjectId, Math.Max(0, wallet - remaining));

            if (remaining > 0)
                this.Save.Save();

            return true;
        }

        int current = GetWalletCount(unqualifiedObjectId);
        if (current < amount)
            return false;

        SetWalletCount(unqualifiedObjectId, current - amount);
        this.Save.Save();
        return true;
    }

    /// <summary>
    /// Reconcile old saves with the current physical-before-Binder / wallet-after-Binder rule.
    /// </summary>
    public (int Normal, int Shiny) SyncStorageModeOnLoad()
    {
        if (!Context.IsWorldReady)
            return (0, 0);

        return this.IsBinderWalletActive
            ? this.MigrateInventoryScraps()
            : this.MaterializeWalletScraps();
    }

    /// <summary>
    /// Called at the Wizard handoff. Every physical Scrap stack is absorbed into the Binder.
    /// </summary>
    public (int Normal, int Shiny) ActivateBinderWallet()
        => this.MigrateInventoryScraps();

    public (int Normal, int Shiny) MigrateInventoryScraps()
    {
        if (!Context.IsWorldReady)
            return (0, 0);

        int normal = RemovePhysicalScraps(DropService.CardboardScrapId, int.MaxValue);
        int shiny = RemovePhysicalScraps(DropService.ShinyScrapId, int.MaxValue);

        if (normal > 0)
            this.Save.Data.CardboardScraps = checked(Math.Max(0, this.Save.Data.CardboardScraps) + normal);
        if (shiny > 0)
            this.Save.Data.ShinyScraps = checked(Math.Max(0, this.Save.Data.ShinyScraps) + shiny);

        if (normal > 0 || shiny > 0)
            this.Save.Save();

        return (normal, shiny);
    }

    private (int Normal, int Shiny) MaterializeWalletScraps()
    {
        int normal = Math.Max(0, this.Save.Data.CardboardScraps);
        int shiny = Math.Max(0, this.Save.Data.ShinyScraps);

        if (normal <= 0 && shiny <= 0)
            return (0, 0);

        this.Save.Data.CardboardScraps = 0;
        this.Save.Data.ShinyScraps = 0;
        this.Save.Save();

        if (normal > 0)
            AddPhysicalScrapsToPlayer(DropService.CardboardScrapId, normal);
        if (shiny > 0)
            AddPhysicalScrapsToPlayer(DropService.ShinyScrapId, shiny);

        return (normal, shiny);
    }

    private int GetWalletCount(string unqualifiedObjectId)
        => unqualifiedObjectId.Equals(DropService.CardboardScrapId, StringComparison.OrdinalIgnoreCase)
            ? Math.Max(0, this.Save.Data.CardboardScraps)
            : unqualifiedObjectId.Equals(DropService.ShinyScrapId, StringComparison.OrdinalIgnoreCase)
                ? Math.Max(0, this.Save.Data.ShinyScraps)
                : 0;

    private void SetWalletCount(string unqualifiedObjectId, int value)
    {
        value = Math.Max(0, value);
        if (unqualifiedObjectId.Equals(DropService.CardboardScrapId, StringComparison.OrdinalIgnoreCase))
            this.Save.Data.CardboardScraps = value;
        else if (unqualifiedObjectId.Equals(DropService.ShinyScrapId, StringComparison.OrdinalIgnoreCase))
            this.Save.Data.ShinyScraps = value;
    }

    private static bool IsScrapId(string unqualifiedObjectId)
        => unqualifiedObjectId.Equals(DropService.CardboardScrapId, StringComparison.OrdinalIgnoreCase)
           || unqualifiedObjectId.Equals(DropService.ShinyScrapId, StringComparison.OrdinalIgnoreCase);

    private static int CountPhysicalScraps(string unqualifiedObjectId)
    {
        if (!Context.IsWorldReady)
            return 0;

        string qualified = $"(O){unqualifiedObjectId}";
        int count = 0;
        foreach (Item? item in Game1.player.Items)
        {
            if (item is not null && item.QualifiedItemId.Equals(qualified, StringComparison.OrdinalIgnoreCase))
                count = checked(count + Math.Max(0, item.Stack));
        }

        return count;
    }

    private static int RemovePhysicalScraps(string unqualifiedObjectId, int requested)
    {
        if (!Context.IsWorldReady || requested <= 0)
            return 0;

        string qualified = $"(O){unqualifiedObjectId}";
        int remaining = requested;
        int moved = 0;

        for (int i = 0; i < Game1.player.Items.Count && remaining > 0; i++)
        {
            Item? item = Game1.player.Items[i];
            if (item is null || !item.QualifiedItemId.Equals(qualified, StringComparison.OrdinalIgnoreCase))
                continue;

            int take = Math.Min(Math.Max(0, item.Stack), remaining);
            moved += take;
            remaining -= take;
            item.Stack -= take;
            if (item.Stack <= 0)
                Game1.player.Items[i] = null;
        }

        return moved;
    }

    private static void AddPhysicalScrapsToPlayer(string unqualifiedObjectId, int amount)
    {
        if (!Context.IsWorldReady || amount <= 0)
            return;

        int remaining = amount;
        while (remaining > 0)
        {
            int stack = Math.Min(999, remaining);
            Item item = ItemRegistry.Create($"(O){unqualifiedObjectId}");
            item.Stack = stack;

            Item? leftover = Game1.player.addItemToInventory(item);
            if (leftover is not null && Game1.currentLocation is not null)
                Game1.createItemDebris(leftover, Game1.player.Position, -1, Game1.currentLocation);

            remaining -= stack;
        }
    }
}

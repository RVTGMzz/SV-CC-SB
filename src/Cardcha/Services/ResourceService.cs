using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Stores Cardcha pull currency in save data instead of backpack slots.
/// Physical Scrap items from older builds are migrated into this wallet on load.
/// </summary>
internal sealed class ResourceService
{
    private readonly SaveService Save;

    public ResourceService(SaveService save)
    {
        this.Save = save;
    }

    public int Count(string unqualifiedObjectId)
        => unqualifiedObjectId switch
        {
            DropService.CardboardScrapId => Math.Max(0, this.Save.Data.CardboardScraps),
            DropService.ShinyScrapId => Math.Max(0, this.Save.Data.ShinyScraps),
            _ => 0
        };

    public void Add(string unqualifiedObjectId, int amount, bool persist = true)
    {
        if (amount <= 0)
            return;

        if (unqualifiedObjectId.Equals(DropService.CardboardScrapId, StringComparison.OrdinalIgnoreCase))
            this.Save.Data.CardboardScraps = checked(Math.Max(0, this.Save.Data.CardboardScraps) + amount);
        else if (unqualifiedObjectId.Equals(DropService.ShinyScrapId, StringComparison.OrdinalIgnoreCase))
            this.Save.Data.ShinyScraps = checked(Math.Max(0, this.Save.Data.ShinyScraps) + amount);
        else
            return;

        if (persist)
            this.Save.Save();
    }

    public bool TryConsume(string unqualifiedObjectId, int amount)
    {
        if (amount <= 0)
            return true;

        int current = Count(unqualifiedObjectId);
        if (current < amount)
            return false;

        if (unqualifiedObjectId.Equals(DropService.CardboardScrapId, StringComparison.OrdinalIgnoreCase))
            this.Save.Data.CardboardScraps = current - amount;
        else if (unqualifiedObjectId.Equals(DropService.ShinyScrapId, StringComparison.OrdinalIgnoreCase))
            this.Save.Data.ShinyScraps = current - amount;
        else
            return false;

        this.Save.Save();
        return true;
    }

    public (int Normal, int Shiny) MigrateInventoryScraps()
    {
        if (!Context.IsWorldReady)
            return (0, 0);

        int normal = RemovePhysicalScraps(DropService.CardboardScrapId);
        int shiny = RemovePhysicalScraps(DropService.ShinyScrapId);

        if (normal > 0)
            this.Save.Data.CardboardScraps += normal;
        if (shiny > 0)
            this.Save.Data.ShinyScraps += shiny;

        if (normal > 0 || shiny > 0)
            this.Save.Save();

        return (normal, shiny);
    }

    private static int RemovePhysicalScraps(string unqualifiedObjectId)
    {
        string qualified = $"(O){unqualifiedObjectId}";
        int moved = 0;

        for (int i = 0; i < Game1.player.Items.Count; i++)
        {
            Item? item = Game1.player.Items[i];
            if (item is null || !item.QualifiedItemId.Equals(qualified, StringComparison.OrdinalIgnoreCase))
                continue;

            moved += Math.Max(0, item.Stack);
            Game1.player.Items[i] = null;
        }

        return moved;
    }
}

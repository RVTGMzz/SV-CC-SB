using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Owns the portable Cardcha Machine entitlement and hotbar interaction.
/// The stationary machine remains a FarmHouse appliance; this item opens the dedicated
/// portable Cardcha UI from normal gameplay locations without being placeable as a world machine.
/// </summary>
internal sealed class PortableMachineService
{
    public const int PurchasePrice = 20000;
    public const int FreeGiftCardMilestone = 20;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly Action OpenMachineMenu;

    public PortableMachineService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        Action openMachineMenu)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.OpenMachineMenu = openMachineMenu;
    }

    public int UniqueCardCount => this.Save.Data.OwnedCards?.Count ?? 0;

    public bool IsAcquired
        => this.Save.Data.PortableMachinePurchased
           || this.Save.Data.PortableMachineGifted;

    public bool IsMilestoneGiftReady
        => Context.IsWorldReady
           && this.Save.Data.MachineDelivered
           && this.Save.Data.BinderUnlocked
           && !this.IsAcquired
           && this.UniqueCardCount >= FreeGiftCardMilestone
           && this.Save.Data.Region1BossDefeated;

    public void OnSaveLoaded()
    {
        if (!Context.IsWorldReady || this.IsAcquired)
            return;

        // Self-heal test saves where a portable device already exists in the backpack
        // but the v11 entitlement flags were not written yet.
        if (Game1.player.Items.Any(item => ItemAssetService.IsPortableMachine(item)))
        {
            this.Save.Data.PortableMachinePurchased = true;
            this.Save.Save();
            this.Monitor.Log(
                "Detected an existing Portable Cardcha Machine in the backpack; entitlement flag restored.",
                LogLevel.Trace
            );
        }
    }

    /// <summary>Compatibility claim path after the 20-card Boss I clear.</summary>
    public bool TryGrantMilestoneGift()
    {
        if (!this.IsMilestoneGiftReady)
            return false;
        return this.GrantRegion1BossReward();
    }

    /// <summary>First-clear Boss I reward. Safe when the player already owns the portable machine.</summary>
    public bool GrantRegion1BossReward()
    {
        if (!Context.IsWorldReady || this.IsAcquired)
            return false;

        this.Save.Data.PortableMachineGifted = true;
        this.GivePortableItem();
        this.Save.Save();
        this.Monitor.Log("Boss I granted the Portable Cardcha Machine.", LogLevel.Info);
        return true;
    }

    public PortablePurchaseResult TryPurchase()
    {
        if (!Context.IsWorldReady || !this.Save.Data.MachineDelivered || !this.Save.Data.BinderUnlocked)
            return PortablePurchaseResult.Locked;

        if (this.IsAcquired)
            return PortablePurchaseResult.AlreadyOwned;

        if (this.IsMilestoneGiftReady)
        {
            this.TryGrantMilestoneGift();
            return PortablePurchaseResult.Gifted;
        }

        if (Game1.player.Money < PurchasePrice)
            return PortablePurchaseResult.NotEnoughMoney;

        Game1.player.Money -= PurchasePrice;
        this.Save.Data.PortableMachinePurchased = true;
        this.GivePortableItem();
        this.Save.Save();

        this.Monitor.Log(
            $"Portable Cardcha Machine purchased from MiMi for {PurchasePrice}g.",
            LogLevel.Info
        );
        return PortablePurchaseResult.Purchased;
    }

    public void GiveForDebug()
    {
        if (!Context.IsWorldReady)
            return;

        this.Save.Data.PortableMachinePurchased = true;
        this.GivePortableItem();
        this.Save.Save();
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady
            || Game1.player is null
            || Game1.activeClickableMenu is not null
            || (!e.Button.IsUseToolButton() && !e.Button.IsActionButton()))
        {
            return;
        }

        Item? active = Game1.player.CurrentItem;
        if (!ItemAssetService.IsPortableMachine(active))
            return;

        // Consume BOTH use-tool and action before vanilla/Cinderbox can route this BigCraftable into placement.
        this.Helper.Input.Suppress(e.Button);

        if (Game1.eventUp || Game1.CurrentEvent is not null)
        {
            Game1.showGlobalMessage(ModEntry.T("portable.machine.busy"));
            Game1.playSound("cancel");
            return;
        }

        if (!this.Save.Data.MachineDelivered || !this.Save.Data.BinderUnlocked)
        {
            Game1.showGlobalMessage(ModEntry.T("portable.machine.locked"));
            Game1.playSound("cancel");
            return;
        }

        Game1.playSound("bigSelect");
        this.OpenMachineMenu();
    }

    public string Describe()
        => $"Portable acquired={this.IsAcquired} " +
           $"(purchased={this.Save.Data.PortableMachinePurchased}, gifted={this.Save.Data.PortableMachineGifted}) | " +
           $"UniqueCards={this.UniqueCardCount}/{FreeGiftCardMilestone} | GiftReady={this.IsMilestoneGiftReady}";

    private void GivePortableItem()
    {
        Item item = ItemAssetService.CreatePortableMachineItem();
        Item? leftover = Game1.player.addItemToInventory(item);
        if (leftover is not null && Game1.currentLocation is not null)
            Game1.createItemDebris(leftover, Game1.player.Position, -1, Game1.currentLocation);
    }
}

internal enum PortablePurchaseResult
{
    Purchased,
    Gifted,
    AlreadyOwned,
    NotEnoughMoney,
    Locked
}

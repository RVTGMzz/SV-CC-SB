using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

/// <summary>
/// MiMi's intentionally shameless Scrap exchange plus her aggressively-priced
/// Portable Cardcha Machine.
/// </summary>
internal sealed class MimiScrapShopMenu : IClickableMenu
{
    // Player-facing prices. MiMi's own perspective is the reverse:
    // normal: she buys for 100g / sells for 1,000g;
    // shiny:  she buys for 1,000g / sells for 10,000g.
    private const int NormalBuyPrice = 1000;
    private const int NormalSellPrice = 100;
    private const int ShinyBuyPrice = 10000;
    private const int ShinySellPrice = 1000;

    private const int CloseId = 100;
    private const int NormalBuyId = 200;
    private const int NormalSellId = 201;
    private const int ShinyBuyId = 202;
    private const int ShinySellId = 203;
    private const int PortableBuyId = 204;

    private readonly ResourceService Resources;
    private readonly SaveService Save;
    private readonly PortableMachineService PortableMachine;
    private readonly Texture2D? ItemTexture;
    private readonly Texture2D? MachineTexture;

    private readonly ClickableComponent CloseButton;
    private readonly ClickableComponent NormalBuyButton;
    private readonly ClickableComponent NormalSellButton;
    private readonly ClickableComponent ShinyBuyButton;
    private readonly ClickableComponent ShinySellButton;
    private readonly ClickableComponent PortableBuyButton;

    private string Status = ModEntry.T("mimi.shop.status.welcome");

    public MimiScrapShopMenu(
        ResourceService resources,
        SaveService save,
        PortableMachineService portableMachine)
        : base(
            Game1.uiViewport.Width / 2 - Math.Min(760, Game1.uiViewport.Width - 32) / 2,
            Game1.uiViewport.Height / 2 - Math.Min(610, Game1.uiViewport.Height - 32) / 2,
            Math.Min(760, Game1.uiViewport.Width - 32),
            Math.Min(610, Game1.uiViewport.Height - 32),
            showUpperRightCloseButton: false)
    {
        this.Resources = resources;
        this.Save = save;
        this.PortableMachine = portableMachine;
        this.ItemTexture = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/items.png");
        this.MachineTexture = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/portable_machine.png");

        int rowX = this.xPositionOnScreen + 50;
        int rowW = this.width - 100;
        int buyX = rowX + rowW - 232;

        int normalY = this.yPositionOnScreen + 170;
        int shinyY = normalY + 96;
        int portableY = shinyY + 96;

        this.NormalBuyButton = new ClickableComponent(
            new Rectangle(buyX, normalY + 22, 106, 42),
            "normal-buy") { myID = NormalBuyId };
        this.NormalSellButton = new ClickableComponent(
            new Rectangle(buyX + 116, normalY + 22, 106, 42),
            "normal-sell") { myID = NormalSellId };
        this.ShinyBuyButton = new ClickableComponent(
            new Rectangle(buyX, shinyY + 22, 106, 42),
            "shiny-buy") { myID = ShinyBuyId };
        this.ShinySellButton = new ClickableComponent(
            new Rectangle(buyX + 116, shinyY + 22, 106, 42),
            "shiny-sell") { myID = ShinySellId };
        this.PortableBuyButton = new ClickableComponent(
            new Rectangle(buyX + 54, portableY + 28, 168, 44),
            "portable-buy") { myID = PortableBuyId };
        this.CloseButton = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + 34, this.yPositionOnScreen + this.height - 62, 150, 40),
            "close") { myID = CloseId };

        this.NormalBuyButton.rightNeighborID = NormalSellId;
        this.NormalBuyButton.downNeighborID = ShinyBuyId;
        this.NormalSellButton.leftNeighborID = NormalBuyId;
        this.NormalSellButton.downNeighborID = ShinySellId;
        this.ShinyBuyButton.upNeighborID = NormalBuyId;
        this.ShinyBuyButton.rightNeighborID = ShinySellId;
        this.ShinyBuyButton.downNeighborID = PortableBuyId;
        this.ShinySellButton.upNeighborID = NormalSellId;
        this.ShinySellButton.leftNeighborID = ShinyBuyId;
        this.ShinySellButton.downNeighborID = PortableBuyId;
        this.PortableBuyButton.upNeighborID = ShinyBuyId;
        this.PortableBuyButton.downNeighborID = CloseId;
        this.CloseButton.upNeighborID = PortableBuyId;

        // Milestone reward is intentionally delivered when MiMi is actually present,
        // so the gift feels like it comes from her rather than appearing from nowhere.
        if (this.PortableMachine.TryGrantMilestoneGift())
            this.Status = ModEntry.T("portable.shop.status.gifted");

        this.populateClickableComponentList();
        if (Game1.options.SnappyMenus)
            this.snapToDefaultClickableComponent();
    }

    public override void populateClickableComponentList()
    {
        base.populateClickableComponentList();
        this.allClickableComponents.Clear();
        this.allClickableComponents.Add(this.NormalBuyButton);
        this.allClickableComponents.Add(this.NormalSellButton);
        this.allClickableComponents.Add(this.ShinyBuyButton);
        this.allClickableComponents.Add(this.ShinySellButton);
        this.allClickableComponents.Add(this.PortableBuyButton);
        this.allClickableComponents.Add(this.CloseButton);
    }

    public override void snapToDefaultClickableComponent()
    {
        this.currentlySnappedComponent = this.NormalBuyButton;
        this.snapCursorToCurrentSnappedComponent();
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        if (this.CloseButton.containsPoint(x, y))
        {
            Game1.playSound("bigDeSelect");
            Game1.exitActiveMenu();
            return;
        }

        if (this.NormalBuyButton.containsPoint(x, y))
        {
            this.Buy(DropService.CardboardScrapId);
            return;
        }

        if (this.NormalSellButton.containsPoint(x, y))
        {
            this.Sell(DropService.CardboardScrapId);
            return;
        }

        if (this.ShinyBuyButton.containsPoint(x, y))
        {
            this.Buy(DropService.ShinyScrapId);
            return;
        }

        if (this.ShinySellButton.containsPoint(x, y))
        {
            this.Sell(DropService.ShinyScrapId);
            return;
        }

        if (this.PortableBuyButton.containsPoint(x, y))
            this.BuyPortableMachine();
    }

    public override void receiveKeyPress(Keys key)
    {
        if (key == Keys.Escape)
        {
            Game1.playSound("bigDeSelect");
            Game1.exitActiveMenu();
            return;
        }

        base.receiveKeyPress(key);
    }

    public override void receiveGamePadButton(Buttons b)
    {
        if (b == Buttons.B)
        {
            Game1.playSound("bigDeSelect");
            Game1.exitActiveMenu();
            return;
        }

        if (b == Buttons.A && this.currentlySnappedComponent is not null)
        {
            switch (this.currentlySnappedComponent.myID)
            {
                case NormalBuyId:
                    this.Buy(DropService.CardboardScrapId);
                    return;
                case NormalSellId:
                    this.Sell(DropService.CardboardScrapId);
                    return;
                case ShinyBuyId:
                    this.Buy(DropService.ShinyScrapId);
                    return;
                case ShinySellId:
                    this.Sell(DropService.ShinyScrapId);
                    return;
                case PortableBuyId:
                    this.BuyPortableMachine();
                    return;
                case CloseId:
                    Game1.playSound("bigDeSelect");
                    Game1.exitActiveMenu();
                    return;
            }
        }

        base.receiveGamePadButton(b);
    }

    private void Buy(string resourceId)
    {
        int price = GetBuyPrice(resourceId);
        if (Game1.player.Money < price)
        {
            this.Status = ModEntry.T("mimi.shop.status.poor");
            Game1.playSound("cancel");
            return;
        }

        Game1.player.Money -= price;
        this.Resources.Add(resourceId, 1);
        this.Status = ModEntry.T("mimi.shop.status.bought", new { price });
        Game1.playSound("coin");
    }

    private void Sell(string resourceId)
    {
        int price = GetSellPrice(resourceId);
        if (!this.Resources.TryConsume(resourceId, 1))
        {
            this.Status = ModEntry.T("mimi.shop.status.empty");
            Game1.playSound("cancel");
            return;
        }

        Game1.player.Money += price;
        this.Save.Save();
        this.Status = ModEntry.T("mimi.shop.status.sold", new { price });
        Game1.playSound("coin");
    }

    private void BuyPortableMachine()
    {
        PortablePurchaseResult result = this.PortableMachine.TryPurchase();
        switch (result)
        {
            case PortablePurchaseResult.Purchased:
                this.Status = ModEntry.T("portable.shop.status.bought");
                Game1.playSound("purchase");
                break;
            case PortablePurchaseResult.Gifted:
                this.Status = ModEntry.T("portable.shop.status.gifted");
                Game1.playSound("coin");
                break;
            case PortablePurchaseResult.AlreadyOwned:
                this.Status = ModEntry.T("portable.shop.status.owned");
                Game1.playSound("cancel");
                break;
            case PortablePurchaseResult.NotEnoughMoney:
                this.Status = ModEntry.T("portable.shop.status.poor");
                Game1.playSound("cancel");
                break;
            default:
                this.Status = ModEntry.T("portable.shop.status.locked");
                Game1.playSound("cancel");
                break;
        }
    }

    private static int GetBuyPrice(string resourceId)
        => resourceId.Equals(DropService.ShinyScrapId, StringComparison.OrdinalIgnoreCase)
            ? ShinyBuyPrice
            : NormalBuyPrice;

    private static int GetSellPrice(string resourceId)
        => resourceId.Equals(DropService.ShinyScrapId, StringComparison.OrdinalIgnoreCase)
            ? ShinySellPrice
            : NormalSellPrice;

    public override void draw(SpriteBatch b)
    {
        b.Draw(
            Game1.fadeToBlackRect,
            Game1.graphics.GraphicsDevice.Viewport.Bounds,
            Color.Black * 0.72f
        );

        Rectangle panel = new(this.xPositionOnScreen, this.yPositionOnScreen, this.width, this.height);
        CardchaUi.DrawInsetPanel(
            b,
            panel,
            new Color(57, 44, 69),
            new Color(119, 79, 84),
            5,
            8
        );

        Rectangle paper = new(panel.X + 24, panel.Y + 24, panel.Width - 48, panel.Height - 48);
        CardchaUi.DrawInsetPanel(
            b,
            paper,
            new Color(240, 218, 181),
            new Color(166, 124, 83),
            3,
            5
        );

        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("mimi.shop.title"),
            new Rectangle(paper.X + 28, paper.Y + 14, paper.Width - 56, 44),
            CardchaUi.InkBrown,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.05f
        );

        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            ModEntry.T("mimi.shop.quip.portable"),
            new Rectangle(paper.X + 40, paper.Y + 64, paper.Width - 80, 74),
            Color.DarkSlateGray,
            maxLines: 3,
            minScale: 0.67f,
            centerX: true,
            maxScale: 1.00f
        );

        int normalY = this.yPositionOnScreen + 170;
        int shinyY = normalY + 96;
        int portableY = shinyY + 96;

        this.DrawResourceRow(
            b,
            normalY,
            0,
            ModEntry.T("item.cardboard.name"),
            this.Resources.Count(DropService.CardboardScrapId),
            DropService.CardboardScrapId,
            this.NormalBuyButton,
            this.NormalSellButton
        );
        this.DrawResourceRow(
            b,
            shinyY,
            1,
            ModEntry.T("item.shiny.name"),
            this.Resources.Count(DropService.ShinyScrapId),
            DropService.ShinyScrapId,
            this.ShinyBuyButton,
            this.ShinySellButton
        );
        this.DrawPortableRow(b, portableY);

        Rectangle status = new(
            paper.X + 190,
            paper.Bottom - 56,
            paper.Width - 226,
            34
        );
        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            this.Status,
            status,
            Color.DarkSlateGray,
            maxLines: 2,
            minScale: 0.65f,
            maxScale: 0.96f
        );

        CardchaUi.DrawButton(
            b,
            this.CloseButton,
            ModEntry.T("mimi.shop.close"),
            new Color(112, 76, 72),
            enabled: true
        );

        this.drawMouse(b);
    }

    private void DrawResourceRow(
        SpriteBatch b,
        int y,
        int spriteIndex,
        string name,
        int count,
        string resourceId,
        ClickableComponent buyButton,
        ClickableComponent sellButton)
    {
        Rectangle row = new(this.xPositionOnScreen + 50, y, this.width - 100, 84);
        b.Draw(Game1.staminaRect, row, new Color(255, 245, 219) * 0.72f);
        CardchaUi.DrawBorder(b, row, new Color(142, 101, 72), 2);

        Rectangle iconBox = new(row.X + 16, row.Y + 10, 62, 62);
        b.Draw(Game1.staminaRect, iconBox, new Color(67, 53, 66));
        CardchaUi.DrawBorder(b, iconBox, CardchaUi.Gold * 0.75f, 2);

        if (this.ItemTexture is not null)
        {
            b.Draw(
                this.ItemTexture,
                iconBox,
                new Rectangle(spriteIndex * 16, 0, 16, 16),
                Color.White
            );
        }

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            name,
            new Rectangle(row.X + 94, row.Y + 8, row.Width - 340, 32),
            CardchaUi.InkBrown,
            padding: 2,
            maxScale: 1.00f
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("mimi.shop.owned", new { count }),
            new Rectangle(row.X + 94, row.Y + 44, row.Width - 340, 26),
            Color.DarkSlateGray,
            padding: 2,
            maxScale: 0.92f
        );

        int buyPrice = GetBuyPrice(resourceId);
        int sellPrice = GetSellPrice(resourceId);
        bool canBuy = Game1.player.Money >= buyPrice;
        bool canSell = count > 0;
        CardchaUi.DrawButton(
            b,
            buyButton,
            ModEntry.T("mimi.shop.buy", new { price = buyPrice }),
            new Color(93, 124, 83),
            canBuy
        );
        CardchaUi.DrawButton(
            b,
            sellButton,
            ModEntry.T("mimi.shop.sell", new { price = sellPrice }),
            new Color(139, 92, 73),
            canSell
        );

        if (this.currentlySnappedComponent?.myID == buyButton.myID)
            CardchaUi.DrawFocus(b, buyButton.bounds);
        if (this.currentlySnappedComponent?.myID == sellButton.myID)
            CardchaUi.DrawFocus(b, sellButton.bounds);
    }

    private void DrawPortableRow(SpriteBatch b, int y)
    {
        Rectangle row = new(this.xPositionOnScreen + 50, y, this.width - 100, 96);
        b.Draw(Game1.staminaRect, row, new Color(248, 232, 202) * 0.84f);
        CardchaUi.DrawBorder(b, row, new Color(142, 101, 72), 2);

        Rectangle iconBox = new(row.X + 16, row.Y + 16, 64, 64);
        b.Draw(Game1.staminaRect, iconBox, new Color(67, 53, 66));
        CardchaUi.DrawBorder(b, iconBox, CardchaUi.Gold, 2);
        if (this.MachineTexture is not null)
        {
            Rectangle machineTarget = new(
                iconBox.Center.X - 16,
                iconBox.Y,
                32,
                64
            );
            b.Draw(
                this.MachineTexture,
                machineTarget,
                new Rectangle(0, 0, 16, 32),
                Color.White
            );
        }

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("portable.machine.name"),
            new Rectangle(row.X + 94, row.Y + 8, row.Width - 350, 32),
            CardchaUi.InkBrown,
            padding: 2,
            maxScale: 0.98f
        );

        string progress = this.PortableMachine.IsAcquired
            ? ModEntry.T("portable.shop.owned")
            : ModEntry.T(
                "portable.shop.progress",
                new
                {
                    count = this.PortableMachine.UniqueCardCount,
                    target = PortableMachineService.FreeGiftCardMilestone
                }
            );

        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            progress,
            new Rectangle(row.X + 94, row.Y + 42, row.Width - 350, 42),
            Color.DarkSlateGray,
            maxLines: 2,
            minScale: 0.62f,
            maxScale: 0.90f
        );

        string buttonLabel = this.PortableMachine.IsAcquired
            ? ModEntry.T("portable.shop.button.owned")
            : this.PortableMachine.IsMilestoneGiftReady
                ? ModEntry.T("portable.shop.button.free")
                : ModEntry.T("mimi.shop.buy", new { price = PortableMachineService.PurchasePrice });

        bool enabled = !this.PortableMachine.IsAcquired
            && (this.PortableMachine.IsMilestoneGiftReady
                || Game1.player.Money >= PortableMachineService.PurchasePrice);

        CardchaUi.DrawButton(
            b,
            this.PortableBuyButton,
            buttonLabel,
            new Color(111, 86, 129),
            enabled
        );

        if (this.currentlySnappedComponent?.myID == this.PortableBuyButton.myID)
            CardchaUi.DrawFocus(b, this.PortableBuyButton.bounds);
    }
}

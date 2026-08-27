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

    private const int QuantityMinusId = 300;
    private const int QuantityPlusId = 301;
    private const int QuantityConfirmId = 302;
    private const int QuantityCancelId = 303;

    private readonly ResourceService Resources;
    private readonly SaveService Save;
    private readonly PortableMachineService PortableMachine;
    private readonly ControllerProfileService Controller;
    private readonly Texture2D? ItemTexture;
    private readonly Texture2D? MachineTexture;

    private readonly ClickableComponent CloseButton;
    private readonly ClickableComponent NormalBuyButton;
    private readonly ClickableComponent NormalSellButton;
    private readonly ClickableComponent ShinyBuyButton;
    private readonly ClickableComponent ShinySellButton;
    private readonly ClickableComponent PortableBuyButton;
    private readonly ClickableComponent QuantityMinusButton;
    private readonly ClickableComponent QuantityPlusButton;
    private readonly ClickableComponent QuantityConfirmButton;
    private readonly ClickableComponent QuantityCancelButton;

    private string? QuantityResourceId;
    private bool QuantityBuying;
    private int Quantity = 1;
    private int QuantityReturnFocusId = NormalBuyId;

    private bool QuantityOpen => !string.IsNullOrEmpty(this.QuantityResourceId);

    private string Status = ModEntry.T("mimi.shop.status.welcome");

    public MimiScrapShopMenu(
        ResourceService resources,
        SaveService save,
        PortableMachineService portableMachine,
        ControllerProfileService controller)
        : base(
            Game1.uiViewport.Width / 2 - Math.Min(860, Game1.uiViewport.Width - 24) / 2,
            Game1.uiViewport.Height / 2 - Math.Min(650, Game1.uiViewport.Height - 24) / 2,
            Math.Min(860, Game1.uiViewport.Width - 24),
            Math.Min(650, Game1.uiViewport.Height - 24),
            showUpperRightCloseButton: false)
    {
        this.Resources = resources;
        this.Save = save;
        this.PortableMachine = portableMachine;
        this.Controller = controller;
        this.ItemTexture = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/items.png");
        this.MachineTexture = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/portable_machine.png");

        int rowX = this.xPositionOnScreen + 50;
        int rowW = this.width - 100;
        int buyX = rowX + rowW - 274;

        int normalY = this.yPositionOnScreen + 180;
        int shinyY = normalY + 102;
        int portableY = shinyY + 102;

        this.NormalBuyButton = new ClickableComponent(
            new Rectangle(buyX, normalY + 22, 124, 48),
            "normal-buy") { myID = NormalBuyId };
        this.NormalSellButton = new ClickableComponent(
            new Rectangle(buyX + 134, normalY + 22, 124, 48),
            "normal-sell") { myID = NormalSellId };
        this.ShinyBuyButton = new ClickableComponent(
            new Rectangle(buyX, shinyY + 22, 124, 48),
            "shiny-buy") { myID = ShinyBuyId };
        this.ShinySellButton = new ClickableComponent(
            new Rectangle(buyX + 134, shinyY + 22, 124, 48),
            "shiny-sell") { myID = ShinySellId };
        this.PortableBuyButton = new ClickableComponent(
            new Rectangle(buyX + 36, portableY + 26, 222, 52),
            "portable-buy") { myID = PortableBuyId };
        this.CloseButton = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + 34, this.yPositionOnScreen + this.height - 66, 170, 46),
            "close") { myID = CloseId };

        int quantityCenterX = this.xPositionOnScreen + this.width / 2;
        int quantityCenterY = this.yPositionOnScreen + this.height / 2 + 12;
        this.QuantityMinusButton = new ClickableComponent(
            new Rectangle(quantityCenterX - 150, quantityCenterY - 12, 72, 58),
            "quantity-minus") { myID = QuantityMinusId };
        this.QuantityPlusButton = new ClickableComponent(
            new Rectangle(quantityCenterX + 78, quantityCenterY - 12, 72, 58),
            "quantity-plus") { myID = QuantityPlusId };
        this.QuantityConfirmButton = new ClickableComponent(
            new Rectangle(quantityCenterX - 160, quantityCenterY + 74, 150, 48),
            "quantity-confirm") { myID = QuantityConfirmId };
        this.QuantityCancelButton = new ClickableComponent(
            new Rectangle(quantityCenterX + 10, quantityCenterY + 74, 150, 48),
            "quantity-cancel") { myID = QuantityCancelId };

        this.QuantityMinusButton.rightNeighborID = QuantityPlusId;
        this.QuantityMinusButton.downNeighborID = QuantityConfirmId;
        this.QuantityPlusButton.leftNeighborID = QuantityMinusId;
        this.QuantityPlusButton.downNeighborID = QuantityCancelId;
        this.QuantityConfirmButton.upNeighborID = QuantityMinusId;
        this.QuantityConfirmButton.rightNeighborID = QuantityCancelId;
        this.QuantityCancelButton.upNeighborID = QuantityPlusId;
        this.QuantityCancelButton.leftNeighborID = QuantityConfirmId;

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
        this.RebuildClickableComponents();
    }

    private void RebuildClickableComponents()
    {
        this.allClickableComponents.Clear();
        if (this.QuantityOpen)
        {
            this.allClickableComponents.Add(this.QuantityMinusButton);
            this.allClickableComponents.Add(this.QuantityPlusButton);
            this.allClickableComponents.Add(this.QuantityConfirmButton);
            this.allClickableComponents.Add(this.QuantityCancelButton);
            return;
        }

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
        if (this.QuantityOpen)
        {
            if (this.QuantityMinusButton.containsPoint(x, y))
                this.ChangeQuantity(-1);
            else if (this.QuantityPlusButton.containsPoint(x, y))
                this.ChangeQuantity(1);
            else if (this.QuantityConfirmButton.containsPoint(x, y))
                this.ConfirmQuantityTransaction();
            else if (this.QuantityCancelButton.containsPoint(x, y))
                this.CloseQuantitySelector();
            return;
        }

        if (this.CloseButton.containsPoint(x, y))
        {
            Game1.playSound("bigDeSelect");
            Game1.exitActiveMenu();
            return;
        }

        if (this.NormalBuyButton.containsPoint(x, y))
        {
            this.OpenQuantitySelector(DropService.CardboardScrapId, buying: true, NormalBuyId);
            return;
        }

        if (this.NormalSellButton.containsPoint(x, y))
        {
            this.OpenQuantitySelector(DropService.CardboardScrapId, buying: false, NormalSellId);
            return;
        }

        if (this.ShinyBuyButton.containsPoint(x, y))
        {
            this.OpenQuantitySelector(DropService.ShinyScrapId, buying: true, ShinyBuyId);
            return;
        }

        if (this.ShinySellButton.containsPoint(x, y))
        {
            this.OpenQuantitySelector(DropService.ShinyScrapId, buying: false, ShinySellId);
            return;
        }

        if (this.PortableBuyButton.containsPoint(x, y))
            this.BuyPortableMachine();
    }

    public override void receiveKeyPress(Keys key)
    {
        if (this.QuantityOpen)
        {
            if (key == Keys.Escape)
            {
                this.CloseQuantitySelector();
                return;
            }
            if (key is Keys.Enter or Keys.Space)
            {
                this.ActivateQuantityComponent(this.currentlySnappedComponent?.myID ?? QuantityConfirmId);
                return;
            }
        }
        else if (key == Keys.Escape)
        {
            Game1.playSound("bigDeSelect");
            Game1.exitActiveMenu();
            return;
        }

        base.receiveKeyPress(key);
    }

    public override void receiveGamePadButton(Buttons b)
    {
        // alpha.23: MiMi's shop uses the same semantic controller profile as the Binder,
        // so Steam Input / Nintendo-native differences can't silently swap confirm and exit.
        if (this.QuantityOpen)
        {
            if (this.Controller.IsExit(b) || this.Controller.IsDeselect(b))
            {
                this.CloseQuantitySelector();
                return;
            }
            if (this.Controller.IsConfirm(b))
            {
                this.ActivateQuantityComponent(this.currentlySnappedComponent?.myID ?? QuantityConfirmId);
                return;
            }
            if (this.Controller.IsFavorite(b))
                return;

            base.receiveGamePadButton(b);
            return;
        }

        if (this.Controller.IsExit(b))
        {
            Game1.playSound("bigDeSelect");
            Game1.exitActiveMenu();
            return;
        }

        if (this.Controller.IsConfirm(b) && this.currentlySnappedComponent is not null)
        {
            switch (this.currentlySnappedComponent.myID)
            {
                case NormalBuyId:
                    this.OpenQuantitySelector(DropService.CardboardScrapId, buying: true, NormalBuyId);
                    return;
                case NormalSellId:
                    this.OpenQuantitySelector(DropService.CardboardScrapId, buying: false, NormalSellId);
                    return;
                case ShinyBuyId:
                    this.OpenQuantitySelector(DropService.ShinyScrapId, buying: true, ShinyBuyId);
                    return;
                case ShinySellId:
                    this.OpenQuantitySelector(DropService.ShinyScrapId, buying: false, ShinySellId);
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

        // Favorite/Deselect don't have a shop action; consume them instead of allowing
        // the base menu to reinterpret a face button as Back/Close.
        if (this.Controller.IsFavorite(b) || this.Controller.IsDeselect(b))
            return;

        base.receiveGamePadButton(b);
    }

    private void OpenQuantitySelector(string resourceId, bool buying, int returnFocusId)
    {
        this.QuantityResourceId = resourceId;
        this.QuantityBuying = buying;
        this.Quantity = 1;
        this.QuantityReturnFocusId = returnFocusId;
        this.RebuildClickableComponents();
        this.currentlySnappedComponent = this.QuantityPlusButton;
        if (Game1.options.SnappyMenus)
            this.snapCursorToCurrentSnappedComponent();
        Game1.playSound("smallSelect");
    }

    private void CloseQuantitySelector()
    {
        this.QuantityResourceId = null;
        this.Quantity = 1;
        this.RebuildClickableComponents();
        this.currentlySnappedComponent = this.getComponentWithID(this.QuantityReturnFocusId) ?? this.NormalBuyButton;
        if (Game1.options.SnappyMenus)
            this.snapCursorToCurrentSnappedComponent();
        Game1.playSound("bigDeSelect");
    }

    private int GetQuantityMaximum()
    {
        if (string.IsNullOrEmpty(this.QuantityResourceId))
            return 1;

        if (this.QuantityBuying)
        {
            int price = GetBuyPrice(this.QuantityResourceId);
            int affordable = price <= 0 ? 999 : Game1.player.Money / price;
            return Math.Clamp(Math.Max(1, affordable), 1, 999);
        }

        return Math.Clamp(Math.Max(1, this.Resources.Count(this.QuantityResourceId)), 1, 999);
    }

    private void ChangeQuantity(int delta)
    {
        int next = Math.Clamp(this.Quantity + delta, 1, this.GetQuantityMaximum());
        if (next == this.Quantity)
        {
            Game1.playSound("cancel");
            return;
        }

        this.Quantity = next;
        Game1.playSound("shiny4");
    }

    private void ActivateQuantityComponent(int componentId)
    {
        switch (componentId)
        {
            case QuantityMinusId:
                this.ChangeQuantity(-1);
                break;
            case QuantityPlusId:
                this.ChangeQuantity(1);
                break;
            case QuantityCancelId:
                this.CloseQuantitySelector();
                break;
            default:
                this.ConfirmQuantityTransaction();
                break;
        }
    }

    private void ConfirmQuantityTransaction()
    {
        if (string.IsNullOrEmpty(this.QuantityResourceId))
            return;

        string resourceId = this.QuantityResourceId;
        int amount = Math.Max(1, this.Quantity);
        bool completed = this.QuantityBuying
            ? this.Buy(resourceId, amount)
            : this.Sell(resourceId, amount);

        if (completed)
        {
            this.QuantityResourceId = null;
            this.Quantity = 1;
            this.RebuildClickableComponents();
            this.currentlySnappedComponent = this.getComponentWithID(this.QuantityReturnFocusId) ?? this.NormalBuyButton;
            if (Game1.options.SnappyMenus)
                this.snapCursorToCurrentSnappedComponent();
        }
    }

    private bool Buy(string resourceId, int amount)
    {
        int price = GetBuyPrice(resourceId);
        int total = checked(price * Math.Max(1, amount));
        if (Game1.player.Money < total)
        {
            this.Status = ModEntry.T("mimi.shop.status.poor");
            Game1.playSound("cancel");
            return false;
        }

        Game1.player.Money -= total;
        this.Resources.Add(resourceId, amount);
        this.Status = ModEntry.T("mimi.shop.status.bought", new { price = total });
        Game1.playSound("coin");
        return true;
    }

    private bool Sell(string resourceId, int amount)
    {
        int price = GetSellPrice(resourceId);
        int count = this.Resources.Count(resourceId);
        if (count < amount)
        {
            this.Status = ModEntry.T("mimi.shop.status.empty");
            Game1.playSound("cancel");
            return false;
        }

        if (!this.Resources.TryConsume(resourceId, amount))
        {
            this.Status = ModEntry.T("mimi.shop.status.empty");
            Game1.playSound("cancel");
            return false;
        }

        int total = checked(price * Math.Max(1, amount));
        Game1.player.Money += total;
        this.Save.Save();
        this.Status = ModEntry.T("mimi.shop.status.sold", new { price = total });
        Game1.playSound("coin");
        return true;
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
            maxScale: 1.18f
        );

        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            ModEntry.T("mimi.shop.quip.portable"),
            new Rectangle(paper.X + 38, paper.Y + 64, paper.Width - 76, 88),
            Color.DarkSlateGray,
            maxLines: 3,
            minScale: 0.82f,
            centerX: true,
            maxScale: 1.32f,
            centerY: true
        );

        int normalY = this.yPositionOnScreen + 180;
        int shinyY = normalY + 102;
        int portableY = shinyY + 102;

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
            minScale: 0.76f,
            maxScale: 1.16f,
            centerY: true
        );

        CardchaUi.DrawButton(
            b,
            this.CloseButton,
            ModEntry.T("mimi.shop.close"),
            new Color(112, 76, 72),
            enabled: true,
            textScale: 1.40f,
            textPadding: 4
        );

        if (this.QuantityOpen)
            this.DrawQuantitySelector(b);

        this.drawMouse(b);
    }

    private void DrawQuantitySelector(SpriteBatch b)
    {
        if (string.IsNullOrEmpty(this.QuantityResourceId))
            return;

        Rectangle dim = Game1.graphics.GraphicsDevice.Viewport.Bounds;
        b.Draw(Game1.fadeToBlackRect, dim, Color.Black * 0.48f);

        Rectangle panel = new(
            this.xPositionOnScreen + this.width / 2 - 230,
            this.yPositionOnScreen + this.height / 2 - 120,
            460,
            270
        );
        CardchaUi.DrawInsetPanel(
            b,
            panel,
            new Color(250, 229, 190),
            new Color(145, 102, 74),
            4,
            7
        );

        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("mimi.shop.quantity.title"),
            new Rectangle(panel.X + 28, panel.Y + 18, panel.Width - 56, 46),
            CardchaUi.InkBrown,
            centerX: true,
            centerY: true,
            maxScale: 1.05f
        );

        CardchaUi.DrawButton(
            b,
            this.QuantityMinusButton,
            "−",
            new Color(139, 93, 75),
            enabled: this.Quantity > 1,
            textScale: 1.7f
        );
        CardchaUi.DrawButton(
            b,
            this.QuantityPlusButton,
            "+",
            new Color(82, 137, 92),
            enabled: this.Quantity < this.GetQuantityMaximum(),
            textScale: 1.7f
        );

        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            this.Quantity.ToString(),
            new Rectangle(panel.Center.X - 65, this.QuantityMinusButton.bounds.Y - 2, 130, 62),
            CardchaUi.InkBrown,
            centerX: true,
            centerY: true,
            maxScale: 1.05f
        );

        int unitPrice = this.QuantityBuying
            ? GetBuyPrice(this.QuantityResourceId)
            : GetSellPrice(this.QuantityResourceId);
        int total = unitPrice * this.Quantity;
        string summary = this.QuantityBuying
            ? ModEntry.T("mimi.shop.quantity.buy", new { count = this.Quantity, total })
            : ModEntry.T("mimi.shop.quantity.sell", new { count = this.Quantity, total });
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            summary,
            new Rectangle(panel.X + 28, panel.Y + 132, panel.Width - 56, 32),
            Color.DarkSlateGray,
            centerX: true,
            centerY: true,
            maxScale: 1.18f
        );

        CardchaUi.DrawButton(
            b,
            this.QuantityConfirmButton,
            ModEntry.T("mimi.shop.quantity.confirm"),
            new Color(76, 137, 83),
            enabled: true,
            textScale: 1.15f
        );
        CardchaUi.DrawButton(
            b,
            this.QuantityCancelButton,
            ModEntry.T("mimi.shop.quantity.cancel"),
            new Color(154, 76, 72),
            enabled: true,
            textScale: 1.15f
        );

        foreach (ClickableComponent component in new[] {
                     this.QuantityMinusButton, this.QuantityPlusButton,
                     this.QuantityConfirmButton, this.QuantityCancelButton })
        {
            if (this.currentlySnappedComponent?.myID == component.myID)
                CardchaUi.DrawFocus(b, component.bounds);
        }
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
        Rectangle row = new(this.xPositionOnScreen + 50, y, this.width - 100, 92);
        b.Draw(Game1.staminaRect, row, new Color(255, 245, 219) * 0.72f);
        CardchaUi.DrawBorder(b, row, new Color(142, 101, 72), 2);

        Rectangle iconBox = new(row.X + 14, row.Y + 11, 70, 70);
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
            new Rectangle(row.X + 98, row.Y + 5, row.Width - 390, 42),
            CardchaUi.InkBrown,
            centerY: true,
            padding: 2,
            maxScale: 1.36f
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("mimi.shop.owned", new { count }),
            new Rectangle(row.X + 98, row.Y + 47, row.Width - 390, 36),
            Color.DarkSlateGray,
            centerY: true,
            padding: 2,
            maxScale: 1.22f
        );

        int buyPrice = GetBuyPrice(resourceId);
        int sellPrice = GetSellPrice(resourceId);
        CardchaUi.DrawButton(
            b,
            buyButton,
            ModEntry.T("mimi.shop.buy", new { price = buyPrice }),
            new Color(72, 142, 82),
            enabled: true,
            textScale: 1.38f,
            textPadding: 4
        );
        CardchaUi.DrawButton(
            b,
            sellButton,
            ModEntry.T("mimi.shop.sell", new { price = sellPrice }),
            new Color(174, 72, 68),
            enabled: true,
            textScale: 1.38f,
            textPadding: 4
        );

        if (this.currentlySnappedComponent?.myID == buyButton.myID)
            CardchaUi.DrawFocus(b, buyButton.bounds);
        if (this.currentlySnappedComponent?.myID == sellButton.myID)
            CardchaUi.DrawFocus(b, sellButton.bounds);
    }

    private void DrawPortableRow(SpriteBatch b, int y)
    {
        Rectangle row = new(this.xPositionOnScreen + 50, y, this.width - 100, 104);
        b.Draw(Game1.staminaRect, row, new Color(248, 232, 202) * 0.84f);
        CardchaUi.DrawBorder(b, row, new Color(142, 101, 72), 2);

        Rectangle iconBox = new(row.X + 14, row.Y + 17, 70, 70);
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
            new Rectangle(row.X + 98, row.Y + 6, row.Width - 410, 42),
            CardchaUi.InkBrown,
            centerY: true,
            padding: 2,
            maxScale: 1.34f
        );

        string progress = this.PortableMachine.IsAcquired
            ? ModEntry.T("portable.shop.secret")
            : ModEntry.T("portable.shop.progress", new
            {
                count = this.PortableMachine.UniqueCardCount,
                target = PortableMachineService.FreeGiftCardMilestone
            });

        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            progress,
            new Rectangle(row.X + 98, row.Y + 48, row.Width - 410, 46),
            Color.DarkSlateGray,
            maxLines: 2,
            minScale: 0.78f,
            maxScale: 1.24f,
            centerY: true
        );

        string buttonLabel = this.PortableMachine.IsAcquired
            ? ModEntry.T("portable.shop.button.owned")
            : this.PortableMachine.IsMilestoneGiftReady
                ? ModEntry.T("portable.shop.button.free")
                : ModEntry.T("mimi.shop.buy", new { price = PortableMachineService.PurchasePrice });

        // Keep the purchase button visibly active even when the player is short on money.
        // Clicking it should explain the problem instead of looking like a broken/disabled control.
        bool enabled = !this.PortableMachine.IsAcquired;

        CardchaUi.DrawButton(
            b,
            this.PortableBuyButton,
            buttonLabel,
            new Color(111, 86, 129),
            enabled,
            textScale: 1.38f,
            textPadding: 4
        );

        if (this.currentlySnappedComponent?.myID == this.PortableBuyButton.myID)
            CardchaUi.DrawFocus(b, this.PortableBuyButton.bounds);
    }
}

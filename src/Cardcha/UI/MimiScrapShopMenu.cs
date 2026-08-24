using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

/// <summary>
/// MiMi's intentionally shameless Scrap exchange. Currency lives in SaveData,
/// so buying/selling never consumes a backpack slot.
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

    private readonly ResourceService Resources;
    private readonly SaveService Save;
    private readonly Texture2D? ItemTexture;

    private readonly ClickableComponent CloseButton;
    private readonly ClickableComponent NormalBuyButton;
    private readonly ClickableComponent NormalSellButton;
    private readonly ClickableComponent ShinyBuyButton;
    private readonly ClickableComponent ShinySellButton;

    private string Status = ModEntry.T("mimi.shop.status.welcome");

    public MimiScrapShopMenu(ResourceService resources, SaveService save)
        : base(
            Game1.uiViewport.Width / 2 - Math.Min(760, Game1.uiViewport.Width - 32) / 2,
            Game1.uiViewport.Height / 2 - Math.Min(560, Game1.uiViewport.Height - 32) / 2,
            Math.Min(760, Game1.uiViewport.Width - 32),
            Math.Min(560, Game1.uiViewport.Height - 32),
            showUpperRightCloseButton: false)
    {
        this.Resources = resources;
        this.Save = save;
        this.ItemTexture = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/items.png");

        int rowX = this.xPositionOnScreen + 54;
        int rowW = this.width - 108;
        int buyX = rowX + rowW - 236;

        this.NormalBuyButton = new ClickableComponent(
            new Rectangle(buyX, this.yPositionOnScreen + 220, 108, 46),
            "normal-buy") { myID = NormalBuyId };
        this.NormalSellButton = new ClickableComponent(
            new Rectangle(buyX + 118, this.yPositionOnScreen + 220, 108, 46),
            "normal-sell") { myID = NormalSellId };
        this.ShinyBuyButton = new ClickableComponent(
            new Rectangle(buyX, this.yPositionOnScreen + 340, 108, 46),
            "shiny-buy") { myID = ShinyBuyId };
        this.ShinySellButton = new ClickableComponent(
            new Rectangle(buyX + 118, this.yPositionOnScreen + 340, 108, 46),
            "shiny-sell") { myID = ShinySellId };
        this.CloseButton = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + 34, this.yPositionOnScreen + this.height - 70, 150, 44),
            "close") { myID = CloseId };

        this.NormalBuyButton.rightNeighborID = NormalSellId;
        this.NormalBuyButton.downNeighborID = ShinyBuyId;
        this.NormalSellButton.leftNeighborID = NormalBuyId;
        this.NormalSellButton.downNeighborID = ShinySellId;
        this.ShinyBuyButton.upNeighborID = NormalBuyId;
        this.ShinyBuyButton.rightNeighborID = ShinySellId;
        this.ShinySellButton.upNeighborID = NormalSellId;
        this.ShinySellButton.leftNeighborID = ShinyBuyId;
        this.CloseButton.upNeighborID = ShinyBuyId;

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
            this.Sell(DropService.ShinyScrapId);
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
            new Rectangle(paper.X + 28, paper.Y + 18, paper.Width - 56, 46),
            CardchaUi.InkBrown,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.05f
        );

        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            ModEntry.T("mimi.shop.quip"),
            new Rectangle(paper.X + 44, paper.Y + 72, paper.Width - 88, 68),
            Color.DarkSlateGray,
            maxLines: 3,
            minScale: 0.72f,
            centerX: true,
            maxScale: 1.05f
        );

        this.DrawResourceRow(
            b,
            this.yPositionOnScreen + 174,
            0,
            ModEntry.T("item.cardboard.name"),
            this.Resources.Count(DropService.CardboardScrapId),
            DropService.CardboardScrapId,
            this.NormalBuyButton,
            this.NormalSellButton
        );
        this.DrawResourceRow(
            b,
            this.yPositionOnScreen + 294,
            1,
            ModEntry.T("item.shiny.name"),
            this.Resources.Count(DropService.ShinyScrapId),
            DropService.ShinyScrapId,
            this.ShinyBuyButton,
            this.ShinySellButton
        );

        Rectangle status = new(
            paper.X + 190,
            paper.Bottom - 74,
            paper.Width - 226,
            46
        );
        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            this.Status,
            status,
            Color.DarkSlateGray,
            maxLines: 2,
            minScale: 0.72f,
            maxScale: 1.05f
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
        Rectangle row = new(this.xPositionOnScreen + 50, y, this.width - 100, 100);
        b.Draw(Game1.staminaRect, row, new Color(255, 245, 219) * 0.72f);
        CardchaUi.DrawBorder(b, row, new Color(142, 101, 72), 2);

        Rectangle iconBox = new(row.X + 18, row.Y + 18, 64, 64);
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
            new Rectangle(row.X + 98, row.Y + 12, row.Width - 350, 34),
            CardchaUi.InkBrown,
            padding: 2,
            maxScale: 1.08f
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("mimi.shop.owned", new { count }),
            new Rectangle(row.X + 98, row.Y + 50, row.Width - 350, 28),
            Color.DarkSlateGray,
            padding: 2,
            maxScale: 1.00f
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
}

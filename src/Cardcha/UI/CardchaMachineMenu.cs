using Cardcha.Models;
using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

internal sealed class CardchaMachineMenu : IClickableMenu
{
    private const int StandardOneId = 100;
    private const int StandardTenId = 101;
    private const int PremiumOneId = 102;
    private const int PremiumTenId = 103;
    private const int BinderId = 104;

    private readonly GachaService Gacha;
    private readonly ResourceService Resources;
    private readonly SaveService Save;
    private readonly CardRegistry Cards;
    private readonly LoadoutService Loadout;
    private readonly CardUpgradeService Upgrades;
    private readonly ModConfig Config;
    private readonly CardRenderer Renderer;
    private readonly Action OnLoadoutChanged;
    private readonly Action<PullType, int>? OnPullResolved;
    private readonly int? InitialFocusId;

    private readonly ClickableComponent StandardOne;
    private readonly ClickableComponent StandardTen;
    private readonly ClickableComponent PremiumOne;
    private readonly ClickableComponent PremiumTen;
    private readonly ClickableComponent Binder;

    private string Status = ModEntry.T("machine.status.default");

    public CardchaMachineMenu(
        GachaService gacha,
        ResourceService resources,
        SaveService save,
        CardRegistry cards,
        LoadoutService loadout,
        CardUpgradeService upgrades,
        ModConfig config,
        CardRenderer renderer,
        Action onLoadoutChanged,
        Action<PullType, int>? onPullResolved = null,
        int? initialFocusId = null
    ) : base(
        Game1.uiViewport.Width / 2 - Math.Min(920, Game1.uiViewport.Width - 48) / 2,
        Game1.uiViewport.Height / 2 - Math.Min(620, Game1.uiViewport.Height - 48) / 2,
        Math.Min(920, Game1.uiViewport.Width - 48),
        Math.Min(620, Game1.uiViewport.Height - 48),
        showUpperRightCloseButton: true)
    {
        this.Gacha = gacha;
        this.Resources = resources;
        this.Save = save;
        this.Cards = cards;
        this.Loadout = loadout;
        this.Upgrades = upgrades;
        this.Config = config;
        this.Renderer = renderer;
        this.OnLoadoutChanged = onLoadoutChanged;
        this.OnPullResolved = onPullResolved;
        this.InitialFocusId = initialFocusId;

        int left = this.xPositionOnScreen + 56;
        int right = this.xPositionOnScreen + this.width / 2 + 32;
        int top = this.yPositionOnScreen + 178;
        int buttonW = Math.Max(140, this.width / 5);
        int buttonH = 64;

        this.StandardOne = new ClickableComponent(
            new Rectangle(left, top + 105, buttonW, buttonH),
            "standard-one"
        ) { myID = StandardOneId };

        this.StandardTen = new ClickableComponent(
            new Rectangle(left + buttonW + 18, top + 105, buttonW, buttonH),
            "standard-ten"
        ) { myID = StandardTenId };

        this.PremiumOne = new ClickableComponent(
            new Rectangle(right, top + 105, buttonW, buttonH),
            "premium-one"
        ) { myID = PremiumOneId };

        this.PremiumTen = new ClickableComponent(
            new Rectangle(right + buttonW + 18, top + 105, buttonW, buttonH),
            "premium-ten"
        ) { myID = PremiumTenId };

        this.Binder = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + this.width / 2 - 150, this.yPositionOnScreen + this.height - 105, 300, 64),
            "binder"
        ) { myID = BinderId };

        this.ConfigureNeighbors();
        this.populateClickableComponentList();

        if (Game1.options.SnappyMenus)
        {
            this.snapToDefaultClickableComponent();

            // Re-assert remembered focus after the whole clickable graph exists.
            ClickableComponent? preferred = this.GetComponentById(this.InitialFocusId);
            if (preferred is not null)
            {
                this.currentlySnappedComponent = preferred;
                this.snapCursorToCurrentSnappedComponent();
            }
        }
    }

    private void ConfigureNeighbors()
    {
        this.StandardOne.rightNeighborID = StandardTenId;
        this.StandardOne.downNeighborID = BinderId;

        this.StandardTen.leftNeighborID = StandardOneId;
        this.StandardTen.rightNeighborID = PremiumOneId;
        this.StandardTen.downNeighborID = BinderId;

        this.PremiumOne.leftNeighborID = StandardTenId;
        this.PremiumOne.rightNeighborID = PremiumTenId;
        this.PremiumOne.downNeighborID = BinderId;

        this.PremiumTen.leftNeighborID = PremiumOneId;
        this.PremiumTen.downNeighborID = BinderId;

        this.Binder.upNeighborID = StandardTenId;

        if (this.upperRightCloseButton is not null)
        {
            this.upperRightCloseButton.myID = IClickableMenu.upperRightCloseButton_ID;
            this.upperRightCloseButton.leftNeighborID = PremiumTenId;
            this.upperRightCloseButton.downNeighborID = PremiumTenId;
            this.PremiumTen.upNeighborID = IClickableMenu.upperRightCloseButton_ID;
        }
    }

    public override void populateClickableComponentList()
    {
        // Stardew initializes allClickableComponents in the base implementation.
        // Calling Clear() before base.populateClickableComponentList() can be null
        // during menu construction.
        base.populateClickableComponentList();
        this.allClickableComponents.Clear();
        this.allClickableComponents.Add(this.StandardOne);
        this.allClickableComponents.Add(this.StandardTen);
        this.allClickableComponents.Add(this.PremiumOne);
        this.allClickableComponents.Add(this.PremiumTen);
        this.allClickableComponents.Add(this.Binder);

        if (this.upperRightCloseButton is not null)
            this.allClickableComponents.Add(this.upperRightCloseButton);
    }

    public override void snapToDefaultClickableComponent()
    {
        this.currentlySnappedComponent = this.GetComponentById(this.InitialFocusId)
            ?? this.StandardOne;
        this.snapCursorToCurrentSnappedComponent();
    }

    private ClickableComponent? GetComponentById(int? id)
    {
        if (!id.HasValue)
            return null;

        return id.Value switch
        {
            StandardOneId => this.StandardOne,
            StandardTenId => this.StandardTen,
            PremiumOneId => this.PremiumOne,
            PremiumTenId => this.PremiumTen,
            BinderId => this.Binder,
            _ => null
        };
    }

    public override void receiveGamePadButton(Buttons b)
    {
        if (b == Buttons.B)
        {
            Game1.exitActiveMenu();
            Game1.playSound("bigDeSelect");
            return;
        }

        if (b == Buttons.A && this.currentlySnappedComponent is not null)
        {
            Point center = this.currentlySnappedComponent.bounds.Center;
            this.receiveLeftClick(center.X, center.Y);
            return;
        }

        base.receiveGamePadButton(b);
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        if (this.upperRightCloseButton?.containsPoint(x, y) == true)
        {
            Game1.exitActiveMenu();
            Game1.playSound("bigDeSelect");
            return;
        }

        if (this.StandardOne.containsPoint(x, y)) { TryPull(PullType.Standard, 1, StandardOneId); return; }
        if (this.StandardTen.containsPoint(x, y)) { TryPull(PullType.Standard, 10, StandardTenId); return; }
        if (this.PremiumOne.containsPoint(x, y)) { TryPull(PullType.Premium, 1, PremiumOneId); return; }
        if (this.PremiumTen.containsPoint(x, y)) { TryPull(PullType.Premium, 10, PremiumTenId); return; }

        if (this.Binder.containsPoint(x, y))
        {
            Game1.playSound("smallSelect");
            Game1.activeClickableMenu = new CardchaBinderMenu(
                this.Cards,
                this.Save,
                this.Loadout,
                this.Upgrades,
                this.Renderer,
                () => Reopen(BinderId),
                this.OnLoadoutChanged
            );
        }
    }

    private void TryPull(PullType type, int count, int returnFocusId)
    {
        int perPull = type == PullType.Standard ? this.Config.StandardPullCost : this.Config.PremiumPullCost;
        int totalCost = perPull * count;
        string resourceId = type == PullType.Standard ? DropService.CardboardScrapId : DropService.ShinyScrapId;

        if (!this.Resources.TryConsume(resourceId, totalCost))
        {
            this.Status = type == PullType.Standard
                ? ModEntry.T("machine.no-scrap")
                : ModEntry.T("machine.no-shiny");

            Game1.playSound("cancel");
            return;
        }

        List<PullResult> results = new(count);
        for (int i = 0; i < count; i++)
            results.Add(this.Gacha.Pull(type));

        // Story progression is updated only after the real pull has succeeded and
        // GachaService has persisted every result. This cannot complete on a failed pull.
        this.OnPullResolved?.Invoke(type, count);

        // v0.1.17-alpha.4: ChaCha now performs the actual machine ritual
        // before the normal reveal screen. Results are already persisted by
        // GachaService.Pull(), so animation timing/skip can never reroll them.
        Game1.activeClickableMenu = new CardchaPullAnimationMenu(
            results,
            this.Renderer,
            () => Reopen(returnFocusId)
        );
    }

    private void Reopen(int? focusId = null)
        => Game1.activeClickableMenu = new CardchaMachineMenu(
            this.Gacha,
            this.Resources,
            this.Save,
            this.Cards,
            this.Loadout,
            this.Upgrades,
            this.Config,
            this.Renderer,
            this.OnLoadoutChanged,
            this.OnPullResolved,
            focusId
        );

    public override void draw(SpriteBatch b)
    {
        b.Draw(
            Game1.fadeToBlackRect,
            Game1.graphics.GraphicsDevice.Viewport.Bounds,
            Color.Black * 0.76f
        );

        Rectangle shell = new(
            this.xPositionOnScreen,
            this.yPositionOnScreen,
            this.width,
            this.height
        );

        // Handmade Cardcha console shell.
        b.Draw(Game1.staminaRect, shell, new Color(48, 38, 45));
        CardchaUi.DrawBorder(b, shell, new Color(24, 19, 23), 6);

        Rectangle shellInset = new(
            shell.X + 8,
            shell.Y + 8,
            shell.Width - 16,
            shell.Height - 16
        );
        b.Draw(Game1.staminaRect, shellInset, new Color(92, 55, 49));
        CardchaUi.DrawBorder(b, shellInset, CardchaUi.Gold * 0.82f, 3);
        CardchaUi.DrawCornerOrnaments(b, shellInset, CardchaUi.Gold * 0.62f);

        Rectangle sign = new(
            this.xPositionOnScreen + this.width / 2 - 190,
            this.yPositionOnScreen + 22,
            380,
            58
        );
        CardchaUi.DrawPaperHeader(
            b,
            sign,
            ModEntry.T("machine.ui.title")
        );

        DrawMachine(b);

        int left = this.xPositionOnScreen + 44;
        int right = this.xPositionOnScreen + this.width / 2 + 18;
        int top = this.yPositionOnScreen + 176;
        int panelW = this.width / 2 - 64;
        int panelH = 200;

        Rectangle standardPanel = new(
            left,
            top,
            panelW,
            panelH
        );
        Rectangle premiumPanel = new(
            right,
            top,
            panelW,
            panelH
        );

        CardchaUi.DrawInsetPanel(
            b,
            standardPanel,
            new Color(210, 225, 232),
            CardchaUi.StandardBlue,
            3,
            5
        );
        CardchaUi.DrawInsetPanel(
            b,
            premiumPanel,
            new Color(226, 211, 234),
            CardchaUi.PremiumPurple,
            3,
            5
        );

        Rectangle stdTitleArea = new(
            standardPanel.X + 12,
            standardPanel.Y + 10,
            standardPanel.Width - 24,
            34
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("machine.standard-pull"),
            stdTitleArea,
            CardchaUi.StandardBlue,
            centerX: true,
            centerY: true,
            padding: 2
        );

        Rectangle preTitleArea = new(
            premiumPanel.X + 12,
            premiumPanel.Y + 10,
            premiumPanel.Width - 24,
            34
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("machine.premium-pull"),
            preTitleArea,
            CardchaUi.PremiumPurple,
            centerX: true,
            centerY: true,
            padding: 2
        );

        int normal = this.Resources.Count(DropService.CardboardScrapId);
        int shiny = this.Resources.Count(DropService.ShinyScrapId);

        Rectangle stdCostArea = new(
            standardPanel.X + 14,
            standardPanel.Y + 50,
            standardPanel.Width - 28,
            22
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T(
                "machine.cost.normal",
                new { cost = this.Config.StandardPullCost }
            ),
            stdCostArea,
            Color.Black,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.28f
        );

        Rectangle preCostArea = new(
            premiumPanel.X + 14,
            premiumPanel.Y + 50,
            premiumPanel.Width - 28,
            22
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T(
                "machine.cost.shiny",
                new { cost = this.Config.PremiumPullCost }
            ),
            preCostArea,
            Color.Black,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.28f
        );

        Rectangle stdResource = new(
            standardPanel.X + 14,
            standardPanel.Y + 78,
            standardPanel.Width - 28,
            24
        );
        Rectangle preResource = new(
            premiumPanel.X + 14,
            premiumPanel.Y + 78,
            premiumPanel.Width - 28,
            24
        );

        b.Draw(Game1.staminaRect, stdResource, Color.White * 0.48f);
        b.Draw(Game1.staminaRect, preResource, Color.White * 0.48f);
        CardchaUi.DrawBorder(b, stdResource, CardchaUi.StandardBlue * 0.45f, 2);
        CardchaUi.DrawBorder(b, preResource, CardchaUi.PremiumPurple * 0.45f, 2);

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("machine.resource.normal", new { count = normal }),
            stdResource,
            Color.Black,
            centerX: true,
            centerY: true,
            padding: 5,
            maxScale: 1.30f
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("machine.resource.shiny", new { count = shiny }),
            preResource,
            Color.Black,
            centerX: true,
            centerY: true,
            padding: 5,
            maxScale: 1.30f
        );

        CardchaUi.DrawButton(
            b,
            this.StandardOne,
            ModEntry.T("machine.pull-one"),
            CardchaUi.StandardBlue,
            normal >= this.Config.StandardPullCost
        );
        CardchaUi.DrawButton(
            b,
            this.StandardTen,
            ModEntry.T("machine.pull-ten"),
            CardchaUi.StandardBlue,
            normal >= this.Config.StandardPullCost * 10
        );
        CardchaUi.DrawButton(
            b,
            this.PremiumOne,
            ModEntry.T("machine.pull-one"),
            CardchaUi.PremiumPurple,
            shiny >= this.Config.PremiumPullCost
        );
        CardchaUi.DrawButton(
            b,
            this.PremiumTen,
            ModEntry.T("machine.pull-ten"),
            CardchaUi.PremiumPurple,
            shiny >= this.Config.PremiumPullCost * 10
        );

        // Machine Sympathy as two real meters instead of loose text.
        int pityY = top + 216;
        Rectangle pityPanel = new(
            this.xPositionOnScreen + 44,
            pityY,
            this.width - 88,
            112
        );
        CardchaUi.DrawInsetPanel(
            b,
            pityPanel,
            new Color(226, 205, 177),
            new Color(103, 70, 62),
            3,
            5
        );

        Rectangle pityTitle = new(
            pityPanel.X + 12,
            pityPanel.Y + 8,
            pityPanel.Width - 24,
            28
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("machine.sympathy"),
            pityTitle,
            CardchaUi.PanelDark,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.20f
        );

        double standardPityProgress =
            this.Config.StandardLegendaryPity <= 0
                ? 0
                : this.Save.Data.StandardSinceLegendary
                  / (double)this.Config.StandardLegendaryPity;

        double premiumPityProgress =
            this.Config.PremiumLegendaryPity <= 0
                ? 0
                : this.Save.Data.PremiumSinceLegendary
                  / (double)this.Config.PremiumLegendaryPity;

        Rectangle stdPityText = new(
            pityPanel.X + 18,
            pityPanel.Y + 42,
            310,
            22
        );
        Rectangle prePityText = new(
            pityPanel.X + pityPanel.Width / 2 + 10,
            pityPanel.Y + 42,
            310,
            22
        );

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T(
                "machine.sympathy.standard",
                new
                {
                    count = this.Save.Data.StandardSinceLegendary,
                    pity = this.Config.StandardLegendaryPity
                }
            ),
            stdPityText,
            Color.Black,
            padding: 1,
            maxScale: 1.24f
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T(
                "machine.sympathy.premium",
                new
                {
                    count = this.Save.Data.PremiumSinceLegendary,
                    pity = this.Config.PremiumLegendaryPity
                }
            ),
            prePityText,
            Color.Black,
            padding: 1,
            maxScale: 1.24f
        );

        CardchaUi.DrawMeter(
            b,
            new Rectangle(
                stdPityText.X,
                stdPityText.Bottom + 6,
                stdPityText.Width,
                18
            ),
            standardPityProgress,
            CardchaUi.StandardBlue,
            new Color(86, 77, 76),
            new Color(59, 48, 50)
        );

        CardchaUi.DrawMeter(
            b,
            new Rectangle(
                prePityText.X,
                prePityText.Bottom + 6,
                prePityText.Width,
                18
            ),
            premiumPityProgress,
            CardchaUi.PremiumPurple,
            new Color(86, 77, 76),
            new Color(59, 48, 50)
        );

        Rectangle statusPanel = new(
            this.xPositionOnScreen + 52,
            this.yPositionOnScreen + this.height - 172,
            this.width - 104,
            62
        );
        b.Draw(
            Game1.staminaRect,
            statusPanel,
            new Color(244, 222, 183) * 0.86f
        );
        CardchaUi.DrawBorder(
            b,
            statusPanel,
            CardchaUi.PaperShadow,
            2
        );
        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            this.Status,
            new Rectangle(
                statusPanel.X + 8,
                statusPanel.Y + 6,
                statusPanel.Width - 16,
                statusPanel.Height - 12
            ),
            Color.DarkSlateGray,
            maxLines: 2,
            minScale: 0.78f,
            maxScale: 1.20f
        );

        CardchaUi.DrawButton(
            b,
            this.Binder,
            ModEntry.T(
                "machine.open-binder",
                new
                {
                    owned = this.Save.Data.OwnedCards.Count,
                    total = this.Cards.All.Count
                }
            ),
            CardchaUi.GoodGreen
        );

        foreach (ClickableComponent c in this.allClickableComponents)
        {
            if (this.currentlySnappedComponent?.myID == c.myID)
                CardchaUi.DrawFocus(b, c.bounds);
        }

        this.upperRightCloseButton?.draw(b);
        drawMouse(b);
    }

    private void DrawMachine(SpriteBatch b)
    {
        try
        {
            Texture2D texture = Game1.content.Load<Texture2D>(ItemAssetService.MachineUiTextureAsset);

            int normal = this.Resources.Count(DropService.CardboardScrapId);
            int shiny = this.Resources.Count(DropService.ShinyScrapId);

            int frame = 0;

            if (this.Status == ModEntry.T("machine.no-scrap")
                || this.Status == ModEntry.T("machine.no-shiny"))
            {
                frame = 3;
            }
            else
            {
                double standardPity = this.Config.StandardLegendaryPity <= 0
                    ? 0
                    : this.Save.Data.StandardSinceLegendary / (double)this.Config.StandardLegendaryPity;

                double premiumPity = this.Config.PremiumLegendaryPity <= 0
                    ? 0
                    : this.Save.Data.PremiumSinceLegendary / (double)this.Config.PremiumLegendaryPity;

                if (Math.Max(standardPity, premiumPity) >= 0.75)
                    frame = 2;
                else if (normal >= this.Config.StandardPullCost * 10 || shiny >= this.Config.PremiumPullCost * 10)
                    frame = 1;
            }

            Rectangle source = new(frame * 48, 0, 48, 96);

            double t = Game1.currentGameTime.TotalGameTime.TotalMilliseconds / 1000.0;
            float bob = (float)Math.Sin(t * 2.1) * 1.5f;
            float scale = 1f + (float)Math.Sin(t * 1.35) * 0.012f;

            Vector2 origin = new(24f, 48f);
            Vector2 center = new(
                this.xPositionOnScreen + this.width / 2,
                this.yPositionOnScreen + 126 + bob
            );

            b.Draw(texture, center, source, Color.White, 0f, origin, scale, SpriteEffects.None, 1f);
        }
        catch
        {
            // Menu stays usable if the optional machine art can't load.
        }
    }
}

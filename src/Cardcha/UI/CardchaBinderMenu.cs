using Cardcha.Models;
using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;
using System.Text;
using System.Text.RegularExpressions;

namespace Cardcha.UI;

/// <summary>
/// Binder v0.3 alpha.23.
/// Design goals: near-full-screen open book, icon-only Base-ID collection, rarity bookmarks,
/// locked grayscale icons with real rarity borders, favorite shortcut, equipped overlay, and a readable
/// detail page. This intentionally keeps combat/effect services separate from the UI refactor.
/// </summary>
internal sealed class CardchaBinderMenu : IClickableMenu
{
    private static readonly Regex EffectNumberRegex = new(
        @"(?<sign>[+-]?)(?<number>\d+(?:[\.,]\d+)?)(?<unit>(?:\s*(?:%\s*Max\s*HP|%\s*HP|%|HP/s|HP|px|Dust|Fate|Defense|Def|s))?)",
        RegexOptions.Compiled | RegexOptions.IgnoreCase
    );

    private const int VisualActiveSlots = 5;
    private const int CardsPerPage = 20;
    private const int GridColumns = 5;
    private const int GridRows = 4;

    private const int BackId = 100;
    private const int ActiveBaseId = 200;
    private const int BossSlotId = 206;
    private const int SecretSlotId = 207;
    private const int CardBaseId = 1000;
    private const int FilterBaseId = 2000;
    private const int FavoriteFilterId = 2010;
    private const int NormalScrapId = 2020;
    private const int ShinyScrapId = 2021;
    private const int PrevPageId = 2100;
    private const int NextPageId = 2101;
    private const int UnlockSlotId = 2102;
    private const int FavoriteActionId = 2200;
    private const int EquipActionId = 2201;
    private const int UpgradeActionId = 2202;
    private const int DeselectActionId = 2203;

    private readonly CardRegistry Cards;
    private readonly SaveService Save;
    private readonly ResourceService Resources;
    private readonly LoadoutService Loadout;
    private readonly CardUpgradeService Upgrades;
    private readonly CardRenderer Renderer;
    private readonly ControllerProfileService Controller;
    private readonly Action OnCloseToMachine;
    private readonly Action OnLoadoutChanged;
    private readonly string BackLabel;
    private readonly IClickableMenu? BackgroundMenu;

    private readonly Rectangle OuterBook;
    private readonly Rectangle LeftPage;
    private readonly Rectangle RightPage;
    private readonly Rectangle CollectionArea;

    private readonly ClickableComponent BackButton;
    private readonly List<ClickableComponent> ActiveSlots = new();
    private readonly ClickableComponent BossSlot;
    private readonly ClickableComponent SecretSlot;
    private readonly List<(BinderFilter Filter, ClickableComponent Button)> MainFilterTabs = new();
    private readonly ClickableComponent FavoriteFilterTab;
    private readonly ClickableComponent NormalScrapButton;
    private readonly ClickableComponent ShinyScrapButton;
    private readonly ClickableComponent PrevPageButton;
    private readonly ClickableComponent NextPageButton;
    private readonly ClickableComponent UnlockSlotButton;
    private readonly ClickableComponent FavoriteActionButton;
    private readonly ClickableComponent EquipActionButton;
    private readonly ClickableComponent UpgradeActionButton;
    private readonly ClickableComponent DeselectActionButton;
    private readonly List<(CardDefinition Card, ClickableComponent Button)> CardButtons = new();

    private BinderFilter CurrentFilter = BinderFilter.All;
    private int CurrentPage;
    // PreviewCard follows free browsing. LockedCard is the explicit A/click action target.
    // Selected is the card currently rendered on the right page and is derived from those states.
    private CardDefinition? Selected;
    private CardDefinition? PreviewCard;
    private CardDefinition? LockedCard;
    private bool ControllerSelectionLocked;
    private string? LastQuickToggleCardId;
    private double LastQuickToggleAtMs;
    private Texture2D? ScrapTexture;
    private bool ScrapTextureChecked;
    private const double QuickToggleMinMs = 0d;
    private const double QuickToggleWindowMs = 650d;
    private string Status = ModEntry.T("binder.status.pick");
    // alpha.23: hint bar follows the most recently used input family and controller profile.
    private bool LastInputWasController;

    private enum BinderFilter
    {
        All,
        Common,
        Rare,
        Epic,
        Legendary,
        Mythic,
        Favorite
    }

    public CardchaBinderMenu(
        CardRegistry cards,
        SaveService save,
        ResourceService resources,
        LoadoutService loadout,
        CardUpgradeService upgrades,
        CardRenderer renderer,
        ControllerProfileService controller,
        Action onCloseToMachine,
        Action onLoadoutChanged,
        string? backLabel = null,
        IClickableMenu? backgroundMenu = null
    ) : base(
        Math.Max(6, (Game1.uiViewport.Width - Math.Min(1600, Game1.uiViewport.Width - 36)) / 2),
        Math.Max(6, (Game1.uiViewport.Height - Math.Min(920, Game1.uiViewport.Height - 74)) / 2),
        Math.Min(1600, Game1.uiViewport.Width - 36),
        Math.Min(920, Game1.uiViewport.Height - 74),
        showUpperRightCloseButton: false)
    {
        this.Cards = cards;
        this.Save = save;
        this.Resources = resources;
        this.Loadout = loadout;
        this.Upgrades = upgrades;
        this.Renderer = renderer;
        this.Controller = controller;
        this.OnCloseToMachine = onCloseToMachine;
        this.OnLoadoutChanged = onLoadoutChanged;
        this.BackLabel = backLabel ?? ModEntry.T("binder.back");
        this.BackgroundMenu = backgroundMenu;

        this.OuterBook = new Rectangle(this.xPositionOnScreen, this.yPositionOnScreen, this.width, this.height);
        Rectangle paper = new(this.OuterBook.X + 18, this.OuterBook.Y + 18, this.OuterBook.Width - 36, this.OuterBook.Height - 36);
        int seam = 8;
        int pageWidth = (paper.Width - seam) / 2;
        this.LeftPage = new Rectangle(paper.X, paper.Y, pageWidth, paper.Height);
        this.RightPage = new Rectangle(this.LeftPage.Right + seam, paper.Y, paper.Width - pageWidth - seam, paper.Height);

        // Keep a compact icon-only back control. The previous text label (e.g. "Túi đồ")
        // consumed valuable header space and duplicated context the player can already see.
        this.BackButton = new ClickableComponent(
            new Rectangle(this.LeftPage.X + 18, this.LeftPage.Y + 14, 52, 42),
            "back") { myID = BackId };

        // v0.3 alpha.12: five normal skills + Boss stay together as one loadout group.
        // ChaCha is deliberately separated to the right because that circle will later open
        // ChaCha management instead of behaving like another combat-skill slot.
        int activeGap = 8;
        int chachaGroupGap = 42;
        int totalCircleCount = VisualActiveSlots + 2;
        int activeAvailableWidth = this.LeftPage.Width - 44;
        int activeDiameter = Math.Clamp(
            (activeAvailableWidth - activeGap * VisualActiveSlots - chachaGroupGap) / totalCircleCount,
            54,
            82
        );
        int activeRowWidth = activeDiameter * totalCircleCount
            + activeGap * VisualActiveSlots
            + chachaGroupGap;
        int activeX = this.LeftPage.Center.X - activeRowWidth / 2;
        int activeY = this.LeftPage.Y + 78;

        for (int i = 0; i < VisualActiveSlots; i++)
        {
            Rectangle r = new(activeX + i * (activeDiameter + activeGap), activeY, activeDiameter, activeDiameter);
            this.ActiveSlots.Add(new ClickableComponent(r, $"active-{i}") { myID = ActiveBaseId + i });
        }

        Rectangle bossRect = new(
            activeX + VisualActiveSlots * (activeDiameter + activeGap),
            activeY,
            activeDiameter,
            activeDiameter
        );
        this.BossSlot = new ClickableComponent(bossRect, "boss-slot") { myID = BossSlotId };

        Rectangle secretRect = new(
            bossRect.Right + chachaGroupGap,
            activeY,
            activeDiameter,
            activeDiameter
        );
        this.SecretSlot = new ClickableComponent(secretRect, "chacha-slot") { myID = SecretSlotId };

        int collectionTop = activeY + activeDiameter + 34;
        int paginationHeight = 48;
        this.CollectionArea = new Rectangle(
            this.LeftPage.X + 22,
            collectionTop,
            this.LeftPage.Width - 44,
            Math.Max(210, this.LeftPage.Bottom - collectionTop - paginationHeight - 18)
        );

        int tabX = Math.Max(4, this.OuterBook.X - 100);
        int tabY = this.OuterBook.Y + 104;
        int tabW = 108;
        int tabH = 56;
        int tabGap = 7;
        BinderFilter[] mainFilters =
        {
            BinderFilter.All,
            BinderFilter.Common,
            BinderFilter.Rare,
            BinderFilter.Epic,
            BinderFilter.Legendary,
            BinderFilter.Mythic
        };

        for (int i = 0; i < mainFilters.Length; i++)
        {
            ClickableComponent button = new(
                new Rectangle(tabX, tabY + i * (tabH + tabGap), tabW, tabH),
                $"filter-{mainFilters[i]}")
            { myID = FilterBaseId + i };
            this.MainFilterTabs.Add((mainFilters[i], button));
        }

        this.FavoriteFilterTab = new ClickableComponent(
            new Rectangle(tabX, this.OuterBook.Bottom - tabH - 24, tabW, tabH),
            "filter-favorite") { myID = FavoriteFilterId };

        // Resource counters live on the left rail, directly below rarity bookmarks and
        // above Favorites, matching the approved reference Binder.
        int resourceGap = 8;
        int resourceY = this.MainFilterTabs.Last().Button.bounds.Bottom + 12;
        int resourceAvailable = Math.Max(0, this.FavoriteFilterTab.bounds.Y - resourceY - 10);
        int resourceSize = Math.Clamp((resourceAvailable - resourceGap) / 2, 36, 62);
        int resourceX = tabX + (tabW - resourceSize) / 2;
        this.NormalScrapButton = new ClickableComponent(
            new Rectangle(resourceX, resourceY, resourceSize, resourceSize),
            "normal-scrap") { myID = NormalScrapId };
        this.ShinyScrapButton = new ClickableComponent(
            new Rectangle(resourceX, resourceY + resourceSize + resourceGap, resourceSize, resourceSize),
            "shiny-scrap") { myID = ShinyScrapId };

        int pageY = this.LeftPage.Bottom - 48;
        this.PrevPageButton = new ClickableComponent(
            new Rectangle(this.LeftPage.X + 24, pageY, 58, 34),
            "prev") { myID = PrevPageId };
        this.NextPageButton = new ClickableComponent(
            new Rectangle(this.LeftPage.Right - 82, pageY, 58, 34),
            "next") { myID = NextPageId };

        this.UnlockSlotButton = new ClickableComponent(
            new Rectangle(this.LeftPage.Right - 202, this.LeftPage.Y + 55, 180, 32),
            "unlock-slot") { myID = UnlockSlotId };

        int actionGap = 10;
        int actionW = Math.Max(120, (this.RightPage.Width - 52 - actionGap) / 2);
        int actionH = 46;
        int actionX = this.RightPage.X + 22;
        int actionY = this.RightPage.Bottom - 112;
        this.FavoriteActionButton = new ClickableComponent(
            new Rectangle(actionX, actionY, actionW, actionH),
            "favorite") { myID = FavoriteActionId };
        this.EquipActionButton = new ClickableComponent(
            new Rectangle(actionX + actionW + actionGap, actionY, actionW, actionH),
            "equip-toggle") { myID = EquipActionId };
        int secondRowY = actionY + actionH + 8;
        int deselectW = Math.Clamp((actionW * 2 + actionGap) / 3, 126, 190);
        int upgradeW = actionW * 2 + actionGap - deselectW - actionGap;
        this.UpgradeActionButton = new ClickableComponent(
            new Rectangle(actionX, secondRowY, upgradeW, actionH),
            "upgrade") { myID = UpgradeActionId };
        this.DeselectActionButton = new ClickableComponent(
            new Rectangle(actionX + upgradeW + actionGap, secondRowY, deselectW, actionH),
            "deselect") { myID = DeselectActionId };

        this.PruneInvalidFavorites();
        this.RebuildCardButtons(resetPage: true);
        this.ConfigureNeighbors();
        this.populateClickableComponentList();

        if (Game1.options.SnappyMenus)
            this.snapToDefaultClickableComponent();
    }

    private int UnlockedSlots => this.Upgrades.GetUnlockedSlotCount();

    private IReadOnlyList<CardDefinition> OrderedCards
        => this.Cards.All
            .OrderBy(p => p.StableBaseId)
            .ThenBy(p => p.Id, StringComparer.OrdinalIgnoreCase)
            .ToList();

    private List<CardDefinition> FilteredCards()
    {
        IEnumerable<CardDefinition> cards = this.OrderedCards;

        cards = this.CurrentFilter switch
        {
            BinderFilter.Common => cards.Where(p => p.Rarity == CardRarity.Common),
            BinderFilter.Rare => cards.Where(p => p.Rarity == CardRarity.Rare),
            BinderFilter.Epic => cards.Where(p => p.Rarity == CardRarity.Epic),
            BinderFilter.Legendary => cards.Where(p => p.Rarity == CardRarity.Legendary),
            BinderFilter.Mythic => cards.Where(p => p.Rarity == CardRarity.Mythic),
            BinderFilter.Favorite => cards.Where(p =>
                this.Save.Data.OwnedCards.Contains(p.Id)
                && this.Save.Data.FavoriteCardIds.Contains(p.Id)),
            _ => cards
        };

        return cards.ToList();
    }

    private void RebuildCardButtons(bool resetPage)
    {
        if (resetPage)
            this.CurrentPage = 0;

        List<CardDefinition> filtered = this.FilteredCards();
        int pages = Math.Max(1, (int)Math.Ceiling(filtered.Count / (double)CardsPerPage));
        this.CurrentPage = Math.Clamp(this.CurrentPage, 0, pages - 1);

        this.CardButtons.Clear();
        List<CardDefinition> pageCards = filtered
            .Skip(this.CurrentPage * CardsPerPage)
            .Take(CardsPerPage)
            .ToList();

        int gap = 12;
        int cellW = Math.Max(58, (this.CollectionArea.Width - gap * (GridColumns - 1)) / GridColumns);
        int cellH = Math.Max(64, (this.CollectionArea.Height - gap * (GridRows - 1)) / GridRows);

        for (int i = 0; i < pageCards.Count; i++)
        {
            int col = i % GridColumns;
            int row = i / GridColumns;
            Rectangle r = new(
                this.CollectionArea.X + col * (cellW + gap),
                this.CollectionArea.Y + row * (cellH + gap),
                cellW,
                cellH
            );
            this.CardButtons.Add((
                pageCards[i],
                new ClickableComponent(r, pageCards[i].Id) { myID = CardBaseId + i }
            ));
        }

        this.ConfigureNeighbors();
        this.populateClickableComponentList();

        // Rebuilding filters/pages must never discard an explicit action lock.
        if (this.ControllerSelectionLocked && this.LockedCard is not null)
            this.Selected = this.LockedCard;
    }

    private void PruneInvalidFavorites()
    {
        HashSet<string> validOwnedIds = this.Cards.All
            .Where(p => this.Save.Data.OwnedCards.Contains(p.Id))
            .Select(p => p.Id)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);

        int before = this.Save.Data.FavoriteCardIds.Count;
        this.Save.Data.FavoriteCardIds.RemoveWhere(id => !validOwnedIds.Contains(id));
        if (before != this.Save.Data.FavoriteCardIds.Count)
            this.Save.Save();
    }

    private void ConfigureNeighbors()
    {
        this.BackButton.downNeighborID = ActiveBaseId;
        this.BackButton.rightNeighborID = ActiveBaseId;

        for (int i = 0; i < this.ActiveSlots.Count; i++)
        {
            ClickableComponent slot = this.ActiveSlots[i];
            slot.leftNeighborID = i == 0 ? FilterBaseId : ActiveBaseId + i - 1;
            slot.rightNeighborID = i < this.ActiveSlots.Count - 1 ? ActiveBaseId + i + 1 : BossSlotId;
            slot.upNeighborID = BackId;
            slot.downNeighborID = this.CardButtons.Count > 0
                ? CardBaseId + Math.Min(i, this.CardButtons.Count - 1)
                : PrevPageId;
        }

        this.BossSlot.leftNeighborID = ActiveBaseId + VisualActiveSlots - 1;
        this.BossSlot.rightNeighborID = SecretSlotId;
        this.BossSlot.upNeighborID = BackId;
        this.BossSlot.downNeighborID = this.CardButtons.Count > 0
            ? CardBaseId + Math.Min(GridColumns - 1, this.CardButtons.Count - 1)
            : NextPageId;

        this.SecretSlot.leftNeighborID = BossSlotId;
        this.SecretSlot.rightNeighborID = FavoriteActionId;
        this.SecretSlot.upNeighborID = BackId;
        this.SecretSlot.downNeighborID = this.CardButtons.Count > 0
            ? CardBaseId + Math.Min(GridColumns - 1, this.CardButtons.Count - 1)
            : NextPageId;

        for (int i = 0; i < this.MainFilterTabs.Count; i++)
        {
            ClickableComponent button = this.MainFilterTabs[i].Button;
            button.rightNeighborID = ActiveBaseId;
            button.upNeighborID = i > 0 ? this.MainFilterTabs[i - 1].Button.myID : FavoriteFilterId;
            button.downNeighborID = i + 1 < this.MainFilterTabs.Count
                ? this.MainFilterTabs[i + 1].Button.myID
                : NormalScrapId;
        }

        this.NormalScrapButton.upNeighborID = this.MainFilterTabs.Last().Button.myID;
        this.NormalScrapButton.downNeighborID = ShinyScrapId;
        this.NormalScrapButton.rightNeighborID = this.CardButtons.Count > 0 ? CardBaseId : ActiveBaseId;
        this.ShinyScrapButton.upNeighborID = NormalScrapId;
        this.ShinyScrapButton.downNeighborID = FavoriteFilterId;
        this.ShinyScrapButton.rightNeighborID = this.CardButtons.Count > 0 ? CardBaseId : ActiveBaseId;

        this.FavoriteFilterTab.rightNeighborID = this.CardButtons.Count > 0 ? CardBaseId : ActiveBaseId;
        this.FavoriteFilterTab.upNeighborID = ShinyScrapId;
        this.FavoriteFilterTab.downNeighborID = this.MainFilterTabs.First().Button.myID;

        for (int i = 0; i < this.CardButtons.Count; i++)
        {
            ClickableComponent button = this.CardButtons[i].Button;
            int col = i % GridColumns;
            int row = i / GridColumns;
            button.leftNeighborID = col > 0 ? CardBaseId + i - 1 : FavoriteFilterId;
            button.rightNeighborID = col < GridColumns - 1 && i + 1 < this.CardButtons.Count
                ? CardBaseId + i + 1
                : EquipActionId;
            button.upNeighborID = row > 0
                ? CardBaseId + i - GridColumns
                : ActiveBaseId + Math.Min(col, VisualActiveSlots - 1);
            button.downNeighborID = i + GridColumns < this.CardButtons.Count
                ? CardBaseId + i + GridColumns
                : UpgradeActionId;
        }

        this.PrevPageButton.leftNeighborID = FavoriteFilterId;
        this.PrevPageButton.rightNeighborID = NextPageId;
        this.PrevPageButton.upNeighborID = this.CardButtons.Count > 0
            ? CardBaseId + Math.Max(0, this.CardButtons.Count - Math.Min(GridColumns, this.CardButtons.Count))
            : ActiveBaseId;

        this.NextPageButton.leftNeighborID = PrevPageId;
        this.NextPageButton.rightNeighborID = FavoriteActionId;
        this.NextPageButton.upNeighborID = this.CardButtons.Count > 0
            ? CardBaseId + this.CardButtons.Count - 1
            : SecretSlotId;

        int actionReturnId = this.CardButtons.Count > 0 ? CardBaseId + this.CardButtons.Count - 1 : SecretSlotId;
        this.FavoriteActionButton.leftNeighborID = actionReturnId;
        this.FavoriteActionButton.rightNeighborID = EquipActionId;
        this.FavoriteActionButton.upNeighborID = actionReturnId;
        this.FavoriteActionButton.downNeighborID = UpgradeActionId;

        this.EquipActionButton.leftNeighborID = FavoriteActionId;
        this.EquipActionButton.rightNeighborID = actionReturnId;
        this.EquipActionButton.upNeighborID = actionReturnId;
        this.EquipActionButton.downNeighborID = DeselectActionId;

        this.UpgradeActionButton.leftNeighborID = actionReturnId;
        this.UpgradeActionButton.rightNeighborID = DeselectActionId;
        this.UpgradeActionButton.upNeighborID = FavoriteActionId;
        this.UpgradeActionButton.downNeighborID = actionReturnId;

        this.DeselectActionButton.leftNeighborID = UpgradeActionId;
        this.DeselectActionButton.rightNeighborID = actionReturnId;
        this.DeselectActionButton.upNeighborID = EquipActionId;
        this.DeselectActionButton.downNeighborID = actionReturnId;
    }

    public override void populateClickableComponentList()
    {
        base.populateClickableComponentList();
        this.allClickableComponents.Clear();
        this.allClickableComponents.Add(this.BackButton);
        this.allClickableComponents.AddRange(this.ActiveSlots);
        this.allClickableComponents.Add(this.BossSlot);
        this.allClickableComponents.Add(this.SecretSlot);
        this.allClickableComponents.AddRange(this.MainFilterTabs.Select(p => p.Button));
        this.allClickableComponents.Add(this.NormalScrapButton);
        this.allClickableComponents.Add(this.ShinyScrapButton);
        this.allClickableComponents.Add(this.FavoriteFilterTab);
        this.allClickableComponents.AddRange(this.CardButtons.Select(p => p.Button));
        this.allClickableComponents.Add(this.PrevPageButton);
        this.allClickableComponents.Add(this.NextPageButton);
        this.allClickableComponents.Add(this.FavoriteActionButton);
        this.allClickableComponents.Add(this.EquipActionButton);
        this.allClickableComponents.Add(this.UpgradeActionButton);
        this.allClickableComponents.Add(this.DeselectActionButton);
    }

    public override void snapToDefaultClickableComponent()
    {
        this.currentlySnappedComponent = this.ActiveSlots.FirstOrDefault() ?? this.BackButton;
        this.snapCursorToCurrentSnappedComponent();
    }

    public override void receiveGamePadButton(Buttons b)
    {
        this.LastInputWasController = true;
        int focusedId = this.currentlySnappedComponent?.myID ?? -1;
        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;

        // alpha.23: controller actions are semantic and profile-driven. Individual menus never
        // hard-code a brand-specific A/B/X/Y layout again.
        if (this.Controller.IsExit(b))
        {
            this.CloseBinderToGameplay();
            return;
        }

        if (this.Controller.IsDeselect(b))
        {
            if (this.ControllerSelectionLocked && this.LockedCard is not null)
                this.ReleaseSelectionLock(returnToCard: true);
            else
                Game1.playSound("cancel");
            return;
        }

        if (this.Controller.IsFavorite(b))
        {
            if (this.ControllerSelectionLocked && this.LockedCard is not null)
            {
                this.RestoreLockedSelectionForAction();
                this.ToggleFavorite();
            }
            else
            {
                this.Status = ModEntry.T("binder.favorite.select-first");
                Game1.playSound("cancel");
            }
            return;
        }

        if (collectionFocused && (b == Buttons.LeftShoulder || b == Buttons.RightShoulder))
        {
            int oldIndex = focusedId - CardBaseId;
            int direction = b == Buttons.LeftShoulder ? -1 : 1;
            this.ChangePage(direction, oldIndex);
            return;
        }

        if (this.Controller.IsConfirm(b) && this.currentlySnappedComponent is not null)
        {
            this.ActivateFocusedComponent(fromController: true);
            return;
        }

        base.receiveGamePadButton(b);
        this.SyncBrowsePreviewToFocusedCard();
    }

    public override void receiveKeyPress(Keys key)
    {
        this.LastInputWasController = false;

        if ((key == Keys.Enter || key == Keys.Space) && this.currentlySnappedComponent is not null)
        {
            this.ActivateFocusedComponent(fromController: true);
            return;
        }

        if (key == Keys.F)
        {
            if (this.ControllerSelectionLocked && this.LockedCard is not null)
            {
                this.RestoreLockedSelectionForAction();
                this.ToggleFavorite();
            }
            else
            {
                this.Status = ModEntry.T("binder.favorite.select-first");
                Game1.playSound("cancel");
            }
            return;
        }

        if (key == Keys.Back)
        {
            if (this.ControllerSelectionLocked && this.LockedCard is not null)
                this.ReleaseSelectionLock(returnToCard: true);
            else
                Game1.playSound("cancel");
            return;
        }

        if (key == Keys.Escape)
        {
            this.CloseBinderToGameplay();
            return;
        }

        base.receiveKeyPress(key);
        this.SyncBrowsePreviewToFocusedCard();
    }

    private void ActivateFocusedComponent(bool fromController)
    {
        ClickableComponent? focused = this.currentlySnappedComponent;
        if (focused is null)
            return;

        int id = focused.myID;
        if (id >= CardBaseId && id < CardBaseId + this.CardButtons.Count)
        {
            int index = id - CardBaseId;
            CardDefinition card = this.CardButtons[index].Card;
            this.HandleCollectionActivation(card, fromController);
            return;
        }

        if (id == FavoriteActionId)
        {
            this.RestoreLockedSelectionForAction();
            this.ToggleFavorite();
            return;
        }

        if (id == EquipActionId)
        {
            this.RestoreLockedSelectionForAction();
            this.ToggleEquip();
            return;
        }

        if (id == UpgradeActionId)
        {
            this.RestoreLockedSelectionForAction();
            this.TryUpgradeSelected();
            return;
        }

        if (id == DeselectActionId)
        {
            this.ReleaseSelectionLock(returnToCard: fromController);
            return;
        }

        if (id == NormalScrapId || id == ShinyScrapId)
        {
            this.Status = id == NormalScrapId
                ? ModEntry.T("item.cardboard.desc")
                : ModEntry.T("item.shiny.desc");
            Game1.playSound("smallSelect");
            return;
        }

        Rectangle r = focused.bounds;
        this.receiveLeftClick(r.Center.X, r.Center.Y, playSound: true);
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        this.LastInputWasController = false;

        if (this.BackButton.bounds.Contains(x, y))
        {
            this.CloseBinderToGameplay();
            return;
        }

        // Handle the three bottom controls before collection/navigation hit testing.
        // A small padded hit target also makes UI-scale rounding at the page edge harmless.
        if (Inflate(this.FavoriteActionButton.bounds, 3).Contains(x, y))
        {
            this.RestoreLockedSelectionForAction();
            this.ToggleFavorite();
            return;
        }

        if (Inflate(this.EquipActionButton.bounds, 3).Contains(x, y))
        {
            this.RestoreLockedSelectionForAction();
            this.ToggleEquip();
            return;
        }

        if (Inflate(this.UpgradeActionButton.bounds, 3).Contains(x, y))
        {
            this.RestoreLockedSelectionForAction();
            this.TryUpgradeSelected();
            return;
        }

        if (Inflate(this.DeselectActionButton.bounds, 3).Contains(x, y))
        {
            this.ReleaseSelectionLock(returnToCard: false);
            return;
        }

        if (this.NormalScrapButton.bounds.Contains(x, y))
        {
            this.Status = ModEntry.T("item.cardboard.desc");
            Game1.playSound("smallSelect");
            return;
        }

        if (this.ShinyScrapButton.bounds.Contains(x, y))
        {
            this.Status = ModEntry.T("item.shiny.desc");
            Game1.playSound("smallSelect");
            return;
        }

        foreach ((BinderFilter filter, ClickableComponent button) in this.MainFilterTabs)
        {
            if (!button.bounds.Contains(x, y))
                continue;

            this.SetFilter(filter);
            return;
        }

        if (this.FavoriteFilterTab.bounds.Contains(x, y))
        {
            this.SetFilter(BinderFilter.Favorite);
            return;
        }

        if (this.PrevPageButton.bounds.Contains(x, y))
        {
            if (this.CurrentPage > 0)
            {
                this.CurrentPage--;
                Game1.playSound("shwip");
                this.RebuildCardButtons(resetPage: false);
            }
            return;
        }

        if (this.NextPageButton.bounds.Contains(x, y))
        {
            int pages = this.PageCount();
            if (this.CurrentPage + 1 < pages)
            {
                this.CurrentPage++;
                Game1.playSound("shwip");
                this.RebuildCardButtons(resetPage: false);
            }
            return;
        }

        for (int i = 0; i < this.ActiveSlots.Count; i++)
        {
            if (!this.ActiveSlots[i].bounds.Contains(x, y))
                continue;

            if (i >= this.UnlockedSlots)
            {
                this.Status = ModEntry.T("binder.status.slot-locked");
                Game1.playSound("cancel");
                return;
            }

            if (i < this.Save.Data.EquippedCards.Count)
            {
                this.Selected = this.Cards.Get(this.Save.Data.EquippedCards[i]);
                this.Status = this.Selected is null
                    ? ModEntry.T("binder.status.pick")
                    : ModEntry.T("binder.status.selected", new { name = this.Selected.Name });
                Game1.playSound("smallSelect");
            }
            else
            {
                this.Status = ModEntry.T("binder.status.slot-empty", new { slot = i + 1 });
                Game1.playSound("smallSelect");
            }
            return;
        }

        if (this.BossSlot.bounds.Contains(x, y))
        {
            this.Status = ModEntry.T("binder.boss-slot.locked");
            Game1.playSound("cancel");
            return;
        }

        if (this.SecretSlot.bounds.Contains(x, y))
        {
            this.Status = ModEntry.T("binder.secret-slot.locked");
            Game1.playSound("cancel");
            return;
        }

        foreach ((CardDefinition card, ClickableComponent button) in this.CardButtons)
        {
            if (!button.bounds.Contains(x, y))
                continue;

            this.HandleCollectionActivation(card, fromController: false);
            return;
        }

        base.receiveLeftClick(x, y, playSound);
    }

    private void HandleCollectionActivation(CardDefinition card, bool fromController)
    {
        bool owned = this.Save.Data.OwnedCards.Contains(card.Id);
        double now = Game1.currentGameTime.TotalGameTime.TotalMilliseconds;
        double elapsed = now - this.LastQuickToggleAtMs;
        bool secondActivation = owned
            && string.Equals(this.LastQuickToggleCardId, card.Id, StringComparison.OrdinalIgnoreCase)
            && elapsed >= QuickToggleMinMs
            && elapsed <= QuickToggleWindowMs;

        this.LastQuickToggleCardId = card.Id;
        this.LastQuickToggleAtMs = now;

        // Any explicit confirm (controller A or mouse click) creates/replaces the hard lock.
        // Free browsing never mutates this card; only DESELECT clears it.
        this.LockedCard = card;
        this.ControllerSelectionLocked = true;
        this.PreviewCard = card;
        this.Selected = card;

        if (secondActivation)
        {
            this.LastQuickToggleCardId = null;
            this.LastQuickToggleAtMs = 0;
            this.ToggleEquip();
            return;
        }

        this.Status = owned
            ? ModEntry.T("binder.status.selected", new { name = card.Name })
            : ModEntry.T("binder.status.not-owned");
        Game1.playSound(owned ? "smallSelect" : "cancel");
    }

    private void ReleaseSelectionLock(bool returnToCard)
    {
        CardDefinition? releasedCard = this.LockedCard ?? this.Selected;

        this.ControllerSelectionLocked = false;
        this.LockedCard = null;
        this.LastQuickToggleCardId = null;
        this.LastQuickToggleAtMs = 0;
        this.Status = ModEntry.T("binder.status.browsing");
        Game1.playSound("shwip");

        if (returnToCard && Game1.options.SnappyMenus && releasedCard is not null)
        {
            ClickableComponent? target = this.CardButtons
                .FirstOrDefault(p => p.Card.Id.Equals(releasedCard.Id, StringComparison.OrdinalIgnoreCase))
                .Button;
            if (target is not null)
            {
                this.currentlySnappedComponent = target;
                this.snapCursorToCurrentSnappedComponent();
            }
        }

        this.SyncBrowsePreviewToFocusedCard();
    }

    private void SyncBrowsePreviewToFocusedCard()
    {
        if (this.ControllerSelectionLocked && this.LockedCard is not null)
        {
            // Keep rendering and all action state pinned to the explicit lock.
            this.Selected = this.LockedCard;
            return;
        }

        int focusedId = this.currentlySnappedComponent?.myID ?? -1;
        if (focusedId < CardBaseId || focusedId >= CardBaseId + this.CardButtons.Count)
            return;

        int index = focusedId - CardBaseId;
        CardDefinition card = this.CardButtons[index].Card;
        this.PreviewCard = card;
        this.Selected = card;
        this.Status = this.Save.Data.OwnedCards.Contains(card.Id)
            ? ModEntry.T("binder.status.preview", new { name = card.Name })
            : ModEntry.T("binder.status.not-owned");
    }

    private void FocusDetailActionsForSelected(int selectedButtonId)
    {
        this.RestoreLockedSelectionForAction();
        if (!this.ControllerSelectionLocked || this.LockedCard is null)
            return;

        this.FavoriteActionButton.leftNeighborID = selectedButtonId;
        this.EquipActionButton.leftNeighborID = selectedButtonId;
        this.UpgradeActionButton.leftNeighborID = selectedButtonId;
        this.DeselectActionButton.leftNeighborID = selectedButtonId;
        this.currentlySnappedComponent = this.EquipActionButton;
        this.snapCursorToCurrentSnappedComponent();
        Game1.playSound("shwip");
    }

    private void RestoreLockedSelectionForAction()
    {
        if (this.ControllerSelectionLocked && this.LockedCard is not null)
            this.Selected = this.LockedCard;
    }

    private void SetFilter(BinderFilter filter)
    {
        if (this.CurrentFilter == filter)
            return;

        this.CurrentFilter = filter;
        this.CurrentPage = 0;
        this.LastQuickToggleCardId = null;
        this.LastQuickToggleAtMs = 0;
        this.Status = filter == BinderFilter.Favorite
            ? ModEntry.T("binder.favorite.filter")
            : ModEntry.T("binder.status.pick");
        Game1.playSound("smallSelect");
        this.RebuildCardButtons(resetPage: true);

        if (Game1.options.SnappyMenus && this.CardButtons.Count > 0)
        {
            this.currentlySnappedComponent = this.CardButtons[0].Button;
            this.snapCursorToCurrentSnappedComponent();
        }
    }

    private void ChangePage(int direction, int preferredCardIndex)
    {
        int next = Math.Clamp(this.CurrentPage + direction, 0, this.PageCount() - 1);
        if (next == this.CurrentPage)
        {
            Game1.playSound("cancel");
            return;
        }

        this.CurrentPage = next;
        this.RebuildCardButtons(resetPage: false);
        if (Game1.options.SnappyMenus && this.CardButtons.Count > 0)
        {
            this.currentlySnappedComponent = this.CardButtons[Math.Min(preferredCardIndex, this.CardButtons.Count - 1)].Button;
            this.snapCursorToCurrentSnappedComponent();
        }
        Game1.playSound("shwip");
    }

    private void ToggleFavorite()
    {
        if (this.Selected is null || !this.Save.Data.OwnedCards.Contains(this.Selected.Id))
        {
            this.Status = ModEntry.T("binder.favorite.locked");
            Game1.playSound("cancel");
            return;
        }

        if (this.Save.Data.FavoriteCardIds.Contains(this.Selected.Id))
        {
            this.Save.Data.FavoriteCardIds.Remove(this.Selected.Id);
            this.Status = ModEntry.T("binder.favorite.removed", new { name = this.Selected.Name });
        }
        else
        {
            this.Save.Data.FavoriteCardIds.Add(this.Selected.Id);
            this.Status = ModEntry.T("binder.favorite.added", new { name = this.Selected.Name });
        }

        this.Save.Save();
        Game1.playSound("coin");

        if (this.CurrentFilter == BinderFilter.Favorite)
            this.RebuildCardButtons(resetPage: false);
    }

    private void ToggleEquip()
    {
        if (this.Selected is null || !this.Save.Data.OwnedCards.Contains(this.Selected.Id))
        {
            this.Status = ModEntry.T("binder.status.not-owned");
            Game1.playSound("cancel");
            return;
        }

        if (this.Loadout.IsEquipped(this.Selected.Id))
        {
            if (this.Loadout.Unequip(this.Selected.Id))
            {
                this.Status = ModEntry.T("binder.status.unequipped", new { name = this.Selected.Name });
                this.OnLoadoutChanged();
                Game1.playSound("dwop");
            }
            return;
        }

        if (this.Loadout.Equip(this.Selected.Id))
        {
            this.Status = ModEntry.T("binder.status.equipped", new { name = this.Selected.Name });
            this.OnLoadoutChanged();
            Game1.playSound("coin");
        }
        else
        {
            this.Status = ModEntry.T("binder.status.full", new { slots = this.UnlockedSlots });
            Game1.playSound("cancel");
        }
    }

    private void TryUnlockSlot()
    {
        if (this.UnlockedSlots >= VisualActiveSlots)
        {
            this.Status = ModEntry.T("binder.status.slot-maxed");
            Game1.playSound("cancel");
            return;
        }

        if (this.Upgrades.TryUnlockNextSlot(out int newSlotCount, out int cost))
        {
            this.Status = ModEntry.T("binder.status.slot-unlocked", new { slot = newSlotCount, cost });
            Game1.playSound("reward");
            return;
        }

        this.Status = ModEntry.T("binder.status.slot-not-enough-dust", new { cost = this.Upgrades.GetNextSlotUnlockCost() });
        Game1.playSound("cancel");
    }

    private void TryUpgradeSelected()
    {
        if (this.Selected is null || !this.Save.Data.OwnedCards.Contains(this.Selected.Id))
        {
            this.Status = ModEntry.T("binder.status.not-owned");
            Game1.playSound("cancel");
            return;
        }

        if (this.Upgrades.IsMaxLevel(this.Selected))
        {
            this.Status = ModEntry.T("binder.status.card-maxed", new { name = this.Selected.Name });
            Game1.playSound("cancel");
            return;
        }

        int have = this.Upgrades.GetCopies(this.Selected);
        int need = this.Upgrades.GetRequiredCopies(this.Selected);
        if (!this.Upgrades.TryUpgrade(this.Selected, out int newLevel, out int copiesSpent))
        {
            this.Status = ModEntry.T("binder.status.card-not-enough-copies", new { have, need });
            Game1.playSound("cancel");
            return;
        }

        this.Status = ModEntry.T("binder.status.card-upgraded", new { name = this.Selected.Name, level = newLevel, copies = copiesSpent });
        Game1.playSound("reward");
    }

    private int PageCount()
        => Math.Max(1, (int)Math.Ceiling(this.FilteredCards().Count / (double)CardsPerPage));

    private string GetDisplayEffectText(CardDefinition card, int level)
    {
        int index = Math.Max(0, level - 1);
        string localizedKey = $"card.{card.Id}.star.{level}";
        string localizedRule = ModEntry.T(localizedKey);
        if (!string.IsNullOrWhiteSpace(localizedRule) && !localizedRule.Equals(localizedKey, StringComparison.OrdinalIgnoreCase))
            return localizedRule;

        // Fallback for third-party language packs which haven't copied alpha.23 star keys yet.
        if (index < card.StarRules.Count && !string.IsNullOrWhiteSpace(card.StarRules[index]))
        {
            string rule = card.StarRules[index];
            if (index > 0 && card.StarRules.Count > 0 && !string.IsNullOrWhiteSpace(card.StarRules[0]))
                return CompleteStarRule(card.StarRules[0], rule);

            return rule;
        }

        return this.Upgrades.GetLevelEffectText(card, level);
    }

    /// <summary>
    /// StarRules intentionally store many later levels as compact deltas (for example "+5%").
    /// Rebuild those deltas onto the level-one sentence so every Binder row names its trigger,
    /// stat, duration, cap, and cooldown instead of showing an isolated number.
    /// </summary>
    private static string CompleteStarRule(string levelOneRule, string compactRule)
    {
        if (string.IsNullOrWhiteSpace(levelOneRule)
            || string.IsNullOrWhiteSpace(compactRule)
            || levelOneRule.Equals(compactRule, StringComparison.OrdinalIgnoreCase))
        {
            return compactRule;
        }

        List<EffectNumberToken> templateTokens = ReadEffectNumberTokens(levelOneRule);
        List<EffectNumberToken> valueTokens = ReadEffectNumberTokens(compactRule);
        if (templateTokens.Count == 0 || valueTokens.Count == 0)
            return AddMissingTriggerContext(levelOneRule, compactRule);

        Dictionary<int, string> replacements = new();
        HashSet<int> usedTemplateIndexes = new();
        int lastMatchedTemplateIndex = -1;

        foreach (EffectNumberToken value in valueTokens)
        {
            List<int> candidates = Enumerable.Range(0, templateTokens.Count)
                .Where(i => !usedTemplateIndexes.Contains(i))
                .Where(i => UnitsCompatible(templateTokens[i].Unit, value.Unit))
                .ToList();

            if (candidates.Count == 0)
                return AddMissingTriggerContext(levelOneRule, compactRule);

            List<int> sameSign = candidates
                .Where(i => templateTokens[i].Sign.Equals(value.Sign, StringComparison.Ordinal))
                .ToList();
            if (sameSign.Count > 0)
                candidates = sameSign;

            int chosen = candidates.FirstOrDefault(i => i > lastMatchedTemplateIndex, -1);
            if (chosen < 0)
                chosen = candidates[0];

            usedTemplateIndexes.Add(chosen);
            lastMatchedTemplateIndex = chosen;
            replacements[chosen] = value.Raw;
        }

        StringBuilder completed = new();
        int cursor = 0;
        for (int i = 0; i < templateTokens.Count; i++)
        {
            EffectNumberToken token = templateTokens[i];
            completed.Append(levelOneRule, cursor, token.Start - cursor);
            completed.Append(replacements.TryGetValue(i, out string? replacement) ? replacement : token.Raw);
            cursor = token.Start + token.Length;
        }
        completed.Append(levelOneRule, cursor, levelOneRule.Length - cursor);
        return completed.ToString();
    }

    private static string AddMissingTriggerContext(string levelOneRule, string compactRule)
    {
        int triggerEnd = levelOneRule.IndexOf(':');
        if (triggerEnd <= 0 || compactRule.Contains(':'))
            return compactRule;

        string trigger = levelOneRule[..(triggerEnd + 1)].Trim();
        return $"{trigger} {compactRule.Trim()}";
    }

    private static List<EffectNumberToken> ReadEffectNumberTokens(string text)
    {
        List<EffectNumberToken> result = new();
        foreach (Match match in EffectNumberRegex.Matches(text))
        {
            string unit = NormalizeEffectUnit(match.Groups["unit"].Value);
            if (unit == "s")
            {
                string prefix = text[..match.Index];
                if (Regex.IsMatch(prefix, @"ICD\s*$", RegexOptions.IgnoreCase))
                    unit = "icd-s";
                else if (Regex.IsMatch(prefix, @"\bCD\s*$", RegexOptions.IgnoreCase))
                    unit = "cd-s";
            }

            result.Add(new EffectNumberToken(
                match.Index,
                match.Length,
                match.Value,
                match.Groups["sign"].Value,
                unit
            ));
        }
        return result;
    }

    private static string NormalizeEffectUnit(string raw)
    {
        string unit = Regex.Replace(raw ?? string.Empty, @"\s+", string.Empty).ToLowerInvariant();
        return unit switch
        {
            "%maxhp" => "percent-max-hp",
            "%hp" => "percent-hp",
            "%" => "percent",
            "hp/s" => "hp-per-second",
            "hp" => "hp",
            "px" => "px",
            "dust" => "dust",
            "fate" => "fate",
            "defense" or "def" => "defense",
            "s" => "s",
            _ => "number"
        };
    }

    private static bool UnitsCompatible(string template, string value)
    {
        if (template.Equals(value, StringComparison.Ordinal))
            return true;

        bool templatePercent = template.StartsWith("percent", StringComparison.Ordinal);
        bool valuePercent = value.StartsWith("percent", StringComparison.Ordinal);
        return templatePercent && valuePercent;
    }

    private readonly record struct EffectNumberToken(
        int Start,
        int Length,
        string Raw,
        string Sign,
        string Unit
    );

    private void CloseBinderToGameplay()
    {
        Game1.playSound("bigDeSelect");
        Game1.exitActiveMenu();
    }

    private void CloseBinder()
        => this.CloseBinderToGameplay();

    public override void draw(SpriteBatch b)
    {
        if (this.BackgroundMenu is not null)
            this.BackgroundMenu.draw(b);
        else
            this.drawBackground(b);
        b.Draw(Game1.fadeToBlackRect, new Rectangle(0, 0, Game1.uiViewport.Width, Game1.uiViewport.Height), Color.Black * 0.34f);

        this.DrawBook(b);
        this.DrawTabs(b);
        this.DrawLeftPage(b);
        this.DrawRightPage(b);
        this.DrawResourceTooltipIfNeeded(b);
        this.DrawControlHintBar(b);

        this.drawMouse(b);
    }

    private void DrawControlHintBar(SpriteBatch b)
    {
        int y = this.OuterBook.Bottom + 6;
        int availableHeight = Game1.uiViewport.Height - y - 4;
        if (availableHeight < 20)
            return;

        int barHeight = Math.Min(34, availableHeight);
        int barWidth = Math.Min(this.OuterBook.Width - 80, 1120);
        Rectangle bar = new(this.OuterBook.Center.X - barWidth / 2, y, barWidth, barHeight);

        DrawRoundedRect(b, bar, new Color(19, 24, 31) * 0.90f, 10);
        DrawRoundedBorder(b, bar, CardchaUi.Gold * 0.72f, 2, 10);

        bool hasLock = this.ControllerSelectionLocked && this.LockedCard is not null;
        if (this.LastInputWasController)
        {
            this.DrawControlHintItems(b, bar, new[]
            {
                new ControlHint(this.Controller.GetLabel(ControllerAction.Confirm), ModEntry.T("binder.hint.select"), true),
                new ControlHint(this.Controller.GetLabel(ControllerAction.Favorite), ModEntry.T("binder.hint.favorite"), hasLock),
                new ControlHint(this.Controller.GetLabel(ControllerAction.Deselect), ModEntry.T("binder.hint.deselect"), hasLock),
                new ControlHint(this.Controller.GetLabel(ControllerAction.Exit), ModEntry.T("binder.hint.close"), true)
            });
        }
        else
        {
            this.DrawControlHintItems(b, bar, new[]
            {
                new ControlHint("Enter/Space", ModEntry.T("binder.hint.select"), true),
                new ControlHint("F", ModEntry.T("binder.hint.favorite"), hasLock),
                new ControlHint("Backspace", ModEntry.T("binder.hint.deselect"), hasLock),
                new ControlHint("Esc", ModEntry.T("binder.hint.close"), true)
            });
        }
    }

    private void DrawControlHintItems(SpriteBatch b, Rectangle bar, IReadOnlyList<ControlHint> hints)
    {
        float totalNatural = 0f;
        foreach (ControlHint hint in hints)
            totalNatural += this.MeasureControlHint(hint);

        float gap = 18f;
        totalNatural += gap * (hints.Count - 1);
        float fitScale = totalNatural > bar.Width - 20
            ? Math.Max(0.62f, (bar.Width - 20) / totalNatural)
            : 1f;

        float x = bar.Center.X - totalNatural * fitScale / 2f;
        float centerY = bar.Center.Y;
        foreach (ControlHint hint in hints)
        {
            float naturalWidth = this.MeasureControlHint(hint);
            this.DrawControlHintItem(b, new Vector2(x, centerY), hint, fitScale);
            x += (naturalWidth + gap) * fitScale;
        }
    }

    private float MeasureControlHint(ControlHint hint)
    {
        Vector2 keySize = Game1.smallFont.MeasureString(hint.Key);
        Vector2 textSize = Game1.smallFont.MeasureString(hint.Label);
        float keyWidth = Math.Max(26f, keySize.X + 12f);
        return keyWidth + 7f + textSize.X;
    }

    private void DrawControlHintItem(SpriteBatch b, Vector2 position, ControlHint hint, float scale)
    {
        Color tint = hint.Enabled ? Color.White : Color.White * 0.38f;
        Vector2 keyText = Game1.smallFont.MeasureString(hint.Key);
        float keyWidth = Math.Max(26f, keyText.X + 12f);
        float keyHeight = 23f;
        Rectangle keyBox = new(
            (int)position.X,
            (int)(position.Y - keyHeight * scale / 2f),
            Math.Max(18, (int)(keyWidth * scale)),
            Math.Max(16, (int)(keyHeight * scale))
        );

        DrawRoundedRect(b, keyBox, new Color(58, 68, 78) * (hint.Enabled ? 0.95f : 0.55f), 6);
        DrawRoundedBorder(b, keyBox, CardchaUi.Gold * (hint.Enabled ? 0.90f : 0.38f), 1, 6);

        Vector2 keyDrawSize = Game1.smallFont.MeasureString(hint.Key) * scale;
        b.DrawString(
            Game1.smallFont,
            hint.Key,
            new Vector2(keyBox.Center.X - keyDrawSize.X / 2f, keyBox.Center.Y - keyDrawSize.Y / 2f),
            tint,
            0f,
            Vector2.Zero,
            scale,
            SpriteEffects.None,
            1f
        );

        Vector2 labelPos = new(keyBox.Right + 7f * scale, position.Y);
        Vector2 labelSize = Game1.smallFont.MeasureString(hint.Label) * scale;
        b.DrawString(
            Game1.smallFont,
            hint.Label,
            new Vector2(labelPos.X, labelPos.Y - labelSize.Y / 2f),
            tint,
            0f,
            Vector2.Zero,
            scale,
            SpriteEffects.None,
            1f
        );
    }

    private readonly record struct ControlHint(string Key, string Label, bool Enabled);

    private void DrawBook(SpriteBatch b)
    {
        DrawRoundedRect(b, this.OuterBook, CardchaUi.LeatherDark, 18);
        DrawRoundedRect(b, Inflate(this.OuterBook, -6), CardchaUi.Leather, 14);
        DrawRoundedBorder(b, this.OuterBook, new Color(105, 56, 32), 4, 18);
        DrawRoundedBorder(b, Inflate(this.OuterBook, -7), CardchaUi.Gold * 0.92f, 3, 14);
        CardchaUi.DrawCornerOrnaments(b, Inflate(this.OuterBook, -3), CardchaUi.Gold);

        DrawRoundedRect(b, this.LeftPage, CardchaUi.ParchmentLight, 12);
        DrawRoundedRect(b, this.RightPage, CardchaUi.ParchmentLight, 12);
        this.DrawPagePattern(b, this.LeftPage);
        this.DrawPagePattern(b, this.RightPage);
        DrawRoundedBorder(b, this.LeftPage, CardchaUi.PaperShadow, 3, 12);
        DrawRoundedBorder(b, this.RightPage, CardchaUi.PaperShadow, 3, 12);
        DrawRoundedBorder(b, Inflate(this.LeftPage, -7), CardchaUi.PaperShadow * 0.35f, 1, 8);
        DrawRoundedBorder(b, Inflate(this.RightPage, -7), CardchaUi.PaperShadow * 0.35f, 1, 8);
        CardchaUi.DrawCornerOrnaments(b, Inflate(this.LeftPage, -8), CardchaUi.PaperShadow * 0.72f);
        CardchaUi.DrawCornerOrnaments(b, Inflate(this.RightPage, -8), CardchaUi.PaperShadow * 0.72f);

        int seamX = (this.LeftPage.Right + this.RightPage.Left) / 2;
        b.Draw(Game1.staminaRect, new Rectangle(seamX - 4, this.LeftPage.Y + 8, 8, this.LeftPage.Height - 16), CardchaUi.LeatherDark * 0.88f);
        b.Draw(Game1.staminaRect, new Rectangle(seamX - 3, this.LeftPage.Y + 12, 1, this.LeftPage.Height - 24), CardchaUi.Gold * 0.65f);
        b.Draw(Game1.staminaRect, new Rectangle(seamX + 2, this.LeftPage.Y + 12, 1, this.LeftPage.Height - 24), CardchaUi.Gold * 0.65f);
        for (int y = this.LeftPage.Y + 60; y < this.LeftPage.Bottom - 50; y += 120)
        {
            Rectangle stud = new(seamX - 7, y, 14, 14);
            DrawCircle(b, stud, CardchaUi.Gold);
            DrawCircle(b, Inflate(stud, -3), new Color(48, 66, 81));
        }
    }

    private void DrawPagePattern(SpriteBatch b, Rectangle page)
    {
        Color ink = CardchaUi.PaperShadow * 0.12f;
        for (int y = page.Y + 34; y < page.Bottom - 28; y += 54)
        {
            int row = (y - page.Y) / 54;
            for (int x = page.X + 34 + (row % 2) * 27; x < page.Right - 28; x += 54)
            {
                b.Draw(Game1.staminaRect, new Rectangle(x, y, 2, 2), ink);
                b.Draw(Game1.staminaRect, new Rectangle(x - 2, y + 2, 6, 1), ink * 0.75f);
            }
        }
    }

    private void DrawTabs(SpriteBatch b)
    {
        foreach ((BinderFilter filter, ClickableComponent button) in this.MainFilterTabs)
            this.DrawBookmark(b, button, this.FilterLabel(filter), this.CurrentFilter == filter, this.FilterColor(filter));

        this.DrawResourceSlot(b, this.NormalScrapButton, shiny: false);
        this.DrawResourceSlot(b, this.ShinyScrapButton, shiny: true);

        this.DrawBookmark(
            b,
            this.FavoriteFilterTab,
            "★ " + ModEntry.T("binder.favorite"),
            this.CurrentFilter == BinderFilter.Favorite,
            CardchaUi.Gold
        );
    }

    private void DrawLeftPage(SpriteBatch b)
    {
        this.DrawSmallButton(b, this.BackButton, "X", CardchaUi.Leather);

        string progress = ModEntry.T("binder.discovered", new
        {
            owned = this.Save.Data.OwnedCards.Count,
            total = this.Cards.All.Count
        });
        Rectangle title = new(this.LeftPage.X + 82, this.LeftPage.Y + 12, this.LeftPage.Width - 104, 42);
        DrawRoundedRect(b, title, new Color(38, 53, 68), 8);
        DrawRoundedBorder(b, title, CardchaUi.Gold, 2, 8);
        CardchaUi.DrawAutoFitWrappedText(b, Game1.dialogueFont, ModEntry.T("binder.title"), Inflate(title, -5), new Color(255, 205, 88), maxLines: 1, minScale: 0.55f, centerX: true, maxScale: 1.0f, centerY: true);

        for (int i = 0; i < this.ActiveSlots.Count; i++)
            this.DrawActiveCircle(b, i, this.ActiveSlots[i]);
        this.DrawBossCircle(b);
        this.DrawSecretCircle(b);

        Utility.drawTextWithShadow(b, ModEntry.T("binder.collection"), Game1.smallFont, new Vector2(this.CollectionArea.X, this.CollectionArea.Y - 29), CardchaUi.InkBrown);
        string filterCaption = this.CurrentFilter == BinderFilter.Favorite
            ? ModEntry.T("binder.favorite")
            : this.FilterLabel(this.CurrentFilter);
        Vector2 filterSize = Game1.smallFont.MeasureString(filterCaption);
        b.DrawString(Game1.smallFont, filterCaption, new Vector2(this.CollectionArea.Right - filterSize.X, this.CollectionArea.Y - 28), this.FilterColor(this.CurrentFilter), 0f, Vector2.Zero, 1f, SpriteEffects.None, 1f);

        if (this.CardButtons.Count == 0 && this.CurrentFilter == BinderFilter.Favorite)
        {
            CardchaUi.DrawAutoFitWrappedText(
                b,
                Game1.smallFont,
                ModEntry.T("binder.favorite.empty"),
                this.CollectionArea,
                Color.DarkSlateGray,
                maxLines: 3,
                minScale: 0.75f,
                centerX: true,
                maxScale: 1.15f,
                centerY: true
            );
        }
        else
        {
            foreach ((CardDefinition card, ClickableComponent button) in this.CardButtons)
                this.DrawCollectionCell(b, card, button);
        }

        int pages = this.PageCount();
        this.DrawPageSeal(b, this.PrevPageButton, pointsLeft: true, enabled: this.CurrentPage > 0);
        this.DrawPageSeal(b, this.NextPageButton, pointsLeft: false, enabled: this.CurrentPage + 1 < pages);

        string pageText = ModEntry.T("binder.collection.page", new { page = this.CurrentPage + 1, pages });
        Rectangle pageArea = new(this.PrevPageButton.bounds.Right + 8, this.PrevPageButton.bounds.Y, this.NextPageButton.bounds.X - this.PrevPageButton.bounds.Right - 16, this.PrevPageButton.bounds.Height);

        // Keep Trang x/y in its existing centered pageArea. The compact discovery count
        // simply shares the same footer line on its left side.
        Rectangle discoveryArea = new(
            pageArea.X,
            pageArea.Y,
            Math.Max(100, pageArea.Width / 2 - 40),
            pageArea.Height
        );
        CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, progress, discoveryArea, Color.DarkSlateGray, maxLines: 1, minScale: 0.75f, centerX: false, maxScale: 1f, centerY: true);
        CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, pageText, pageArea, Color.DarkSlateGray, maxLines: 1, minScale: 0.65f, centerX: true, maxScale: 1f);
    }

    private void DrawRightPage(SpriteBatch b)
    {
        Rectangle header = new(this.RightPage.X + 24, this.RightPage.Y + 18, this.RightPage.Width - 48, 44);
        DrawRoundedRect(b, header, new Color(38, 53, 68), 8);
        DrawRoundedBorder(b, header, CardchaUi.Gold, 2, 8);
        CardchaUi.DrawAutoFitWrappedText(b, Game1.dialogueFont, ModEntry.T("binder.details"), Inflate(header, -5), new Color(255, 205, 88), maxLines: 1, minScale: 0.55f, centerX: true, maxScale: 1.05f, centerY: true);

        if (this.Selected is null)
        {
            Rectangle empty = new(this.RightPage.X + 44, this.RightPage.Y + 120, this.RightPage.Width - 88, this.RightPage.Height - 250);
            CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, ModEntry.T("binder.inspect-help"), empty, Color.DarkSlateGray, maxLines: 5, minScale: 0.80f, centerX: true, maxScale: 1.25f, centerY: true);
            this.DrawStatus(b);
            this.DrawActionButtons(b, owned: false);
            return;
        }

        bool owned = this.Save.Data.OwnedCards.Contains(this.Selected.Id);
        int baseId = this.Selected.StableBaseId;
        Rectangle icon = new(this.RightPage.X + 32, this.RightPage.Y + 76, 104, 104);
        DrawRoundedRect(b, icon, new Color(225, 205, 171), 12);
        DrawRoundedBorder(b, icon, CardchaUi.RarityColor(this.Selected.Rarity), 4, 12);
        Rectangle iconInner = new(icon.X + 12, icon.Y + 12, icon.Width - 24, icon.Height - 24);
        if (owned)
            this.Renderer.DrawIcon(b, iconInner, this.Selected);
        else
            this.Renderer.DrawIconGrayscale(b, iconInner, this.Selected, 0.82f);

        Rectangle nameArea = new(icon.Right + 18, icon.Y, this.RightPage.Right - icon.Right - 42, 48);
        string name = owned ? this.Selected.Name : "???";
        DrawRoundedRect(b, nameArea, new Color(51, 50, 51), 7);
        DrawRoundedBorder(b, nameArea, CardchaUi.Gold * 0.85f, 2, 7);
        CardchaUi.DrawAutoFitWrappedText(b, Game1.dialogueFont, name, Inflate(nameArea, -6), new Color(255, 205, 88), maxLines: 2, minScale: 0.50f, centerX: true, maxScale: 0.95f, centerY: true);
        Utility.drawTextWithShadow(b, $"#{baseId:00}", Game1.smallFont, new Vector2(nameArea.X, nameArea.Bottom + 2), Color.DarkSlateGray);
        Utility.drawTextWithShadow(b, CardchaUi.RarityText(this.Selected.Rarity), Game1.smallFont, new Vector2(nameArea.X + 70, nameArea.Bottom + 2), CardchaUi.RarityColor(this.Selected.Rarity));

        if (!owned)
        {
            Rectangle lockedInfo = new(this.RightPage.X + 34, icon.Bottom + 40, this.RightPage.Width - 68, 180);
            DrawRoundedRect(b, lockedInfo, new Color(224, 214, 196), 10);
            CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, ModEntry.T("binder.status.not-owned"), Inflate(lockedInfo, -18), Color.DarkSlateGray, maxLines: 3, minScale: 0.75f, centerX: true, maxScale: 1.0f, centerY: true);
            this.DrawStatus(b);
            this.DrawActionButtons(b, owned: false);
            return;
        }

        int level = this.Upgrades.GetLevel(this.Selected);
        int maxLevel = this.Upgrades.GetMaxLevel(this.Selected);
        Utility.drawTextWithShadow(b, $"Lv{level}   •   {new string('★', level)}{new string('☆', Math.Max(0, maxLevel - level))}", Game1.smallFont, new Vector2(nameArea.X, nameArea.Bottom + 31), CardchaUi.InkBrown);

        Rectangle current = new(this.RightPage.X + 30, icon.Bottom + 22, this.RightPage.Width - 60, 112);
        DrawRoundedRect(b, current, new Color(238, 220, 187), 10);
        DrawRoundedBorder(b, current, CardchaUi.PaperShadow, 2, 10);
        Utility.drawTextWithShadow(b, ModEntry.T("binder.current-effect"), Game1.smallFont, new Vector2(current.X + 12, current.Y + 8), CardchaUi.InkBrown);
        Rectangle currentText = new(current.X + 12, current.Y + 36, current.Width - 24, current.Height - 44);
        CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, this.GetDisplayEffectText(this.Selected, level), currentText, Color.DarkSlateGray, maxLines: 3, minScale: 0.86f, centerX: true, maxScale: 1.28f, centerY: true);

        Rectangle levels = new(this.RightPage.X + 30, current.Bottom + 12, this.RightPage.Width - 60, Math.Max(155, this.UpgradeActionButton.bounds.Y - current.Bottom - 56));
        DrawRoundedRect(b, levels, new Color(246, 229, 198), 10);
        DrawRoundedBorder(b, levels, CardchaUi.PaperShadow, 2, 10);
        Utility.drawTextWithShadow(b, ModEntry.T("binder.all-levels"), Game1.smallFont, new Vector2(levels.X + 12, levels.Y + 7), CardchaUi.InkBrown);

        int rowY = levels.Y + 34;
        int availableH = levels.Bottom - rowY - 8;
        int rowH = Math.Max(24, availableH / Math.Max(1, maxLevel));
        for (int star = 1; star <= maxLevel; star++)
        {
            Rectangle row = new(levels.X + 10, rowY + (star - 1) * rowH, levels.Width - 20, rowH - 2);
            if (star == level)
                DrawRoundedRect(b, row, CardchaUi.Gold * 0.18f, 5);

            string rowText = $"★{star}   {this.GetDisplayEffectText(this.Selected, star)}";
            CardchaUi.DrawAutoFitWrappedText(
                b,
                Game1.smallFont,
                rowText,
                Inflate(row, -4),
                star <= level ? CardchaUi.InkBrown : Color.DarkSlateGray,
                maxLines: 2,
                minScale: 0.84f,
                centerX: true,
                maxScale: 1.25f,
                centerY: true
            );
        }

        this.DrawStatus(b);
        this.DrawActionButtons(b, owned: true);
    }

    private void DrawCollectionCell(SpriteBatch b, CardDefinition card, ClickableComponent button)
    {
        bool owned = this.Save.Data.OwnedCards.Contains(card.Id);
        bool equipped = this.Loadout.IsEquipped(card.Id);
        bool favorite = this.Save.Data.FavoriteCardIds.Contains(card.Id);
        bool selected = ReferenceEquals(this.Selected, card) || this.Selected?.Id.Equals(card.Id, StringComparison.OrdinalIgnoreCase) == true;
        bool locked = this.ControllerSelectionLocked
            && this.LockedCard?.Id.Equals(card.Id, StringComparison.OrdinalIgnoreCase) == true;
        bool focused = this.currentlySnappedComponent?.myID == button.myID;
        Color rarity = CardchaUi.RarityColor(card.Rarity);

        Rectangle r = button.bounds;
        Color outerEdge = locked ? new Color(82, 205, 255) : focused ? Color.White : selected ? Color.White : rarity;
        DrawRoundedRect(b, r, outerEdge, 9);
        if (locked)
            DrawRoundedBorder(b, Inflate(r, -2), Color.White * 0.92f, 2, 8);
        Rectangle inner = new(r.X + 4, r.Y + 4, r.Width - 8, r.Height - 8);
        DrawRoundedRect(b, inner, owned ? new Color(239, 220, 187) : new Color(198, 194, 184), 7);

        int level = owned ? this.Upgrades.GetLevel(card) : 0;
        int badgeSize = Math.Clamp(Math.Min(inner.Width, inner.Height) / 3, 22, 30);
        Rectangle idBadge = new(inner.X + 3, inner.Y + 3, badgeSize, badgeSize);
        Rectangle levelBadge = new(inner.Right - badgeSize - 3, inner.Y + 3, badgeSize, badgeSize);
        DrawCircle(b, idBadge, rarity);
        DrawCircle(b, Inflate(idBadge, -2), new Color(249, 235, 205));
        DrawCircle(b, levelBadge, rarity);
        DrawCircle(b, Inflate(levelBadge, -2), new Color(249, 235, 205));
        CardchaUi.DrawScaledText(b, Game1.smallFont, card.StableBaseId.ToString("00"), idBadge, CardchaUi.InkBrown, centerX: true, centerY: true, padding: 4, maxScale: 0.68f);
        CardchaUi.DrawScaledText(b, Game1.smallFont, owned ? level.ToString() : "–", levelBadge, CardchaUi.InkBrown, centerX: true, centerY: true, padding: 4, maxScale: 0.68f);

        int topPad = badgeSize / 2 + 5;
        int bottomPad = 8;
        int iconSize = Math.Max(24, Math.Min(inner.Width - 14, inner.Height - topPad - bottomPad));
        Rectangle icon = new(inner.Center.X - iconSize / 2, inner.Y + topPad, iconSize, iconSize);
        if (owned)
            this.Renderer.DrawIcon(b, icon, card);
        else
            this.Renderer.DrawIconGrayscale(b, icon, card, 0.82f);

        if (favorite && owned)
        {
            string mark = "★";
            Vector2 markSize = Game1.tinyFont.MeasureString(mark);
            Utility.drawTextWithShadow(b, mark, Game1.tinyFont, new Vector2(inner.Right - markSize.X - 4, inner.Bottom - markSize.Y + 2), CardchaUi.Gold);
        }

        if (equipped)
        {
            Rectangle overlay = new(inner.X + 1, inner.Y + 1, inner.Width - 2, inner.Height - 2);
            DrawRoundedRect(b, overlay, Color.Black * 0.42f, 7);
            CardchaUi.DrawAutoFitWrappedText(
                b,
                Game1.smallFont,
                ModEntry.T("binder.collection.equipped"),
                overlay,
                new Color(255, 236, 184),
                maxLines: 2,
                minScale: 0.48f,
                centerX: true,
                maxScale: 0.84f,
                centerY: true
            );
        }
    }

    private void DrawActiveCircle(SpriteBatch b, int index, ClickableComponent slot)
    {
        bool unlocked = index < this.UnlockedSlots;
        CardDefinition? card = index < this.Save.Data.EquippedCards.Count
            ? this.Cards.Get(this.Save.Data.EquippedCards[index])
            : null;
        Color border = !unlocked ? new Color(120, 105, 100) : card is null ? new Color(168, 150, 125) : CardchaUi.RarityColor(card.Rarity);
        bool focused = this.currentlySnappedComponent?.myID == slot.myID;

        DrawCircle(b, slot.bounds, focused ? Color.White : border);
        Rectangle inner = Inflate(slot.bounds, -4);
        DrawCircle(b, inner, unlocked ? new Color(231, 211, 178) : new Color(178, 166, 150));

        if (!unlocked)
        {
            DrawLockIcon(b, inner);
            return;
        }

        if (card is null)
        {
            DrawCircle(b, Inflate(inner, -10), new Color(189, 173, 151));
            return;
        }

        Rectangle icon = Inflate(inner, -9);
        this.Renderer.DrawIcon(b, icon, card);
    }

    private void DrawBossCircle(SpriteBatch b)
    {
        bool focused = this.currentlySnappedComponent?.myID == BossSlotId;
        Color mythic = CardchaUi.RarityColor(CardRarity.Mythic);
        DrawCircle(b, this.BossSlot.bounds, focused ? Color.White : mythic);
        Rectangle inner = Inflate(this.BossSlot.bounds, -4);
        DrawCircle(b, inner, new Color(181, 176, 164));
        DrawLockIcon(b, Inflate(inner, -8));
    }

    private void DrawSecretCircle(SpriteBatch b)
    {
        bool focused = this.currentlySnappedComponent?.myID == SecretSlotId;
        Color chachaPink = new(238, 105, 181);
        DrawCircle(b, this.SecretSlot.bounds, focused ? Color.White : chachaPink);
        Rectangle inner = Inflate(this.SecretSlot.bounds, -4);
        DrawCircle(b, inner, new Color(161, 137, 157));
        DrawLockIcon(b, Inflate(inner, -8));
    }

    private void DrawActionButtons(SpriteBatch b, bool owned)
    {
        bool favorite = owned && this.Selected is not null && this.Save.Data.FavoriteCardIds.Contains(this.Selected.Id);
        bool equipped = owned && this.Selected is not null && this.Loadout.IsEquipped(this.Selected.Id);
        bool maxed = !owned || this.Selected is null || this.Upgrades.IsMaxLevel(this.Selected);
        int have = this.Selected is null ? 0 : this.Upgrades.GetCopies(this.Selected);
        int need = this.Selected is null ? 0 : this.Upgrades.GetRequiredCopies(this.Selected);

        this.DrawSmallButton(
            b,
            this.FavoriteActionButton,
            favorite ? "★ " + ModEntry.T("binder.favorite.remove") : "☆ " + ModEntry.T("binder.favorite.add"),
            owned ? CardchaUi.Gold : new Color(130, 120, 112)
        );

        this.DrawSmallButton(
            b,
            this.EquipActionButton,
            equipped ? ModEntry.T("binder.unequip") : ModEntry.T("binder.equip"),
            owned ? (equipped ? CardchaUi.DangerRed : CardchaUi.GoodGreen) : new Color(130, 120, 112)
        );

        string upgrade = maxed
            ? ModEntry.T("binder.upgrade.max")
            : ModEntry.T("binder.upgrade", new { have, need });
        Color upgradeColor = !maxed && have >= need ? CardchaUi.PremiumPurple : new Color(130, 120, 112);
        this.DrawSmallButton(b, this.UpgradeActionButton, upgrade, upgradeColor);

        this.DrawSmallButton(
            b,
            this.DeselectActionButton,
            ModEntry.T("binder.deselect"),
            this.ControllerSelectionLocked ? new Color(75, 102, 123) : new Color(130, 120, 112)
        );
    }

    private void DrawStatus(SpriteBatch b)
    {
        Rectangle statusArea = new(
            this.RightPage.X + 28,
            this.FavoriteActionButton.bounds.Y - 38,
            this.RightPage.Width - 56,
            32
        );
        CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, this.Status, statusArea, Color.DarkSlateGray, maxLines: 1, minScale: 0.75f, centerX: true, maxScale: 1.0f, centerY: true);
    }

    private string FilterLabel(BinderFilter filter)
        => filter switch
        {
            BinderFilter.All => ModEntry.T("binder.filter.all"),
            BinderFilter.Common => ModEntry.T("rarity.common"),
            BinderFilter.Rare => ModEntry.T("rarity.rare"),
            BinderFilter.Epic => ModEntry.T("rarity.epic"),
            BinderFilter.Legendary => ModEntry.T("rarity.legendary"),
            BinderFilter.Mythic => ModEntry.T("rarity.mythic"),
            BinderFilter.Favorite => ModEntry.T("binder.favorite"),
            _ => ModEntry.T("binder.filter.all")
        };

    private Color FilterColor(BinderFilter filter)
        => filter switch
        {
            BinderFilter.Common => CardchaUi.RarityColor(CardRarity.Common),
            BinderFilter.Rare => CardchaUi.RarityColor(CardRarity.Rare),
            BinderFilter.Epic => CardchaUi.RarityColor(CardRarity.Epic),
            BinderFilter.Legendary => CardchaUi.RarityColor(CardRarity.Legendary),
            BinderFilter.Mythic => CardchaUi.RarityColor(CardRarity.Mythic),
            BinderFilter.Favorite => CardchaUi.Gold,
            _ => CardchaUi.Leather
        };

    private void DrawBookmark(SpriteBatch b, ClickableComponent button, string text, bool active, Color accent)
    {
        Rectangle r = button.bounds;
        Point mouse = CardchaUi.GetUiMousePoint();
        bool hover = r.Contains(mouse.X, mouse.Y);
        Color fill = active ? CardchaUi.ParchmentLight : hover ? CardchaUi.LeatherLight : CardchaUi.LeatherDark;
        Color ink = active ? CardchaUi.InkBrown : Color.White;
        DrawRoundedRect(b, r, accent, 7);
        DrawRoundedRect(b, Inflate(r, -3), fill, 5);
        CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, text, Inflate(r, -7), ink, maxLines: 2, minScale: 0.70f, centerX: true, maxScale: 1.18f, centerY: true);
    }

    private void DrawResourceSlot(SpriteBatch b, ClickableComponent button, bool shiny)
    {
        Point mouse = CardchaUi.GetUiMousePoint();
        bool highlighted = button.bounds.Contains(mouse.X, mouse.Y)
            || this.currentlySnappedComponent?.myID == button.myID;
        Color edge = highlighted
            ? Color.White
            : shiny ? CardchaUi.PremiumPurple : new Color(154, 91, 43);

        DrawRoundedRect(b, button.bounds, edge, 7);
        DrawRoundedRect(b, Inflate(button.bounds, -3), new Color(77, 47, 35), 5);
        DrawRoundedBorder(b, Inflate(button.bounds, -5), CardchaUi.Gold * 0.72f, 2, 4);

        if (!this.ScrapTextureChecked)
        {
            this.ScrapTextureChecked = true;
            try
            {
                this.ScrapTexture = Game1.content.Load<Texture2D>(ItemAssetService.TextureAsset);
            }
            catch
            {
                this.ScrapTexture = null;
            }
        }

        int insetX = 4;
        int insetTop = 2;
        int reservedCountHeight = 18;
        Rectangle iconArea = new(
            button.bounds.X + insetX,
            button.bounds.Y + insetTop,
            button.bounds.Width - insetX * 2,
            Math.Max(26, button.bounds.Height - reservedCountHeight - insetTop)
        );

        if (this.ScrapTexture is not null)
        {
            Rectangle source = new(shiny ? 16 : 0, 0, 16, 16);
            b.Draw(this.ScrapTexture, iconArea, source, Color.White);
        }
        else
        {
            DrawCircle(b, iconArea, shiny ? new Color(199, 90, 232) : new Color(205, 136, 65));
        }

        int count = this.Resources.Count(shiny ? DropService.ShinyScrapId : DropService.CardboardScrapId);
        Rectangle countArea = new(button.bounds.X + 1, button.bounds.Bottom - 27, button.bounds.Width - 2, 25);
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            $"×{count}",
            countArea,
            Color.White,
            centerX: true,
            centerY: true,
            padding: 1,
            maxScale: 1.40f
        );
    }

    private void DrawResourceTooltipIfNeeded(SpriteBatch b)
    {
        Point mouse = CardchaUi.GetUiMousePoint();
        ClickableComponent? target = null;
        bool shiny = false;

        if (this.NormalScrapButton.bounds.Contains(mouse.X, mouse.Y)
            || this.currentlySnappedComponent?.myID == NormalScrapId)
        {
            target = this.NormalScrapButton;
        }
        else if (this.ShinyScrapButton.bounds.Contains(mouse.X, mouse.Y)
            || this.currentlySnappedComponent?.myID == ShinyScrapId)
        {
            target = this.ShinyScrapButton;
            shiny = true;
        }

        if (target is null)
            return;

        string name = ModEntry.T(shiny ? "item.shiny.name" : "item.cardboard.name");
        string desc = ModEntry.T(shiny ? "item.shiny.desc" : "item.cardboard.desc");
        int count = this.Resources.Count(shiny ? DropService.ShinyScrapId : DropService.CardboardScrapId);
        int maxWidth = Math.Min(360, Math.Max(230, Game1.uiViewport.Width / 3));
        int pad = 12;
        string body = Game1.parseText($"{name}  ×{count}\n{desc}", Game1.smallFont, maxWidth - pad * 2);
        Vector2 measured = Game1.smallFont.MeasureString(body);
        int width = Math.Min(maxWidth, Math.Max(220, (int)Math.Ceiling(measured.X) + pad * 2));
        int height = Math.Max(72, (int)Math.Ceiling(measured.Y) + pad * 2);
        int x = Math.Min(target.bounds.Right + 12, Game1.uiViewport.Width - width - 8);
        int y = Math.Clamp(target.bounds.Y, 8, Game1.uiViewport.Height - height - 8);
        Rectangle panel = new(x, y, width, height);

        DrawRoundedRect(b, panel, new Color(34, 37, 45) * 0.96f, 8);
        DrawRoundedBorder(b, panel, shiny ? CardchaUi.PremiumPurple : CardchaUi.Gold, 2, 8);
        b.DrawString(Game1.smallFont, body, new Vector2(panel.X + pad, panel.Y + pad), Color.White);
    }

    private void DrawPageSeal(SpriteBatch b, ClickableComponent button, bool pointsLeft, bool enabled)
    {
        bool focused = this.currentlySnappedComponent?.myID == button.myID;
        Color edge = focused ? Color.White : enabled ? CardchaUi.Gold : new Color(126, 111, 103);
        DrawCircle(b, button.bounds, edge);
        DrawCircle(b, Inflate(button.bounds, -4), enabled ? CardchaUi.Leather : new Color(145, 130, 120));
        this.DrawPixelChevron(b, button.bounds, pointsLeft, Color.White * (enabled ? 1f : 0.72f));
    }

    private void DrawPixelChevron(SpriteBatch b, Rectangle bounds, bool pointsLeft, Color color)
    {
        // Draw with tiny rectangles instead of a font glyph. Stardew's font maps some
        // punctuation/triangle glyphs to hearts/stars, which caused the old page buttons.
        int step = Math.Max(2, bounds.Height / 8);
        int dot = Math.Max(2, step);
        int arm = Math.Max(3, bounds.Height / (step * 2) - 1);
        int pointX = bounds.Center.X + (pointsLeft ? -step * 2 : step * 2);
        int dir = pointsLeft ? 1 : -1;

        for (int i = 0; i <= arm; i++)
        {
            int x = pointX + dir * i * step;
            int dy = i * step;
            b.Draw(Game1.staminaRect, new Rectangle(x - dot / 2, bounds.Center.Y - dy - dot / 2, dot, dot), color);
            if (i > 0)
                b.Draw(Game1.staminaRect, new Rectangle(x - dot / 2, bounds.Center.Y + dy - dot / 2, dot, dot), color);
        }
    }

    private void DrawSmallButton(SpriteBatch b, ClickableComponent button, string text, Color fill)
    {
        Point mouse = CardchaUi.GetUiMousePoint();
        bool hover = button.bounds.Contains(mouse.X, mouse.Y);
        Color edge = hover || this.currentlySnappedComponent?.myID == button.myID ? Color.White : Color.Black * 0.45f;
        DrawRoundedRect(b, button.bounds, edge, 7);
        DrawRoundedRect(b, Inflate(button.bounds, -3), fill, 5);
        CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, text, Inflate(button.bounds, -6), Color.White, maxLines: 2, minScale: 0.62f, centerX: true, maxScale: 1.08f, centerY: true);
    }

    private static void DrawLockIcon(SpriteBatch b, Rectangle area)
    {
        int bodyW = Math.Clamp(area.Width / 2, 14, 28);
        int bodyH = Math.Clamp(area.Height / 3, 11, 21);
        int shackleH = Math.Clamp(area.Height / 4, 7, 15);
        int line = Math.Clamp(area.Width / 18, 2, 4);
        int bodyX = area.Center.X - bodyW / 2;
        int bodyY = area.Center.Y - bodyH / 4;
        int shackleLeft = bodyX + line + 1;
        int shackleRight = bodyX + bodyW - line * 2 - 1;
        int shackleTop = bodyY - shackleH;

        b.Draw(Game1.staminaRect, new Rectangle(shackleLeft, shackleTop, Math.Max(3, shackleRight - shackleLeft), line), CardchaUi.Gold);
        b.Draw(Game1.staminaRect, new Rectangle(shackleLeft, shackleTop, line, shackleH + line), CardchaUi.Gold);
        b.Draw(Game1.staminaRect, new Rectangle(shackleRight, shackleTop, line, shackleH + line), CardchaUi.Gold);

        Rectangle body = new(bodyX, bodyY, bodyW, bodyH);
        DrawRoundedRect(b, body, CardchaUi.LeatherDark, 3);
        DrawRoundedBorder(b, body, CardchaUi.Gold, Math.Max(1, line - 1), 3);

        int keySize = Math.Clamp(bodyW / 6, 3, 5);
        Rectangle key = new(body.Center.X - keySize / 2, body.Y + Math.Max(3, bodyH / 4), keySize, keySize);
        DrawCircle(b, key, CardchaUi.Gold);
        b.Draw(Game1.staminaRect, new Rectangle(body.Center.X - 1, key.Bottom - 1, 2, Math.Max(2, body.Bottom - key.Bottom - 3)), CardchaUi.Gold);
    }

    private static Rectangle Inflate(Rectangle rect, int amount)
        => new(rect.X - amount, rect.Y - amount, rect.Width + amount * 2, rect.Height + amount * 2);

    private static void DrawRoundedBorder(SpriteBatch b, Rectangle rect, Color color, int thickness, int radius)
    {
        // Keep the already-drawn rounded fill intact; use a thin conventional border on top.
        // The corner silhouette remains rounded because the fill underneath is rounded.
        CardchaUi.DrawBorder(b, rect, color, Math.Max(1, thickness));
    }

    private static void DrawRoundedRect(SpriteBatch b, Rectangle rect, Color color, int radius)
    {
        radius = Math.Clamp(radius, 1, Math.Min(rect.Width, rect.Height) / 2);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X + radius, rect.Y, rect.Width - radius * 2, rect.Height), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y + radius, rect.Width, rect.Height - radius * 2), color);

        DrawQuarterCircle(b, new Point(rect.X + radius, rect.Y + radius), radius, color, 0);
        DrawQuarterCircle(b, new Point(rect.Right - radius - 1, rect.Y + radius), radius, color, 1);
        DrawQuarterCircle(b, new Point(rect.X + radius, rect.Bottom - radius - 1), radius, color, 2);
        DrawQuarterCircle(b, new Point(rect.Right - radius - 1, rect.Bottom - radius - 1), radius, color, 3);
    }

    private static void DrawQuarterCircle(SpriteBatch b, Point center, int radius, Color color, int quadrant)
    {
        for (int y = 0; y < radius; y++)
        {
            int x = (int)Math.Floor(Math.Sqrt(Math.Max(0, radius * radius - y * y)));
            int width = Math.Max(1, x);
            int drawY = quadrant < 2 ? center.Y - y : center.Y + y;
            int drawX = quadrant is 0 or 2 ? center.X - width : center.X;
            b.Draw(Game1.staminaRect, new Rectangle(drawX, drawY, width, 1), color);
        }
    }

    private static void DrawCircle(SpriteBatch b, Rectangle rect, Color color)
    {
        int cx = rect.Center.X;
        int cy = rect.Center.Y;
        int rx = Math.Max(1, rect.Width / 2);
        int ry = Math.Max(1, rect.Height / 2);

        for (int y = -ry; y <= ry; y++)
        {
            double normalized = 1d - (y * y) / (double)(ry * ry);
            int half = (int)Math.Floor(rx * Math.Sqrt(Math.Max(0d, normalized)));
            b.Draw(Game1.staminaRect, new Rectangle(cx - half, cy + y, Math.Max(1, half * 2 + 1), 1), color);
        }
    }
}

using Cardcha.Models;
using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

/// <summary>
/// Cardcha v0.2 visual binder pass.
/// Replaces the alpha.11.45 binder layout while preserving the existing save/loadout/upgrade logic.
/// The physical book uses the approved balanced cover/page shell, while all gameplay text/cards stay dynamic.
/// </summary>
internal sealed class CardchaBinderMenu : IClickableMenu
{
    private const int DesignWidth = 1180;
    private const int DesignHeight = 760;
    private const int VisualActiveSlots = 5;
    private const int CardsPerPage = 10;
    private const int CardColumns = 5;
    private const int BaseCollectionTarget = 80;
    private const int BossUnlockMilestone = 20;

    private const int BackId = 100;
    private const int ActiveBaseId = 200;
    private const int CardBaseId = 300;
    private const int EquipId = 500;
    private const int UnequipId = 501;
    private const int UpgradeId = 502;
    private const int UnlockSlotId = 503;
    private const int NormalScrapId = 504;
    private const int ShinyScrapId = 505;
    private const int DetailScrollId = 506;

    private const int RarityTabBaseId = 600;
    private const int BossSlotId = 610;
    private const int PrevPageId = 611;
    private const int NextPageId = 612;

    private readonly CardRegistry Cards;
    private readonly SaveService Save;
    private readonly LoadoutService Loadout;
    private readonly CardUpgradeService Upgrades;
    private readonly CardRenderer Renderer;
    private readonly Action OnCloseToMachine;
    private readonly Action OnLoadoutChanged;
    private readonly string BackLabel;

    private readonly Texture2D? ScrapIcons;
    private readonly Texture2D? BookFrame;

    private readonly List<(CardDefinition Card, ClickableComponent Button)> CardButtons = new();
    private readonly List<(int Slot, ClickableComponent Body, ClickableComponent Remove)> ActiveSlots = new();
    private readonly List<(CardRarity Rarity, ClickableComponent Button)> RarityTabs = new();

    private readonly ClickableComponent BackButton;
    private readonly ClickableComponent EquipButton;
    private readonly ClickableComponent UnequipButton;
    private readonly ClickableComponent UpgradeButton;
    private readonly ClickableComponent UnlockSlotButton;
    private readonly ClickableComponent NormalScrapButton;
    private readonly ClickableComponent ShinyScrapButton;
    private readonly ClickableComponent DetailScrollButton;
    private readonly ClickableComponent BossSlotButton;
    private readonly ClickableComponent PrevPageButton;
    private readonly ClickableComponent NextPageButton;

    private readonly Rectangle DetailScrollViewport;
    private readonly Rectangle DetailScrollTrack;

    private CardDefinition? Selected;
    private CardRarity? ActiveRarityFilter;
    private int CollectionPage;
    private string Status = ModEntry.T("binder.status.pick");

    private int DetailScrollOffset;
    private int DetailContentHeight = 1;
    private bool DetailScrollDragging;
    private int DetailScrollDragOffset;
    private bool DetailInspectMode;

    private long LastQuickClickAtMs;
    private string LastQuickClickKey = "";
    private const int DoubleClickWindowMs = 360;

    public CardchaBinderMenu(
        CardRegistry cards,
        SaveService save,
        LoadoutService loadout,
        CardUpgradeService upgrades,
        CardRenderer renderer,
        Action onCloseToMachine,
        Action onLoadoutChanged,
        string? backLabel = null
    ) : base(
        Game1.uiViewport.Width / 2 - Math.Min(DesignWidth, Game1.uiViewport.Width - 24) / 2,
        Game1.uiViewport.Height / 2 - Math.Min(DesignHeight, Game1.uiViewport.Height - 24) / 2,
        Math.Min(DesignWidth, Game1.uiViewport.Width - 24),
        Math.Min(DesignHeight, Game1.uiViewport.Height - 24),
        showUpperRightCloseButton: false)
    {
        this.Cards = cards;
        this.Save = save;
        this.Loadout = loadout;
        this.Upgrades = upgrades;
        this.Renderer = renderer;
        this.OnCloseToMachine = onCloseToMachine;
        this.OnLoadoutChanged = onLoadoutChanged;
        this.BackLabel = backLabel ?? ModEntry.T("binder.back");

        try
        {
            this.ScrapIcons = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/items.png");
        }
        catch
        {
            this.ScrapIcons = null;
        }

        try
        {
            this.BookFrame = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/binder_book_frame.png");
        }
        catch (Exception ex)
        {
            this.BookFrame = null;
            ModEntry.LogOnce("binder-book-frame", $"Couldn't load approved Cardcha book frame; using runtime fallback. {ex.Message}");
        }

        this.BackButton = new ClickableComponent(this.R(72, 34, 82, 40), "back") { myID = BackId };

        for (int i = 0; i < VisualActiveSlots; i++)
        {
            Rectangle bodyRect = this.R(112 + i * 69, 218, 62, 88);
            Rectangle removeRect = new(
                bodyRect.Right - Math.Max(16, this.SW(18)),
                bodyRect.Y + Math.Max(2, this.SH(3)),
                Math.Max(15, this.SW(17)),
                Math.Max(15, this.SH(17))
            );
            this.ActiveSlots.Add((
                i,
                new ClickableComponent(bodyRect, $"active-{i}") { myID = ActiveBaseId + i },
                new ClickableComponent(removeRect, $"remove-{i}") { myID = -1 }
            ));
        }

        this.BossSlotButton = new ClickableComponent(this.R(466, 222, 72, 72), "boss-slot") { myID = BossSlotId };
        this.UnlockSlotButton = new ClickableComponent(this.R(420, 178, 126, 30), "unlock-slot") { myID = UnlockSlotId };
        this.NormalScrapButton = new ClickableComponent(this.R(449, 112, 44, 54), "normal-scrap") { myID = NormalScrapId };
        this.ShinyScrapButton = new ClickableComponent(this.R(500, 112, 44, 54), "shiny-scrap") { myID = ShinyScrapId };

        for (int i = 0; i < 5; i++)
        {
            CardRarity rarity = (CardRarity)i;
            this.RarityTabs.Add((
                rarity,
                new ClickableComponent(this.R(-8, 156 + i * 73, 70, 64), $"rarity-{rarity}") { myID = RarityTabBaseId + i }
            ));
        }

        this.PrevPageButton = new ClickableComponent(this.R(245, 625, 44, 36), "prev-page") { myID = PrevPageId };
        this.NextPageButton = new ClickableComponent(this.R(370, 625, 44, 36), "next-page") { myID = NextPageId };

        this.DetailScrollViewport = this.R(664, 328, 382, 174);
        this.DetailScrollTrack = this.R(1052, 328, 12, 174);
        this.DetailScrollButton = new ClickableComponent(
            Rectangle.Union(this.DetailScrollViewport, this.DetailScrollTrack),
            "detail-scroll"
        ) { myID = DetailScrollId };

        this.EquipButton = new ClickableComponent(this.R(688, 590, 355, 45), "equip") { myID = EquipId };
        this.UnequipButton = new ClickableComponent(this.R(688, 646, 355, 45), "unequip") { myID = UnequipId };
        this.UpgradeButton = new ClickableComponent(this.R(688, 702, 355, 42), "upgrade") { myID = UpgradeId };

        this.RebuildCardButtons();
        this.ConfigureNeighbors();
        this.populateClickableComponentList();

        if (Game1.options.SnappyMenus)
            this.snapToDefaultClickableComponent();
    }

    private int UnlockedSlots => this.Upgrades.GetUnlockedSlotCount();
    private bool BossSlotUnlocked => this.Save.Data.OwnedCards.Count >= BossUnlockMilestone;

    private int SX(int designX) => this.xPositionOnScreen + (int)Math.Round(designX * (this.width / (double)DesignWidth));
    private int SY(int designY) => this.yPositionOnScreen + (int)Math.Round(designY * (this.height / (double)DesignHeight));
    private int SW(int designW) => Math.Max(1, (int)Math.Round(designW * (this.width / (double)DesignWidth)));
    private int SH(int designH) => Math.Max(1, (int)Math.Round(designH * (this.height / (double)DesignHeight)));
    private Rectangle R(int x, int y, int w, int h) => new(this.SX(x), this.SY(y), this.SW(w), this.SH(h));

    private List<CardDefinition> GetFilteredCards()
    {
        IEnumerable<CardDefinition> source = this.Cards.All;
        if (this.ActiveRarityFilter.HasValue)
            source = source.Where(p => p.Rarity == this.ActiveRarityFilter.Value);

        return source
            .OrderByDescending(p => this.Save.Data.OwnedCards.Contains(p.Id))
            .ThenBy(p => p.Name, StringComparer.CurrentCultureIgnoreCase)
            .ToList();
    }

    private int GetPageCount()
    {
        int count = this.GetFilteredCards().Count;
        return Math.Max(1, (int)Math.Ceiling(count / (double)CardsPerPage));
    }

    private void RebuildCardButtons()
    {
        this.CardButtons.Clear();

        List<CardDefinition> filtered = this.GetFilteredCards();
        int pageCount = Math.Max(1, (int)Math.Ceiling(filtered.Count / (double)CardsPerPage));
        this.CollectionPage = Math.Clamp(this.CollectionPage, 0, pageCount - 1);

        List<CardDefinition> visible = filtered
            .Skip(this.CollectionPage * CardsPerPage)
            .Take(CardsPerPage)
            .ToList();

        for (int i = 0; i < visible.Count; i++)
        {
            int col = i % CardColumns;
            int row = i / CardColumns;
            Rectangle rect = this.R(108 + col * 89, 374 + row * 118, 80, 108);
            this.CardButtons.Add((
                visible[i],
                new ClickableComponent(rect, visible[i].Id) { myID = CardBaseId + i }
            ));
        }
    }

    private void ConfigureNeighbors()
    {
        int firstTabId = RarityTabBaseId;
        this.BackButton.downNeighborID = ActiveBaseId;
        this.BackButton.leftNeighborID = firstTabId;
        this.BackButton.rightNeighborID = NormalScrapId;

        for (int i = 0; i < this.RarityTabs.Count; i++)
        {
            ClickableComponent tab = this.RarityTabs[i].Button;
            tab.upNeighborID = i > 0 ? RarityTabBaseId + i - 1 : BackId;
            tab.downNeighborID = i < this.RarityTabs.Count - 1 ? RarityTabBaseId + i + 1 : PrevPageId;
            tab.rightNeighborID = i < 2 ? ActiveBaseId : CardBaseId;
            tab.leftNeighborID = -1;
        }

        this.NormalScrapButton.leftNeighborID = BackId;
        this.NormalScrapButton.rightNeighborID = ShinyScrapId;
        this.NormalScrapButton.downNeighborID = ActiveBaseId + 4;

        this.ShinyScrapButton.leftNeighborID = NormalScrapId;
        this.ShinyScrapButton.rightNeighborID = UnlockSlotId;
        this.ShinyScrapButton.downNeighborID = BossSlotId;

        this.UnlockSlotButton.leftNeighborID = ActiveBaseId + 4;
        this.UnlockSlotButton.rightNeighborID = BossSlotId;
        this.UnlockSlotButton.downNeighborID = BossSlotId;

        for (int i = 0; i < this.ActiveSlots.Count; i++)
        {
            ClickableComponent body = this.ActiveSlots[i].Body;
            body.leftNeighborID = i > 0 ? ActiveBaseId + i - 1 : firstTabId;
            body.rightNeighborID = i < VisualActiveSlots - 1 ? ActiveBaseId + i + 1 : BossSlotId;
            body.upNeighborID = BackId;
            body.downNeighborID = this.CardButtons.Count > 0
                ? CardBaseId + Math.Min(i, this.CardButtons.Count - 1)
                : PrevPageId;
        }

        this.BossSlotButton.leftNeighborID = ActiveBaseId + VisualActiveSlots - 1;
        this.BossSlotButton.rightNeighborID = DetailScrollId;
        this.BossSlotButton.upNeighborID = ShinyScrapId;
        this.BossSlotButton.downNeighborID = this.CardButtons.Count > 0
            ? CardBaseId + Math.Min(4, this.CardButtons.Count - 1)
            : NextPageId;

        for (int i = 0; i < this.CardButtons.Count; i++)
        {
            ClickableComponent button = this.CardButtons[i].Button;
            int col = i % CardColumns;
            int row = i / CardColumns;
            button.leftNeighborID = col > 0 ? CardBaseId + i - 1 : RarityTabBaseId + Math.Min(4, row + 2);
            button.rightNeighborID = col < CardColumns - 1 && i + 1 < this.CardButtons.Count
                ? CardBaseId + i + 1
                : DetailScrollId;
            button.upNeighborID = row > 0
                ? CardBaseId + i - CardColumns
                : ActiveBaseId + Math.Min(col, VisualActiveSlots - 1);
            button.downNeighborID = i + CardColumns < this.CardButtons.Count
                ? CardBaseId + i + CardColumns
                : (col <= 2 ? PrevPageId : NextPageId);
        }

        this.PrevPageButton.leftNeighborID = RarityTabBaseId + 4;
        this.PrevPageButton.rightNeighborID = NextPageId;
        this.PrevPageButton.upNeighborID = this.CardButtons.Count > 0
            ? CardBaseId + Math.Max(0, this.CardButtons.Count - Math.Min(CardColumns, this.CardButtons.Count))
            : ActiveBaseId;
        this.NextPageButton.leftNeighborID = PrevPageId;
        this.NextPageButton.rightNeighborID = DetailScrollId;
        this.NextPageButton.upNeighborID = this.CardButtons.Count > 0
            ? CardBaseId + this.CardButtons.Count - 1
            : BossSlotId;

        this.DetailScrollButton.leftNeighborID = this.CardButtons.Count > 0
            ? CardBaseId + Math.Min(4, this.CardButtons.Count - 1)
            : BossSlotId;
        this.DetailScrollButton.rightNeighborID = EquipId;
        this.DetailScrollButton.upNeighborID = DetailScrollId;
        this.DetailScrollButton.downNeighborID = DetailScrollId;

        this.EquipButton.leftNeighborID = DetailScrollId;
        this.EquipButton.upNeighborID = DetailScrollId;
        this.EquipButton.downNeighborID = UnequipId;
        this.UnequipButton.leftNeighborID = DetailScrollId;
        this.UnequipButton.upNeighborID = EquipId;
        this.UnequipButton.downNeighborID = UpgradeId;
        this.UpgradeButton.leftNeighborID = DetailScrollId;
        this.UpgradeButton.upNeighborID = UnequipId;
        this.UpgradeButton.downNeighborID = BackId;
    }

    public override void populateClickableComponentList()
    {
        base.populateClickableComponentList();
        this.allClickableComponents.Clear();

        this.allClickableComponents.Add(this.BackButton);
        this.allClickableComponents.Add(this.NormalScrapButton);
        this.allClickableComponents.Add(this.ShinyScrapButton);
        this.allClickableComponents.Add(this.UnlockSlotButton);
        this.allClickableComponents.Add(this.BossSlotButton);
        this.allClickableComponents.Add(this.PrevPageButton);
        this.allClickableComponents.Add(this.NextPageButton);
        this.allClickableComponents.Add(this.DetailScrollButton);

        foreach ((_, ClickableComponent button) in this.RarityTabs)
            this.allClickableComponents.Add(button);
        foreach ((_, ClickableComponent body, _) in this.ActiveSlots)
            this.allClickableComponents.Add(body);
        foreach ((_, ClickableComponent button) in this.CardButtons)
            this.allClickableComponents.Add(button);

        this.allClickableComponents.Add(this.EquipButton);
        this.allClickableComponents.Add(this.UnequipButton);
        this.allClickableComponents.Add(this.UpgradeButton);
    }

    public override void snapToDefaultClickableComponent()
    {
        this.currentlySnappedComponent = this.ActiveSlots.FirstOrDefault().Body ?? this.BackButton;
        this.snapCursorToCurrentSnappedComponent();
    }

    public override void update(GameTime time)
    {
        base.update(time);
        if (this.currentlySnappedComponent is not null)
            this.SyncSelectionFromControllerFocus();
    }

    public override void applyMovementKey(int direction)
    {
        if (this.currentlySnappedComponent?.myID == DetailScrollId)
        {
            if (this.DetailInspectMode)
            {
                if (direction == 0) { this.ScrollDetailBy(-28); return; }
                if (direction == 2) { this.ScrollDetailBy(28); return; }
                if (direction == 3)
                {
                    this.DetailInspectMode = false;
                    this.FocusCollectionFromDetail();
                    return;
                }
                if (direction == 1)
                {
                    this.DetailInspectMode = false;
                    this.Focus(this.EquipButton);
                    return;
                }
            }
            else
            {
                // Detail is a normal focus stop. A explicitly enters scroll/inspect mode;
                // navigation remains free so the player never has to scroll to the bottom
                // before reaching the action buttons.
                if (direction == 3) { this.FocusCollectionFromDetail(); return; }
                if (direction is 1 or 2) { this.Focus(this.EquipButton); return; }
                if (direction == 0) { this.Focus(this.BossSlotButton); return; }
            }
        }

        base.applyMovementKey(direction);
    }

    public override void receiveGamePadButton(Buttons b)
    {
        if (b == Buttons.B)
        {
            if (this.DetailInspectMode)
            {
                this.DetailInspectMode = false;
                this.Status = ModEntry.T("binder.detail.inspect-exit");
                Game1.playSound("smallSelect");
                return;
            }

            Game1.playSound("bigDeSelect");
            this.OnCloseToMachine();
            return;
        }

        if (this.currentlySnappedComponent?.myID == DetailScrollId)
        {
            if (b == Buttons.A)
            {
                this.DetailInspectMode = !this.DetailInspectMode;
                this.Status = ModEntry.T(this.DetailInspectMode
                    ? "binder.detail.inspect-on"
                    : "binder.detail.inspect-exit");
                Game1.playSound("smallSelect");
                return;
            }

            if (this.DetailInspectMode)
            {
                if (b is Buttons.LeftThumbstickUp or Buttons.DPadUp) { this.ScrollDetailBy(-28); return; }
                if (b is Buttons.LeftThumbstickDown or Buttons.DPadDown) { this.ScrollDetailBy(28); return; }
                if (b is Buttons.LeftThumbstickLeft or Buttons.DPadLeft)
                {
                    this.DetailInspectMode = false;
                    this.FocusCollectionFromDetail();
                    return;
                }
                if (b is Buttons.LeftThumbstickRight or Buttons.DPadRight)
                {
                    this.DetailInspectMode = false;
                    this.Focus(this.EquipButton);
                    return;
                }
            }
            else
            {
                if (b is Buttons.LeftThumbstickLeft or Buttons.DPadLeft) { this.FocusCollectionFromDetail(); return; }
                if (b is Buttons.LeftThumbstickRight or Buttons.DPadRight or Buttons.LeftThumbstickDown or Buttons.DPadDown)
                {
                    this.Focus(this.EquipButton);
                    return;
                }
                if (b is Buttons.LeftThumbstickUp or Buttons.DPadUp) { this.Focus(this.BossSlotButton); return; }
            }
        }

        if (b == Buttons.A && this.currentlySnappedComponent is not null)
        {
            Point center = this.currentlySnappedComponent.bounds.Center;
            this.receiveLeftClick(center.X, center.Y);
            return;
        }

        if ((b == Buttons.X || b == Buttons.Y) && this.currentlySnappedComponent is not null
            && this.currentlySnappedComponent.myID >= ActiveBaseId
            && this.currentlySnappedComponent.myID < ActiveBaseId + VisualActiveSlots)
        {
            int slot = this.currentlySnappedComponent.myID - ActiveBaseId;
            if (slot >= this.UnlockedSlots) return;

            string? id = this.Save.Data.EquippedCards.ElementAtOrDefault(slot);
            CardDefinition? card = id is null ? null : this.Cards.Get(id);
            if (card is not null)
            {
                this.Selected = card;
                this.ResetDetailScroll();
                this.UnequipCard(card, ModEntry.T("binder.status.unequipped-slot", new { name = card.Name, slot = slot + 1 }));
            }
            return;
        }

        if (b == Buttons.Y && this.currentlySnappedComponent is not null
            && this.currentlySnappedComponent.myID >= CardBaseId
            && this.currentlySnappedComponent.myID < CardBaseId + this.CardButtons.Count)
        {
            CardDefinition card = this.CardButtons[this.currentlySnappedComponent.myID - CardBaseId].Card;
            this.Selected = card;
            this.ResetDetailScroll();
            this.QuickEquipCard(card);
            return;
        }

        base.receiveGamePadButton(b);
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        if (this.BackButton.containsPoint(x, y))
        {
            Game1.playSound("smallSelect");
            this.OnCloseToMachine();
            return;
        }

        foreach ((CardRarity rarity, ClickableComponent tab) in this.RarityTabs)
        {
            if (!tab.containsPoint(x, y)) continue;

            this.ActiveRarityFilter = rarity;
            this.CollectionPage = 0;
            this.RebuildAfterCollectionChange();
            this.Status = ModEntry.T(
                "binder.filter.active",
                new { rarity = CardchaUi.RarityText(rarity) }
            );
            Game1.playSound("smallSelect");
            return;
        }

        if (this.PrevPageButton.containsPoint(x, y))
        {
            if (this.CollectionPage > 0)
            {
                this.CollectionPage--;
                this.RebuildAfterCollectionChange();
                Game1.playSound("smallSelect");
            }
            else Game1.playSound("cancel");
            return;
        }

        if (this.NextPageButton.containsPoint(x, y))
        {
            if (this.CollectionPage + 1 < this.GetPageCount())
            {
                this.CollectionPage++;
                this.RebuildAfterCollectionChange();
                Game1.playSound("smallSelect");
            }
            else Game1.playSound("cancel");
            return;
        }

        if (this.BossSlotButton.containsPoint(x, y))
        {
            if (this.BossSlotUnlocked)
            {
                this.Status = ModEntry.T("binder.boss.ready");
                Game1.playSound("smallSelect");
            }
            else
            {
                this.Status = ModEntry.T("binder.boss.locked", new { cards = BossUnlockMilestone });
                Game1.playSound("cancel");
            }
            return;
        }

        if (this.Selected is not null && this.DetailScrollViewport.Contains(x, y))
        {
            this.DetailInspectMode = !this.DetailInspectMode;
            this.Status = ModEntry.T(this.DetailInspectMode
                ? "binder.detail.inspect-on"
                : "binder.detail.inspect-exit");
            Game1.playSound("smallSelect");
            return;
        }

        if (this.Selected is not null && this.DetailInspectMode && this.DetailScrollTrack.Contains(x, y))
        {
            Rectangle thumb = this.GetDetailScrollThumb();
            this.DetailScrollDragging = true;
            if (thumb.Contains(x, y)) this.DetailScrollDragOffset = y - thumb.Y;
            else
            {
                this.DetailScrollDragOffset = thumb.Height / 2;
                this.SetDetailScrollFromThumbY(y - this.DetailScrollDragOffset);
            }
            Game1.playSound("smallSelect");
            return;
        }

        foreach ((int slot, ClickableComponent body, ClickableComponent remove) in this.ActiveSlots)
        {
            bool unlocked = slot < this.UnlockedSlots;
            string? id = this.Save.Data.EquippedCards.ElementAtOrDefault(slot);
            CardDefinition? card = id is null ? null : this.Cards.Get(id);

            if (!unlocked && body.containsPoint(x, y))
            {
                int nextCost = this.Upgrades.GetNextSlotUnlockCost();
                this.Status = nextCost > 0
                    ? ModEntry.T("binder.unlock-slot", new { cost = nextCost })
                    : ModEntry.T("binder.status.slot-locked");
                Game1.playSound("cancel");
                return;
            }

            if (unlocked && remove.containsPoint(x, y) && card is not null)
            {
                this.Selected = card;
                this.ResetDetailScroll();
                this.UnequipCard(card, ModEntry.T("binder.status.unequipped-slot", new { name = card.Name, slot = slot + 1 }));
                return;
            }

            if (!body.containsPoint(x, y)) continue;
            if (card is null)
            {
                this.Status = ModEntry.T("binder.status.slot-empty", new { slot = slot + 1 });
                Game1.playSound("smallSelect");
                return;
            }

            this.Selected = card;
            this.ResetDetailScroll();
            if (this.IsQuickDoubleClick($"active:{slot}"))
            {
                this.UnequipCard(card, ModEntry.T("binder.status.unequipped-slot", new { name = card.Name, slot = slot + 1 }));
                return;
            }

            this.Status = ModEntry.T("binder.status.slot-equipped", new { slot = slot + 1 });
            Game1.playSound("smallSelect");
            return;
        }

        foreach ((CardDefinition card, ClickableComponent button) in this.CardButtons)
        {
            if (!button.containsPoint(x, y)) continue;
            if (!this.Save.Data.OwnedCards.Contains(card.Id))
            {
                this.Status = ModEntry.T("binder.status.not-owned");
                Game1.playSound("cancel");
                return;
            }

            this.Selected = card;
            this.ResetDetailScroll();
            if (this.IsQuickDoubleClick($"card:{card.Id}"))
            {
                this.QuickEquipCard(card);
                return;
            }

            this.Status = ModEntry.T("binder.status.selected", new { name = card.Name });
            Game1.playSound("smallSelect");
            return;
        }

        if (this.UnlockSlotButton.containsPoint(x, y))
        {
            int unlockCost = this.Upgrades.GetNextSlotUnlockCost();
            if (unlockCost <= 0)
            {
                this.Status = ModEntry.T("binder.status.slot-maxed");
                Game1.playSound("smallSelect");
            }
            else if (this.Upgrades.TryUnlockNextSlot(out int newCount, out int cost))
            {
                this.Status = ModEntry.T("binder.status.slot-unlocked", new { slot = newCount, cost });
                Game1.playSound("discoverMineral");
            }
            else
            {
                this.Status = ModEntry.T("binder.status.slot-not-enough-dust", new { cost = unlockCost });
                Game1.playSound("cancel");
            }
            return;
        }

        if (this.Selected is not null && this.EquipButton.containsPoint(x, y))
        {
            if (this.Loadout.IsEquipped(this.Selected.Id))
            {
                this.Status = ModEntry.T("binder.status.already-equipped", new { name = this.Selected.Name });
                Game1.playSound("smallSelect");
            }
            else if (this.Loadout.Equip(this.Selected.Id))
            {
                this.OnLoadoutChanged();
                this.Status = ModEntry.T("binder.status.equipped", new { name = this.Selected.Name });
                Game1.playSound("coin");
            }
            else
            {
                this.Status = ModEntry.T("binder.status.full", new { slots = this.UnlockedSlots });
                Game1.playSound("cancel");
            }
            return;
        }

        if (this.Selected is not null && this.UnequipButton.containsPoint(x, y))
        {
            this.UnequipCard(this.Selected, ModEntry.T("binder.status.unequipped", new { name = this.Selected.Name }));
            return;
        }

        if (this.Selected is not null && this.UpgradeButton.containsPoint(x, y))
        {
            int required = this.Upgrades.GetRequiredCopies(this.Selected);
            int ownedCopies = this.Upgrades.GetCopies(this.Selected);
            if (required <= 0)
            {
                this.Status = ModEntry.T("binder.status.card-maxed", new { name = this.Selected.Name });
                Game1.playSound("smallSelect");
            }
            else if (this.Upgrades.TryUpgrade(this.Selected, out int newLevel, out int spent))
            {
                this.Status = ModEntry.T("binder.status.card-upgraded", new { name = this.Selected.Name, level = newLevel, copies = spent });
                Game1.playSound("reward");
            }
            else
            {
                this.Status = ModEntry.T("binder.status.card-not-enough-copies", new { have = ownedCopies, need = required });
                Game1.playSound("cancel");
            }
        }
    }

    public override void receiveRightClick(int x, int y, bool playSound = true)
    {
        foreach ((int slot, ClickableComponent body, _) in this.ActiveSlots)
        {
            if (slot >= this.UnlockedSlots || !body.containsPoint(x, y)) continue;
            string? id = this.Save.Data.EquippedCards.ElementAtOrDefault(slot);
            CardDefinition? card = id is null ? null : this.Cards.Get(id);
            if (card is null) return;
            this.Selected = card;
            this.ResetDetailScroll();
            this.UnequipCard(card, ModEntry.T("binder.status.unequipped-slot", new { name = card.Name, slot = slot + 1 }));
            return;
        }
        base.receiveRightClick(x, y, playSound);
    }

    public override void receiveScrollWheelAction(int direction)
    {
        if (this.Selected is not null && this.DetailInspectMode)
        {
            Point mouse = new(Game1.getMouseX(ui_scale: true), Game1.getMouseY(ui_scale: true));
            if (this.DetailScrollViewport.Contains(mouse) || this.DetailScrollTrack.Contains(mouse))
            {
                this.ScrollDetailBy(direction > 0 ? -48 : 48);
                return;
            }
        }
        base.receiveScrollWheelAction(direction);
    }

    public override void leftClickHeld(int x, int y)
    {
        if (this.DetailInspectMode && this.DetailScrollDragging)
        {
            this.SetDetailScrollFromThumbY(y - this.DetailScrollDragOffset);
            return;
        }
        base.leftClickHeld(x, y);
    }

    public override void releaseLeftClick(int x, int y)
    {
        this.DetailScrollDragging = false;
        base.releaseLeftClick(x, y);
    }

    private void RebuildAfterCollectionChange()
    {
        this.RebuildCardButtons();
        this.ConfigureNeighbors();
        this.populateClickableComponentList();
        if (Game1.options.SnappyMenus && this.CardButtons.Count > 0)
            this.Focus(this.CardButtons[0].Button);
    }

    private void Focus(ClickableComponent component)
    {
        this.currentlySnappedComponent = component;
        this.snapCursorToCurrentSnappedComponent();
    }

    private void FocusCollectionFromDetail()
    {
        if (this.CardButtons.Count > 0)
            this.Focus(this.CardButtons[Math.Min(4, this.CardButtons.Count - 1)].Button);
        else
            this.Focus(this.BossSlotButton);
    }

    private bool IsQuickDoubleClick(string key)
    {
        long now = Environment.TickCount64;
        bool result = this.LastQuickClickKey.Equals(key, StringComparison.Ordinal)
            && now - this.LastQuickClickAtMs <= DoubleClickWindowMs;
        this.LastQuickClickKey = key;
        this.LastQuickClickAtMs = now;
        if (result)
        {
            this.LastQuickClickKey = "";
            this.LastQuickClickAtMs = 0;
        }
        return result;
    }

    private void QuickEquipCard(CardDefinition card)
    {
        if (!this.Save.Data.OwnedCards.Contains(card.Id))
        {
            this.Status = ModEntry.T("binder.status.not-owned");
            Game1.playSound("cancel");
            return;
        }
        if (this.Loadout.IsEquipped(card.Id))
        {
            this.Status = ModEntry.T("binder.status.already-equipped", new { name = card.Name });
            Game1.playSound("smallSelect");
            return;
        }
        if (this.Loadout.Equip(card.Id))
        {
            this.OnLoadoutChanged();
            this.Status = ModEntry.T("binder.status.equipped", new { name = card.Name });
            Game1.playSound("coin");
        }
        else
        {
            this.Status = ModEntry.T("binder.status.full", new { slots = this.UnlockedSlots });
            Game1.playSound("cancel");
        }
    }

    public override void draw(SpriteBatch b)
    {
        b.Draw(Game1.fadeToBlackRect, Game1.graphics.GraphicsDevice.Viewport.Bounds, Color.Black * 0.76f);
        Rectangle book = new(this.xPositionOnScreen, this.yPositionOnScreen, this.width, this.height);
        if (this.BookFrame is not null) b.Draw(this.BookFrame, book, Color.White);
        else CardchaUi.DrawBookFrame(b, book);

        this.DrawRarityTabs(b);
        this.DrawBackButton(b);
        this.DrawHeader(b);
        this.DrawScrapWallet(b);
        this.DrawLoadout(b);
        this.DrawCollection(b);
        this.DrawDetails(b);
        this.DrawActionButtons(b);

        if (this.currentlySnappedComponent?.myID == DetailScrollId)
        {
            Rectangle focusRect = Rectangle.Union(this.DetailScrollViewport, this.DetailScrollTrack);
            CardchaUi.DrawFocus(b, focusRect);
            if (this.Selected is not null)
            {
                string prompt = ModEntry.T(this.DetailInspectMode
                    ? "binder.detail.inspect-prompt-on"
                    : "binder.detail.inspect-prompt-off");
                Rectangle promptArea = new(
                    this.DetailScrollViewport.X + this.SW(6),
                    this.DetailScrollViewport.Bottom - this.SH(24),
                    this.DetailScrollViewport.Width - this.SW(12),
                    this.SH(20)
                );
                b.Draw(Game1.staminaRect, promptArea, new Color(67, 46, 39) * 0.90f);
                CardchaUi.DrawScaledText(b, Game1.smallFont, prompt, promptArea, Color.White, centerX: true, centerY: true, padding: 3, maxScale: 0.72f);
            }
        }
        drawMouse(b);
    }

    private void DrawBackButton(SpriteBatch b)
    {
        Color fill = this.BackButton.bounds.Contains(CardchaUi.GetUiMousePoint()) ? new Color(115, 72, 48) : new Color(79, 48, 36);
        b.Draw(Game1.staminaRect, this.BackButton.bounds, fill);
        CardchaUi.DrawBorder(b, this.BackButton.bounds, CardchaUi.Gold * 0.9f, 2);
        CardchaUi.DrawScaledText(b, Game1.smallFont, "<", this.BackButton.bounds, Color.White, centerX: true, centerY: true, padding: 5, maxScale: 1.15f);
        if (this.currentlySnappedComponent?.myID == BackId) CardchaUi.DrawFocus(b, this.BackButton.bounds);
    }

    private void DrawHeader(SpriteBatch b)
    {
        this.DrawPlaque(b, this.R(176, 52, 300, 48), ModEntry.T("binder.title"), new Color(38, 45, 61), CardchaUi.Gold);
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("binder.discovered", new { owned = this.Save.Data.OwnedCards.Count, total = BaseCollectionTarget }),
            this.R(126, 112, 310, 38),
            CardchaUi.InkBrown,
            padding: 2,
            maxScale: 1.12f
        );
    }

    private void DrawRarityTabs(SpriteBatch b)
    {
        foreach ((CardRarity rarity, ClickableComponent button) in this.RarityTabs)
        {
            bool active = this.ActiveRarityFilter == rarity;
            bool focused = this.currentlySnappedComponent?.myID == button.myID;
            bool hovered = button.bounds.Contains(CardchaUi.GetUiMousePoint());
            Color baseColor = rarity switch
            {
                CardRarity.Common => new Color(139, 88, 66),
                CardRarity.Rare => new Color(61, 105, 150),
                CardRarity.Epic => new Color(126, 72, 149),
                CardRarity.Legendary => new Color(169, 111, 42),
                CardRarity.Mythic => new Color(55, 136, 119),
                _ => CardchaUi.Leather
            };
            Color fill = active || hovered ? Lighten(baseColor, 0.14f) : baseColor;
            Rectangle r = button.bounds;
            b.Draw(Game1.staminaRect, new Rectangle(r.X + this.SW(3), r.Y + this.SH(4), r.Width, r.Height), new Color(45, 30, 25) * 0.55f);
            b.Draw(Game1.staminaRect, r, fill);
            CardchaUi.DrawBorder(b, r, active ? Color.White : CardchaUi.Gold * 0.9f, active ? 4 : 3);
            CardchaUi.DrawScaledText(b, Game1.smallFont, "*", new Rectangle(r.X + r.Width / 2 - this.SW(13), r.Y + this.SH(7), this.SW(26), this.SH(22)), Color.White, centerX: true, centerY: true, padding: 1, maxScale: 0.9f);
            CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, CardchaUi.RarityText(rarity), new Rectangle(r.X + this.SW(4), r.Y + this.SH(31), r.Width - this.SW(8), r.Height - this.SH(34)), Color.White, maxLines: 2, minScale: 0.45f, centerX: true, maxScale: 0.72f);
            if (focused) CardchaUi.DrawFocus(b, r);
        }
    }

    private void DrawScrapWallet(SpriteBatch b)
    {
        if (!this.Save.Data.BinderUnlocked) return;
        this.DrawScrapSlot(b, this.NormalScrapButton.bounds, 0, this.Save.Data.CardboardScraps);
        this.DrawScrapSlot(b, this.ShinyScrapButton.bounds, 1, this.Save.Data.ShinyScraps);
        if (this.currentlySnappedComponent?.myID == NormalScrapId) CardchaUi.DrawFocus(b, this.NormalScrapButton.bounds);
        if (this.currentlySnappedComponent?.myID == ShinyScrapId) CardchaUi.DrawFocus(b, this.ShinyScrapButton.bounds);
    }

    private void DrawScrapSlot(SpriteBatch b, Rectangle slot, int spriteIndex, int count)
    {
        b.Draw(Game1.staminaRect, slot, new Color(83, 53, 40));
        CardchaUi.DrawBorder(b, slot, CardchaUi.Gold * 0.9f, 2);
        Rectangle icon = new(slot.X + slot.Width / 2 - this.SW(13), slot.Y + this.SH(4), this.SW(26), this.SH(26));
        if (this.ScrapIcons is not null) b.Draw(this.ScrapIcons, icon, new Rectangle(spriteIndex * 16, 0, 16, 16), Color.White);
        CardchaUi.DrawScaledText(b, Game1.smallFont, $"×{Math.Max(0, count)}", new Rectangle(slot.X + this.SW(2), slot.Bottom - this.SH(20), slot.Width - this.SW(4), this.SH(18)), Color.White, centerX: true, centerY: true, padding: 1, maxScale: 0.75f);
    }

    private void DrawLoadout(SpriteBatch b)
    {
        this.DrawRibbon(b, this.R(154, 174, 250, 34), ModEntry.T("binder.active-loadout", new { slots = this.UnlockedSlots }), new Color(127, 52, 37));
        int nextSlotCost = this.Upgrades.GetNextSlotUnlockCost();
        string unlockLabel = nextSlotCost <= 0 ? ModEntry.T("binder.slot.maxed") : ModEntry.T("binder.unlock-slot", new { cost = nextSlotCost });
        bool canUnlock = nextSlotCost > 0 && this.Save.Data.SuspiciousDust >= nextSlotCost;
        CardchaUi.DrawButton(b, this.UnlockSlotButton, unlockLabel, new Color(103, 74, 113), canUnlock);
        if (this.currentlySnappedComponent?.myID == UnlockSlotId) CardchaUi.DrawFocus(b, this.UnlockSlotButton.bounds);

        foreach ((int slot, ClickableComponent body, ClickableComponent remove) in this.ActiveSlots)
        {
            bool unlocked = slot < this.UnlockedSlots;
            string? id = this.Save.Data.EquippedCards.ElementAtOrDefault(slot);
            CardDefinition? card = id is null ? null : this.Cards.Get(id);
            bool focused = this.currentlySnappedComponent?.myID == body.myID;
            bool selected = card is not null && this.Selected?.Id.Equals(card.Id, StringComparison.OrdinalIgnoreCase) == true;
            if (!unlocked) this.DrawLockedNormalSlot(b, body.bounds, slot + 1, focused || selected);
            else this.Renderer.DrawActiveSlot(b, body.bounds, remove.bounds, card, slot + 1, focused || selected, unlocked: true);
            if (focused) CardchaUi.DrawFocus(b, body.bounds);
        }

        this.DrawBossSlot(b);
        CardchaUi.DrawScaledText(b, Game1.smallFont, ModEntry.T("binder.hint"), this.R(118, 309, 420, 24), new Color(105, 78, 61), centerX: true, centerY: true, padding: 2, maxScale: 0.84f);
    }

    private void DrawLockedNormalSlot(SpriteBatch b, Rectangle r, int slotNumber, bool selected)
    {
        b.Draw(Game1.staminaRect, r, new Color(205, 181, 147));
        CardchaUi.DrawBorder(b, r, selected ? Color.White : new Color(135, 108, 82), selected ? 4 : 3);
        Utility.drawTextWithShadow(b, slotNumber.ToString(), Game1.tinyFont, new Vector2(r.X + this.SW(5), r.Y + this.SH(3)), new Color(87, 68, 55));
        int badgeW = Math.Min(this.SW(34), Math.Max(this.SW(24), r.Width - this.SW(20)));
        int badgeH = Math.Min(this.SH(42), Math.Max(this.SH(30), r.Height - this.SH(42)));
        this.DrawKeyholeBadge(b, new Rectangle(r.Center.X - badgeW / 2, r.Center.Y - badgeH / 2 - this.SH(4), badgeW, badgeH));
        CardchaUi.DrawScaledText(b, Game1.smallFont, ModEntry.T("binder.slot.locked"), new Rectangle(r.X + this.SW(4), r.Bottom - this.SH(23), r.Width - this.SW(8), this.SH(20)), new Color(87, 68, 55), centerX: true, centerY: true, padding: 1, maxScale: 0.64f);
    }

    private void DrawBossSlot(SpriteBatch b)
    {
        Rectangle r = this.BossSlotButton.bounds;
        bool focused = this.currentlySnappedComponent?.myID == BossSlotId;
        bool hovered = r.Contains(CardchaUi.GetUiMousePoint());
        Color outer = this.BossSlotUnlocked ? new Color(54, 87, 119) : new Color(102, 92, 84);
        Color border = this.BossSlotUnlocked ? CardchaUi.Gold : new Color(122, 108, 94);
        this.DrawPixelCircle(b, r.Center, Math.Min(r.Width, r.Height) / 2, border);
        this.DrawPixelCircle(b, r.Center, Math.Max(4, Math.Min(r.Width, r.Height) / 2 - this.SW(4)), outer);
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            this.BossSlotUnlocked ? "BOSS" : ModEntry.T("binder.boss.short", new { cards = BossUnlockMilestone }),
            new Rectangle(r.X, r.Bottom - this.SH(19), r.Width, this.SH(18)),
            Color.White,
            centerX: true,
            centerY: true,
            padding: 1,
            maxScale: 0.62f
        );
        if (!this.BossSlotUnlocked)
            this.DrawKeyholeBadge(b, new Rectangle(r.Center.X - this.SW(14), r.Center.Y - this.SH(20), this.SW(28), this.SH(31)));
        else
            CardchaUi.DrawScaledText(b, Game1.smallFont, "*", new Rectangle(r.Center.X - this.SW(13), r.Center.Y - this.SH(19), this.SW(26), this.SH(26)), CardchaUi.Gold, centerX: true, centerY: true, padding: 1, maxScale: 0.95f);
        if (focused || hovered) CardchaUi.DrawFocus(b, r);
    }

    private void DrawCollection(SpriteBatch b)
    {
        string filter = this.ActiveRarityFilter.HasValue ? $" — {CardchaUi.RarityText(this.ActiveRarityFilter.Value)}" : "";
        this.DrawRibbon(b, this.R(155, 338, 280, 32), $"{ModEntry.T("binder.collection")}{filter}", new Color(39, 72, 103));

        foreach ((CardDefinition card, ClickableComponent button) in this.CardButtons)
        {
            bool owned = this.Save.Data.OwnedCards.Contains(card.Id);
            bool equipped = this.Loadout.IsEquipped(card.Id);
            bool focused = this.currentlySnappedComponent?.myID == button.myID;
            this.Renderer.DrawCollectionCard(b, button.bounds, card, owned, equipped, this.Selected?.Id == card.Id || focused);
            if (owned)
            {
                Rectangle badge = new(button.bounds.X + this.SW(3), button.bounds.Y + this.SH(3), this.SW(34), this.SH(19));
                b.Draw(Game1.staminaRect, badge, new Color(45, 38, 38) * 0.90f);
                CardchaUi.DrawBorder(b, badge, CardchaUi.Gold * 0.65f, 1);
                CardchaUi.DrawScaledText(b, Game1.smallFont, $"Lv{this.Upgrades.GetLevel(card)}", badge, Color.White, centerX: true, centerY: true, padding: 1, maxScale: 0.66f);
            }
            if (focused) CardchaUi.DrawFocus(b, button.bounds);
        }

        int pageCount = this.GetPageCount();
        this.DrawPageArrow(b, this.PrevPageButton, "<", this.CollectionPage > 0);
        this.DrawPageArrow(b, this.NextPageButton, ">", this.CollectionPage + 1 < pageCount);
        CardchaUi.DrawScaledText(b, Game1.smallFont, $"{this.CollectionPage + 1} / {pageCount}", this.R(293, 625, 72, 36), CardchaUi.InkBrown, centerX: true, centerY: true, padding: 2, maxScale: 0.92f);
    }

    private void DrawDetails(SpriteBatch b)
    {
        CardchaUi.DrawScaledText(b, Game1.dialogueFont, ModEntry.T("binder.details"), this.R(716, 58, 300, 42), CardchaUi.InkBrown, centerX: true, centerY: true, padding: 2, maxScale: 0.92f);

        if (this.Selected is null)
        {
            this.DrawPlaque(b, this.R(724, 113, 286, 46), "—", new Color(43, 44, 52), CardchaUi.Gold);
            CardchaUi.DrawWrappedText(b, Game1.smallFont, ModEntry.T("binder.inspect-help"), this.R(698, 190, 342, 116), CardchaUi.InkBrown, maxLines: 5);
        }
        else
        {
            this.DrawPlaque(b, this.R(714, 112, 306, 48), this.Selected.Name, new Color(43, 44, 52), CardchaUi.RarityColor(this.Selected.Rarity));
            Rectangle iconFrame = this.R(684, 184, 78, 78);
            b.Draw(Game1.staminaRect, iconFrame, new Color(232, 205, 158));
            CardchaUi.DrawBorder(b, iconFrame, CardchaUi.RarityColor(this.Selected.Rarity), 3);
            this.Renderer.DrawIcon(b, new Rectangle(iconFrame.X + this.SW(9), iconFrame.Y + this.SH(9), iconFrame.Width - this.SW(18), iconFrame.Height - this.SH(18)), this.Selected);
            int level = this.Upgrades.GetLevel(this.Selected);
            int maxLevel = this.Upgrades.GetMaxLevel(this.Selected);
            CardchaUi.DrawScaledText(b, Game1.smallFont, CardchaUi.RarityText(this.Selected.Rarity), this.R(778, 184, 250, 24), CardchaUi.RarityColor(this.Selected.Rarity), padding: 1, maxScale: 0.95f);
            CardchaUi.DrawScaledText(b, Game1.smallFont, ModEntry.T("binder.level", new { level, max = maxLevel }), this.R(778, 210, 250, 22), CardchaUi.InkBrown, padding: 1, maxScale: 0.88f);
            CardchaUi.DrawStars(b, this.R(778, 236, 250, 22), level, maxLevel, CardchaUi.Gold);
            CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, this.Upgrades.GetLevelEffectText(this.Selected, level), this.R(684, 269, 356, 48), new Color(91, 63, 48), maxLines: 2, minScale: 0.62f, maxScale: 0.88f);

            // Give the star-requirement area its own paper surface. This prevents the
            // underlying book art from visually bleeding through on small UI scales.
            b.Draw(Game1.staminaRect, this.DetailScrollViewport, new Color(239, 217, 178) * 0.96f);
            CardchaUi.DrawBorder(b, this.DetailScrollViewport, new Color(151, 112, 75), 2);
            this.DrawScrollableDetailContent(b);
        }

        Rectangle noteBox = this.R(678, 516, 375, 62);
        b.Draw(Game1.staminaRect, noteBox, new Color(239, 217, 178) * 0.94f);
        CardchaUi.DrawBorder(b, noteBox, new Color(151, 112, 75), 2);
        CardchaUi.DrawScaledText(b, Game1.smallFont, "GHI CHÚ", this.R(690, 520, 160, 22), CardchaUi.InkBrown, padding: 1, maxScale: 0.78f);
        CardchaUi.DrawAutoFitWrappedText(b, Game1.smallFont, this.Status, this.R(690, 543, 350, 31), new Color(103, 79, 63), maxLines: 2, minScale: 0.56f, maxScale: 0.78f);
    }

    private void DrawActionButtons(SpriteBatch b)
    {
        bool canEquip = this.Selected is not null && !this.Loadout.IsEquipped(this.Selected.Id);
        bool canUnequip = this.Selected is not null && this.Loadout.IsEquipped(this.Selected.Id);
        bool canUpgrade = this.Selected is not null
            && this.Upgrades.GetRequiredCopies(this.Selected) > 0
            && this.Upgrades.GetCopies(this.Selected) >= this.Upgrades.GetRequiredCopies(this.Selected)
            && this.Save.Data.OwnedCards.Contains(this.Selected.Id);
        CardchaUi.DrawButton(b, this.EquipButton, ModEntry.T("binder.equip"), new Color(43, 83, 128), canEquip);
        CardchaUi.DrawButton(b, this.UnequipButton, ModEntry.T("binder.unequip"), new Color(104, 76, 51), canUnequip);
        string upgradeLabel = this.Selected is null || this.Upgrades.GetRequiredCopies(this.Selected) <= 0
            ? ModEntry.T("binder.upgrade.max")
            : ModEntry.T("binder.upgrade", new { have = this.Upgrades.GetCopies(this.Selected), need = this.Upgrades.GetRequiredCopies(this.Selected) });
        CardchaUi.DrawButton(b, this.UpgradeButton, upgradeLabel, new Color(81, 77, 75), canUpgrade);
        if (this.currentlySnappedComponent?.myID == EquipId) CardchaUi.DrawFocus(b, this.EquipButton.bounds);
        if (this.currentlySnappedComponent?.myID == UnequipId) CardchaUi.DrawFocus(b, this.UnequipButton.bounds);
        if (this.currentlySnappedComponent?.myID == UpgradeId) CardchaUi.DrawFocus(b, this.UpgradeButton.bounds);
    }

    private void DrawRibbon(SpriteBatch b, Rectangle r, string text, Color fill)
    {
        b.Draw(Game1.staminaRect, new Rectangle(r.X + this.SW(3), r.Y + this.SH(4), r.Width, r.Height), new Color(76, 42, 29) * 0.35f);
        b.Draw(Game1.staminaRect, r, fill);
        CardchaUi.DrawBorder(b, r, CardchaUi.Gold * 0.92f, 2);
        CardchaUi.DrawScaledText(b, Game1.smallFont, text, r, new Color(255, 223, 154), centerX: true, centerY: true, padding: 6, maxScale: 0.92f);
    }

    private void DrawPlaque(SpriteBatch b, Rectangle r, string text, Color fill, Color accent)
    {
        b.Draw(Game1.staminaRect, r, fill);
        CardchaUi.DrawBorder(b, r, accent, 3);
        Rectangle inner = new(r.X + this.SW(4), r.Y + this.SH(4), r.Width - this.SW(8), r.Height - this.SH(8));
        CardchaUi.DrawBorder(b, inner, CardchaUi.Gold * 0.38f, 1);
        CardchaUi.DrawAutoFitWrappedText(b, Game1.dialogueFont, text, inner, new Color(244, 203, 117), maxLines: 1, minScale: 0.48f, centerX: true, maxScale: 0.78f);
    }

    private void DrawPageArrow(SpriteBatch b, ClickableComponent button, string glyph, bool enabled)
    {
        b.Draw(Game1.staminaRect, button.bounds, enabled ? new Color(99, 64, 42) : new Color(138, 126, 112));
        CardchaUi.DrawBorder(b, button.bounds, enabled ? CardchaUi.Gold : new Color(104, 97, 91), 2);
        CardchaUi.DrawScaledText(b, Game1.smallFont, glyph, button.bounds, enabled ? Color.White : new Color(220, 214, 203), centerX: true, centerY: true, padding: 5, maxScale: 0.80f);
        if (this.currentlySnappedComponent?.myID == button.myID) CardchaUi.DrawFocus(b, button.bounds);
    }

    private void DrawKeyholeBadge(SpriteBatch b, Rectangle r)
    {
        b.Draw(Game1.staminaRect, r, new Color(91, 71, 59));
        CardchaUi.DrawBorder(b, r, new Color(184, 142, 78), 2);
        int shackleW = Math.Max(6, r.Width / 2);
        int shackleH = Math.Max(5, r.Height / 3);
        int shackleX = r.Center.X - shackleW / 2;
        int shackleY = r.Y + Math.Max(2, r.Height / 10);
        int stroke = Math.Max(2, r.Width / 9);
        b.Draw(Game1.staminaRect, new Rectangle(shackleX, shackleY, stroke, shackleH), new Color(209, 163, 87));
        b.Draw(Game1.staminaRect, new Rectangle(shackleX + shackleW - stroke, shackleY, stroke, shackleH), new Color(209, 163, 87));
        b.Draw(Game1.staminaRect, new Rectangle(shackleX, shackleY, shackleW, Math.Max(2, r.Height / 12)), new Color(209, 163, 87));
        Rectangle body = new(r.X + r.Width / 5, r.Y + r.Height / 3, r.Width * 3 / 5, r.Height / 2);
        b.Draw(Game1.staminaRect, body, new Color(190, 141, 70));
        CardchaUi.DrawBorder(b, body, new Color(92, 65, 43), 1);
        int keySize = Math.Max(3, Math.Min(r.Width, r.Height) / 7);
        b.Draw(Game1.staminaRect, new Rectangle(r.Center.X - keySize / 2, body.Y + body.Height / 4, keySize, keySize), new Color(79, 55, 43));
        b.Draw(Game1.staminaRect, new Rectangle(r.Center.X - Math.Max(1, keySize / 4), body.Y + body.Height / 4 + keySize, Math.Max(2, keySize / 2), Math.Max(4, body.Height / 3)), new Color(79, 55, 43));
    }

    private void DrawPixelCircle(SpriteBatch b, Point center, int radius, Color color)
    {
        if (radius <= 0) return;
        for (int dy = -radius; dy <= radius; dy++)
        {
            int span = (int)Math.Floor(Math.Sqrt(Math.Max(0, radius * radius - dy * dy)));
            b.Draw(Game1.staminaRect, new Rectangle(center.X - span, center.Y + dy, span * 2 + 1, 1), color);
        }
    }

    private static Color Lighten(Color color, float amount)
    {
        amount = Math.Clamp(amount, 0f, 1f);
        return new Color(
            (byte)Math.Clamp(color.R + (255 - color.R) * amount, 0, 255),
            (byte)Math.Clamp(color.G + (255 - color.G) * amount, 0, 255),
            (byte)Math.Clamp(color.B + (255 - color.B) * amount, 0, 255),
            color.A
        );
    }

    private void SyncSelectionFromControllerFocus()
    {
        int id = this.currentlySnappedComponent?.myID ?? -1;
        CardDefinition? next = null;
        if (id >= CardBaseId && id < CardBaseId + this.CardButtons.Count)
            next = this.CardButtons[id - CardBaseId].Card;
        else if (id >= ActiveBaseId && id < ActiveBaseId + this.ActiveSlots.Count)
        {
            int slot = id - ActiveBaseId;
            string? cardId = this.Save.Data.EquippedCards.ElementAtOrDefault(slot);
            if (!string.IsNullOrWhiteSpace(cardId)) next = this.Cards.Get(cardId);
        }
        if (next is null || string.Equals(this.Selected?.Id, next.Id, StringComparison.OrdinalIgnoreCase)) return;
        this.Selected = next;
        this.ResetDetailScroll();
    }

    private void ResetDetailScroll()
    {
        this.DetailScrollOffset = 0;
        this.DetailScrollDragging = false;
        this.DetailInspectMode = false;
    }

    private void ScrollDetailBy(int delta)
    {
        int max = this.GetDetailMaxScroll();
        if (max <= 0) { this.DetailScrollOffset = 0; return; }
        int before = this.DetailScrollOffset;
        this.DetailScrollOffset = Math.Clamp(this.DetailScrollOffset + delta, 0, max);
        if (this.DetailScrollOffset != before) Game1.playSound("smallSelect");
    }

    private int GetDetailMaxScroll() => Math.Max(0, this.DetailContentHeight - this.DetailScrollViewport.Height);

    private Rectangle GetDetailScrollThumb()
    {
        int maxScroll = this.GetDetailMaxScroll();
        if (maxScroll <= 0) return this.DetailScrollTrack;
        int thumbHeight = Math.Max(this.SH(26), (int)Math.Round(this.DetailScrollTrack.Height * (this.DetailScrollViewport.Height / (double)Math.Max(this.DetailContentHeight, 1))));
        thumbHeight = Math.Min(this.DetailScrollTrack.Height, thumbHeight);
        int travel = Math.Max(1, this.DetailScrollTrack.Height - thumbHeight);
        int y = this.DetailScrollTrack.Y + (int)Math.Round(travel * (this.DetailScrollOffset / (double)maxScroll));
        return new Rectangle(this.DetailScrollTrack.X, y, this.DetailScrollTrack.Width, thumbHeight);
    }

    private void SetDetailScrollFromThumbY(int thumbY)
    {
        int maxScroll = this.GetDetailMaxScroll();
        if (maxScroll <= 0) { this.DetailScrollOffset = 0; return; }
        Rectangle thumb = this.GetDetailScrollThumb();
        int travel = Math.Max(1, this.DetailScrollTrack.Height - thumb.Height);
        int local = Math.Clamp(thumbY - this.DetailScrollTrack.Y, 0, travel);
        this.DetailScrollOffset = (int)Math.Round(maxScroll * (local / (double)travel));
    }

    private void DrawScrollableDetailContent(SpriteBatch b)
    {
        if (this.Selected is null) return;
        CardDefinition card = this.Selected;
        int currentLevel = this.Upgrades.GetLevel(card);
        int maxLevel = this.Upgrades.GetMaxLevel(card);
        int copies = this.Upgrades.GetCopies(card);
        int needed = this.Upgrades.GetRequiredCopies(card);
        int virtualY = 0;
        this.DrawDetailBlock(b, ref virtualY, ModEntry.T("binder.current-effect"), this.Upgrades.GetLevelEffectText(card, currentLevel), current: true);
        string copyText = needed <= 0 ? ModEntry.T("binder.copies.max", new { have = copies }) : ModEntry.T("binder.copies", new { have = copies, need = needed });
        this.DrawDetailBlock(b, ref virtualY, ModEntry.T("binder.upgrade-material"), copyText, current: false);
        this.DrawDetailHeader(b, ref virtualY, ModEntry.T("binder.all-levels"));
        for (int level = 1; level <= maxLevel; level++)
            this.DrawDetailBlock(b, ref virtualY, ModEntry.T("binder.level-row", new { level, max = maxLevel }), this.Upgrades.GetLevelEffectText(card, level), level == currentLevel);
        this.DetailContentHeight = Math.Max(this.DetailScrollViewport.Height, virtualY + this.SH(6));
        this.DetailScrollOffset = Math.Clamp(this.DetailScrollOffset, 0, this.GetDetailMaxScroll());
        CardchaUi.DrawScrollbar(b, this.DetailScrollTrack, this.GetDetailScrollThumb(), this.DetailScrollDragging);
    }

    private void DrawDetailHeader(SpriteBatch b, ref int virtualY, string text)
    {
        int height = Game1.smallFont.LineSpacing + this.SH(8);
        Rectangle vr = new(this.DetailScrollViewport.X, this.DetailScrollViewport.Y + virtualY - this.DetailScrollOffset, this.DetailScrollViewport.Width, height);
        if (vr.Top >= this.DetailScrollViewport.Top && vr.Bottom <= this.DetailScrollViewport.Bottom)
            Utility.drawTextWithShadow(b, text, Game1.smallFont, new Vector2(vr.X + this.SW(2), vr.Y + this.SH(2)), CardchaUi.InkBrown);
        virtualY += height + this.SH(2);
    }

    private void DrawDetailBlock(SpriteBatch b, ref int virtualY, string title, string body, bool current)
    {
        int pad = this.SW(8);
        int titleHeight = Game1.smallFont.LineSpacing + this.SH(6);
        int bodyWidth = this.DetailScrollViewport.Width - pad * 2;
        int bodyHeight = CardchaUi.MeasureWrappedTextHeight(Game1.smallFont, body, bodyWidth, minimumLines: 1, maximumLines: 5);
        int height = titleHeight + bodyHeight + this.SH(10);
        Rectangle vr = new(this.DetailScrollViewport.X, this.DetailScrollViewport.Y + virtualY - this.DetailScrollOffset, this.DetailScrollViewport.Width, height);
        if (vr.Bottom >= this.DetailScrollViewport.Top && vr.Top <= this.DetailScrollViewport.Bottom)
        {
            Rectangle visible = Rectangle.Intersect(vr, this.DetailScrollViewport);
            b.Draw(Game1.staminaRect, visible, current ? new Color(250, 226, 172) * 0.82f : new Color(237, 216, 181) * 0.62f);
            if (visible.Height >= this.SH(14)) CardchaUi.DrawBorder(b, visible, current ? CardchaUi.Gold * 0.72f : CardchaUi.PaperShadow * 0.58f, 2);
            Rectangle titleArea = new(vr.X + pad, vr.Y + this.SH(4), bodyWidth, titleHeight);
            if (titleArea.Top >= this.DetailScrollViewport.Top && titleArea.Bottom <= this.DetailScrollViewport.Bottom)
                Utility.drawTextWithShadow(b, title, Game1.smallFont, new Vector2(titleArea.X, titleArea.Y), current ? new Color(126, 78, 39) : CardchaUi.InkBrown);
            Rectangle bodyArea = new(vr.X + pad, vr.Y + titleHeight, bodyWidth, bodyHeight);
            CardchaUi.DrawWrappedTextFixedClipped(b, Game1.smallFont, body, bodyArea, this.DetailScrollViewport, Color.Black, maximumLines: 5);
        }
        virtualY += height + this.SH(4);
    }

    private void UnequipCard(CardDefinition card, string successMessage)
    {
        if (this.Loadout.Unequip(card.Id))
        {
            this.OnLoadoutChanged();
            this.Status = successMessage;
            Game1.playSound("smallSelect");
        }
        else
        {
            this.Status = ModEntry.T("binder.status.not-equipped");
            Game1.playSound("cancel");
        }
    }
}

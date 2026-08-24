
using Cardcha.Models;
using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

internal sealed class CardchaBinderMenu : IClickableMenu
{
    private const int VisualActiveSlots = 5;

    private const int BackId = 100;
    private const int ActiveBaseId = 200;
    private const int CardBaseId = 300;
    private const int EquipId = 500;
    private const int UnequipId = 501;
    private const int UpgradeId = 502;
    private const int UnlockSlotId = 503;

    private readonly CardRegistry Cards;
    private readonly SaveService Save;
    private readonly LoadoutService Loadout;
    private readonly CardUpgradeService Upgrades;
    private readonly CardRenderer Renderer;
    private readonly Action OnCloseToMachine;
    private readonly Action OnLoadoutChanged;
    private readonly string BackLabel;
    private readonly Texture2D? ScrapIcons;
    private readonly List<(CardDefinition Card, ClickableComponent Button)> CardButtons = new();
    private readonly List<(int Slot, ClickableComponent Body, ClickableComponent Remove)> ActiveSlots = new();
    private readonly ClickableComponent EquipButton;
    private readonly ClickableComponent UnequipButton;
    private readonly ClickableComponent UpgradeButton;
    private readonly ClickableComponent UnlockSlotButton;
    private readonly ClickableComponent BackButton;

    private CardDefinition? Selected;
    private string Status = ModEntry.T("binder.status.pick");
    private long LastQuickClickAtMs;
    private string LastQuickClickKey = "";
    private const int DoubleClickWindowMs = 360;

    private readonly Rectangle DetailScrollViewport;
    private readonly Rectangle DetailScrollTrack;
    private int DetailScrollOffset;
    private int DetailContentHeight = 1;
    private bool DetailScrollDragging;
    private int DetailScrollDragOffset;

    // v0.1.16 Upgrade Experience.
    private int UpgradeCelebrationMs;
    private const int UpgradeCelebrationDurationMs = 2100;
    private CardDefinition? UpgradeCelebrationCard;
    private int UpgradeCelebrationFromLevel;
    private int UpgradeCelebrationToLevel;
    private int UpgradeCelebrationCopiesSpent;
    private string UpgradeCelebrationBefore = "";
    private string UpgradeCelebrationAfter = "";

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
        Game1.uiViewport.Width / 2 - Math.Min(1180, Game1.uiViewport.Width - 24) / 2,
        Game1.uiViewport.Height / 2 - Math.Min(760, Game1.uiViewport.Height - 24) / 2,
        Math.Min(1180, Game1.uiViewport.Width - 24),
        Math.Min(760, Game1.uiViewport.Height - 24),
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
        this.ScrapIcons = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/items.png");

        int activeX = this.xPositionOnScreen + 52;
        int activeY = this.yPositionOnScreen + 166;
        int activeW = 98;
        int activeH = 102;
        int activeGap = 10;

        for (int i = 0; i < VisualActiveSlots; i++)
        {
            Rectangle bodyRect = new(activeX + i * (activeW + activeGap), activeY, activeW, activeH);
            Rectangle removeRect = new(bodyRect.Right - 26, bodyRect.Y + 4, 22, 22);

            ClickableComponent body = new(bodyRect, $"active-{i}") { myID = ActiveBaseId + i };
            ClickableComponent remove = new(removeRect, $"remove-{i}") { myID = -1 };

            this.ActiveSlots.Add((i, body, remove));
        }

        int gridX = this.xPositionOnScreen + 52;
        int gridY = this.yPositionOnScreen + 322;
        int gap = 12;
        int cardW = 112;
        int cardH = 128;

        List<CardDefinition> ordered = this.Cards.All
            .OrderByDescending(p => this.Save.Data.OwnedCards.Contains(p.Id))
            .ThenBy(p => (int)p.Rarity)
            .ThenBy(p => p.Name, StringComparer.CurrentCultureIgnoreCase)
            .ToList();

        for (int i = 0; i < ordered.Count; i++)
        {
            int col = i % 5;
            int row = i / 5;
            Rectangle r = new(gridX + col * (cardW + gap), gridY + row * (cardH + gap), cardW, cardH);
            this.CardButtons.Add((
                ordered[i],
                new ClickableComponent(r, ordered[i].Id) { myID = CardBaseId + i }
            ));
        }

        int sideX = this.xPositionOnScreen + this.width - 325;

        this.DetailScrollViewport = new Rectangle(
            sideX + 16,
            this.yPositionOnScreen + 326,
            220,
            164
        );
        this.DetailScrollTrack = new Rectangle(
            sideX + 242,
            this.yPositionOnScreen + 326,
            14,
            164
        );

        this.EquipButton = new ClickableComponent(
            new Rectangle(sideX, this.yPositionOnScreen + this.height - 202, 260, 52),
            "equip"
        ) { myID = EquipId };

        this.UnequipButton = new ClickableComponent(
            new Rectangle(sideX, this.yPositionOnScreen + this.height - 142, 260, 52),
            "unequip"
        ) { myID = UnequipId };

        this.UpgradeButton = new ClickableComponent(
            new Rectangle(sideX, this.yPositionOnScreen + this.height - 82, 260, 52),
            "upgrade"
        ) { myID = UpgradeId };

        this.UnlockSlotButton = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + 624, this.yPositionOnScreen + 188, 176, 40),
            "unlock-slot"
        ) { myID = UnlockSlotId };

        this.BackButton = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + 42, this.yPositionOnScreen + 34, 160, 50),
            "back"
        ) { myID = BackId };

        this.ConfigureNeighbors();
        this.populateClickableComponentList();

        if (Game1.options.SnappyMenus)
            this.snapToDefaultClickableComponent();
    }

    private int UnlockedSlots => this.Upgrades.GetUnlockedSlotCount();

    private void ConfigureNeighbors()
    {
        this.BackButton.downNeighborID = ActiveBaseId;
        this.BackButton.rightNeighborID = ActiveBaseId;

        for (int i = 0; i < this.ActiveSlots.Count; i++)
        {
            ClickableComponent body = this.ActiveSlots[i].Body;
            body.leftNeighborID = i > 0 ? ActiveBaseId + i - 1 : BackId;
            body.rightNeighborID = i < this.ActiveSlots.Count - 1 ? ActiveBaseId + i + 1 : UnlockSlotId;
            body.upNeighborID = BackId;
            body.downNeighborID = CardBaseId + Math.Min(i, Math.Max(0, this.CardButtons.Count - 1));
        }

        this.UnlockSlotButton.leftNeighborID = ActiveBaseId + (VisualActiveSlots - 1);
        this.UnlockSlotButton.rightNeighborID = EquipId;
        this.UnlockSlotButton.upNeighborID = BackId;
        this.UnlockSlotButton.downNeighborID = EquipId;

        for (int i = 0; i < this.CardButtons.Count; i++)
        {
            ClickableComponent button = this.CardButtons[i].Button;
            int col = i % 5;
            int row = i / 5;

            button.leftNeighborID = col > 0 ? CardBaseId + i - 1 : -1;
            button.rightNeighborID = col < 4 && i + 1 < this.CardButtons.Count ? CardBaseId + i + 1 : EquipId;
            button.upNeighborID = row > 0 ? CardBaseId + i - 5 : ActiveBaseId + Math.Min(col, VisualActiveSlots - 1);
            button.downNeighborID = i + 5 < this.CardButtons.Count ? CardBaseId + i + 5 : EquipId;
        }

        this.EquipButton.leftNeighborID = this.CardButtons.Count > 0 ? CardBaseId + Math.Min(9, this.CardButtons.Count - 1) : UnlockSlotId;
        this.EquipButton.upNeighborID = UnlockSlotId;
        this.EquipButton.downNeighborID = UnequipId;

        this.UnequipButton.leftNeighborID = this.EquipButton.leftNeighborID;
        this.UnequipButton.upNeighborID = EquipId;
        this.UnequipButton.downNeighborID = UpgradeId;

        this.UpgradeButton.leftNeighborID = this.EquipButton.leftNeighborID;
        this.UpgradeButton.upNeighborID = UnequipId;
        this.UpgradeButton.downNeighborID = BackId;
    }

    public override void populateClickableComponentList()
    {
        base.populateClickableComponentList();
        this.allClickableComponents.Clear();
        this.allClickableComponents.Add(this.BackButton);
        this.allClickableComponents.Add(this.UnlockSlotButton);

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

        if (this.UpgradeCelebrationMs > 0)
        {
            this.UpgradeCelebrationMs = Math.Max(
                0,
                this.UpgradeCelebrationMs - (int)time.ElapsedGameTime.TotalMilliseconds
            );

            if (this.UpgradeCelebrationMs <= 0)
                this.ClearUpgradeCelebration();
        }
    }

    public override void receiveGamePadButton(Buttons b)
    {
        if (this.UpgradeCelebrationMs > 0)
        {
            if (b is Buttons.A or Buttons.B or Buttons.X or Buttons.Y)
            {
                this.ClearUpgradeCelebration();
                Game1.playSound("smallSelect");
            }
            return;
        }

        if (b == Buttons.B)
        {
            Game1.playSound("bigDeSelect");
            this.OnCloseToMachine();
            return;
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
            if (slot >= this.UnlockedSlots)
                return;

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
            int index = this.currentlySnappedComponent.myID - CardBaseId;
            CardDefinition card = this.CardButtons[index].Card;
            this.Selected = card;
            this.ResetDetailScroll();
            this.QuickEquipCard(card);
            return;
        }

        base.receiveGamePadButton(b);
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        if (this.UpgradeCelebrationMs > 0)
        {
            this.ClearUpgradeCelebration();
            Game1.playSound("smallSelect");
            return;
        }

        if (this.Selected is not null && this.DetailScrollTrack.Contains(x, y))
        {
            Rectangle thumb = this.GetDetailScrollThumb();
            this.DetailScrollDragging = true;

            if (thumb.Contains(x, y))
            {
                this.DetailScrollDragOffset = y - thumb.Y;
            }
            else
            {
                this.DetailScrollDragOffset = thumb.Height / 2;
                this.SetDetailScrollFromThumbY(y - this.DetailScrollDragOffset);
            }

            Game1.playSound("smallSelect");
            return;
        }

        if (this.BackButton.containsPoint(x, y))
        {
            Game1.playSound("smallSelect");
            this.OnCloseToMachine();
            return;
        }

        foreach ((int slot, ClickableComponent body, ClickableComponent remove) in this.ActiveSlots)
        {
            bool unlocked = slot < this.UnlockedSlots;
            string? id = this.Save.Data.EquippedCards.ElementAtOrDefault(slot);
            CardDefinition? card = id is null ? null : this.Cards.Get(id);

            if (!unlocked && body.containsPoint(x, y))
            {
                this.Status = ModEntry.T("binder.status.slot-locked");
                Game1.playSound("cancel");
                return;
            }

            if (unlocked && remove.containsPoint(x, y) && card is not null)
            {
                this.Selected = card;
                this.ResetDetailScroll();
                this.UnequipCard(
                    card,
                    ModEntry.T("binder.status.unequipped-slot", new { name = card.Name, slot = slot + 1 })
                );
                return;
            }

            if (body.containsPoint(x, y))
            {
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
        }

        foreach ((CardDefinition card, ClickableComponent button) in this.CardButtons)
        {
            if (!button.containsPoint(x, y))
                continue;

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
            this.UnequipCard(
                this.Selected,
                ModEntry.T("binder.status.unequipped", new { name = this.Selected.Name })
            );
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
            else
            {
                int oldLevel = this.Upgrades.GetLevel(this.Selected);
                string beforeEffect =
                    this.Upgrades.GetLevelEffectText(this.Selected, oldLevel);

                if (this.Upgrades.TryUpgrade(
                    this.Selected,
                    out int newLevel,
                    out int spent))
                {
                    string afterEffect =
                        this.Upgrades.GetLevelEffectText(this.Selected, newLevel);

                    this.Status = ModEntry.T(
                        "binder.status.card-upgraded",
                        new
                        {
                            name = this.Selected.Name,
                            level = newLevel,
                            copies = spent
                        }
                    );

                    this.StartUpgradeCelebration(
                        this.Selected,
                        oldLevel,
                        newLevel,
                        spent,
                        beforeEffect,
                        afterEffect
                    );

                    Game1.playSound("reward");
                }
                else
                {
                    this.Status = ModEntry.T(
                        "binder.status.card-not-enough-copies",
                        new { have = ownedCopies, need = required }
                    );
                    Game1.playSound("cancel");
                }
            }
        }
    }

    public override void receiveScrollWheelAction(int direction)
    {
        if (this.Selected is not null)
        {
            Point mouse = new(Game1.getMouseX(ui_scale: true), Game1.getMouseY(ui_scale: true));
            if (this.DetailScrollViewport.Contains(mouse)
                || this.DetailScrollTrack.Contains(mouse))
            {
                int delta = direction > 0 ? -48 : 48;
                this.DetailScrollOffset = Math.Clamp(
                    this.DetailScrollOffset + delta,
                    0,
                    this.GetDetailMaxScroll()
                );
                return;
            }
        }

        base.receiveScrollWheelAction(direction);
    }

    public override void leftClickHeld(int x, int y)
    {
        if (this.DetailScrollDragging)
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

    public override void receiveRightClick(int x, int y, bool playSound = true)
    {
        foreach ((int slot, ClickableComponent body, _) in this.ActiveSlots)
        {
            if (slot >= this.UnlockedSlots || !body.containsPoint(x, y))
                continue;

            string? id = this.Save.Data.EquippedCards.ElementAtOrDefault(slot);
            CardDefinition? card = id is null ? null : this.Cards.Get(id);
            if (card is null)
                return;

            this.Selected = card;
            this.ResetDetailScroll();
            this.UnequipCard(
                card,
                ModEntry.T("binder.status.unequipped-slot", new { name = card.Name, slot = slot + 1 })
            );
            return;
        }

        base.receiveRightClick(x, y, playSound);
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

    private void DrawScrapWallet(SpriteBatch b)
    {
        // The two Scrap currencies unlock with MiMi/Wizard's Binder handoff and live
        // here permanently instead of consuming backpack slots.
        if (!this.Save.Data.BinderUnlocked)
            return;

        int splitX = this.xPositionOnScreen + this.width - 350;
        int startX = splitX - 126;
        int y = this.yPositionOnScreen + 30;
        const int slotW = 54;
        const int slotH = 66;
        const int gap = 8;

        DrawScrapSlot(
            b,
            new Rectangle(startX, y, slotW, slotH),
            0,
            this.Save.Data.CardboardScraps
        );
        DrawScrapSlot(
            b,
            new Rectangle(startX + slotW + gap, y, slotW, slotH),
            1,
            this.Save.Data.ShinyScraps
        );
    }

    private void DrawScrapSlot(SpriteBatch b, Rectangle slot, int spriteIndex, int count)
    {
        b.Draw(Game1.staminaRect, slot, new Color(58, 45, 62));
        CardchaUi.DrawBorder(b, slot, CardchaUi.Gold * 0.72f, 2);

        Rectangle icon = new(slot.X + 10, slot.Y + 6, 34, 34);
        if (this.ScrapIcons is not null)
        {
            b.Draw(
                this.ScrapIcons,
                icon,
                new Rectangle(spriteIndex * 16, 0, 16, 16),
                Color.White
            );
        }

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            $"×{Math.Max(0, count)}",
            new Rectangle(slot.X + 3, slot.Bottom - 23, slot.Width - 6, 20),
            Color.White,
            centerX: true,
            centerY: true,
            padding: 1,
            maxScale: 0.92f
        );
    }

    public override void draw(SpriteBatch b)
    {
        b.Draw(
            Game1.fadeToBlackRect,
            Game1.graphics.GraphicsDevice.Viewport.Bounds,
            Color.Black * 0.80f
        );

        Rectangle book = new(
            this.xPositionOnScreen,
            this.yPositionOnScreen,
            this.width,
            this.height
        );

        // Outer leather shell.
        b.Draw(Game1.staminaRect, book, CardchaUi.LeatherDark);
        CardchaUi.DrawBorder(b, book, new Color(35, 23, 28), 6);

        Rectangle leatherInset = new(
            book.X + 8,
            book.Y + 8,
            book.Width - 16,
            book.Height - 16
        );
        b.Draw(Game1.staminaRect, leatherInset, CardchaUi.Leather);
        CardchaUi.DrawBorder(b, leatherInset, CardchaUi.Gold * 0.85f, 3);
        CardchaUi.DrawCornerOrnaments(b, leatherInset, CardchaUi.Gold * 0.72f);

        // Two-page spread inspired by a real collector journal.
        int splitX = this.xPositionOnScreen + this.width - 350;
        Rectangle leftPage = new(
            this.xPositionOnScreen + 28,
            this.yPositionOnScreen + 22,
            splitX - (this.xPositionOnScreen + 28) - 10,
            this.height - 44
        );
        Rectangle rightPage = new(
            splitX + 10,
            this.yPositionOnScreen + 22,
            this.xPositionOnScreen + this.width - 28 - (splitX + 10),
            this.height - 44
        );

        CardchaUi.DrawInsetPanel(
            b,
            leftPage,
            new Color(48, 39, 56),
            new Color(112, 82, 67),
            3,
            5
        );
        CardchaUi.DrawInsetPanel(
            b,
            rightPage,
            new Color(239, 218, 183),
            CardchaUi.PaperShadow,
            3,
            5
        );

        // Center spine / page shadow.
        b.Draw(
            Game1.staminaRect,
            new Rectangle(splitX - 2, this.yPositionOnScreen + 28, 5, this.height - 56),
            new Color(43, 31, 37)
        );
        b.Draw(
            Game1.staminaRect,
            new Rectangle(splitX + 3, this.yPositionOnScreen + 32, 2, this.height - 64),
            Color.White * 0.12f
        );

        // Decorative category bookmarks on the far-left edge.
        Color[] tabColors =
        {
            new Color(154, 85, 58),
            new Color(62, 111, 151),
            new Color(74, 124, 83),
            new Color(151, 68, 75)
        };

        for (int i = 0; i < tabColors.Length; i++)
        {
            Rectangle tab = new(
                this.xPositionOnScreen - 8,
                this.yPositionOnScreen + 164 + i * 76,
                42,
                58
            );
            b.Draw(Game1.staminaRect, tab, tabColors[i]);
            CardchaUi.DrawBorder(b, tab, new Color(45, 31, 35), 2);

            string glyph = i switch
            {
                0 => "★",
                1 => "◆",
                2 => "✦",
                _ => "?"
            };

            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                glyph,
                tab,
                Color.White,
                centerX: true,
                centerY: true,
                padding: 8
            );
        }

        CardchaUi.DrawNotebookTab(b, this.BackButton, this.BackLabel);

        Rectangle titlePaper = new(
            this.xPositionOnScreen + 260,
            this.yPositionOnScreen + 26,
            430,
            72
        );
        CardchaUi.DrawPaperHeader(
            b,
            titlePaper,
            ModEntry.T("binder.title"),
            ModEntry.T(
                "binder.discovered",
                new
                {
                    owned = this.Save.Data.OwnedCards.Count,
                    total = this.Cards.All.Count
                }
            )
        );

        this.DrawScrapWallet(b);

        // Active cards rack.
        Rectangle activeRack = new(
            this.xPositionOnScreen + 42,
            this.yPositionOnScreen + 100,
            600,
            190
        );
        CardchaUi.DrawInsetPanel(
            b,
            activeRack,
            new Color(65, 51, 69),
            new Color(144, 102, 74),
            3,
            5
        );

        Rectangle activeTitle = new(
            activeRack.X + 12,
            activeRack.Y + 8,
            370,
            32
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("binder.active-loadout", new { slots = this.UnlockedSlots }),
            activeTitle,
            new Color(247, 224, 181),
            padding: 2,
            maxScale: 1.30f
        );

        Rectangle hintArea = new(
            activeRack.X + 12,
            activeRack.Y + 38,
            540,
            22
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("binder.hint"),
            hintArea,
            new Color(207, 196, 184),
            padding: 2,
            maxScale: 1.18f
        );

        int nextSlotCost = this.Upgrades.GetNextSlotUnlockCost();
        string unlockLabel = nextSlotCost <= 0
            ? ModEntry.T("binder.slot.maxed")
            : ModEntry.T("binder.unlock-slot", new { cost = nextSlotCost });

        bool canUnlockSlot =
            nextSlotCost > 0
            && this.Save.Data.SuspiciousDust >= nextSlotCost;

        CardchaUi.DrawButton(
            b,
            this.UnlockSlotButton,
            unlockLabel,
            CardchaUi.PremiumPurple,
            enabled: canUnlockSlot
        );

        foreach ((int slot, ClickableComponent body, ClickableComponent remove) in this.ActiveSlots)
        {
            bool unlocked = slot < this.UnlockedSlots;
            string? id = this.Save.Data.EquippedCards.ElementAtOrDefault(slot);
            CardDefinition? card = id is null ? null : this.Cards.Get(id);

            bool selected =
                card is not null
                && this.Selected?.Id.Equals(card.Id, StringComparison.OrdinalIgnoreCase) == true;

            bool focused = this.currentlySnappedComponent?.myID == body.myID;

            this.Renderer.DrawActiveSlot(
                b,
                body.bounds,
                remove.bounds,
                card,
                slot + 1,
                selected || focused,
                unlocked
            );

            if (focused)
                CardchaUi.DrawFocus(b, body.bounds);
        }

        // Collection page.
        Rectangle collectionHeader = new(
            this.xPositionOnScreen + 48,
            this.yPositionOnScreen + 292,
            590,
            28
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("binder.collection"),
            collectionHeader,
            new Color(247, 224, 181),
            padding: 2,
            maxScale: 1.30f
        );

        foreach ((CardDefinition card, ClickableComponent button) in this.CardButtons)
        {
            bool owned = this.Save.Data.OwnedCards.Contains(card.Id);
            bool equipped = this.Loadout.IsEquipped(card.Id);
            bool focused = this.currentlySnappedComponent?.myID == button.myID;

            this.Renderer.DrawCollectionCard(
                b,
                button.bounds,
                card,
                owned,
                equipped,
                this.Selected?.Id == card.Id || focused
            );

            if (owned)
            {
                Rectangle levelBadge = new(
                    button.bounds.X + 4,
                    button.bounds.Y + 4,
                    40,
                    23
                );
                b.Draw(
                    Game1.staminaRect,
                    levelBadge,
                    new Color(42, 34, 43) * 0.88f
                );
                CardchaUi.DrawBorder(
                    b,
                    levelBadge,
                    CardchaUi.Gold * 0.65f,
                    1
                );
                CardchaUi.DrawScaledText(
                    b,
                    Game1.smallFont,
                    $"Lv{this.Upgrades.GetLevel(card)}",
                    levelBadge,
                    Color.White,
                    centerX: true,
                    centerY: true,
                    padding: 2,
                    maxScale: 0.82f
                );
            }

            if (focused)
                CardchaUi.DrawFocus(b, button.bounds);
        }

        // Right detail page.
        int sideX = this.xPositionOnScreen + this.width - 325;
        int sideY = this.yPositionOnScreen + 52;

        Rectangle detailTitle = new(
            sideX + 8,
            sideY,
            254,
            42
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("binder.details"),
            detailTitle,
            CardchaUi.InkBrown,
            centerX: true,
            centerY: true,
            padding: 2
        );

        // Decorative divider.
        b.Draw(
            Game1.staminaRect,
            new Rectangle(sideX + 24, sideY + 46, 220, 2),
            CardchaUi.PaperShadow
        );
        b.Draw(
            Game1.staminaRect,
            new Rectangle(sideX + 112, sideY + 42, 44, 10),
            CardchaUi.Gold * 0.55f
        );

        if (this.Selected is null)
        {
            CardchaUi.DrawWrappedText(
                b,
                Game1.smallFont,
                ModEntry.T("binder.inspect-help"),
                new Rectangle(sideX + 20, sideY + 74, 230, 150),
                Color.DarkSlateGray,
                maxLines: 6
            );
        }
        else
        {
            Rectangle iconFrame = new(
                sideX + 89,
                sideY + 56,
                92,
                92
            );
            b.Draw(
                Game1.staminaRect,
                iconFrame,
                new Color(228, 196, 145)
            );
            CardchaUi.DrawBorder(
                b,
                iconFrame,
                CardchaUi.RarityColor(this.Selected.Rarity),
                4
            );
            CardchaUi.DrawCornerOrnaments(
                b,
                iconFrame,
                CardchaUi.Gold * 0.55f
            );
            this.Renderer.DrawIcon(
                b,
                new Rectangle(
                    iconFrame.X + 12,
                    iconFrame.Y + 12,
                    iconFrame.Width - 24,
                    iconFrame.Height - 24
                ),
                this.Selected
            );

            Rectangle nameArea = new(
                sideX + 18,
                sideY + 146,
                234,
                44
            );
            CardchaUi.DrawAutoFitWrappedText(
                b,
                Game1.smallFont,
                this.Selected.Name,
                nameArea,
                CardchaUi.RarityColor(this.Selected.Rarity),
                maxLines: 2,
                minScale: 0.62f,
                centerX: true,
                maxScale: 1.12f
            );

            Rectangle rarityArea = new(
                sideX + 18,
                sideY + 190,
                234,
                22
            );
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                CardchaUi.RarityText(this.Selected.Rarity),
                rarityArea,
                Color.Black,
                padding: 0,
                maxScale: 1.22f
            );

            int level = this.Upgrades.GetLevel(this.Selected);
            int maxLevel = this.Upgrades.GetMaxLevel(this.Selected);

            Rectangle levelArea = new(
                sideX + 18,
                sideY + 214,
                234,
                22
            );
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                ModEntry.T("binder.level", new { level, max = maxLevel }),
                levelArea,
                Color.Black,
                padding: 0,
                maxScale: 1.22f
            );

            CardchaUi.DrawStars(
                b,
                new Rectangle(sideX + 18, sideY + 238, 234, 24),
                level,
                maxLevel,
                CardchaUi.Gold
            );

            this.DrawScrollableDetailContent(b);
        }

        // Status parchment strip deliberately bounded so long Vietnamese text
        // never overlaps the buttons below.
        Rectangle statusStrip = new(
            sideX + 10,
            this.yPositionOnScreen + this.height - 270,
            250,
            56
        );
        b.Draw(
            Game1.staminaRect,
            statusStrip,
            new Color(228, 196, 145) * 0.70f
        );
        CardchaUi.DrawBorder(
            b,
            statusStrip,
            Color.SaddleBrown * 0.45f,
            2
        );
        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            this.Status,
            new Rectangle(
                statusStrip.X + 6,
                statusStrip.Y + 5,
                statusStrip.Width - 12,
                statusStrip.Height - 10
            ),
            Color.DarkSlateGray,
            maxLines: 2,
            minScale: 0.78f,
            maxScale: 1.16f
        );

        bool canEquip =
            this.Selected is not null
            && !this.Loadout.IsEquipped(this.Selected.Id);

        bool canUnequip =
            this.Selected is not null
            && this.Loadout.IsEquipped(this.Selected.Id);

        bool canUpgrade =
            this.Selected is not null
            && this.Upgrades.GetRequiredCopies(this.Selected) > 0
            && this.Upgrades.GetCopies(this.Selected) >= this.Upgrades.GetRequiredCopies(this.Selected)
            && this.Save.Data.OwnedCards.Contains(this.Selected.Id);

        CardchaUi.DrawButton(
            b,
            this.EquipButton,
            ModEntry.T("binder.equip"),
            CardchaUi.GoodGreen,
            canEquip
        );
        CardchaUi.DrawButton(
            b,
            this.UnequipButton,
            ModEntry.T("binder.unequip"),
            CardchaUi.DangerRed,
            canUnequip
        );

        string upgradeLabel =
            this.Selected is null
            || this.Upgrades.GetRequiredCopies(this.Selected) <= 0
                ? ModEntry.T("binder.upgrade.max")
                : ModEntry.T(
                    "binder.upgrade",
                    new
                    {
                        have = this.Upgrades.GetCopies(this.Selected),
                        need = this.Upgrades.GetRequiredCopies(this.Selected)
                    }
                );

        CardchaUi.DrawButton(
            b,
            this.UpgradeButton,
            upgradeLabel,
            CardchaUi.Gold,
            canUpgrade
        );

        if (this.currentlySnappedComponent?.myID == EquipId)
            CardchaUi.DrawFocus(b, this.EquipButton.bounds);
        if (this.currentlySnappedComponent?.myID == UnequipId)
            CardchaUi.DrawFocus(b, this.UnequipButton.bounds);
        if (this.currentlySnappedComponent?.myID == UpgradeId)
            CardchaUi.DrawFocus(b, this.UpgradeButton.bounds);
        if (this.currentlySnappedComponent?.myID == BackId)
            CardchaUi.DrawFocus(b, this.BackButton.bounds);
        if (this.currentlySnappedComponent?.myID == UnlockSlotId)
            CardchaUi.DrawFocus(b, this.UnlockSlotButton.bounds);

        if (this.UpgradeCelebrationMs > 0)
            this.DrawUpgradeCelebration(b);

        drawMouse(b);
    }

    private void StartUpgradeCelebration(
        CardDefinition card,
        int fromLevel,
        int toLevel,
        int copiesSpent,
        string beforeEffect,
        string afterEffect)
    {
        this.UpgradeCelebrationCard = card;
        this.UpgradeCelebrationFromLevel = fromLevel;
        this.UpgradeCelebrationToLevel = toLevel;
        this.UpgradeCelebrationCopiesSpent = copiesSpent;
        this.UpgradeCelebrationBefore = beforeEffect;
        this.UpgradeCelebrationAfter = afterEffect;
        this.UpgradeCelebrationMs = UpgradeCelebrationDurationMs;
    }

    private void ClearUpgradeCelebration()
    {
        this.UpgradeCelebrationMs = 0;
        this.UpgradeCelebrationCard = null;
        this.UpgradeCelebrationBefore = "";
        this.UpgradeCelebrationAfter = "";
    }

    private void DrawUpgradeCelebration(SpriteBatch b)
    {
        CardDefinition? card = this.UpgradeCelebrationCard;
        if (card is null)
            return;

        float progress = 1f - Math.Clamp(
            this.UpgradeCelebrationMs / (float)UpgradeCelebrationDurationMs,
            0f,
            1f
        );

        float fadeIn = Math.Clamp(progress / 0.12f, 0f, 1f);
        float fadeOut = Math.Clamp(this.UpgradeCelebrationMs / 260f, 0f, 1f);
        float alpha = Math.Min(fadeIn, fadeOut);

        Rectangle screen = Game1.graphics.GraphicsDevice.Viewport.Bounds;
        b.Draw(
            Game1.fadeToBlackRect,
            screen,
            Color.Black * (0.58f * alpha)
        );

        int panelW = Math.Min(720, screen.Width - 48);
        int panelH = Math.Min(430, screen.Height - 48);

        Rectangle panel = new(
            screen.Center.X - panelW / 2,
            screen.Center.Y - panelH / 2,
            panelW,
            panelH
        );

        b.Draw(
            Game1.staminaRect,
            panel,
            CardchaUi.ParchmentLight * alpha
        );
        CardchaUi.DrawBorder(
            b,
            panel,
            CardchaUi.Gold * alpha,
            5
        );
        CardchaUi.DrawCornerOrnaments(
            b,
            panel,
            CardchaUi.Gold * (0.85f * alpha)
        );

        Rectangle title =
            new(panel.X + 28, panel.Y + 18, panel.Width - 56, 46);

        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("binder.upgrade-celebration.title"),
            title,
            new Color(105, 62, 34) * alpha,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.05f
        );

        Rectangle cardRect =
            new(panel.X + 38, panel.Y + 86, 168, 214);

        this.Renderer.DrawRevealCard(
            b,
            cardRect,
            card,
            ModEntry.T(
                "binder.upgrade-celebration.level",
                new
                {
                    from = this.UpgradeCelebrationFromLevel,
                    to = this.UpgradeCelebrationToLevel
                }
            )
        );

        string stars =
            new string('★', Math.Max(1, this.UpgradeCelebrationToLevel));

        Rectangle starsRect =
            new(cardRect.X - 4, cardRect.Bottom + 6, cardRect.Width + 8, 32);

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            stars,
            starsRect,
            CardchaUi.Gold * alpha,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.20f
        );

        int infoX = panel.X + 236;
        int infoW = panel.Right - infoX - 28;

        Rectangle nameRect =
            new(infoX, panel.Y + 82, infoW, 42);

        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            card.Name,
            nameRect,
            CardchaUi.InkBrown * alpha,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 0.95f
        );

        Rectangle beforeBox =
            new(infoX, panel.Y + 138, infoW, 92);
        Rectangle afterBox =
            new(infoX, panel.Y + 242, infoW, 112);

        CardchaUi.DrawInsetPanel(
            b,
            beforeBox,
            new Color(231, 213, 188) * alpha,
            CardchaUi.PaperShadow * alpha,
            2,
            3
        );
        CardchaUi.DrawInsetPanel(
            b,
            afterBox,
            new Color(255, 232, 167) * alpha,
            CardchaUi.Gold * alpha,
            3,
            3
        );

        Rectangle beforeTitle =
            new(beforeBox.X + 10, beforeBox.Y + 6, beforeBox.Width - 20, 26);
        Rectangle beforeBody =
            new(beforeBox.X + 10, beforeBox.Y + 32, beforeBox.Width - 20, beforeBox.Height - 38);
        Rectangle afterTitle =
            new(afterBox.X + 10, afterBox.Y + 6, afterBox.Width - 20, 26);
        Rectangle afterBody =
            new(afterBox.X + 10, afterBox.Y + 32, afterBox.Width - 20, afterBox.Height - 38);

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("binder.upgrade-celebration.before"),
            beforeTitle,
            CardchaUi.InkBrown * alpha,
            padding: 1,
            maxScale: 1.05f
        );

        CardchaUi.DrawWrappedTextFixedClipped(
            b,
            Game1.smallFont,
            this.UpgradeCelebrationBefore,
            beforeBody,
            beforeBox,
            Color.Black * alpha,
            maximumLines: 3
        );

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("binder.upgrade-celebration.after"),
            afterTitle,
            new Color(130, 78, 26) * alpha,
            padding: 1,
            maxScale: 1.08f
        );

        CardchaUi.DrawWrappedTextFixedClipped(
            b,
            Game1.smallFont,
            this.UpgradeCelebrationAfter,
            afterBody,
            afterBox,
            Color.Black * alpha,
            maximumLines: 4
        );

        Rectangle footer =
            new(panel.X + 30, panel.Bottom - 54, panel.Width - 60, 32);

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T(
                "binder.upgrade-celebration.footer",
                new { copies = this.UpgradeCelebrationCopiesSpent }
            ),
            footer,
            new Color(92, 72, 61) * alpha,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.05f
        );
    }

    private void ResetDetailScroll()
    {
        this.DetailScrollOffset = 0;
        this.DetailScrollDragging = false;
    }

    private int GetDetailMaxScroll()
        => Math.Max(0, this.DetailContentHeight - this.DetailScrollViewport.Height);

    private Rectangle GetDetailScrollThumb()
    {
        int maxScroll = this.GetDetailMaxScroll();
        if (maxScroll <= 0)
            return this.DetailScrollTrack;

        int thumbHeight = Math.Max(
            30,
            (int)Math.Round(
                this.DetailScrollTrack.Height
                * (this.DetailScrollViewport.Height / (double)Math.Max(this.DetailContentHeight, 1))
            )
        );

        thumbHeight = Math.Min(this.DetailScrollTrack.Height, thumbHeight);
        int travel = Math.Max(1, this.DetailScrollTrack.Height - thumbHeight);
        int y = this.DetailScrollTrack.Y
            + (int)Math.Round(travel * (this.DetailScrollOffset / (double)maxScroll));

        return new Rectangle(
            this.DetailScrollTrack.X,
            y,
            this.DetailScrollTrack.Width,
            thumbHeight
        );
    }

    private void SetDetailScrollFromThumbY(int thumbY)
    {
        int maxScroll = this.GetDetailMaxScroll();
        if (maxScroll <= 0)
        {
            this.DetailScrollOffset = 0;
            return;
        }

        Rectangle thumb = this.GetDetailScrollThumb();
        int travel = Math.Max(1, this.DetailScrollTrack.Height - thumb.Height);
        int local = Math.Clamp(
            thumbY - this.DetailScrollTrack.Y,
            0,
            travel
        );

        this.DetailScrollOffset = (int)Math.Round(
            maxScroll * (local / (double)travel)
        );
    }

    private void DrawScrollableDetailContent(SpriteBatch b)
    {
        if (this.Selected is null)
            return;

        CardDefinition card = this.Selected;
        int currentLevel = this.Upgrades.GetLevel(card);
        int maxLevel = this.Upgrades.GetMaxLevel(card);
        int copies = this.Upgrades.GetCopies(card);
        int needed = this.Upgrades.GetRequiredCopies(card);

        int virtualY = 0;

        string currentEffect = this.Upgrades.GetLevelEffectText(card, currentLevel);
        this.DrawDetailBlock(
            b,
            ref virtualY,
            ModEntry.T("binder.current-effect"),
            currentEffect,
            current: true
        );

        string copyText = needed <= 0
            ? ModEntry.T("binder.copies.max", new { have = copies })
            : ModEntry.T("binder.copies", new { have = copies, need = needed });

        this.DrawDetailBlock(
            b,
            ref virtualY,
            ModEntry.T("binder.upgrade-material"),
            copyText,
            current: false
        );

        virtualY += 4;

        this.DrawDetailHeader(
            b,
            ref virtualY,
            ModEntry.T("binder.all-levels")
        );

        for (int level = 1; level <= maxLevel; level++)
        {
            bool isCurrent = level == currentLevel;
            string label = ModEntry.T(
                "binder.level-row",
                new { level, max = maxLevel }
            );
            string effectText = this.Upgrades.GetLevelEffectText(card, level);

            this.DrawDetailBlock(
                b,
                ref virtualY,
                label,
                effectText,
                isCurrent
            );
        }

        this.DetailContentHeight = Math.Max(
            this.DetailScrollViewport.Height,
            virtualY + 6
        );

        this.DetailScrollOffset = Math.Clamp(
            this.DetailScrollOffset,
            0,
            this.GetDetailMaxScroll()
        );

        Rectangle thumb = this.GetDetailScrollThumb();
        CardchaUi.DrawScrollbar(
            b,
            this.DetailScrollTrack,
            thumb,
            this.DetailScrollDragging
        );
    }

    private void DrawDetailHeader(
        SpriteBatch b,
        ref int virtualY,
        string text)
    {
        int height = Game1.smallFont.LineSpacing + 12;

        Rectangle virtualRect = new(
            this.DetailScrollViewport.X,
            this.DetailScrollViewport.Y + virtualY - this.DetailScrollOffset,
            this.DetailScrollViewport.Width,
            height
        );

        if (virtualRect.Top >= this.DetailScrollViewport.Top
            && virtualRect.Bottom <= this.DetailScrollViewport.Bottom)
        {
            Utility.drawTextWithShadow(
                b,
                text,
                Game1.smallFont,
                new Vector2(virtualRect.X, virtualRect.Y + 3),
                CardchaUi.InkBrown
            );
        }

        virtualY += height + 2;
    }

    private void DrawDetailBlock(
        SpriteBatch b,
        ref int virtualY,
        string title,
        string body,
        bool current)
    {
        int horizontalPadding = 8;
        int titleHeight = Game1.smallFont.LineSpacing + 8;
        int bodyWidth = this.DetailScrollViewport.Width - horizontalPadding * 2;

        int bodyHeight = CardchaUi.MeasureWrappedTextHeight(
            Game1.smallFont,
            body,
            bodyWidth,
            minimumLines: 1,
            maximumLines: 6
        );

        // The FRAME grows to fit the readable text. We no longer shrink the text
        // to fit a predetermined box.
        int height = titleHeight + bodyHeight + 12;

        Rectangle virtualRect = new(
            this.DetailScrollViewport.X,
            this.DetailScrollViewport.Y + virtualY - this.DetailScrollOffset,
            this.DetailScrollViewport.Width,
            height
        );

        if (virtualRect.Bottom >= this.DetailScrollViewport.Top
            && virtualRect.Top <= this.DetailScrollViewport.Bottom)
        {
            Rectangle visible = Rectangle.Intersect(
                virtualRect,
                this.DetailScrollViewport
            );

            b.Draw(
                Game1.staminaRect,
                visible,
                current
                    ? new Color(255, 231, 172) * 0.78f
                    : new Color(246, 228, 195) * 0.60f
            );

            if (visible.Height >= 18)
            {
                CardchaUi.DrawBorder(
                    b,
                    visible,
                    current
                        ? CardchaUi.Gold * 0.75f
                        : CardchaUi.PaperShadow * 0.55f,
                    2
                );
            }

            Rectangle titleArea = new(
                virtualRect.X + horizontalPadding,
                virtualRect.Y + 5,
                bodyWidth,
                titleHeight - 4
            );

            if (titleArea.Top >= this.DetailScrollViewport.Top
                && titleArea.Bottom <= this.DetailScrollViewport.Bottom)
            {
                Utility.drawTextWithShadow(
                    b,
                    title,
                    Game1.smallFont,
                    new Vector2(titleArea.X, titleArea.Y),
                    current
                        ? new Color(126, 78, 39)
                        : CardchaUi.InkBrown
                );
            }

            Rectangle bodyArea = new(
                virtualRect.X + horizontalPadding,
                virtualRect.Y + titleHeight,
                bodyWidth,
                bodyHeight
            );

            CardchaUi.DrawWrappedTextFixedClipped(
                b,
                Game1.smallFont,
                body,
                bodyArea,
                this.DetailScrollViewport,
                Color.Black,
                maximumLines: 6
            );
        }

        virtualY += height + 4;
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

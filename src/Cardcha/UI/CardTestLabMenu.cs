using Cardcha.Models;
using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

/// <summary>
/// TEST-only visual harness for stepping through the 76 active Base Set cards.
/// The Lab session may remain active while this menu is closed so real gameplay can be tested.
/// END LAB / RESTORE returns the player's real collection/loadout snapshot.
/// </summary>
internal sealed class CardTestLabMenu : IClickableMenu
{
    private readonly CardTestLabService Lab;
    private readonly CardRenderer Renderer;
    private readonly CardTestArenaService Arena;
    private readonly IReadOnlyList<CardDefinition> Cards;

    private const int PreferredWidth = 1776;
    private const int PreferredHeight = 1080;
    private const long SelectionDebounceMs = 160L;
    private long LastSelectionInputAtMs;

    private int SelectedIndex;
    private int RequestedLevel = 1;

    private Rectangle PrevRect;
    private Rectangle NextRect;
    private Rectangle LevelDownRect;
    private Rectangle LevelUpRect;
    private Rectangle EquipRect;
    private Rectangle UnequipRect;
    private Rectangle PassRect;
    private Rectangle FailRect;
    private Rectangle ResetRect;
    private Rectangle HpFullRect;
    private Rectangle HpLowRect;
    private Rectangle DummyFullRect;
    private Rectangle DummyLowRect;
    private Rectangle ArenaRect;
    private Rectangle ReturnRect;
    private Rectangle EndLabRect;
    private Rectangle CloseRect;

    public CardTestLabMenu(CardTestLabService lab, CardRenderer renderer, CardTestArenaService arena)
        : base(
            x: Math.Max(12, (Game1.uiViewport.Width - Math.Min(PreferredWidth, Game1.uiViewport.Width - 24)) / 2),
            y: Math.Max(12, (Game1.uiViewport.Height - Math.Min(PreferredHeight, Game1.uiViewport.Height - 24)) / 2),
            width: Math.Min(PreferredWidth, Game1.uiViewport.Width - 24),
            height: Math.Min(PreferredHeight, Game1.uiViewport.Height - 24),
            showUpperRightCloseButton: false)
    {
        this.Lab = lab;
        this.Renderer = renderer;
        this.Arena = arena;
        this.Cards = lab.ActiveCards;
        this.Lab.BeginSession();

        if (!string.IsNullOrWhiteSpace(this.Lab.ActiveCardId))
        {
            int activeIndex = this.Cards
                .Select((card, index) => (card, index))
                .FirstOrDefault(pair => pair.card.Id.Equals(this.Lab.ActiveCardId, StringComparison.OrdinalIgnoreCase))
                .index;
            if (activeIndex >= 0 && activeIndex < this.Cards.Count)
                this.SelectedIndex = activeIndex;
            this.RequestedLevel = Math.Clamp(this.Lab.ActiveLevel, 1, Math.Max(1, this.Selected.MaxLevel));
        }

        this.RebuildRects();
    }

    private CardDefinition Selected => this.Cards[Math.Clamp(this.SelectedIndex, 0, Math.Max(0, this.Cards.Count - 1))];

    public override void receiveKeyPress(Keys key)
    {
        if (key is Keys.Escape or Keys.Q)
        {
            this.ReturnToGame();
            return;
        }

        switch (key)
        {
            case Keys.Up:
            case Keys.W:
                this.MoveSelection(-1);
                return;
            case Keys.Down:
            case Keys.S:
                this.MoveSelection(1);
                return;
            case Keys.Left:
            case Keys.A:
                this.ChangeLevel(-1);
                return;
            case Keys.Right:
            case Keys.D:
                this.ChangeLevel(1);
                return;
            case Keys.Enter:
            case Keys.Space:
                this.EquipAndPlay();
                return;
            case Keys.U:
                this.UnequipAndPlay();
                return;
            case Keys.P:
                this.Lab.SetVerdict(this.Selected, CardLabVerdict.Pass);
                Game1.playSound("coin");
                return;
            case Keys.F:
                this.Lab.SetVerdict(this.Selected, CardLabVerdict.Fail);
                Game1.playSound("cancel");
                return;
            case Keys.R:
                this.Lab.ResetTelemetry();
                Game1.playSound("smallSelect");
                return;
            case Keys.D1:
                this.Lab.SetHealthPercent(1.0);
                return;
            case Keys.D2:
                this.Lab.SetHealthPercent(0.19);
                return;
            case Keys.T:
                this.EnterArenaAndPlay();
                return;
            case Keys.F7:
                this.Arena.ResetDummy(1.0);
                return;
            case Keys.F6:
                this.Arena.ResetDummy(0.19);
                return;
            case Keys.End:
                this.EndLabAndRestore();
                return;
        }

        base.receiveKeyPress(key);
    }

    public override void receiveGamePadButton(Buttons b)
    {
        switch (b)
        {
            case Buttons.B:
                this.ReturnToGame();
                return;
            case Buttons.DPadUp:
            case Buttons.LeftThumbstickUp:
                this.MoveSelection(-1);
                return;
            case Buttons.DPadDown:
            case Buttons.LeftThumbstickDown:
                this.MoveSelection(1);
                return;
            case Buttons.DPadLeft:
            case Buttons.LeftThumbstickLeft:
                this.ChangeLevel(-1);
                return;
            case Buttons.DPadRight:
            case Buttons.LeftThumbstickRight:
                this.ChangeLevel(1);
                return;
            case Buttons.A:
                this.EquipAndPlay();
                return;
            case Buttons.X:
                this.UnequipAndPlay();
                return;
            case Buttons.Y:
                this.Lab.SetVerdict(this.Selected, CardLabVerdict.Pass);
                Game1.playSound("coin");
                return;
            case Buttons.RightShoulder:
                this.Lab.SetVerdict(this.Selected, CardLabVerdict.Fail);
                Game1.playSound("cancel");
                return;
            case Buttons.LeftShoulder:
                this.Lab.ResetTelemetry();
                Game1.playSound("smallSelect");
                return;
            case Buttons.RightTrigger:
                this.EnterArenaAndPlay();
                return;
            case Buttons.LeftTrigger:
                this.Arena.ResetDummy(1.0);
                return;
            case Buttons.RightStick:
                this.Arena.ResetDummy(0.19);
                return;
            case Buttons.Start:
                this.EndLabAndRestore();
                return;
        }

        base.receiveGamePadButton(b);
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        if (this.TrySelectCardRowAt(x, y))
            return;

        if (this.PrevRect.Contains(x, y)) this.MoveSelection(-1, force: true);
        else if (this.NextRect.Contains(x, y)) this.MoveSelection(1, force: true);
        else if (this.LevelDownRect.Contains(x, y)) this.ChangeLevel(-1);
        else if (this.LevelUpRect.Contains(x, y)) this.ChangeLevel(1);
        else if (this.EquipRect.Contains(x, y)) this.EquipAndPlay();
        else if (this.UnequipRect.Contains(x, y)) this.UnequipAndPlay();
        else if (this.PassRect.Contains(x, y))
        {
            this.Lab.SetVerdict(this.Selected, CardLabVerdict.Pass);
            Game1.playSound("coin");
        }
        else if (this.FailRect.Contains(x, y))
        {
            this.Lab.SetVerdict(this.Selected, CardLabVerdict.Fail);
            Game1.playSound("cancel");
        }
        else if (this.ResetRect.Contains(x, y))
        {
            this.Lab.ResetTelemetry();
            Game1.playSound("smallSelect");
        }
        else if (this.HpFullRect.Contains(x, y)) this.Lab.SetHealthPercent(1.0);
        else if (this.HpLowRect.Contains(x, y)) this.Lab.SetHealthPercent(0.19);
        else if (this.DummyFullRect.Contains(x, y)) this.Arena.ResetDummy(1.0);
        else if (this.DummyLowRect.Contains(x, y)) this.Arena.ResetDummy(0.19);
        else if (this.ArenaRect.Contains(x, y)) this.EnterArenaAndPlay();
        else if (this.ReturnRect.Contains(x, y) || this.CloseRect.Contains(x, y)) this.ReturnToGame();
        else if (this.EndLabRect.Contains(x, y)) this.EndLabAndRestore();
        else base.receiveLeftClick(x, y, playSound);
    }

    public override void receiveScrollWheelAction(int direction)
    {
        if (direction > 0)
            this.MoveSelection(-1, force: true);
        else if (direction < 0)
            this.MoveSelection(1, force: true);
    }

    public override void gameWindowSizeChanged(Rectangle oldBounds, Rectangle newBounds)
    {
        this.width = Math.Min(PreferredWidth, Game1.uiViewport.Width - 24);
        this.height = Math.Min(PreferredHeight, Game1.uiViewport.Height - 24);
        this.xPositionOnScreen = Math.Max(12, (Game1.uiViewport.Width - this.width) / 2);
        this.yPositionOnScreen = Math.Max(12, (Game1.uiViewport.Height - this.height) / 2);
        this.RebuildRects();
        base.gameWindowSizeChanged(oldBounds, newBounds);
    }

    protected override void cleanupBeforeExit()
    {
        // Deliberately keep the Lab session alive while returning to gameplay.
        // Save/title handlers restore the real snapshot if the player forgets to press END LAB.
        base.cleanupBeforeExit();
    }

    public override void draw(SpriteBatch b)
    {
        b.Draw(Game1.fadeToBlackRect, new Microsoft.Xna.Framework.Rectangle(0, 0, Game1.uiViewport.Width, Game1.uiViewport.Height), Color.Black * 0.72f);

        Rectangle outer = new(this.xPositionOnScreen, this.yPositionOnScreen, this.width, this.height);
        CardchaUi.DrawRoundedPanel(b, outer, new Color(32, 30, 47), new Color(174, 139, 224), 4, 16);

        string title = "CARDCHA CARD TEST LAB  •  BASE SET 76";
        Vector2 titleSize = Game1.dialogueFont.MeasureString(title);
        float titleScale = Math.Min(1.0f, (outer.Width - 300f) / Math.Max(1f, titleSize.X));
        b.DrawString(Game1.dialogueFont, title, new Vector2(outer.Center.X - titleSize.X * titleScale / 2f, outer.Y + 16), Color.White, 0f, Vector2.Zero, titleScale, SpriteEffects.None, 1f);

        (int pass, int fail, int untested) = this.Lab.GetVerdictCounts();
        string progress = $"MANUAL: PASS {pass}   FAIL {fail}   UNTESTED {untested}";
        Vector2 progressSize = Game1.smallFont.MeasureString(progress);
        b.DrawString(Game1.smallFont, progress, new Vector2(outer.Center.X - progressSize.X * 0.9f / 2f, outer.Y + 58), new Color(224, 213, 244), 0f, Vector2.Zero, 0.9f, SpriteEffects.None, 1f);

        (int autoPass, int autoReview, int autoBlocked) = GeneratedCardAutoAudit.Counts();
        string autoProgress = $"AUTO CONTRACT: {autoPass} PASS   {autoReview} REVIEW   {autoBlocked} BLOCKED   •   MANUAL TEST IS OPTIONAL SPOT-CHECK";
        Vector2 autoProgressSize = Game1.smallFont.MeasureString(autoProgress);
        float autoProgressScale = Math.Min(0.88f, (outer.Width - 80f) / Math.Max(1f, autoProgressSize.X));
        b.DrawString(Game1.smallFont, autoProgress, new Vector2(outer.Center.X - autoProgressSize.X * autoProgressScale / 2f, outer.Y + 86), new Color(145, 214, 255), 0f, Vector2.Zero, autoProgressScale, SpriteEffects.None, 1f);

        string guide = "↑↓ CHỌN LÁ   •   ←→ LEVEL   •   A EQUIP   •   X BASELINE   •   RT ARENA   •   B THU NHỎ   •   F8 / R-STICK MỞ LẠI";
        Vector2 guideSize = Game1.smallFont.MeasureString(guide);
        float guideScale = Math.Min(0.86f, (outer.Width - 80f) / Math.Max(1f, guideSize.X));
        b.DrawString(Game1.smallFont, guide, new Vector2(outer.Center.X - guideSize.X * guideScale / 2f, outer.Y + 116), new Color(255, 218, 116), 0f, Vector2.Zero, guideScale, SpriteEffects.None, 1f);

        int contentTop = outer.Y + 158;
        int controlsHeight = 144;
        int panelHeight = outer.Bottom - controlsHeight - contentTop;
        int listWidth = Math.Min(546, Math.Max(396, outer.Width / 3));
        Rectangle listPanel = new(outer.X + 20, contentTop, listWidth, panelHeight);
        Rectangle detailPanel = new(listPanel.Right + 16, contentTop, outer.Right - listPanel.Right - 36, panelHeight);
        CardchaUi.DrawRoundedPanel(b, listPanel, new Color(47, 44, 64), new Color(105, 91, 139), 2, 10);
        CardchaUi.DrawRoundedPanel(b, detailPanel, new Color(43, 40, 59), new Color(105, 91, 139), 2, 10);

        this.DrawCardList(b, listPanel);
        this.DrawSelectedDetail(b, detailPanel);
        this.DrawButtons(b);

        drawMouse(b);
    }

    private void DrawCardList(SpriteBatch b, Rectangle panel)
    {
        int rowHeight = 51;
        int visible = Math.Max(7, (panel.Height - 20) / rowHeight);
        int start = Math.Clamp(this.SelectedIndex - visible / 2, 0, Math.Max(0, this.Cards.Count - visible));
        int end = Math.Min(this.Cards.Count, start + visible);

        for (int i = start; i < end; i++)
        {
            CardDefinition card = this.Cards[i];
            int row = i - start;
            Rectangle r = new(panel.X + 10, panel.Y + 10 + row * rowHeight, panel.Width - 20, rowHeight - 4);
            bool selected = i == this.SelectedIndex;
            if (selected)
            {
                b.Draw(Game1.staminaRect, r, new Color(92, 75, 126));
                CardchaUi.DrawBorder(b, r, new Color(210, 178, 255), 2);
            }

            CardLabVerdict verdict = this.Lab.GetVerdict(card);
            string marker = verdict switch
            {
                CardLabVerdict.Pass => "PASS",
                CardLabVerdict.Fail => "FAIL",
                _ => " • "
            };
            Color markerColor = verdict switch
            {
                CardLabVerdict.Pass => new Color(122, 221, 153),
                CardLabVerdict.Fail => new Color(240, 118, 130),
                _ => new Color(172, 164, 191)
            };

            b.DrawString(Game1.smallFont, marker, new Vector2(r.X + 8, r.Y + 7), markerColor, 0f, Vector2.Zero, 0.94f, SpriteEffects.None, 1f);
            string label = $"#{card.StableBaseId:00}  {card.Name}";
            DrawClippedText(b, Game1.smallFont, label, new Rectangle(r.X + 72, r.Y + 5, r.Width - 80, r.Height - 6), Color.White, 1.0f);
        }
    }

    private void DrawSelectedDetail(SpriteBatch b, Rectangle panel)
    {
        CardDefinition card = this.Selected;
        CardLabVerdict verdict = this.Lab.GetVerdict(card);
        CardAutoAuditEntry autoAudit = GeneratedCardAutoAudit.Get(card);

        Rectangle icon = new(panel.X + 20, panel.Y + 20, 128, 128);
        this.Renderer.DrawIcon(b, icon, card);
        CardchaUi.DrawBorder(b, icon, CardchaUi.RarityColor(card.Rarity), 3);

        int nameX = icon.Right + 18;
        DrawClippedText(b, Game1.dialogueFont, $"#{card.StableBaseId:00} {card.Name}", new Rectangle(nameX, panel.Y + 18, panel.Right - nameX - 20, 52), Color.White, 1.0f);
        b.DrawString(Game1.smallFont, $"Rarity: {card.Rarity}   EffectKey: {card.EffectKey}", new Vector2(nameX, panel.Y + 72), new Color(206, 196, 225), 0f, Vector2.Zero, 0.96f, SpriteEffects.None, 1f);
        b.DrawString(Game1.smallFont, $"TEST LEVEL: {this.RequestedLevel}/{Math.Max(1, card.MaxLevel)}", new Vector2(nameX, panel.Y + 105), new Color(255, 218, 116), 0f, Vector2.Zero, 1.08f, SpriteEffects.None, 1f);

        Color autoColor = autoAudit.Status switch
        {
            CardAutoAuditStatus.Pass => new Color(122, 221, 153),
            CardAutoAuditStatus.Blocked => new Color(240, 118, 130),
            _ => new Color(255, 199, 96)
        };
        string autoLabel = autoAudit.Status.ToString().ToUpperInvariant();
        b.DrawString(
            Game1.smallFont,
            $"AUTO CONTRACT: {autoLabel}  •  runtime refs {autoAudit.RuntimeRefs}  •  level rules {autoAudit.StarRuleCount}/{autoAudit.MaxLevel}",
            new Vector2(nameX, panel.Y + 136),
            autoColor,
            0f,
            Vector2.Zero,
            0.90f,
            SpriteEffects.None,
            1f
        );

        bool selectedEquipped = this.Lab.IsSelectedCardEquipped(card);
        string runState = selectedEquipped
            ? "ACTIVE TEST: EQUIPPED"
            : this.Lab.IsSessionActive && this.Lab.ActiveCardId.Equals(card.Id, StringComparison.OrdinalIgnoreCase)
                ? "ACTIVE TEST: BASELINE / UNEQUIPPED"
                : "SELECTED / NOT PREPARED";
        Color runColor = selectedEquipped ? new Color(122, 221, 153) : new Color(145, 214, 255);
        b.DrawString(Game1.smallFont, runState, new Vector2(nameX, panel.Y + 166), runColor, 0f, Vector2.Zero, 0.90f, SpriteEffects.None, 1f);

        string verdictText = verdict == CardLabVerdict.Untested ? "MANUAL: UNTESTED" : $"MANUAL: {verdict.ToString().ToUpperInvariant()}";
        Color verdictColor = verdict switch
        {
            CardLabVerdict.Pass => new Color(122, 221, 153),
            CardLabVerdict.Fail => new Color(240, 118, 130),
            _ => new Color(190, 183, 206)
        };
        b.DrawString(Game1.smallFont, verdictText, new Vector2(panel.Right - 190, panel.Y + 110), verdictColor, 0f, Vector2.Zero, 0.88f, SpriteEffects.None, 1f);

        b.DrawString(Game1.smallFont, "SELECTED LEVEL EFFECT", new Vector2(panel.X + 20, panel.Y + 204), new Color(255, 218, 116), 0f, Vector2.Zero, 1.0f, SpriteEffects.None, 1f);
        Rectangle descriptionArea = new(panel.X + 20, panel.Y + 238, panel.Width - 40, 76);
        DrawWrapped(b, Game1.smallFont, GetSelectedLevelText(card, this.RequestedLevel), descriptionArea, new Color(241, 234, 220), 1.0f, maxLines: 4);

        b.DrawString(Game1.smallFont, "WHAT TO DO / CÁCH TEST", new Vector2(panel.X + 20, panel.Y + 324), new Color(255, 218, 116), 0f, Vector2.Zero, 1.02f, SpriteEffects.None, 1f);
        Rectangle instructionArea = new(panel.X + 20, panel.Y + 358, panel.Width - 40, 78);
        DrawWrapped(b, Game1.smallFont, this.Lab.BuildInstruction(card), instructionArea, Color.White, 0.94f, maxLines: 4);

        b.DrawString(Game1.smallFont, "LIVE TELEMETRY / KẾT QUẢ THỰC TẾ", new Vector2(panel.X + 20, panel.Y + 446), new Color(145, 214, 255), 0f, Vector2.Zero, 1.02f, SpriteEffects.None, 1f);
        Rectangle telemetryArea = new(panel.X + 20, panel.Y + 482, panel.Width - 40, Math.Max(70, panel.Bottom - (panel.Y + 494)));
        DrawWrapped(b, Game1.smallFont, this.Lab.BuildTelemetry(card), telemetryArea, new Color(215, 230, 239), 0.90f, maxLines: 12);
    }

    private void DrawButtons(SpriteBatch b)
    {
        DrawButton(b, this.PrevRect, "CARD ↑", new Color(73, 67, 97));
        DrawButton(b, this.NextRect, "CARD ↓", new Color(73, 67, 97));
        DrawButton(b, this.LevelDownRect, "← LV", new Color(88, 73, 105));
        DrawButton(b, this.LevelUpRect, "LV →", new Color(88, 73, 105));
        DrawButton(b, this.EquipRect, "EQUIP & PLAY [A]", new Color(72, 119, 188));
        DrawButton(b, this.UnequipRect, "UNEQUIP & PLAY [X]", new Color(115, 89, 151));
        DrawButton(b, this.ResetRect, "RESET TELEMETRY [LB]", new Color(86, 86, 102));

        DrawButton(b, this.PassRect, "MANUAL PASS [Y/P]", new Color(57, 137, 92));
        DrawButton(b, this.FailRect, "MANUAL FAIL [RB/F]", new Color(155, 62, 75));
        DrawButton(b, this.HpFullRect, "ME 100% [1]", new Color(69, 111, 96));
        DrawButton(b, this.HpLowRect, "ME 19% [2]", new Color(145, 91, 78));
        DrawButton(b, this.DummyFullRect, "DUMMY 100% [LT/F7]", new Color(74, 105, 126));
        DrawButton(b, this.DummyLowRect, "DUMMY 19% [R3/F6]", new Color(111, 82, 128));
        DrawButton(b, this.ArenaRect, "TEST ARENA [RT/T]", new Color(56, 128, 126));
        DrawButton(b, this.ReturnRect, "MINIMIZE [B/Q]", new Color(74, 79, 105));
        DrawButton(b, this.EndLabRect, "END LAB / RESTORE [START]", new Color(120, 75, 82));
        DrawButton(b, this.CloseRect, "RETURN [B/Q]", new Color(68, 64, 79));
    }

    private static void DrawButton(SpriteBatch b, Rectangle rect, string text, Color fill)
    {
        CardchaUi.DrawRoundedPanel(b, rect, fill, Color.White * 0.35f, 2, 7);
        Vector2 size = Game1.smallFont.MeasureString(text);
        float scale = Math.Min(0.96f, (rect.Width - 12f) / Math.Max(1f, size.X));
        b.DrawString(Game1.smallFont, text, new Vector2(rect.Center.X - size.X * scale / 2f, rect.Center.Y - size.Y * scale / 2f), Color.White, 0f, Vector2.Zero, scale, SpriteEffects.None, 1f);
    }

    private void MoveSelection(int delta, bool force = false)
    {
        if (this.Cards.Count == 0 || delta == 0)
            return;

        long now = Environment.TickCount64;
        if (!force && now - this.LastSelectionInputAtMs < SelectionDebounceMs)
            return;

        this.LastSelectionInputAtMs = now;
        this.SelectIndex((this.SelectedIndex + delta + this.Cards.Count) % this.Cards.Count);
    }

    private void SelectIndex(int index)
    {
        if (this.Cards.Count == 0)
            return;

        int next = Math.Clamp(index, 0, this.Cards.Count - 1);
        if (next == this.SelectedIndex)
            return;

        this.SelectedIndex = next;
        this.RequestedLevel = Math.Clamp(this.RequestedLevel, 1, Math.Max(1, this.Selected.MaxLevel));
        Game1.playSound("shiny4");
    }

    private bool TrySelectCardRowAt(int x, int y)
    {
        Rectangle outer = new(this.xPositionOnScreen, this.yPositionOnScreen, this.width, this.height);
        int contentTop = outer.Y + 132;
        int controlsHeight = 144;
        int panelHeight = outer.Bottom - controlsHeight - contentTop;
        int listWidth = Math.Min(546, Math.Max(396, outer.Width / 3));
        Rectangle panel = new(outer.X + 20, contentTop, listWidth, panelHeight);

        if (!panel.Contains(x, y))
            return false;

        const int rowHeight = 51;
        int visible = Math.Max(7, (panel.Height - 20) / rowHeight);
        int start = Math.Clamp(this.SelectedIndex - visible / 2, 0, Math.Max(0, this.Cards.Count - visible));
        int end = Math.Min(this.Cards.Count, start + visible);

        for (int i = start; i < end; i++)
        {
            int row = i - start;
            Rectangle rowRect = new(panel.X + 10, panel.Y + 10 + row * rowHeight, panel.Width - 20, rowHeight - 4);
            if (!rowRect.Contains(x, y))
                continue;

            this.LastSelectionInputAtMs = Environment.TickCount64;
            this.SelectIndex(i);
            return true;
        }

        return false;
    }

    private void ChangeLevel(int delta)
    {
        int max = Math.Max(1, this.Selected.MaxLevel);
        int old = this.RequestedLevel;
        this.RequestedLevel = Math.Clamp(this.RequestedLevel + delta, 1, max);
        if (this.RequestedLevel != old)
            Game1.playSound("smallSelect");
    }

    private void EquipAndPlay()
    {
        this.Lab.PrepareCard(this.Selected, this.RequestedLevel);
        Game1.playSound("discoverMineral");
        this.exitThisMenu();
    }

    private void UnequipAndPlay()
    {
        this.Lab.PrepareBaseline(this.Selected, this.RequestedLevel);
        Game1.playSound("smallSelect");
        this.exitThisMenu();
    }

    private void EnterArenaAndPlay()
    {
        Game1.playSound("wand");
        this.exitThisMenu();
        this.Arena.EnterArena();
    }

    private void ReturnToGame()
    {
        Game1.playSound("smallSelect");
        this.exitThisMenu();
    }

    private void EndLabAndRestore()
    {
        this.Arena.ExitArena();
        this.Lab.EndSession();
        Game1.playSound("bigDeSelect");
        this.exitThisMenu();
    }

    private void RebuildRects()
    {
        int left = this.xPositionOnScreen + 20;
        int available = this.width - 40;
        int gap = 8;
        int row1Y = this.yPositionOnScreen + this.height - 124;
        int row2Y = this.yPositionOnScreen + this.height - 66;

        int x = left;
        this.PrevRect = new Rectangle(x, row1Y, 118, 50); x += 118 + gap;
        this.NextRect = new Rectangle(x, row1Y, 118, 50); x += 118 + gap;
        this.LevelDownRect = new Rectangle(x, row1Y, 88, 50); x += 88 + gap;
        this.LevelUpRect = new Rectangle(x, row1Y, 88, 50); x += 88 + gap;
        this.EquipRect = new Rectangle(x, row1Y, 198, 50); x += 198 + gap;
        this.UnequipRect = new Rectangle(x, row1Y, 218, 50); x += 218 + gap;
        this.ResetRect = new Rectangle(x, row1Y, Math.Max(168, Math.Min(228, left + available - x)), 50);

        x = left;
        this.PassRect = new Rectangle(x, row2Y, 108, 50); x += 108 + gap;
        this.FailRect = new Rectangle(x, row2Y, 108, 50); x += 108 + gap;
        this.HpFullRect = new Rectangle(x, row2Y, 116, 50); x += 116 + gap;
        this.HpLowRect = new Rectangle(x, row2Y, 110, 50); x += 110 + gap;
        this.DummyFullRect = new Rectangle(x, row2Y, 170, 50); x += 170 + gap;
        this.DummyLowRect = new Rectangle(x, row2Y, 166, 50); x += 166 + gap;
        this.ArenaRect = new Rectangle(x, row2Y, 164, 50); x += 164 + gap;
        this.ReturnRect = new Rectangle(x, row2Y, 148, 50); x += 148 + gap;
        this.EndLabRect = new Rectangle(x, row2Y, Math.Max(198, Math.Min(258, left + available - x)), 50);

        this.CloseRect = new Rectangle(this.xPositionOnScreen + this.width - 164, this.yPositionOnScreen + 18, 142, 42);
    }

    private static string GetSelectedLevelText(CardDefinition card, int level)
    {
        int max = Math.Max(1, card.MaxLevel);
        int selected = Math.Clamp(level, 1, max);
        if (card.StarRules is not null && card.StarRules.Count >= selected)
        {
            string rule = card.StarRules[selected - 1];
            if (!string.IsNullOrWhiteSpace(rule))
                return $"★{selected}: {rule}";
        }

        return card.Description;
    }

    private static void DrawWrapped(SpriteBatch b, SpriteFont font, string text, Rectangle area, Color color, float scale, int maxLines)
    {
        if (string.IsNullOrWhiteSpace(text))
            return;

        List<string> lines = new();
        foreach (string paragraph in text.Replace("\r", "").Split('\n'))
        {
            string current = "";
            foreach (string word in paragraph.Split(' ', StringSplitOptions.RemoveEmptyEntries))
            {
                string candidate = string.IsNullOrEmpty(current) ? word : current + " " + word;
                if (font.MeasureString(candidate).X * scale <= area.Width || string.IsNullOrEmpty(current))
                    current = candidate;
                else
                {
                    lines.Add(current);
                    current = word;
                    if (lines.Count >= maxLines)
                        break;
                }
            }
            if (lines.Count >= maxLines)
                break;
            if (!string.IsNullOrEmpty(current))
                lines.Add(current);
        }

        float lineHeight = font.LineSpacing * scale;
        for (int i = 0; i < Math.Min(maxLines, lines.Count); i++)
            b.DrawString(font, lines[i], new Vector2(area.X, area.Y + i * lineHeight), color, 0f, Vector2.Zero, scale, SpriteEffects.None, 1f);
    }

    private static void DrawClippedText(SpriteBatch b, SpriteFont font, string text, Rectangle area, Color color, float scale)
    {
        string value = text;
        while (value.Length > 3 && font.MeasureString(value).X * scale > area.Width)
            value = value[..^2];
        if (!string.Equals(value, text, StringComparison.Ordinal) && value.Length > 3)
            value = value[..Math.Max(1, value.Length - 1)] + "…";
        b.DrawString(font, value, new Vector2(area.X, area.Y), color, 0f, Vector2.Zero, scale, SpriteEffects.None, 1f);
    }
}

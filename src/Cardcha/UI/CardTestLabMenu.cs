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
/// Nothing in this menu is persisted to SaveData; CardTestLabService restores the real loadout on exit.
/// </summary>
internal sealed class CardTestLabMenu : IClickableMenu
{
    private readonly CardTestLabService Lab;
    private readonly CardRenderer Renderer;
    private readonly IReadOnlyList<CardDefinition> Cards;

    private int SelectedIndex;
    private int RequestedLevel = 1;

    private Rectangle PrevRect;
    private Rectangle NextRect;
    private Rectangle LevelDownRect;
    private Rectangle LevelUpRect;
    private Rectangle PrepareRect;
    private Rectangle PassRect;
    private Rectangle FailRect;
    private Rectangle ResetRect;
    private Rectangle HpFullRect;
    private Rectangle HpLowRect;
    private Rectangle CloseRect;

    public CardTestLabMenu(CardTestLabService lab, CardRenderer renderer)
        : base(
            x: Math.Max(32, (Game1.uiViewport.Width - 1180) / 2),
            y: Math.Max(24, (Game1.uiViewport.Height - 760) / 2),
            width: Math.Min(1180, Game1.uiViewport.Width - 64),
            height: Math.Min(760, Game1.uiViewport.Height - 48),
            showUpperRightCloseButton: false)
    {
        this.Lab = lab;
        this.Renderer = renderer;
        this.Cards = lab.ActiveCards;
        this.Lab.BeginSession();
        this.RebuildRects();
    }

    private CardDefinition Selected => this.Cards[Math.Clamp(this.SelectedIndex, 0, Math.Max(0, this.Cards.Count - 1))];

    public override void receiveKeyPress(Keys key)
    {
        if (key is Keys.Escape or Keys.Q)
        {
            this.CloseLab();
            return;
        }

        switch (key)
        {
            case Keys.Left:
            case Keys.A:
                this.MoveSelection(-1);
                return;
            case Keys.Right:
            case Keys.D:
                this.MoveSelection(1);
                return;
            case Keys.Up:
            case Keys.W:
                this.ChangeLevel(1);
                return;
            case Keys.Down:
            case Keys.S:
                this.ChangeLevel(-1);
                return;
            case Keys.Enter:
            case Keys.Space:
                this.PrepareSelected();
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
        }

        base.receiveKeyPress(key);
    }

    public override void receiveGamePadButton(Buttons b)
    {
        switch (b)
        {
            case Buttons.B:
                this.CloseLab();
                return;
            case Buttons.DPadLeft:
            case Buttons.LeftThumbstickLeft:
                this.MoveSelection(-1);
                return;
            case Buttons.DPadRight:
            case Buttons.LeftThumbstickRight:
                this.MoveSelection(1);
                return;
            case Buttons.DPadUp:
                this.ChangeLevel(1);
                return;
            case Buttons.DPadDown:
                this.ChangeLevel(-1);
                return;
            case Buttons.A:
                this.PrepareSelected();
                return;
            case Buttons.X:
                this.Lab.SetVerdict(this.Selected, CardLabVerdict.Pass);
                Game1.playSound("coin");
                return;
            case Buttons.Y:
                this.Lab.SetVerdict(this.Selected, CardLabVerdict.Fail);
                Game1.playSound("cancel");
                return;
            case Buttons.RightShoulder:
                this.Lab.ResetTelemetry();
                Game1.playSound("smallSelect");
                return;
            case Buttons.LeftShoulder:
                this.Lab.SetHealthPercent(0.19);
                return;
        }

        base.receiveGamePadButton(b);
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        if (this.PrevRect.Contains(x, y)) this.MoveSelection(-1);
        else if (this.NextRect.Contains(x, y)) this.MoveSelection(1);
        else if (this.LevelDownRect.Contains(x, y)) this.ChangeLevel(-1);
        else if (this.LevelUpRect.Contains(x, y)) this.ChangeLevel(1);
        else if (this.PrepareRect.Contains(x, y)) this.PrepareSelected();
        else if (this.PassRect.Contains(x, y)) this.Lab.SetVerdict(this.Selected, CardLabVerdict.Pass);
        else if (this.FailRect.Contains(x, y)) this.Lab.SetVerdict(this.Selected, CardLabVerdict.Fail);
        else if (this.ResetRect.Contains(x, y)) this.Lab.ResetTelemetry();
        else if (this.HpFullRect.Contains(x, y)) this.Lab.SetHealthPercent(1.0);
        else if (this.HpLowRect.Contains(x, y)) this.Lab.SetHealthPercent(0.19);
        else if (this.CloseRect.Contains(x, y)) this.CloseLab();
    }

    public override void gameWindowSizeChanged(Rectangle oldBounds, Rectangle newBounds)
    {
        this.xPositionOnScreen = Math.Max(32, (Game1.uiViewport.Width - this.width) / 2);
        this.yPositionOnScreen = Math.Max(24, (Game1.uiViewport.Height - this.height) / 2);
        this.RebuildRects();
        base.gameWindowSizeChanged(oldBounds, newBounds);
    }

    public override void cleanupBeforeExit()
    {
        this.Lab.EndSession();
        base.cleanupBeforeExit();
    }

    public override void draw(SpriteBatch b)
    {
        b.Draw(Game1.fadeToBlackRect, Game1.uiViewport.Bounds, Color.Black * 0.72f);

        Rectangle outer = new(this.xPositionOnScreen, this.yPositionOnScreen, this.width, this.height);
        CardchaUi.DrawRoundedPanel(b, outer, new Color(32, 30, 47), new Color(174, 139, 224), 4, 16);

        string title = "CARDCHA CARD TEST LAB  •  BASE SET 76";
        Vector2 titleSize = Game1.dialogueFont.MeasureString(title);
        b.DrawString(Game1.dialogueFont, title, new Vector2(outer.Center.X - titleSize.X / 2f, outer.Y + 18), Color.White);

        (int pass, int fail, int untested) = this.Lab.GetVerdictCounts();
        string progress = $"PASS {pass}   FAIL {fail}   UNTESTED {untested}";
        Vector2 progressSize = Game1.smallFont.MeasureString(progress);
        b.DrawString(Game1.smallFont, progress, new Vector2(outer.Center.X - progressSize.X / 2f, outer.Y + 63), new Color(224, 213, 244));

        int contentTop = outer.Y + 100;
        Rectangle listPanel = new(outer.X + 20, contentTop, Math.Min(400, outer.Width / 3), outer.Height - 190);
        Rectangle detailPanel = new(listPanel.Right + 16, contentTop, outer.Right - listPanel.Right - 36, outer.Height - 190);
        CardchaUi.DrawRoundedPanel(b, listPanel, new Color(47, 44, 64), new Color(105, 91, 139), 2, 10);
        CardchaUi.DrawRoundedPanel(b, detailPanel, new Color(43, 40, 59), new Color(105, 91, 139), 2, 10);

        this.DrawCardList(b, listPanel);
        this.DrawSelectedDetail(b, detailPanel);
        this.DrawButtons(b);

        drawMouse(b);
    }

    private void DrawCardList(SpriteBatch b, Rectangle panel)
    {
        int rowHeight = 36;
        int visible = Math.Max(8, (panel.Height - 24) / rowHeight);
        int start = Math.Clamp(this.SelectedIndex - visible / 2, 0, Math.Max(0, this.Cards.Count - visible));
        int end = Math.Min(this.Cards.Count, start + visible);

        for (int i = start; i < end; i++)
        {
            CardDefinition card = this.Cards[i];
            int row = i - start;
            Rectangle r = new(panel.X + 10, panel.Y + 10 + row * rowHeight, panel.Width - 20, rowHeight - 3);
            bool selected = i == this.SelectedIndex;
            if (selected)
                b.Draw(Game1.staminaRect, r, new Color(92, 75, 126));

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

            b.DrawString(Game1.smallFont, marker, new Vector2(r.X + 8, r.Y + 5), markerColor, 0f, Vector2.Zero, 0.75f, SpriteEffects.None, 1f);
            string label = $"#{card.StableBaseId:00}  {card.Name}";
            DrawClippedText(b, Game1.smallFont, label, new Rectangle(r.X + 66, r.Y + 3, r.Width - 72, r.Height - 4), Color.White, 0.78f);
        }
    }

    private void DrawSelectedDetail(SpriteBatch b, Rectangle panel)
    {
        CardDefinition card = this.Selected;
        CardLabVerdict verdict = this.Lab.GetVerdict(card);

        Rectangle icon = new(panel.X + 18, panel.Y + 18, 112, 112);
        this.Renderer.DrawIcon(b, icon, card);
        CardchaUi.DrawBorder(b, icon, CardchaUi.RarityColor(card.Rarity), 3);

        float nameX = icon.Right + 16;
        DrawClippedText(b, Game1.dialogueFont, $"#{card.StableBaseId:00} {card.Name}", new Rectangle((int)nameX, panel.Y + 18, panel.Right - (int)nameX - 18, 48), Color.White, 0.78f);
        b.DrawString(Game1.smallFont, $"Rarity: {card.Rarity}   EffectKey: {card.EffectKey}", new Vector2(nameX, panel.Y + 68), new Color(206, 196, 225), 0f, Vector2.Zero, 0.78f, SpriteEffects.None, 1f);
        b.DrawString(Game1.smallFont, $"TEST LEVEL: {this.RequestedLevel}/{Math.Max(1, card.MaxLevel)}", new Vector2(nameX, panel.Y + 97), new Color(255, 218, 116), 0f, Vector2.Zero, 0.9f, SpriteEffects.None, 1f);

        string verdictText = verdict == CardLabVerdict.Untested ? "UNTESTED" : verdict.ToString().ToUpperInvariant();
        Color verdictColor = verdict switch
        {
            CardLabVerdict.Pass => new Color(122, 221, 153),
            CardLabVerdict.Fail => new Color(240, 118, 130),
            _ => new Color(190, 183, 206)
        };
        b.DrawString(Game1.smallFont, verdictText, new Vector2(panel.Right - 105, panel.Y + 103), verdictColor, 0f, Vector2.Zero, 0.8f, SpriteEffects.None, 1f);

        Rectangle descriptionArea = new(panel.X + 18, panel.Y + 145, panel.Width - 36, 92);
        DrawWrapped(b, Game1.smallFont, card.Description, descriptionArea, new Color(241, 234, 220), 0.78f, maxLines: 4);

        b.DrawString(Game1.smallFont, "WHAT TO DO / CÁCH TEST", new Vector2(panel.X + 18, panel.Y + 245), new Color(255, 218, 116), 0f, Vector2.Zero, 0.82f, SpriteEffects.None, 1f);
        Rectangle instructionArea = new(panel.X + 18, panel.Y + 275, panel.Width - 36, 76);
        DrawWrapped(b, Game1.smallFont, this.Lab.BuildInstruction(card), instructionArea, Color.White, 0.76f, maxLines: 3);

        b.DrawString(Game1.smallFont, "LIVE TELEMETRY", new Vector2(panel.X + 18, panel.Y + 360), new Color(145, 214, 255), 0f, Vector2.Zero, 0.82f, SpriteEffects.None, 1f);
        Rectangle telemetryArea = new(panel.X + 18, panel.Y + 390, panel.Width - 36, panel.Bottom - (panel.Y + 404));
        DrawWrapped(b, Game1.smallFont, this.Lab.BuildTelemetry(card), telemetryArea, new Color(215, 230, 239), 0.67f, maxLines: 11);
    }

    private void DrawButtons(SpriteBatch b)
    {
        DrawButton(b, this.PrevRect, "◀ CARD", new Color(73, 67, 97));
        DrawButton(b, this.NextRect, "CARD ▶", new Color(73, 67, 97));
        DrawButton(b, this.LevelDownRect, "LV -", new Color(88, 73, 105));
        DrawButton(b, this.LevelUpRect, "LV +", new Color(88, 73, 105));
        DrawButton(b, this.PrepareRect, "PREPARE / EQUIP", new Color(89, 111, 184));
        DrawButton(b, this.PassRect, "PASS [X/P]", new Color(57, 137, 92));
        DrawButton(b, this.FailRect, "FAIL [Y/F]", new Color(155, 62, 75));
        DrawButton(b, this.ResetRect, "RESET TELEMETRY", new Color(86, 86, 102));
        DrawButton(b, this.HpFullRect, "HP 100%", new Color(69, 111, 96));
        DrawButton(b, this.HpLowRect, "HP 19%", new Color(145, 91, 78));
        DrawButton(b, this.CloseRect, "CLOSE [B/Q]", new Color(68, 64, 79));
    }

    private static void DrawButton(SpriteBatch b, Rectangle rect, string text, Color fill)
    {
        CardchaUi.DrawRoundedPanel(b, rect, fill, Color.White * 0.35f, 2, 7);
        Vector2 size = Game1.smallFont.MeasureString(text);
        float scale = Math.Min(0.78f, (rect.Width - 12f) / Math.Max(1f, size.X));
        b.DrawString(Game1.smallFont, text, new Vector2(rect.Center.X - size.X * scale / 2f, rect.Center.Y - size.Y * scale / 2f), Color.White, 0f, Vector2.Zero, scale, SpriteEffects.None, 1f);
    }

    private void MoveSelection(int delta)
    {
        if (this.Cards.Count == 0)
            return;
        this.SelectedIndex = (this.SelectedIndex + delta + this.Cards.Count) % this.Cards.Count;
        this.RequestedLevel = Math.Clamp(this.RequestedLevel, 1, Math.Max(1, this.Selected.MaxLevel));
        Game1.playSound("shiny4");
    }

    private void ChangeLevel(int delta)
    {
        int max = Math.Max(1, this.Selected.MaxLevel);
        this.RequestedLevel = Math.Clamp(this.RequestedLevel + delta, 1, max);
        Game1.playSound("smallSelect");
    }

    private void PrepareSelected()
    {
        this.Lab.PrepareCard(this.Selected, this.RequestedLevel);
        Game1.playSound("discoverMineral");
    }

    private void CloseLab()
    {
        this.Lab.EndSession();
        this.exitThisMenu();
    }

    private void RebuildRects()
    {
        int y = this.yPositionOnScreen + this.height - 72;
        int x = this.xPositionOnScreen + 20;
        this.PrevRect = new Rectangle(x, y, 88, 42); x += 94;
        this.NextRect = new Rectangle(x, y, 88, 42); x += 94;
        this.LevelDownRect = new Rectangle(x, y, 62, 42); x += 68;
        this.LevelUpRect = new Rectangle(x, y, 62, 42); x += 68;
        this.PrepareRect = new Rectangle(x, y, 150, 42); x += 156;
        this.PassRect = new Rectangle(x, y, 105, 42); x += 111;
        this.FailRect = new Rectangle(x, y, 105, 42); x += 111;
        this.ResetRect = new Rectangle(x, y, 138, 42); x += 144;
        this.HpFullRect = new Rectangle(x, y, 86, 42); x += 92;
        this.HpLowRect = new Rectangle(x, y, 82, 42);
        this.CloseRect = new Rectangle(this.xPositionOnScreen + this.width - 142, this.yPositionOnScreen + 20, 122, 38);
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

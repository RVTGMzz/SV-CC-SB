from pathlib import Path

p = Path('src/Cardcha/UI/CardTestLabMenu.cs')
s = p.read_text(encoding='utf-8')

def once(old: str, new: str):
    global s
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'missing anchor: {old[:160]!r}')
    s = s.replace(old, new, 1)

once(
'''        (int pass, int fail, int untested) = this.Lab.GetVerdictCounts();
        string progress = $"PASS {pass}   FAIL {fail}   UNTESTED {untested}   •   ONE CARD AT A TIME";
        Vector2 progressSize = Game1.smallFont.MeasureString(progress);
        b.DrawString(Game1.smallFont, progress, new Vector2(outer.Center.X - progressSize.X * 0.9f / 2f, outer.Y + 60), new Color(224, 213, 244), 0f, Vector2.Zero, 0.9f, SpriteEffects.None, 1f);

        string guide = "↑↓ CHỌN LÁ   •   ←→ LEVEL   •   A EQUIP   •   X BASELINE   •   RT VÀO ARENA   •   B THU NHỎ   •   F8 / R-STICK MỞ LẠI";
        Vector2 guideSize = Game1.smallFont.MeasureString(guide);
        float guideScale = Math.Min(0.86f, (outer.Width - 80f) / Math.Max(1f, guideSize.X));
        b.DrawString(Game1.smallFont, guide, new Vector2(outer.Center.X - guideSize.X * guideScale / 2f, outer.Y + 91), new Color(255, 218, 116), 0f, Vector2.Zero, guideScale, SpriteEffects.None, 1f);

        int contentTop = outer.Y + 132;
''',
'''        (int pass, int fail, int untested) = this.Lab.GetVerdictCounts();
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
''')

once(
'''        CardDefinition card = this.Selected;
        CardLabVerdict verdict = this.Lab.GetVerdict(card);

        Rectangle icon = new(panel.X + 20, panel.Y + 20, 128, 128);
''',
'''        CardDefinition card = this.Selected;
        CardLabVerdict verdict = this.Lab.GetVerdict(card);
        CardAutoAuditEntry autoAudit = GeneratedCardAutoAudit.Get(card);

        Rectangle icon = new(panel.X + 20, panel.Y + 20, 128, 128);
''')

old_detail = '''        bool selectedEquipped = this.Lab.IsSelectedCardEquipped(card);
        string runState = selectedEquipped
            ? "ACTIVE TEST: EQUIPPED"
            : this.Lab.IsSessionActive && this.Lab.ActiveCardId.Equals(card.Id, StringComparison.OrdinalIgnoreCase)
                ? "ACTIVE TEST: BASELINE / UNEQUIPPED"
                : "SELECTED / NOT PREPARED";
        Color runColor = selectedEquipped ? new Color(122, 221, 153) : new Color(145, 214, 255);
        b.DrawString(Game1.smallFont, runState, new Vector2(nameX, panel.Y + 136), runColor, 0f, Vector2.Zero, 0.94f, SpriteEffects.None, 1f);

        string verdictText = verdict == CardLabVerdict.Untested ? "UNTESTED" : verdict.ToString().ToUpperInvariant();
        Color verdictColor = verdict switch
        {
            CardLabVerdict.Pass => new Color(122, 221, 153),
            CardLabVerdict.Fail => new Color(240, 118, 130),
            _ => new Color(190, 183, 206)
        };
        b.DrawString(Game1.smallFont, verdictText, new Vector2(panel.Right - 125, panel.Y + 110), verdictColor, 0f, Vector2.Zero, 0.98f, SpriteEffects.None, 1f);

        Rectangle descriptionArea = new(panel.X + 20, panel.Y + 168, panel.Width - 40, 68);
        DrawWrapped(b, Game1.smallFont, card.Description, descriptionArea, new Color(241, 234, 220), 0.98f, maxLines: 4);

        b.DrawString(Game1.smallFont, "WHAT TO DO / CÁCH TEST", new Vector2(panel.X + 20, panel.Y + 244), new Color(255, 218, 116), 0f, Vector2.Zero, 1.02f, SpriteEffects.None, 1f);
        Rectangle instructionArea = new(panel.X + 20, panel.Y + 278, panel.Width - 40, 74);
        DrawWrapped(b, Game1.smallFont, this.Lab.BuildInstruction(card), instructionArea, Color.White, 0.96f, maxLines: 4);

        b.DrawString(Game1.smallFont, "LIVE TELEMETRY / KẾT QUẢ THỰC TẾ", new Vector2(panel.X + 20, panel.Y + 360), new Color(145, 214, 255), 0f, Vector2.Zero, 1.02f, SpriteEffects.None, 1f);
        Rectangle telemetryArea = new(panel.X + 20, panel.Y + 396, panel.Width - 40, Math.Max(70, panel.Bottom - (panel.Y + 408)));
        DrawWrapped(b, Game1.smallFont, this.Lab.BuildTelemetry(card), telemetryArea, new Color(215, 230, 239), 0.90f, maxLines: 12);
'''
new_detail = '''        Color autoColor = autoAudit.Status switch
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
'''
once(old_detail, new_detail)

s = s.replace('DrawButton(b, this.PassRect, "PASS [Y/P]",', 'DrawButton(b, this.PassRect, "MANUAL PASS [Y/P]",')
s = s.replace('DrawButton(b, this.FailRect, "FAIL [RB/F]",', 'DrawButton(b, this.FailRect, "MANUAL FAIL [RB/F]",')

if '    private static string GetSelectedLevelText(CardDefinition card, int level)\n' not in s:
    anchor = '    private static void DrawWrapped(SpriteBatch b, SpriteFont font, string text, Rectangle area, Color color, float scale, int maxLines)\n'
    helper = '''    private static string GetSelectedLevelText(CardDefinition card, int level)
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

'''
    if anchor not in s:
        raise SystemExit('missing DrawWrapped anchor')
    s = s.replace(anchor, helper + anchor, 1)

p.write_text(s, encoding='utf-8')
print('Applied Card Test Lab auto-contract + per-level UI')

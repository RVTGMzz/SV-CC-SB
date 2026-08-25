from pathlib import Path
import hashlib

ROOT = Path('src/Cardcha')


def replace(rel, old, new):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'alpha.10 pattern missing in {rel}: {old[:120]!r}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


# The player-approved RAR contains this exact 128x192 MiMi walking sheet.
# Keep it as the canonical world-walk asset and fail the build if it is accidentally replaced.
walk = ROOT / 'assets/mimi_walk.png'
expected_walk_sha256 = '79a2ddd16e423c5052231a00a3b609585286eefc21551f5f1136c72a7efa0c5a'
actual_walk_sha256 = hashlib.sha256(walk.read_bytes()).hexdigest()
if actual_walk_sha256 != expected_walk_sha256:
    raise SystemExit(f'approved MiMi walk sheet mismatch: {actual_walk_sha256}')

# The approved sheet has four deliberately different frames per direction. Alpha.9 skipped frame 0
# while moving (1->2->3->1), which made the feet read like sliding. Play all four frames in order.
replace(
    'Services/MimiMysteryTownService.cs',
    '        int walkFrame = 1 + (int)(now / 170L) % 3;\n',
    '        int walkFrame = (int)(now / 155L) % 4;\n'
)

# Boss slot is intentionally only a visual teaser in this build. Keep it locked regardless of
# collection count until the actual Boss Card gameplay lands in a later version.
replace(
    'UI/CardchaBinderMenuV2.cs',
    '    private bool BossSlotUnlocked => this.Save.Data.OwnedCards.Count >= BossUnlockMilestone;\n',
    '    private bool BossSlotUnlocked => false;\n'
)
replace(
    'UI/CardchaBinderMenuV2.cs',
'''        if (this.BossSlotButton.containsPoint(x, y))
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
''',
'''        if (this.BossSlotButton.containsPoint(x, y))
        {
            this.Status = ModEntry.T("binder.slot.locked");
            Game1.playSound("cancel");
            return;
        }
'''
)
replace(
    'UI/CardchaBinderMenuV2.cs',
'''            this.BossSlotUnlocked ? "BOSS" : ModEntry.T("binder.boss.short", new { cards = BossUnlockMilestone }),''',
'''            ModEntry.T("binder.slot.locked"),'''
)

# Alpha.9 already lifted the general scale ceiling. The player asked for another 1.5x pass because
# the book still has generous whitespace, so raise both single-line and wrapped ceilings again.
replace(
    'UI/CardchaUi.cs',
    '        float requestedScale = Math.Max(0.25f, maxScale * 1.50f);\n',
    '        float requestedScale = Math.Max(0.25f, maxScale * 2.25f);\n'
)
replace(
    'UI/CardchaUi.cs',
    '        float startScale = Math.Max(minScale, maxScale * 1.45f);\n',
    '        float startScale = Math.Max(minScale, maxScale * 2.175f);\n'
)

# The scrollable detail body was still drawn at native 1.0 scale and therefore ignored the global
# typography pass. Draw it at 1.5x and wrap using the corresponding logical width.
replace(
    'UI/CardchaUi.cs',
'''        string wrapped = Game1.parseText(
            text ?? string.Empty,
            font,
            Math.Max(24, width)
        );

        int lines = Math.Clamp(
            wrapped.Replace("\\r", "").Split('\\n').Length,
            Math.Max(1, minimumLines),
            Math.Max(minimumLines, maximumLines)
        );

        return lines * (font.LineSpacing + 2);''',
'''        const float textScale = 1.50f;
        int logicalWidth = Math.Max(24, (int)Math.Floor(width / textScale));
        string wrapped = Game1.parseText(
            text ?? string.Empty,
            font,
            logicalWidth
        );

        int lines = Math.Clamp(
            wrapped.Replace("\\r", "").Split('\\n').Length,
            Math.Max(1, minimumLines),
            Math.Max(minimumLines, maximumLines)
        );

        return (int)Math.Ceiling(lines * (font.LineSpacing + 2) * textScale);'''
)
replace(
    'UI/CardchaUi.cs',
'''        string wrapped = Game1.parseText(
            text ?? string.Empty,
            font,
            Math.Max(24, area.Width)
        );

        string[] lines = wrapped
            .Replace("\\r", "")
            .Split('\\n')
            .Take(Math.Max(1, maximumLines))
            .ToArray();

        int lineHeight = font.LineSpacing + 2;
        int y = area.Y;

        foreach (string line in lines)
        {
            Rectangle lineRect = new(
                area.X,
                y,
                area.Width,
                lineHeight
            );

            // Keep the font at its native readable size.
            // Only lines which are fully inside the scroll viewport are drawn.
            if (lineRect.Top >= clip.Top && lineRect.Bottom <= clip.Bottom)
            {
                Utility.drawTextWithShadow(
                    b,
                    line,
                    font,
                    new Vector2(area.X, y),
                    color
                );
            }

            y += lineHeight;
        }''',
'''        const float textScale = 1.50f;
        int logicalWidth = Math.Max(24, (int)Math.Floor(area.Width / textScale));
        string wrapped = Game1.parseText(
            text ?? string.Empty,
            font,
            logicalWidth
        );

        string[] lines = wrapped
            .Replace("\\r", "")
            .Split('\\n')
            .Take(Math.Max(1, maximumLines))
            .ToArray();

        int lineHeight = (int)Math.Ceiling((font.LineSpacing + 2) * textScale);
        int y = area.Y;

        foreach (string line in lines)
        {
            Rectangle lineRect = new(
                area.X,
                y,
                area.Width,
                lineHeight
            );

            if (lineRect.Top >= clip.Top && lineRect.Bottom <= clip.Bottom)
            {
                b.DrawString(
                    font,
                    line,
                    new Vector2(area.X, y),
                    color,
                    0f,
                    Vector2.Zero,
                    textScale,
                    SpriteEffects.None,
                    1f
                );
            }

            y += lineHeight;
        }'''
)

# Card names use their own bottom-aligned renderer, so give them the same larger type treatment.
replace(
    'UI/CardRenderer.cs',
    '        Rectangle nameArea = new(rect.X + 5, rect.Bottom - 42, rect.Width - 10, 34);\n',
    '        Rectangle nameArea = new(rect.X + 5, rect.Bottom - 52, rect.Width - 10, 44);\n'
)
replace(
    'UI/CardRenderer.cs',
    '        Rectangle nameArea = new(rect.X + 4, rect.Bottom - 31, rect.Width - 8, 24);\n',
    '        Rectangle nameArea = new(rect.X + 4, rect.Bottom - 39, rect.Width - 8, 32);\n'
)
replace(
    'UI/CardRenderer.cs',
    '        for (float scale = maxScale; scale >= minScale; scale -= 0.04f)\n',
    '        for (float scale = maxScale * 1.50f; scale >= minScale; scale -= 0.04f)\n'
)

# One clean test-package version.
for rel in ('Cardcha.csproj', 'manifest.json'):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if '0.2.0-alpha.9' not in text:
        raise SystemExit(f'alpha.9 version missing in {rel}')
    path.write_text(text.replace('0.2.0-alpha.9', '0.2.0-alpha.10'), encoding='utf-8')

print('alpha.10: approved MiMi walk cycle, permanently locked Boss teaser, larger unified binder typography')

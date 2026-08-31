
using Cardcha.Models;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

internal static class CardchaUi
{
    public static readonly Color PanelDark = new(69, 47, 61);
    public static readonly Color StandardBlue = new(50, 118, 164);
    public static readonly Color PremiumPurple = new(129, 70, 160);
    public static readonly Color GoodGreen = new(88, 146, 70);
    public static readonly Color DangerRed = new(176, 68, 49);
    public static readonly Color Gold = new(229, 166, 62);
    public static readonly Color LeatherDark = new(67, 39, 36);
    public static readonly Color Leather = new(112, 66, 50);
    public static readonly Color LeatherLight = new(147, 91, 62);
    public static readonly Color Parchment = new(242, 211, 159);
    public static readonly Color ParchmentLight = new(255, 228, 179);
    public static readonly Color PaperShadow = new(196, 153, 104);
    public static readonly Color InkBrown = new(78, 49, 43);


    public static void DrawRoundedPanel(SpriteBatch b, Rectangle rect, Color fill, Color border, int thickness = 3, int radius = 10)
    {
        thickness = Math.Max(1, thickness);
        DrawRoundedRect(b, rect, border, radius);
        Rectangle inner = new(rect.X + thickness, rect.Y + thickness, Math.Max(1, rect.Width - thickness * 2), Math.Max(1, rect.Height - thickness * 2));
        DrawRoundedRect(b, inner, fill, Math.Max(2, radius - thickness));
    }

    public static void DrawRoundedRect(SpriteBatch b, Rectangle rect, Color color, int radius = 10)
    {
        if (rect.Width <= 0 || rect.Height <= 0)
            return;

        radius = Math.Clamp(radius, 1, Math.Max(1, Math.Min(rect.Width, rect.Height) / 2));
        int horizontalWidth = Math.Max(1, rect.Width - radius * 2);
        int verticalHeight = Math.Max(1, rect.Height - radius * 2);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X + radius, rect.Y, horizontalWidth, rect.Height), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y + radius, rect.Width, verticalHeight), color);

        DrawRoundedQuarter(b, new Point(rect.X + radius, rect.Y + radius), radius, color, 0);
        DrawRoundedQuarter(b, new Point(rect.Right - radius - 1, rect.Y + radius), radius, color, 1);
        DrawRoundedQuarter(b, new Point(rect.X + radius, rect.Bottom - radius - 1), radius, color, 2);
        DrawRoundedQuarter(b, new Point(rect.Right - radius - 1, rect.Bottom - radius - 1), radius, color, 3);
    }

    private static void DrawRoundedQuarter(SpriteBatch b, Point center, int radius, Color color, int quadrant)
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

    public static Color RarityColor(CardRarity rarity) => rarity switch
    {
        CardRarity.Common => new Color(170, 170, 170),
        CardRarity.Rare => new Color(72, 168, 221),
        CardRarity.Epic => new Color(176, 86, 202),
        CardRarity.Legendary => new Color(255, 179, 50),
        CardRarity.Mythic => new Color(96, 230, 190),
        _ => Color.White
    };

    public static string RarityText(CardRarity rarity)
        => ModEntry.T($"rarity.{rarity.ToString().ToLowerInvariant()}");

    public static void DrawFocus(SpriteBatch b, Rectangle rect)
    {
        Rectangle glow = new(rect.X - 5, rect.Y - 5, rect.Width + 10, rect.Height + 10);
        Rectangle outer = new(rect.X - 3, rect.Y - 3, rect.Width + 6, rect.Height + 6);

        DrawBorder(b, glow, Gold * 0.55f, 2);
        DrawBorder(b, outer, Color.White * 0.90f, 2);
        DrawBorder(b, rect, Gold, 2);
    }

    public static void DrawButton(
        SpriteBatch b,
        ClickableComponent button,
        string text,
        Color fill,
        bool enabled = true,
        float textScale = 1.18f,
        int textPadding = 8)
    {
        Point mouse = GetUiMousePoint();
        bool hovered = enabled && button.bounds.Contains(mouse.X, mouse.Y);

        Color color;
        Color border;
        Color ink;

        if (!enabled)
        {
            color = new Color(118, 113, 110);
            border = new Color(76, 72, 70);
            ink = new Color(220, 216, 209);
        }
        else if (hovered)
        {
            color = Lighten(fill, 0.15f);
            border = Gold;
            ink = Color.White;
        }
        else
        {
            color = fill;
            border = Color.Black * 0.55f;
            ink = Color.White;
        }

        b.Draw(Game1.staminaRect, button.bounds, color);
        DrawBorder(b, button.bounds, border, hovered ? 4 : 3);

        Rectangle topHighlight = new(
            button.bounds.X + 4,
            button.bounds.Y + 4,
            Math.Max(0, button.bounds.Width - 8),
            2
        );
        b.Draw(Game1.staminaRect, topHighlight, enabled ? Color.White * 0.20f : Color.White * 0.08f);

        DrawScaledText(
            b,
            Game1.smallFont,
            text,
            button.bounds,
            ink,
            centerX: true,
            centerY: true,
            padding: textPadding,
            maxScale: textScale
        );
    }

    public static void DrawBookFrame(SpriteBatch b, Rectangle outer)
    {
        b.Draw(Game1.staminaRect, outer, LeatherDark);
        DrawBorder(b, outer, new Color(43, 27, 29), 5);

        Rectangle leather = new(outer.X + 6, outer.Y + 6, outer.Width - 12, outer.Height - 12);
        b.Draw(Game1.staminaRect, leather, Leather);
        DrawBorder(b, leather, Gold * 0.78f, 3);

        Rectangle page = new(outer.X + 22, outer.Y + 20, outer.Width - 44, outer.Height - 38);
        b.Draw(Game1.staminaRect, page, Parchment);
        DrawBorder(b, page, PaperShadow, 3);

        b.Draw(Game1.staminaRect, new Rectangle(page.X + 4, page.Y + 4, page.Width - 8, 3), ParchmentLight * 0.8f);
        b.Draw(Game1.staminaRect, new Rectangle(page.X + 4, page.Bottom - 7, page.Width - 8, 3), PaperShadow * 0.55f);

        for (int x = outer.X + 18; x < outer.Right - 18; x += 18)
        {
            b.Draw(Game1.staminaRect, new Rectangle(x, outer.Y + 11, 8, 2), ParchmentLight * 0.65f);
            b.Draw(Game1.staminaRect, new Rectangle(x, outer.Bottom - 13, 8, 2), ParchmentLight * 0.45f);
        }

        int ringX = outer.X + 11;
        for (int y = outer.Y + 118; y < outer.Bottom - 76; y += 94)
        {
            b.Draw(Game1.staminaRect, new Rectangle(ringX, y, 20, 7), new Color(45, 39, 43));
            b.Draw(Game1.staminaRect, new Rectangle(ringX + 3, y + 1, 14, 3), new Color(183, 161, 132));
            b.Draw(Game1.staminaRect, new Rectangle(ringX + 5, y + 4, 10, 2), Gold * 0.55f);
        }
    }

    public static void DrawNotebookTab(SpriteBatch b, ClickableComponent button, string text, bool active = false)
    {
        Rectangle r = button.bounds;
        Point mouse = GetUiMousePoint();
        bool hovered = r.Contains(mouse.X, mouse.Y);

        Color fill = active
            ? ParchmentLight
            : hovered
                ? Lighten(LeatherDark, 0.14f)
                : LeatherDark;
        Color ink = active ? InkBrown : Color.White;

        b.Draw(Game1.staminaRect, r, fill);
        DrawBorder(b, r, hovered ? Color.White * 0.90f : Gold, hovered ? 4 : 3);

        Rectangle lip = new(r.Right - 8, r.Y + 8, 10, r.Height - 16);
        b.Draw(Game1.staminaRect, lip, fill);
        b.Draw(Game1.staminaRect, new Rectangle(lip.Right - 2, lip.Y, 2, lip.Height), Gold * 0.8f);

        DrawScaledText(
            b,
            Game1.smallFont,
            text,
            r,
            ink,
            centerX: true,
            centerY: true,
            padding: 8,
            maxScale: 1.12f
        );
    }

    public static void DrawPaperHeader(SpriteBatch b, Rectangle rect, string title, string? subtitle = null)
    {
        b.Draw(Game1.staminaRect, rect, ParchmentLight);
        DrawBorder(b, rect, PaperShadow, 3);

        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, 10, 10), Gold * 0.55f);
        b.Draw(Game1.staminaRect, new Rectangle(rect.Right - 10, rect.Y, 10, 10), Gold * 0.55f);

        if (string.IsNullOrWhiteSpace(subtitle))
        {
            DrawScaledText(b, Game1.dialogueFont, title, rect, InkBrown, centerX: true, centerY: true, padding: 12);
            return;
        }

        Rectangle top = new(rect.X + 12, rect.Y + 5, rect.Width - 24, 30);
        Rectangle bottom = new(rect.X + 12, rect.Y + 36, rect.Width - 24, rect.Height - 40);
        DrawScaledText(
            b,
            Game1.smallFont,
            title,
            top,
            InkBrown,
            centerX: true,
            centerY: true,
            padding: 4,
            maxScale: 1.32f
        );
        DrawScaledText(
            b,
            Game1.smallFont,
            subtitle,
            bottom,
            Color.DarkSlateGray,
            centerX: true,
            centerY: true,
            padding: 4,
            maxScale: 1.24f
        );
    }

    public static List<string> WrapText(SpriteFont font, string text, int width, int maxLines = int.MaxValue)
    {
        string wrapped = Game1.parseText(text ?? string.Empty, font, Math.Max(20, width));
        List<string> lines = wrapped.Split('\n').Select(p => p.TrimEnd()).ToList();

        if (lines.Count <= maxLines)
            return lines;

        lines = lines.Take(maxLines).ToList();
        string last = lines[^1];
        if (!last.EndsWith("…", StringComparison.Ordinal))
            lines[^1] = last.TrimEnd('.', ' ') + "…";
        return lines;
    }

    public static void DrawWrappedText(SpriteBatch b, SpriteFont font, string text, Rectangle area, Color color, int maxLines = int.MaxValue)
    {
        List<string> lines = WrapText(font, text, area.Width, maxLines);
        int lineHeight = font.LineSpacing + 2;
        for (int i = 0; i < lines.Count; i++)
        {
            Vector2 pos = new(area.X, area.Y + i * lineHeight);
            Utility.drawTextWithShadow(b, lines[i], font, pos, color);
        }
    }

    public static void DrawAutoFitWrappedText(
        SpriteBatch b,
        SpriteFont font,
        string text,
        Rectangle area,
        Color color,
        int maxLines = 3,
        float minScale = 0.42f,
        bool centerX = false,
        float maxScale = 1f,
        bool centerY = false)
    {
        string safe = text ?? string.Empty;
        float startScale = Math.Max(minScale, maxScale);
        float chosenScale = startScale;
        List<string> chosenLines = new() { safe };

        for (float scale = startScale; scale >= minScale; scale -= 0.05f)
        {
            int logicalWidth = Math.Max(24, (int)Math.Floor(area.Width / scale));
            List<string> lines = WrapWords(font, safe, logicalWidth);

            float totalHeight = lines.Count * (font.LineSpacing + 1) * scale;
            bool widthFits = lines.All(line => font.MeasureString(line).X * scale <= area.Width + 0.5f);
            if (lines.Count <= maxLines && totalHeight <= area.Height && widthFits)
            {
                chosenScale = scale;
                chosenLines = lines;
                break;
            }

            chosenScale = minScale;
            chosenLines = WrapWords(font, safe, Math.Max(24, (int)Math.Floor(area.Width / minScale)));
        }

        if (chosenLines.Count > maxLines)
        {
            chosenLines = chosenLines.Take(maxLines).ToList();
            string last = chosenLines[^1];
            chosenLines[^1] = last.TrimEnd('.', ' ') + "…";
        }

        float lineHeight = (font.LineSpacing + 1) * chosenScale;
        float totalChosenHeight = chosenLines.Count * lineHeight;
        float y = centerY
            ? area.Center.Y - totalChosenHeight / 2f
            : area.Y;

        foreach (string line in chosenLines)
        {
            Vector2 size = font.MeasureString(line) * chosenScale;
            float x = centerX
                ? area.Center.X - size.X / 2f
                : area.X;

            b.DrawString(
                font,
                line,
                new Vector2(x, y),
                color,
                0f,
                Vector2.Zero,
                chosenScale,
                SpriteEffects.None,
                1f
            );

            y += lineHeight;
        }
    }

    private static List<string> WrapWords(SpriteFont font, string text, int width)
    {
        List<string> result = new();
        string[] paragraphs = (text ?? string.Empty).Replace("\r", "").Split('\n');

        foreach (string paragraph in paragraphs)
        {
            if (string.IsNullOrWhiteSpace(paragraph))
            {
                result.Add(string.Empty);
                continue;
            }

            string current = string.Empty;
            foreach (string word in paragraph.Split(' ', StringSplitOptions.RemoveEmptyEntries))
            {
                if (font.MeasureString(word).X > width)
                {
                    if (!string.IsNullOrEmpty(current))
                    {
                        result.Add(current);
                        current = string.Empty;
                    }

                    foreach (char ch in word)
                    {
                        string trialChunk = current + ch;
                        if (string.IsNullOrEmpty(current) || font.MeasureString(trialChunk).X <= width)
                        {
                            current = trialChunk;
                        }
                        else
                        {
                            result.Add(current);
                            current = ch.ToString();
                        }
                    }
                    continue;
                }

                string trial = string.IsNullOrEmpty(current) ? word : current + " " + word;
                if (string.IsNullOrEmpty(current) || font.MeasureString(trial).X <= width)
                {
                    current = trial;
                }
                else
                {
                    result.Add(current);
                    current = word;
                }
            }

            if (!string.IsNullOrEmpty(current))
                result.Add(current);
        }

        return result.Count == 0 ? new List<string> { string.Empty } : result;
    }

    public static int MeasureWrappedTextHeight(
        SpriteFont font,
        string text,
        int width,
        int minimumLines = 1,
        int maximumLines = 8)
    {
        string wrapped = Game1.parseText(
            text ?? string.Empty,
            font,
            Math.Max(24, width)
        );

        int lines = Math.Clamp(
            wrapped.Replace("\r", "").Split('\n').Length,
            Math.Max(1, minimumLines),
            Math.Max(minimumLines, maximumLines)
        );

        return lines * (font.LineSpacing + 2);
    }

    public static void DrawWrappedTextFixedClipped(
        SpriteBatch b,
        SpriteFont font,
        string text,
        Rectangle area,
        Rectangle clip,
        Color color,
        int maximumLines = 8)
    {
        string wrapped = Game1.parseText(
            text ?? string.Empty,
            font,
            Math.Max(24, area.Width)
        );

        string[] lines = wrapped
            .Replace("\r", "")
            .Split('\n')
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
        }
    }

    public static void DrawScaledText(
        SpriteBatch b,
        SpriteFont font,
        string text,
        Rectangle area,
        Color color,
        bool centerX = false,
        bool centerY = false,
        int padding = 0,
        float maxScale = 1f)
    {
        string safe = text ?? string.Empty;
        Vector2 size = font.MeasureString(safe);
        float maxWidth = Math.Max(1f, area.Width - padding * 2);
        float maxHeight = Math.Max(1f, area.Height - padding * 2);
        float scale = Math.Min(
            Math.Max(0.25f, maxScale),
            Math.Min(maxWidth / Math.Max(1f, size.X), maxHeight / Math.Max(1f, size.Y))
        );

        float x = area.X + padding;
        float y = area.Y + padding;
        if (centerX)
            x = area.Center.X - size.X * scale / 2f;
        if (centerY)
            y = area.Center.Y - size.Y * scale / 2f;

        b.DrawString(font, safe, new Vector2(x, y), color, 0f, Vector2.Zero, scale, SpriteEffects.None, 1f);
    }

    public static void DrawStars(SpriteBatch b, Rectangle area, int level, int maxLevel, Color color)
    {
        string filled = new string('★', Math.Max(0, level));
        string empty = new string('☆', Math.Max(0, maxLevel - level));
        string text = filled + empty;
        DrawScaledText(
            b,
            Game1.smallFont,
            text,
            area,
            color,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.16f
        );
    }


    public static void DrawInsetPanel(
        SpriteBatch b,
        Rectangle rect,
        Color fill,
        Color border,
        int borderThickness = 3,
        int inset = 5)
    {
        b.Draw(Game1.staminaRect, rect, fill);
        DrawBorder(b, rect, border, borderThickness);

        if (inset > 0 && rect.Width > inset * 2 && rect.Height > inset * 2)
        {
            Rectangle inner = new(
                rect.X + inset,
                rect.Y + inset,
                rect.Width - inset * 2,
                rect.Height - inset * 2
            );
            DrawBorder(b, inner, Color.White * 0.10f, 1);
        }
    }

    public static void DrawMeter(
        SpriteBatch b,
        Rectangle rect,
        double progress,
        Color fill,
        Color back,
        Color border)
    {
        double p = Math.Clamp(progress, 0d, 1d);

        b.Draw(Game1.staminaRect, rect, back);
        DrawBorder(b, rect, border, 2);

        Rectangle inner = new(
            rect.X + 3,
            rect.Y + 3,
            Math.Max(0, rect.Width - 6),
            Math.Max(0, rect.Height - 6)
        );

        int fillWidth = (int)Math.Round(inner.Width * p);
        if (fillWidth > 0)
            b.Draw(Game1.staminaRect, new Rectangle(inner.X, inner.Y, fillWidth, inner.Height), fill);

        if (p >= 0.75)
        {
            int shineX = inner.X + Math.Max(0, fillWidth - 4);
            if (shineX < inner.Right)
                b.Draw(Game1.staminaRect, new Rectangle(shineX, inner.Y, 2, inner.Height), Color.White * 0.55f);
        }
    }

    public static void DrawCornerOrnaments(SpriteBatch b, Rectangle rect, Color color)
    {
        int s = 10;
        int t = 2;

        b.Draw(Game1.staminaRect, new Rectangle(rect.X + 6, rect.Y + 6, s, t), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X + 6, rect.Y + 6, t, s), color);

        b.Draw(Game1.staminaRect, new Rectangle(rect.Right - 6 - s, rect.Y + 6, s, t), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.Right - 8, rect.Y + 6, t, s), color);

        b.Draw(Game1.staminaRect, new Rectangle(rect.X + 6, rect.Bottom - 8, s, t), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X + 6, rect.Bottom - 16, t, s), color);

        b.Draw(Game1.staminaRect, new Rectangle(rect.Right - 6 - s, rect.Bottom - 8, s, t), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.Right - 8, rect.Bottom - 16, t, s), color);
    }

    public static Point GetUiMousePoint()
        => new(Game1.getMouseX(ui_scale: true), Game1.getMouseY(ui_scale: true));

    public static void DrawScrollbar(
        SpriteBatch b,
        Rectangle track,
        Rectangle thumb,
        bool dragging)
    {
        Point mouse = GetUiMousePoint();
        bool trackHovered = track.Contains(mouse.X, mouse.Y);
        bool thumbHovered = thumb.Contains(mouse.X, mouse.Y);

        Color trackFill = trackHovered
            ? new Color(151, 126, 99) * 0.55f
            : new Color(151, 126, 99) * 0.38f;

        b.Draw(Game1.staminaRect, track, trackFill);
        DrawBorder(
            b,
            track,
            trackHovered ? PaperShadow : PaperShadow * 0.70f,
            2
        );

        Color thumbFill = dragging || thumbHovered
            ? new Color(151, 93, 61)
            : new Color(119, 78, 62);

        b.Draw(Game1.staminaRect, thumb, thumbFill);
        DrawBorder(
            b,
            thumb,
            dragging || thumbHovered ? Gold : Gold * 0.72f,
            dragging || thumbHovered ? 2 : 1
        );

        int gripY = thumb.Center.Y - 4;
        for (int i = 0; i < 3; i++)
        {
            b.Draw(
                Game1.staminaRect,
                new Rectangle(
                    thumb.X + 3,
                    gripY + i * 4,
                    Math.Max(2, thumb.Width - 6),
                    1
                ),
                Color.White * 0.42f
            );
        }
    }

    private static Color Lighten(Color color, float amount)
    {
        float a = Math.Clamp(amount, 0f, 1f);
        return new Color(
            (byte)Math.Clamp(color.R + (255 - color.R) * a, 0, 255),
            (byte)Math.Clamp(color.G + (255 - color.G) * a, 0, 255),
            (byte)Math.Clamp(color.B + (255 - color.B) * a, 0, 255),
            color.A
        );
    }

    public static void DrawBorder(SpriteBatch b, Rectangle rect, Color color, int thickness)
    {
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, rect.Width, thickness), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Bottom - thickness, rect.Width, thickness), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, thickness, rect.Height), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.Right - thickness, rect.Y, thickness, rect.Height), color);
    }
}

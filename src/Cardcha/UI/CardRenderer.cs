
using Cardcha.Models;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.UI;

internal sealed class CardRenderer
{
    public const int IconCellSize = 64;
    public const string IconAtlasRelativePath = "assets/card_icons.png";

    private readonly IModHelper Helper;
    private Texture2D? IconAtlas;
    private bool AtlasChecked;

    public CardRenderer(IModHelper helper)
    {
        this.Helper = helper;
    }

    public void DrawCollectionCard(SpriteBatch b, Rectangle rect, CardDefinition? card, bool owned, bool equipped, bool selected)
    {
        Color frame = card is null ? Color.DimGray : CardchaUi.RarityColor(card.Rarity);
        b.Draw(Game1.staminaRect, rect, new Color(236, 202, 145));
        CardchaUi.DrawBorder(b, rect, selected ? Color.White : frame, selected ? 5 : 4);

        if (!owned || card is null)
        {
            CardchaUi.DrawScaledText(b, Game1.dialogueFont, "???", rect, Color.DarkSlateGray, centerX: true, centerY: true, padding: 10);
            return;
        }

        int iconSize = Math.Min(52, Math.Min(rect.Width - 20, rect.Height - 78));
        Rectangle icon = new(rect.Center.X - iconSize / 2, rect.Y + 14, iconSize, iconSize);
        this.DrawIcon(b, icon, card);

        Rectangle nameArea = new(rect.X + 6, rect.Bottom - 43, rect.Width - 12, 32);
        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            card.Name,
            nameArea,
            Color.Black,
            maxLines: 2,
            minScale: 0.68f,
            centerX: true,
            maxScale: 1.10f
        );

        if (equipped)
        {
            Rectangle badge = new(rect.Right - 30, rect.Y + 4, 26, 26);
            b.Draw(Game1.staminaRect, badge, CardchaUi.GoodGreen);
            Utility.drawTextWithShadow(b, "✓", Game1.smallFont, new Vector2(badge.X + 5, badge.Y + 1), Color.White);
        }
    }

    public void DrawActiveSlot(
        SpriteBatch b,
        Rectangle rect,
        Rectangle removeRect,
        CardDefinition? card,
        int slotNumber,
        bool selected,
        bool unlocked = true)
    {
        Color frame = !unlocked ? new Color(125, 105, 97) : card is null ? Color.Gray : CardchaUi.RarityColor(card.Rarity);
        Color fill = unlocked ? new Color(224, 187, 127) : new Color(196, 167, 135);
        b.Draw(Game1.staminaRect, rect, fill);
        CardchaUi.DrawBorder(b, rect, selected ? Color.White : frame, selected ? 5 : 4);

        Utility.drawTextWithShadow(b, $"{slotNumber}", Game1.tinyFont, new Vector2(rect.X + 6, rect.Y + 4), Color.DarkSlateGray);

        if (!unlocked)
        {
            CardchaUi.DrawScaledText(b, Game1.smallFont, ModEntry.T("binder.slot.locked"), new Rectangle(rect.X + 8, rect.Center.Y - 16, rect.Width - 16, 32), Color.DarkSlateGray, centerX: true, centerY: true, padding: 2);
            return;
        }

        if (card is null)
        {
            CardchaUi.DrawScaledText(b, Game1.smallFont, ModEntry.T("binder.empty"), new Rectangle(rect.X + 8, rect.Center.Y - 16, rect.Width - 16, 32), Color.DarkSlateGray, centerX: true, centerY: true, padding: 2);
            return;
        }

        int iconSize = Math.Min(42, rect.Width - 24);
        Rectangle icon = new(rect.Center.X - iconSize / 2, rect.Y + 16, iconSize, iconSize);
        this.DrawIcon(b, icon, card);

        Rectangle nameArea = new(rect.X + 5, rect.Bottom - 32, rect.Width - 10, 24);
        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            card.Name,
            nameArea,
            Color.Black,
            maxLines: 2,
            minScale: 0.64f,
            centerX: true,
            maxScale: 1.08f
        );

        b.Draw(Game1.staminaRect, removeRect, CardchaUi.DangerRed);
        CardchaUi.DrawBorder(b, removeRect, Color.Black * 0.5f, 2);
        CardchaUi.DrawScaledText(b, Game1.smallFont, "×", removeRect, Color.White, centerX: true, centerY: true, padding: 2);
    }

    public void DrawRevealCard(SpriteBatch b, Rectangle rect, CardDefinition card, string? resultText = null)
    {
        b.Draw(Game1.staminaRect, rect, new Color(240, 205, 145));
        CardchaUi.DrawBorder(b, rect, CardchaUi.RarityColor(card.Rarity), 5);

        Rectangle titleArea = new(rect.X + 8, rect.Y + 8, rect.Width - 16, 40);
        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            card.Name,
            titleArea,
            Color.Black,
            maxLines: 2,
            minScale: 0.72f,
            centerX: true,
            maxScale: 1.14f
        );
        Utility.drawTextWithShadow(
            b,
            CardchaUi.RarityText(card.Rarity),
            Game1.smallFont,
            new Vector2(rect.X + 8, rect.Y + 48),
            CardchaUi.RarityColor(card.Rarity)
        );

        int reservedBottom = resultText is null ? 20 : 64;
        int iconSize = Math.Min(72, Math.Min(rect.Width - 24, rect.Height - 96 - reservedBottom));
        iconSize = Math.Max(28, iconSize);
        Rectangle icon = new(rect.Center.X - iconSize / 2, rect.Center.Y - iconSize / 2 + 6, iconSize, iconSize);
        this.DrawIcon(b, icon, card);

        if (!string.IsNullOrWhiteSpace(resultText))
        {
            Rectangle resultArea = new(rect.X + 8, rect.Bottom - 58, rect.Width - 16, 48);
            CardchaUi.DrawWrappedText(
                b,
                Game1.smallFont,
                resultText,
                resultArea,
                resultText.StartsWith(ModEntry.T("reveal.new"), StringComparison.OrdinalIgnoreCase) ? CardchaUi.GoodGreen : CardchaUi.PremiumPurple,
                maxLines: 2
            );
        }
    }

    public void DrawCardBack(SpriteBatch b, Rectangle rect, bool highlighted = false)
    {
        Color outer = highlighted ? CardchaUi.Gold : new Color(72, 55, 92);
        Color inner = new Color(42, 48, 76);

        b.Draw(Game1.staminaRect, rect, new Color(30, 31, 49));
        CardchaUi.DrawBorder(b, rect, outer, highlighted ? 5 : 4);

        Rectangle innerRect = new(rect.X + 8, rect.Y + 8, rect.Width - 16, rect.Height - 16);
        b.Draw(Game1.staminaRect, innerRect, inner);
        CardchaUi.DrawBorder(b, innerRect, CardchaUi.Gold * 0.65f, 2);

        int cx = rect.Center.X;
        int cy = rect.Center.Y - 4;
        int diamond = Math.Max(10, Math.Min(rect.Width, rect.Height) / 7);

        b.Draw(Game1.staminaRect, new Rectangle(cx - diamond / 2, cy - diamond * 2, diamond, diamond * 4), CardchaUi.Gold * 0.80f);
        b.Draw(Game1.staminaRect, new Rectangle(cx - diamond * 2, cy - diamond / 2, diamond * 4, diamond), CardchaUi.Gold * 0.80f);

        string mark = "★";
        Vector2 markSize = Game1.dialogueFont.MeasureString(mark);
        float scale = Math.Min(0.8f, (rect.Width * 0.42f) / Math.Max(1f, markSize.X));
        b.DrawString(
            Game1.dialogueFont,
            mark,
            new Vector2(cx - markSize.X * scale / 2f, cy - markSize.Y * scale / 2f),
            Color.White,
            0f,
            Vector2.Zero,
            scale,
            SpriteEffects.None,
            1f
        );
    }

    public void DrawIcon(SpriteBatch b, Rectangle destination, CardDefinition card)
    {
        Texture2D? atlas = this.TryGetAtlas();
        if (atlas is not null && card.IconIndex >= 0)
        {
            int columns = Math.Max(1, atlas.Width / IconCellSize);
            int sourceX = (card.IconIndex % columns) * IconCellSize;
            int sourceY = (card.IconIndex / columns) * IconCellSize;
            Rectangle source = new(sourceX, sourceY, IconCellSize, IconCellSize);

            if (source.Right <= atlas.Width && source.Bottom <= atlas.Height)
            {
                b.Draw(atlas, destination, source, Color.White);
                return;
            }
        }

        string initial = card.Name.Length > 0 ? card.Name[..1].ToUpperInvariant() : "?";
        Vector2 size = Game1.dialogueFont.MeasureString(initial);
        float scale = Math.Min(destination.Width / Math.Max(1f, size.X), destination.Height / Math.Max(1f, size.Y));
        scale = Math.Min(1f, scale * 0.82f);
        Vector2 pos = new(
            destination.Center.X - size.X * scale / 2f,
            destination.Center.Y - size.Y * scale / 2f
        );
        b.DrawString(
            Game1.dialogueFont,
            initial,
            pos,
            CardchaUi.RarityColor(card.Rarity),
            0f,
            Vector2.Zero,
            scale,
            SpriteEffects.None,
            1f
        );
    }

    private Texture2D? TryGetAtlas()
    {
        if (this.AtlasChecked)
            return this.IconAtlas;

        this.AtlasChecked = true;
        string file = Path.Combine(this.Helper.DirectoryPath, "assets", "card_icons.png");
        if (!File.Exists(file))
            return null;

        try
        {
            this.IconAtlas = this.Helper.ModContent.Load<Texture2D>(IconAtlasRelativePath);
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("card-icon-atlas", $"Couldn't load {IconAtlasRelativePath}; using runtime initials instead. {ex.Message}");
        }

        return this.IconAtlas;
    }
}

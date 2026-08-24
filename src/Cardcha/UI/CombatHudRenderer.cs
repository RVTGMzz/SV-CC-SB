using Cardcha.Models;
using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.UI;

/// <summary>
/// Compact runtime combat feedback for conditional cards.
/// Uses the existing single card icon atlas; no HUD-only icon assets.
/// </summary>
internal sealed class CombatHudRenderer
{
    private readonly ModConfig Config;
    private readonly CombatService Combat;
    private readonly LoadoutService Loadout;
    private readonly SaveService Save;
    private readonly CardRegistry Cards;
    private readonly CardRenderer Renderer;

    public CombatHudRenderer(
        ModConfig config,
        CombatService combat,
        LoadoutService loadout,
        SaveService save,
        CardRegistry cards,
        CardRenderer renderer
    )
    {
        this.Config = config;
        this.Combat = combat;
        this.Loadout = loadout;
        this.Save = save;
        this.Cards = cards;
        this.Renderer = renderer;
    }

    public void Draw(SpriteBatch b)
    {
        if (!Context.IsWorldReady
            || !this.Config.EnableCombatCards
            || !this.Config.EnableCombatHud
            || !this.Loadout.CardEffectsActive
            || Game1.activeClickableMenu is not null
            || Game1.player is null)
        {
            return;
        }

        List<HudRow> rows = BuildRows();
        string toast = this.Combat.CurrentHudToast;

        if (rows.Count == 0 && string.IsNullOrWhiteSpace(toast))
            return;

        float scale = (float)Math.Clamp(this.Config.CombatHudScale, 0.75, 1.5);
        int panelW = (int)(270 * scale);
        int rowH = (int)(48 * scale);
        int gap = (int)(5 * scale);
        int pad = (int)(10 * scale);

        // Lower-left keeps clear of Stardew's top-right clock/money UI.
        int totalRowsH = rows.Count == 0 ? 0 : rows.Count * rowH + (rows.Count - 1) * gap;
        int toastH = string.IsNullOrWhiteSpace(toast) ? 0 : (int)(50 * scale);
        int totalH = totalRowsH + (toastH > 0 && totalRowsH > 0 ? gap : 0) + toastH;

        int x = 18;
        int y = Math.Max(18, Game1.uiViewport.Height - totalH - 150);

        foreach (HudRow row in rows)
        {
            Rectangle rect = new(x, y, panelW, rowH);
            DrawRow(b, rect, row, scale);
            y += rowH + gap;
        }

        if (!string.IsNullOrWhiteSpace(toast))
        {
            Rectangle toastRect = new(x, y, panelW, toastH);
            DrawToast(b, toastRect, toast, scale);
        }
    }

    private List<HudRow> BuildRows()
    {
        List<HudRow> rows = new();

        if (this.Loadout.IsEquipped("chain_hunter"))
        {
            int stacks = this.Combat.CurrentChainHunterStacks;
            double seconds = this.Combat.CurrentChainSecondsRemaining;

            if (stacks > 0)
            {
                rows.Add(new HudRow(
                    "chain_hunter",
                    ModEntry.T("hud.chain", new { stacks, max = this.Config.ChainHunterMaxStacks }),
                    $"{seconds:0.0}s",
                    Math.Clamp(seconds / this.Combat.CurrentChainDurationSeconds, 0, 1),
                    Active: true
                ));
            }
        }

        if (this.Loadout.IsEquipped("last_stand") && this.Combat.IsLastStandActive)
        {
            rows.Add(new HudRow(
                "last_stand",
                ModEntry.T("hud.last-stand"),
                ModEntry.T("hud.active"),
                null,
                Active: true
            ));
        }

        if (this.Loadout.IsEquipped("swift_feet") && this.Combat.IsSwiftFeetActive)
        {
            rows.Add(new HudRow(
                "swift_feet",
                ModEntry.T("hud.swift-feet"),
                "+1",
                null,
                Active: true
            ));
        }

        if (this.Loadout.IsEquipped("blood_fang"))
        {
            double cooldown = this.Combat.BloodFangCooldownSecondsRemaining;
            if (cooldown > 0.05)
            {
                rows.Add(new HudRow(
                    "blood_fang",
                    ModEntry.T("hud.blood-fang"),
                    $"{cooldown:0.0}s",
                    Math.Clamp(1.0 - cooldown / this.Combat.BloodFangCooldownTotalSeconds, 0, 1),
                    Active: false
                ));
            }
        }

        if (this.Loadout.IsEquipped("phoenix_heart"))
        {
            rows.Add(new HudRow(
                "phoenix_heart",
                ModEntry.T("hud.phoenix"),
                this.Combat.IsPhoenixReady ? ModEntry.T("hud.ready") : ModEntry.T("hud.used"),
                null,
                Active: this.Combat.IsPhoenixReady
            ));
        }

        return rows;
    }

    private void DrawRow(SpriteBatch b, Rectangle rect, HudRow row, float scale)
    {
        Color bg = row.Active ? new Color(47, 55, 66) : new Color(65, 60, 63);
        b.Draw(Game1.staminaRect, rect, bg * 0.92f);
        CardchaUi.DrawBorder(b, rect, row.Active ? CardchaUi.Gold : Color.Gray, 2);

        int iconSize = Math.Min(rect.Height - 8, (int)(40 * scale));
        Rectangle iconRect = new(rect.X + 4, rect.Center.Y - iconSize / 2, iconSize, iconSize);

        CardDefinition? card = this.Cards.Get(row.CardId);
        if (card is not null)
            this.Renderer.DrawIcon(b, iconRect, card);

        int textX = iconRect.Right + (int)(8 * scale);
        int valueRight = rect.Right - (int)(8 * scale);

        Vector2 labelSize = Game1.smallFont.MeasureString(row.Label);
        float labelScale = Math.Min(
            scale * 0.82f,
            (valueRight - textX - (int)(65 * scale)) / Math.Max(1f, labelSize.X)
        );
        labelScale = Math.Max(0.55f, labelScale);

        b.DrawString(
            Game1.smallFont,
            row.Label,
            new Vector2(textX, rect.Y + (int)(7 * scale)),
            Color.White,
            0f,
            Vector2.Zero,
            labelScale,
            SpriteEffects.None,
            1f
        );

        Vector2 valueSize = Game1.smallFont.MeasureString(row.Value);
        float valueScale = Math.Min(scale * 0.75f, (int)(70 * scale) / Math.Max(1f, valueSize.X));
        valueScale = Math.Max(0.52f, valueScale);

        b.DrawString(
            Game1.smallFont,
            row.Value,
            new Vector2(valueRight - valueSize.X * valueScale, rect.Y + (int)(7 * scale)),
            row.Active ? CardchaUi.Gold : Color.LightGray,
            0f,
            Vector2.Zero,
            valueScale,
            SpriteEffects.None,
            1f
        );

        if (row.Progress is double progress)
        {
            int barX = textX;
            int barY = rect.Bottom - (int)(10 * scale);
            int barW = rect.Right - barX - (int)(8 * scale);
            int barH = Math.Max(4, (int)(5 * scale));

            Rectangle back = new(barX, barY, barW, barH);
            Rectangle fill = new(barX, barY, (int)(barW * progress), barH);

            b.Draw(Game1.staminaRect, back, Color.Black * 0.45f);
            if (fill.Width > 0)
                b.Draw(Game1.staminaRect, fill, row.Active ? CardchaUi.Gold : Color.LightGray);
        }
    }

    private static void DrawToast(SpriteBatch b, Rectangle rect, string text, float scale)
    {
        b.Draw(Game1.staminaRect, rect, new Color(50, 35, 47) * 0.94f);
        CardchaUi.DrawBorder(b, rect, CardchaUi.PremiumPurple, 3);

        string wrapped = Game1.parseText(text, Game1.smallFont, rect.Width - (int)(16 * scale));
        Vector2 size = Game1.smallFont.MeasureString(wrapped);
        float drawScale = Math.Min(scale * 0.78f, (rect.Width - 16) / Math.Max(1f, size.X));
        drawScale = Math.Max(0.55f, drawScale);

        b.DrawString(
            Game1.smallFont,
            wrapped,
            new Vector2(rect.X + (int)(8 * scale), rect.Center.Y - size.Y * drawScale / 2f),
            Color.White,
            0f,
            Vector2.Zero,
            drawScale,
            SpriteEffects.None,
            1f
        );
    }

    private sealed record HudRow(
        string CardId,
        string Label,
        string Value,
        double? Progress,
        bool Active
    );
}

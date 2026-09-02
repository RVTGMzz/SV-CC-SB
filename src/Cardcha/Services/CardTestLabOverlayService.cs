using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>TEST-only minimized HUD tab for reopening Card Test Lab without retyping console commands.</summary>
internal sealed class CardTestLabOverlayService
{
    private readonly IModHelper Helper;
    private readonly CardTestLabService Lab;
    private readonly CardTestArenaService Arena;
    private readonly Action OpenLab;
    private readonly Action EndLab;

    public CardTestLabOverlayService(
        IModHelper helper,
        CardTestLabService lab,
        CardTestArenaService arena,
        Action openLab,
        Action endLab)
    {
        this.Helper = helper;
        this.Lab = lab;
        this.Arena = arena;
        this.OpenLab = openLab;
        this.EndLab = endLab;
    }

    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Lab.IsSessionActive || Game1.activeClickableMenu is not null)
            return;

        Rectangle tab = this.GetTabRect();
        e.SpriteBatch.Draw(Game1.staminaRect, tab, new Color(45, 38, 69) * 0.94f);
        DrawBorder(e.SpriteBatch, tab, this.Arena.IsInArena ? new Color(113, 226, 194) : new Color(195, 156, 244), 2);

        string label = this.Arena.IsInArena ? "CARD LAB • ARENA" : "CARD LAB • TEST";
        Vector2 size = Game1.smallFont.MeasureString(label);
        float scale = Math.Min(0.82f, (tab.Width - 16f) / Math.Max(1f, size.X));
        e.SpriteBatch.DrawString(
            Game1.smallFont,
            label,
            new Vector2(tab.Center.X - size.X * scale / 2f, tab.Y + 8),
            Color.White,
            0f,
            Vector2.Zero,
            scale,
            SpriteEffects.None,
            1f
        );

        string hint = "CLICK / F8 / R-STICK";
        Vector2 hintSize = Game1.smallFont.MeasureString(hint);
        float hintScale = 0.58f;
        e.SpriteBatch.DrawString(
            Game1.smallFont,
            hint,
            new Vector2(tab.Center.X - hintSize.X * hintScale / 2f, tab.Bottom - 18),
            new Color(219, 210, 237),
            0f,
            Vector2.Zero,
            hintScale,
            SpriteEffects.None,
            1f
        );

        this.Arena.DrawHud(e.SpriteBatch);
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Lab.IsSessionActive || Game1.activeClickableMenu is not null)
            return;

        bool reopen = e.Button == SButton.F8
                      || e.Button.ToString().Equals("ControllerRightStick", StringComparison.OrdinalIgnoreCase);

        if (e.Button == SButton.MouseLeft)
        {
            Vector2 cursor = this.Helper.Input.GetCursorPosition().ScreenPixels;
            reopen = this.GetTabRect().Contains((int)cursor.X, (int)cursor.Y);
        }

        if (!reopen)
            return;

        this.Helper.Input.Suppress(e.Button);
        Game1.playSound("bigSelect");
        this.OpenLab();
    }

    public void StopFromCommand()
    {
        this.EndLab();
    }

    private Rectangle GetTabRect()
    {
        int width = 176;
        int height = 54;
        int x = Math.Max(12, Game1.uiViewport.Width - width - 16);
        int y = Math.Clamp(Game1.uiViewport.Height / 2 - 90, 120, Math.Max(120, Game1.uiViewport.Height - height - 90));
        return new Rectangle(x, y, width, height);
    }

    private static void DrawBorder(SpriteBatch b, Rectangle rect, Color color, int thickness)
    {
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, rect.Width, thickness), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Bottom - thickness, rect.Width, thickness), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, thickness, rect.Height), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.Right - thickness, rect.Y, thickness, rect.Height), color);
    }
}

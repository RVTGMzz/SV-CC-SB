using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Runtime-only ChaCha Boss Form foundation.
/// Full Boss Energy unlocks a flashing activation card. Mouse/touch activates directly;
/// controller Select/View must be pressed three times within a short confirmation window.
/// This foundation intentionally grants no combat stat bonuses yet.
/// </summary>
internal sealed class ChaChaBossFormService
{
    public const int BossFormDurationMs = 10000;
    public const int TripleSelectWindowMs = 1200;
    public const int RequiredSelectPresses = 3;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly BossEnergyService BossEnergy;
    private readonly WorldActorService WorldActors;

    private int SelectPressCount;
    private long LastSelectPressAt;
    private long ActiveUntil;
    private bool ReadyAnnounced;

    public ChaChaBossFormService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        BossEnergyService bossEnergy,
        WorldActorService worldActors)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.BossEnergy = bossEnergy;
        this.WorldActors = worldActors;
    }

    public bool IsActive => this.ActiveUntil > Environment.TickCount64;
    public bool IsReady => !this.IsActive
                           && this.Save.Data.ChaChaLoaned
                           && this.BossEnergy.CurrentEnergy >= BossEnergyService.MaxEnergy - 0.001d;

    public int CurrentSelectPressCount
    {
        get
        {
            this.ExpireTripleSelectIfNeeded();
            return this.SelectPressCount;
        }
    }

    public double SecondsRemaining
        => this.IsActive ? Math.Max(0d, (this.ActiveUntil - Environment.TickCount64) / 1000d) : 0d;

    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        long now = Environment.TickCount64;
        if (this.ActiveUntil > 0 && now >= this.ActiveUntil)
        {
            this.EndBossForm("timer");
            return;
        }

        this.ExpireTripleSelectIfNeeded();

        if (this.IsActive)
        {
            this.WorldActors.SetChaChaBossVisual(true);
            return;
        }

        this.WorldActors.SetChaChaBossVisual(false);

        if (!this.IsReady)
        {
            this.ReadyAnnounced = false;
            this.SelectPressCount = 0;
            return;
        }

        if (!this.ReadyAnnounced)
        {
            this.ReadyAnnounced = true;
            Game1.playSound("yoba");
            this.WorldActors.TriggerChaChaEmote(56);
            this.Monitor.Log("ChaCha Boss Form READY: Boss Energy reached 100.", LogLevel.Info);
        }
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady || !this.CanAcceptActivationInput())
            return;

        if (e.Button == SButton.MouseLeft)
        {
            Vector2 cursor = this.Helper.Input.GetCursorPosition().ScreenPixels;
            if (this.GetActivationRect().Contains((int)cursor.X, (int)cursor.Y) && this.IsReady)
            {
                this.Helper.Input.Suppress(e.Button);
                this.TryActivate("virtual button");
            }
            return;
        }

        if (!this.IsSelectViewButton(e.Button) || !this.IsReady)
            return;

        this.Helper.Input.Suppress(e.Button);
        long now = Environment.TickCount64;
        if (this.LastSelectPressAt <= 0 || now - this.LastSelectPressAt > TripleSelectWindowMs)
            this.SelectPressCount = 0;

        this.LastSelectPressAt = now;
        this.SelectPressCount = Math.Min(RequiredSelectPresses, this.SelectPressCount + 1);
        Game1.playSound(this.SelectPressCount >= RequiredSelectPresses ? "bigSelect" : "smallSelect");

        if (this.SelectPressCount >= RequiredSelectPresses)
            this.TryActivate("Select/View x3");
    }

    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned || Game1.activeClickableMenu is not null)
            return;

        if (!this.IsReady && !this.IsActive)
            return;

        Rectangle rect = this.GetActivationRect();
        long now = Environment.TickCount64;
        float pulse = 0.5f + 0.5f * (float)Math.Sin(now / 135d);
        Color fill = this.IsActive
            ? new Color(61, 35, 92) * 0.93f
            : new Color(93, 54, 133) * (0.78f + pulse * 0.17f);
        Color border = this.IsActive
            ? new Color(210, 176, 255)
            : Color.Lerp(new Color(225, 196, 255), Color.White, pulse);

        e.SpriteBatch.Draw(Game1.staminaRect, rect, fill);
        DrawBorder(e.SpriteBatch, rect, border, this.IsReady ? 3 : 2);

        string title = this.IsActive
            ? ModEntry.T("chacha.boss.active")
            : ModEntry.T("chacha.boss.ready");
        string detail = this.IsActive
            ? ModEntry.T("chacha.boss.timer", new { seconds = this.SecondsRemaining.ToString("0.0") })
            : this.CurrentSelectPressCount > 0
                ? ModEntry.T("chacha.boss.triple", new { count = this.CurrentSelectPressCount, max = RequiredSelectPresses })
                : ModEntry.T("chacha.boss.hint");

        Vector2 titleSize = Game1.smallFont.MeasureString(title);
        float titleScale = Math.Min(1f, (rect.Width - 24f) / Math.Max(1f, titleSize.X));
        e.SpriteBatch.DrawString(
            Game1.smallFont,
            title,
            new Vector2(rect.Center.X - titleSize.X * titleScale / 2f, rect.Y + 13),
            Color.White,
            0f,
            Vector2.Zero,
            titleScale,
            SpriteEffects.None,
            1f
        );

        Vector2 detailSize = Game1.smallFont.MeasureString(detail);
        float detailScale = Math.Min(0.72f, (rect.Width - 20f) / Math.Max(1f, detailSize.X));
        e.SpriteBatch.DrawString(
            Game1.smallFont,
            detail,
            new Vector2(rect.Center.X - detailSize.X * detailScale / 2f, rect.Bottom - 27),
            new Color(238, 225, 255),
            0f,
            Vector2.Zero,
            detailScale,
            SpriteEffects.None,
            1f
        );
    }

    public bool TryActivate(string source)
    {
        if (!Context.IsWorldReady || !this.IsReady || !this.CanAcceptActivationInput())
            return false;

        if (!this.BossEnergy.TrySpend(BossEnergyService.MaxEnergy))
            return false;

        this.SelectPressCount = 0;
        this.LastSelectPressAt = 0;
        this.ReadyAnnounced = false;
        this.ActiveUntil = Environment.TickCount64 + BossFormDurationMs;
        this.BossEnergy.SetGainSuppressed(true);
        this.WorldActors.SetChaChaBossVisual(true);
        this.WorldActors.TriggerChaChaEmote(16);
        Game1.playSound("wand");
        Game1.showGlobalMessage(ModEntry.T("chacha.boss.activated"));
        this.Monitor.Log($"ChaCha Boss Form activated via {source}; duration={BossFormDurationMs}ms.", LogLevel.Info);
        return true;
    }

    public void EndBossForm(string reason)
    {
        bool wasActive = this.ActiveUntil > 0 || this.WorldActors.IsChaChaBossVisualActive;
        this.ActiveUntil = 0;
        this.SelectPressCount = 0;
        this.LastSelectPressAt = 0;
        this.BossEnergy.SetGainSuppressed(false);
        this.WorldActors.SetChaChaBossVisual(false);

        if (wasActive && Context.IsWorldReady)
        {
            Game1.playSound("smallSelect");
            this.WorldActors.TriggerChaChaEmote(32);
        }

        if (wasActive)
            this.Monitor.Log($"ChaCha Boss Form ended ({reason}).", LogLevel.Trace);
    }

    public void OnDayStarted(object? sender, DayStartedEventArgs e)
        => this.ResetRuntime();

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
        => this.ResetRuntime();

    public void OnSaving()
        => this.EndBossForm("save");

    public void DebugPrimeReady()
    {
        if (!Context.IsWorldReady)
            return;
        this.EndBossForm("debug prime");
        this.BossEnergy.DebugSetEnergy(BossEnergyService.MaxEnergy);
        this.ReadyAnnounced = false;
    }

    public string Describe()
        => $"Ready={this.IsReady} | Active={this.IsActive} | Remaining={this.SecondsRemaining:0.0}s | " +
           $"Select={this.CurrentSelectPressCount}/{RequiredSelectPresses} | {this.BossEnergy.Describe()}";

    private void ResetRuntime()
    {
        this.ActiveUntil = 0;
        this.SelectPressCount = 0;
        this.LastSelectPressAt = 0;
        this.ReadyAnnounced = false;
        this.BossEnergy.SetGainSuppressed(false);
        this.WorldActors.SetChaChaBossVisual(false);
    }

    private bool CanAcceptActivationInput()
        => Game1.player is not null
           && Game1.player.health > 0
           && Game1.activeClickableMenu is null
           && !Game1.eventUp
           && !Game1.dialogueUp;

    private bool IsSelectViewButton(SButton button)
    {
        string name = button.ToString();
        return name.Equals("ControllerBack", StringComparison.OrdinalIgnoreCase)
               || name.Equals("ControllerSelect", StringComparison.OrdinalIgnoreCase)
               || name.Equals("ControllerView", StringComparison.OrdinalIgnoreCase);
    }

    private void ExpireTripleSelectIfNeeded()
    {
        if (this.SelectPressCount <= 0 || this.LastSelectPressAt <= 0)
            return;

        if (Environment.TickCount64 - this.LastSelectPressAt <= TripleSelectWindowMs)
            return;

        this.SelectPressCount = 0;
        this.LastSelectPressAt = 0;
    }

    private Rectangle GetActivationRect()
    {
        const int width = 250;
        const int height = 76;
        int x = Math.Max(18, Game1.uiViewport.Width - width - 24);
        int y = Math.Clamp(Game1.uiViewport.Height / 2 + 110, 150, Math.Max(150, Game1.uiViewport.Height - height - 130));
        return new Rectangle(x, y, width, height);
    }

    private static void DrawBorder(SpriteBatch batch, Rectangle rect, Color color, int thickness)
    {
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, rect.Width, thickness), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Bottom - thickness, rect.Width, thickness), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, thickness, rect.Height), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.Right - thickness, rect.Y, thickness, rect.Height), color);
    }
}

using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Runtime-only ChaCha Boss Form foundation.
/// ChaCha visibly charges through four aura stages, owns one unified Energy HUD, and activates
/// through a semantic controller chord, Left Shift+A on keyboard, or a click on the READY bar.
/// This foundation intentionally grants no combat stat bonuses yet.
/// </summary>
internal sealed class ChaChaBossFormService
{
    public const int BossFormDurationMs = 10000;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly BossEnergyService BossEnergy;
    private readonly WorldActorService WorldActors;
    private readonly ControllerProfileService Controller;

    private long ActiveUntil;
    private bool ReadyAnnounced;
    private Texture2D? AuraTexture;

    public ChaChaBossFormService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        BossEnergyService bossEnergy,
        WorldActorService worldActors,
        ControllerProfileService controller)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.BossEnergy = bossEnergy;
        this.WorldActors = worldActors;
        this.Controller = controller;
    }

    public bool IsActive => this.ActiveUntil > Environment.TickCount64;
    public bool IsReady => !this.IsActive
                           && this.Save.Data.ChaChaLoaned
                           && this.BossEnergy.CurrentEnergy >= BossEnergyService.MaxEnergy - 0.001d;

    public double SecondsRemaining
        => this.IsActive ? Math.Max(0d, (this.ActiveUntil - Environment.TickCount64) / 1000d) : 0d;

    public int EnergyAuraStage
    {
        get
        {
            if (this.IsActive || this.IsReady)
                return 4;
            double energy = this.BossEnergy.CurrentEnergy;
            if (energy >= 75d) return 3;
            if (energy >= 50d) return 2;
            if (energy >= 25d) return 1;
            return 0;
        }
    }

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

        if (this.IsActive)
        {
            this.WorldActors.SetChaChaBossVisual(true);
            return;
        }

        this.WorldActors.SetChaChaBossVisual(false);

        if (!this.IsReady)
        {
            this.ReadyAnnounced = false;
            return;
        }

        if (!this.ReadyAnnounced)
        {
            this.ReadyAnnounced = true;
            Game1.playSound("yoba");
            this.WorldActors.TriggerChaChaEmote(56);
            this.Monitor.Log("ChaCha Boss Form READY: ChaCha Energy reached 100.", LogLevel.Info);
        }
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady || !this.IsReady || !this.CanAcceptActivationInput())
            return;

        // .5.6.1: the persistent ChaCha Energy panel was removed from gameplay HUD.
        // Do not leave its former rectangle as an invisible mouse activation hotspot.
        if (e.Button == SButton.MouseLeft)
            return;

        SButton confirm = this.Controller.GetButton(ControllerAction.Confirm);
        SButton deselect = this.Controller.GetButton(ControllerAction.Deselect);
        bool controllerCandidate = e.Button == confirm || e.Button == deselect;
        bool controllerChord = controllerCandidate
                               && confirm != SButton.None
                               && deselect != SButton.None
                               && this.Helper.Input.IsDown(confirm)
                               && this.Helper.Input.IsDown(deselect);

        if (controllerChord)
        {
            this.Helper.Input.Suppress(confirm);
            this.Helper.Input.Suppress(deselect);
            this.TryActivate($"{this.Controller.GetLabel(ControllerAction.Confirm)}+{this.Controller.GetLabel(ControllerAction.Deselect)} controller chord");
            return;
        }

        bool keyboardCandidate = e.Button == SButton.A || e.Button == SButton.LeftShift;
        bool keyboardChord = keyboardCandidate
                             && this.Helper.Input.IsDown(SButton.LeftShift)
                             && this.Helper.Input.IsDown(SButton.A);
        if (keyboardChord)
        {
            this.Helper.Input.Suppress(SButton.LeftShift);
            this.Helper.Input.Suppress(SButton.A);
            this.TryActivate("Left Shift+A keyboard chord");
        }
    }

    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        // .5.6.1: user-approved HUD cleanup. Boss Energy continues charging internally and
        // READY still announces through sound/ChaCha emote; activation remains controller chord
        // or Left Shift+A. The old always-on rectangular meter is intentionally not drawn.
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned)
            return;

        int stage = this.EnergyAuraStage;
        if (stage <= 0)
            return;

        NPC? actor = this.WorldActors.FindChaChaActor();
        if (actor is null || actor.isInvisible.Value || actor.currentLocation != Game1.currentLocation)
            return;

        this.EnsureAuraTexture();
        if (this.AuraTexture is null)
            return;

        Vector2 center = Game1.GlobalToLocal(Game1.viewport, actor.Position + new Vector2(16f, 17f));
        long now = Environment.TickCount64;
        float pulse = stage >= 4
            ? 0.88f + 0.12f * (float)Math.Sin(now / 105d)
            : 0.96f + 0.04f * (float)Math.Sin(now / 240d);

        float scale = (stage switch { 1 => 1.18f, 2 => 1.30f, 3 => 1.43f, _ => 1.62f }) * pulse;
        if (this.IsActive)
            scale *= 1.10f;

        Color color = this.GetStageColor(stage);
        float alpha = stage switch { 1 => 0.23f, 2 => 0.30f, 3 => 0.38f, _ => 0.48f };
        Vector2 origin = new(this.AuraTexture.Width / 2f, this.AuraTexture.Height / 2f);

        e.SpriteBatch.Draw(this.AuraTexture, center, null, color * alpha, 0f, origin, scale, SpriteEffects.None, 0.99f);
        e.SpriteBatch.Draw(this.AuraTexture, center, null, color * (alpha * 0.52f), 0f, origin, scale * 0.72f, SpriteEffects.None, 0.99f);

        int sparks = stage + (stage >= 4 ? 3 : 1);
        for (int i = 0; i < sparks; i++)
        {
            float phase = (float)(now * (stage >= 4 ? 0.006 : 0.0035) + i * 2.11);
            float radius = 29f + stage * 4f + i * 2f;
            Vector2 p = center + new Vector2((float)Math.Cos(phase) * radius, (float)Math.Sin(phase * 1.13f) * radius * 0.62f);
            int size = stage >= 4 && i % 2 == 0 ? 3 : 2;
            Color spark = color * (0.45f + 0.18f * (float)Math.Abs(Math.Sin(phase)));
            e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle((int)p.X - size, (int)p.Y, size * 2 + 1, 1), spark);
            e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle((int)p.X, (int)p.Y - size, 1, size * 2 + 1), spark);
        }
    }

    public bool TryActivate(string source)
    {
        if (!Context.IsWorldReady || !this.IsReady || !this.CanAcceptActivationInput())
            return false;

        if (!this.BossEnergy.TrySpend(BossEnergyService.MaxEnergy))
            return false;

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
    {
        this.ResetRuntime();
        this.DisposeAuraTexture();
    }

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
    {
        string chord = $"{this.Controller.GetLabel(ControllerAction.Confirm)}+{this.Controller.GetLabel(ControllerAction.Deselect)}";
        return $"Ready={this.IsReady} | Active={this.IsActive} | Remaining={this.SecondsRemaining:0.0}s | " +
               $"AuraStage={this.EnergyAuraStage} | ControllerChord={chord} | Keyboard=LeftShift+A | {this.BossEnergy.Describe()}";
    }

    private void ResetRuntime()
    {
        this.ActiveUntil = 0;
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

    private Rectangle GetEnergyHudRect()
    {
        const int width = 318;
        const int height = 58;
        int x = Math.Max(12, (Game1.uiViewport.Width - width) / 2);
        int y = Math.Clamp(108, 72, Math.Max(72, Game1.uiViewport.Height - height - 120));
        return new Rectangle(x, y, width, height);
    }

    private Color GetStageColor(int stage)
        => stage switch
        {
            1 => new Color(242, 244, 255),
            2 => new Color(255, 226, 82),
            3 => new Color(255, 145, 45),
            4 => new Color(232, 54, 48),
            _ => new Color(126, 116, 145)
        };

    private void EnsureAuraTexture()
    {
        if (this.AuraTexture is not null && !this.AuraTexture.IsDisposed)
            return;

        const int size = 64;
        Texture2D texture = new(Game1.staminaRect.GraphicsDevice, size, size);
        Color[] pixels = new Color[size * size];
        Vector2 center = new((size - 1) / 2f, (size - 1) / 2f);
        float radius = size / 2f;
        for (int y = 0; y < size; y++)
        {
            for (int x = 0; x < size; x++)
            {
                float distance = Vector2.Distance(new Vector2(x, y), center) / radius;
                float opacity = Math.Clamp(1f - distance, 0f, 1f);
                opacity = opacity * opacity * 0.88f;
                pixels[y * size + x] = Color.White * opacity;
            }
        }
        texture.SetData(pixels);
        this.AuraTexture = texture;
    }

    private void DisposeAuraTexture()
    {
        if (this.AuraTexture is null)
            return;
        try { this.AuraTexture.Dispose(); } catch { }
        this.AuraTexture = null;
    }

    private static void DrawBorder(SpriteBatch batch, Rectangle rect, Color color, int thickness)
    {
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, rect.Width, thickness), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Bottom - thickness, rect.Width, thickness), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, thickness, rect.Height), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.Right - thickness, rect.Y, thickness, rect.Height), color);
    }
}

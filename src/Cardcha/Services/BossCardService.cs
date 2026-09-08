using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Runtime owner for the separate Boss Card slot. Boss Cards never enter the normal 76-card pool.
/// 0661 materializes Verdant Core as the first real Boss Card while keeping the slot architecture
/// ready for the 40/60/80 milestone rewards.
/// </summary>
internal sealed class BossCardService
{
    public const string VerdantCoreId = "verdant_core";
    public const double VerdantGuardThreshold = 0.50d;
    public const double VerdantDamageReduction = 0.35d;
    public const int VerdantActiveDurationMs = 6000;
    public const int VerdantCooldownMs = 24000;
    public const int VerdantHealIntervalMs = 1000;
    public const int VerdantHealPerTick = 2;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly ModConfig Config;

    private long ActiveUntilMs;
    private long CooldownUntilMs;
    private long LastHealAtMs;
    private long LastPulseAtMs;
    private bool WasUnlocked;
    private Texture2D? VerdantIcon;

    public long ActivationCount { get; private set; }
    public int TotalHealing { get; private set; }
    public int LastPreventedDamage { get; private set; }
    public string LastActivationReason { get; private set; } = "none";

    public BossCardService(IModHelper helper, IMonitor monitor, SaveService save, ModConfig config)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.Config = config;
    }

    public bool VerdantUnlocked
        => this.Save.Data.BossCardsUnlocked?.Contains(VerdantCoreId) == true;

    public bool VerdantEquipped
        => this.Config.EnableCombatCards
           && this.VerdantUnlocked
           && string.Equals(this.Save.Data.EquippedBossCardId, VerdantCoreId, StringComparison.OrdinalIgnoreCase);

    public bool VerdantActive
        => this.VerdantEquipped && Environment.TickCount64 < this.ActiveUntilMs;

    public double ActiveSecondsRemaining
        => Math.Max(0d, (this.ActiveUntilMs - Environment.TickCount64) / 1000d);

    public double CooldownSecondsRemaining
        => Math.Max(0d, (this.CooldownUntilMs - Environment.TickCount64) / 1000d);

    public bool IsReady
        => this.VerdantEquipped && !this.VerdantActive && Environment.TickCount64 >= this.CooldownUntilMs;

    public int ModifyIncomingDamage(int damage, Farmer farmer)
    {
        if (damage <= 0 || !Context.IsWorldReady || farmer?.IsLocalPlayer != true || !this.VerdantEquipped)
            return damage;

        long now = Environment.TickCount64;
        if (now >= this.ActiveUntilMs && now >= this.CooldownUntilMs)
        {
            int projectedHealth = farmer.health - damage;
            int thresholdHealth = Math.Max(1, (int)Math.Ceiling(farmer.maxHealth * VerdantGuardThreshold));
            if (projectedHealth <= thresholdHealth)
                this.Activate(now, "low-hp guard");
        }

        if (now >= this.ActiveUntilMs)
            return damage;

        int reduced = Math.Max(1, (int)Math.Round(damage * (1d - VerdantDamageReduction), MidpointRounding.AwayFromZero));
        this.LastPreventedDamage = Math.Max(0, damage - reduced);
        return reduced;
    }

    public void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
    {
        this.ResetRuntime();
        this.WasUnlocked = this.VerdantUnlocked;
    }

    public void OnDayStarted(object? sender, DayStartedEventArgs e)
    {
        this.ResetRuntime();
        this.WasUnlocked = this.VerdantUnlocked;
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.ResetRuntime();
        this.WasUnlocked = false;
        this.VerdantIcon = null;
    }

    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady || Game1.player is null)
            return;

        bool unlocked = this.VerdantUnlocked;
        if (unlocked && !this.WasUnlocked)
        {
            this.WasUnlocked = true;
            Game1.playSound("discoverMineral");
            Game1.showGlobalMessage(ModEntry.T("boss.card.verdant_core.unlocked"));
        }
        else if (!unlocked)
        {
            this.WasUnlocked = false;
        }

        if (!this.VerdantActive)
            return;

        long now = Environment.TickCount64;
        if (now - this.LastHealAtMs < VerdantHealIntervalMs)
            return;

        int ticks = Math.Max(1, (int)((now - this.LastHealAtMs) / VerdantHealIntervalMs));
        this.LastHealAtMs += ticks * VerdantHealIntervalMs;
        int healWanted = ticks * VerdantHealPerTick;
        int before = Game1.player.health;
        Game1.player.health = Math.Min(Game1.player.maxHealth, Game1.player.health + healWanted);
        int healed = Math.Max(0, Game1.player.health - before);
        this.TotalHealing += healed;

        if (healed > 0 && now - this.LastPulseAtMs >= 900)
        {
            this.LastPulseAtMs = now;
            Game1.playSound("leafrustle");
        }
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!this.VerdantActive || Game1.player is null || Game1.currentLocation is null)
            return;

        Texture2D? icon = this.LoadIcon();
        if (icon is null)
            return;

        long now = Environment.TickCount64;
        float pulse = 1f + 0.10f * (float)Math.Sin(now / 110d);
        float alpha = 0.72f + 0.18f * (float)Math.Sin(now / 145d);
        Vector2 world = Game1.player.Position + new Vector2(32f, -24f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        e.SpriteBatch.Draw(
            icon,
            local,
            null,
            Color.White * Math.Clamp(alpha, 0.45f, 0.92f),
            0f,
            new Vector2(icon.Width / 2f, icon.Height / 2f),
            0.72f * pulse,
            SpriteEffects.None,
            Math.Clamp((Game1.player.Position.Y + 96f) / 10000f, 0f, 0.999f)
        );
    }

    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        if (!Context.IsWorldReady
            || !this.Config.EnableCombatCards
            || !this.Config.EnableCombatHud
            || !this.VerdantEquipped
            || Game1.activeClickableMenu is not null)
        {
            return;
        }

        Texture2D? icon = this.LoadIcon();
        if (icon is null)
            return;

        long now = Environment.TickCount64;
        string state;
        Color accent;
        if (this.VerdantActive)
        {
            state = ModEntry.T("boss.card.state.active", new { seconds = this.ActiveSecondsRemaining.ToString("0.0") });
            accent = new Color(126, 226, 113);
        }
        else if (this.CooldownSecondsRemaining > 0.05d)
        {
            state = ModEntry.T("boss.card.state.cooldown", new { seconds = this.CooldownSecondsRemaining.ToString("0.0") });
            accent = new Color(99, 145, 91);
        }
        else
        {
            state = ModEntry.T("boss.card.state.ready");
            accent = new Color(174, 232, 134);
        }

        const int size = 52;
        int x = 24;
        int y = Math.Clamp((int)(Game1.uiViewport.Height * 0.115f), 74, 124);
        Rectangle outer = new(x, y, 252, 62);
        e.SpriteBatch.Draw(Game1.staminaRect, outer, new Color(12, 27, 22) * 0.86f);
        e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle(outer.X, outer.Y, 4, outer.Height), accent * 0.95f);
        Rectangle iconRect = new(outer.X + 7, outer.Y + 5, size, size);
        e.SpriteBatch.Draw(icon, iconRect, Color.White);

        string title = ModEntry.T("boss.card.verdant_core.name");
        e.SpriteBatch.DrawString(Game1.smallFont, title, new Vector2(iconRect.Right + 9, outer.Y + 7), Color.White);
        e.SpriteBatch.DrawString(Game1.smallFont, state, new Vector2(iconRect.Right + 9, outer.Y + 31), accent);

        if (this.VerdantActive)
        {
            float ratio = (float)Math.Clamp(this.ActiveSecondsRemaining / (VerdantActiveDurationMs / 1000d), 0d, 1d);
            e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle(outer.X + 5, outer.Bottom - 5, (int)((outer.Width - 10) * ratio), 3), accent * 0.92f);
        }
        else if (this.CooldownSecondsRemaining > 0d)
        {
            float ratio = 1f - (float)Math.Clamp(this.CooldownSecondsRemaining / (VerdantCooldownMs / 1000d), 0d, 1d);
            e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle(outer.X + 5, outer.Bottom - 5, (int)((outer.Width - 10) * ratio), 3), accent * 0.75f);
        }
    }

    public string DebugUnlock()
    {
        if (!Context.IsWorldReady)
            return "Load a save first.";
        this.Save.Data.BossCardsUnlocked ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        bool added = this.Save.Data.BossCardsUnlocked.Add(VerdantCoreId);
        if (string.IsNullOrWhiteSpace(this.Save.Data.EquippedBossCardId))
            this.Save.Data.EquippedBossCardId = VerdantCoreId;
        this.Save.Save();
        this.WasUnlocked = true;
        return added ? "TEST: Verdant Core unlocked and equipped if the Boss Card slot was empty." : "Verdant Core was already unlocked.";
    }

    public string DebugEquip(string? id)
    {
        if (!Context.IsWorldReady)
            return "Load a save first.";

        id = (id ?? string.Empty).Trim();
        if (string.IsNullOrWhiteSpace(id) || id.Equals("none", StringComparison.OrdinalIgnoreCase))
        {
            this.Save.Data.EquippedBossCardId = string.Empty;
            this.Save.Save();
            this.ResetRuntime();
            return "Boss Card slot cleared.";
        }

        if (!id.Equals(VerdantCoreId, StringComparison.OrdinalIgnoreCase))
            return $"Unknown Boss Card '{id}'. Current runtime supports: {VerdantCoreId}.";
        if (!this.VerdantUnlocked)
            return "Verdant Core is still locked. Defeat Boss I or use cardcha_boss_card_unlock for testing.";

        this.Save.Data.EquippedBossCardId = VerdantCoreId;
        this.Save.Save();
        this.ResetRuntime();
        return "Verdant Core equipped in the dedicated Boss Card slot.";
    }

    public string DebugTrigger()
    {
        if (!Context.IsWorldReady || Game1.player is null)
            return "Load a save first.";
        if (!this.VerdantEquipped)
            return "Verdant Core must be unlocked and equipped first.";
        this.Activate(Environment.TickCount64, "debug force");
        return "TEST: Verdant Guard forced active for 6 seconds.";
    }

    public string Describe()
    {
        string equipped = string.IsNullOrWhiteSpace(this.Save.Data.EquippedBossCardId) ? "none" : this.Save.Data.EquippedBossCardId;
        return $"BossCardSlot={equipped} | VerdantUnlocked={this.VerdantUnlocked} | Active={this.VerdantActive} " +
               $"({this.ActiveSecondsRemaining:0.0}s) | Cooldown={this.CooldownSecondsRemaining:0.0}s | " +
               $"Guard=-{VerdantDamageReduction * 100:0}% dmg | Regen={VerdantHealPerTick}/s x {VerdantActiveDurationMs / 1000}s | " +
               $"Activations={this.ActivationCount} | TotalHealing={this.TotalHealing} | LastPrevented={this.LastPreventedDamage} | Reason={this.LastActivationReason}";
    }

    private void Activate(long now, string reason)
    {
        this.ActiveUntilMs = now + VerdantActiveDurationMs;
        this.CooldownUntilMs = now + VerdantCooldownMs;
        this.LastHealAtMs = now;
        this.LastPulseAtMs = now;
        this.LastActivationReason = reason;
        this.ActivationCount++;
        Game1.playSound("discoverMineral");
        Game1.showGlobalMessage(ModEntry.T("boss.card.verdant_core.activated"));
        this.Monitor.Log($"Verdant Core activated: reason={reason}, duration={VerdantActiveDurationMs}ms, cooldown={VerdantCooldownMs}ms.", LogLevel.Info);
    }

    private Texture2D? LoadIcon()
    {
        if (this.VerdantIcon is not null)
            return this.VerdantIcon;
        try
        {
            this.VerdantIcon = this.Helper.ModContent.Load<Texture2D>("assets/boss_cards/verdant_core_icon.png");
            return this.VerdantIcon;
        }
        catch (Exception ex)
        {
            ModEntry.LogOnce("verdant-core-icon", $"Couldn't load Verdant Core icon: {ex.Message}");
            return null;
        }
    }

    private void ResetRuntime()
    {
        this.ActiveUntilMs = 0;
        this.CooldownUntilMs = 0;
        this.LastHealAtMs = 0;
        this.LastPulseAtMs = 0;
        this.LastPreventedDamage = 0;
        this.LastActivationReason = "none";
    }
}

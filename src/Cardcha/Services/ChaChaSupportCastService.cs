using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Buffs;

namespace Cardcha.Services;

/// <summary>
/// One normal-form ChaCha Support Cast. Region skills are modules on this one cast, not
/// independent active skills. Cooldown is transient and never persisted.
/// </summary>
internal sealed class ChaChaSupportCastService
{
    private const string LuckBuffId = "Ronvotri.Cardcha_ChaChaLuck";
    private const int ShieldDurationMs = 20000;
    private const int LuckDurationMs = 10000;
    private const int CastModuleVisualMs = 1150;
    private const double EmergencyThreshold = 0.30d;
    private const double SpiritProcChance = 0.30d;
    private const double LuckProcChance = 0.50d;
    private const int LuckBuffAmount = 1;

    public static readonly double[] KillChanceByLevel = { 0.06d, 0.09d, 0.12d, 0.15d, 0.18d };
    public static readonly double[] LuckyDamageChanceByLevel = { 0.04d, 0.05d, 0.06d, 0.07d, 0.08d };
    public static readonly int[] CooldownSecondsByLevel = { 40, 35, 30, 25, 20 };
    public static readonly double[] VitalHealPercentByLevel = { 0.10d, 0.13d, 0.16d, 0.20d, 0.25d };
    public static readonly double[] ShieldReductionByLevel = { 0.20d, 0.25d, 0.30d, 0.35d, 0.40d };
    public static readonly double[] StaminaRestorePercentByLevel = { 0.10d, 0.15d, 0.20d, 0.25d, 0.30d };

    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly ChaChaSkillService Skills;
    private readonly Func<bool> IsBossFormActive;

    private long CooldownReadyAtMs;
    private long ShieldUntilMs;
    private double ShieldReduction;
    private long ModuleVisualUntilMs;
    private bool LastVisualShield;
    private bool LastVisualSpirit;
    private bool LastVisualLuck;
    private string LastTrigger = "none";
    private int LastHeal;
    private float LastStamina;
    private Queue<double>? DebugForcedRolls;
    private Texture2D? SkillIcons;
    private bool SkillIconsFailed;

    private long CastCount;
    private long KillCastCount;
    private long LuckyCastCount;
    private long EmergencyCastCount;
    private long SpiritProcCount;
    private long LuckProcCount;

    public ChaChaSupportCastService(
        IMonitor monitor,
        SaveService save,
        ChaChaSkillService skills,
        Func<bool> isBossFormActive)
    {
        this.Monitor = monitor;
        this.Save = save;
        this.Skills = skills;
        this.IsBossFormActive = isBossFormActive;
    }

    public bool IsShieldActive => Context.IsWorldReady && Environment.TickCount64 < this.ShieldUntilMs;
    public double CurrentShieldReduction => this.IsShieldActive ? Math.Max(0d, this.ShieldReduction) : 0d;
    public double CooldownSecondsRemaining => Math.Max(0d, (this.CooldownReadyAtMs - Environment.TickCount64) / 1000d);
    public bool CooldownReady => this.CooldownSecondsRemaining <= 0.001d;

    public static double GetKillChance(int level) => KillChanceByLevel[LevelIndex(level)];
    public static double GetLuckyDamageChance(int level) => LuckyDamageChanceByLevel[LevelIndex(level)];
    public static int GetCooldownSeconds(int level) => CooldownSecondsByLevel[LevelIndex(level)];
    public static double GetVitalHealPercent(int level) => VitalHealPercentByLevel[LevelIndex(level)];
    public static double GetShieldReduction(int level) => ShieldReductionByLevel[LevelIndex(level)];
    public static double GetStaminaRestorePercent(int level) => StaminaRestorePercentByLevel[LevelIndex(level)];

    /// <summary>Called from the deduplicated monster-death pipeline.</summary>
    public void OnMonsterKilled(Farmer? who)
    {
        if (!this.CanSupport(who) || !this.CooldownReady)
            return;

        int level = this.Skills.GetLevel(ChaChaSkillService.VitalSkillId);
        if (this.NextRoll() >= GetKillChance(level))
            return;

        if (this.PerformCast(who!, "kill", ignoreCooldown: false))
            this.KillCastCount++;
    }

    /// <summary>
    /// Called after Stardew has applied a real hit. healthAfterHit is captured before Cardcha's
    /// post-hit revive hooks so the 30% crossing contract reflects the hit itself.
    /// </summary>
    public void AfterFarmerTakesDamage(Farmer farmer, int healthBefore, int healthAfterHit)
    {
        if (!this.CanSupport(farmer) || healthAfterHit >= healthBefore)
            return;

        int level = this.Skills.GetLevel(ChaChaSkillService.VitalSkillId);
        bool lucky = this.NextRoll() < GetLuckyDamageChance(level);

        double beforeRatio = farmer.maxHealth > 0 ? healthBefore / (double)farmer.maxHealth : 1d;
        double afterRatio = farmer.maxHealth > 0 ? healthAfterHit / (double)farmer.maxHealth : 1d;
        bool emergency = beforeRatio > EmergencyThreshold && afterRatio <= EmergencyThreshold;

        if (!lucky && !emergency)
            return;

        string trigger = lucky && emergency ? "lucky+emergency" : emergency ? "emergency" : "lucky";
        if (!this.PerformCast(farmer, trigger, ignoreCooldown: true))
            return;

        if (lucky)
            this.LuckyCastCount++;
        if (emergency)
            this.EmergencyCastCount++;
    }

    /// <summary>Percent shield reduction is applied after Cardcha card reductions, before Stardew receives the hit.</summary>
    public int ModifyIncomingDamage(int damage, Farmer farmer)
    {
        if (damage <= 0 || farmer?.IsLocalPlayer != true || !this.IsShieldActive)
            return damage;

        double reduction = Math.Clamp(this.CurrentShieldReduction, 0d, 0.95d);
        if (reduction <= 0d)
            return damage;

        return Math.Max(1, (int)Math.Ceiling(damage * (1d - reduction)));
    }

    public void OnDayStarted(object? sender, DayStartedEventArgs e) => this.ResetRuntime(removeLuckBuff: true);
    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e) => this.ResetRuntime(removeLuckBuff: false);

    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned || !this.Skills.HasSkill(ChaChaSkillService.VitalSkillId))
            return;
        if (Game1.activeClickableMenu is not null || Game1.eventUp)
            return;

        this.TryLoadIcons();
        Rectangle panel = new(16, 154, 62, 76);
        e.SpriteBatch.Draw(Game1.staminaRect, panel, new Color(31, 25, 39) * 0.82f);
        DrawBorder(e.SpriteBatch, panel, this.CooldownReady ? new Color(133, 255, 195) : new Color(199, 151, 224), 2);

        Rectangle iconRect = new(panel.X + 9, panel.Y + 7, 44, 44);
        if (this.SkillIcons is not null)
            e.SpriteBatch.Draw(this.SkillIcons, iconRect, new Rectangle(0, 0, 32, 32), Color.White);
        else
            e.SpriteBatch.Draw(Game1.staminaRect, iconRect, new Color(91, 210, 158) * 0.62f);

        string label = this.CooldownReady ? "READY" : $"{Math.Ceiling(this.CooldownSecondsRemaining):0}s";
        Vector2 size = Game1.smallFont.MeasureString(label);
        e.SpriteBatch.DrawString(Game1.smallFont, label, new Vector2(panel.Center.X - size.X / 2f, panel.Bottom - 23), Color.White * 0.90f);
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned || Game1.player is null)
            return;

        long now = Environment.TickCount64;
        Vector2 playerCenter = Game1.GlobalToLocal(Game1.viewport, Game1.player.Position + new Vector2(32f, 34f));
        double seconds = Game1.currentGameTime.TotalGameTime.TotalSeconds;

        if (this.IsShieldActive)
        {
            float pulse = 0.55f + 0.18f * (float)Math.Sin(seconds * 4.2);
            DrawDiamond(e.SpriteBatch, playerCenter, 34f + pulse * 5f, new Color(118, 194, 255) * (0.24f + pulse * 0.18f));
            DrawDiamond(e.SpriteBatch, playerCenter, 27f + pulse * 3f, new Color(246, 181, 241) * 0.20f);
        }

        if (now < this.ModuleVisualUntilMs)
        {
            float remaining = Math.Clamp((this.ModuleVisualUntilMs - now) / (float)CastModuleVisualMs, 0f, 1f);
            if (this.LastVisualShield)
                DrawDiamond(e.SpriteBatch, playerCenter, 42f + (1f - remaining) * 16f, new Color(135, 207, 255) * (0.46f * remaining));

            if (this.LastVisualSpirit)
            {
                for (int i = 0; i < 6; i++)
                {
                    float phase = (float)(seconds * 4.5 + i * MathHelper.TwoPi / 6f);
                    Vector2 p = playerCenter + new Vector2((float)Math.Cos(phase) * 34f, (float)Math.Sin(phase) * 19f - 10f);
                    e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle((int)p.X - 2, (int)p.Y - 5, 4, 10), new Color(103, 235, 244) * (0.62f * remaining));
                }
            }

            if (this.LastVisualLuck)
            {
                for (int i = 0; i < 7; i++)
                {
                    float phase = (float)(seconds * 3.8 + i * MathHelper.TwoPi / 7f);
                    Vector2 p = playerCenter + new Vector2((float)Math.Cos(phase) * 40f, (float)Math.Sin(phase) * 24f - 18f);
                    int s = i % 2 == 0 ? 5 : 3;
                    e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle((int)p.X - s / 2, (int)p.Y - s / 2, s, s), new Color(255, 221, 99) * (0.72f * remaining));
                }
            }
        }
    }

    internal void DebugSetForcedRolls(params double[] rolls)
        => this.DebugForcedRolls = new Queue<double>((rolls ?? Array.Empty<double>()).Select(v => Math.Clamp(v, 0d, 0.999999999d)));

    public bool DebugForceCast(string trigger = "debug")
        => Context.IsWorldReady && Game1.player is not null && this.PerformCast(Game1.player, trigger, ignoreCooldown: true);

    public string Describe()
    {
        int vital = this.Skills.GetLevel(ChaChaSkillService.VitalSkillId);
        return $"SupportCast={(this.Skills.HasSkill(ChaChaSkillService.VitalSkillId) ? "learned" : "locked")} | " +
               $"VitalLv={vital} | KillChance={(vital > 0 ? GetKillChance(vital) : 0):P0} | LuckyDamage={(vital > 0 ? GetLuckyDamageChance(vital) : 0):P0} | " +
               $"Cooldown={(vital > 0 ? GetCooldownSeconds(vital) : 0)}s / remaining={this.CooldownSecondsRemaining:0.0}s | " +
               $"Shield={(this.IsShieldActive ? $"ON {this.CurrentShieldReduction:P0}" : "off")} | " +
               $"Casts={this.CastCount} (kill={this.KillCastCount}, lucky={this.LuckyCastCount}, emergency={this.EmergencyCastCount}) | " +
               $"SpiritProcs={this.SpiritProcCount} | LuckProcs={this.LuckProcCount} | Last={this.LastTrigger} heal={this.LastHeal} stamina={this.LastStamina:0.#}";
    }

    private bool PerformCast(Farmer farmer, string trigger, bool ignoreCooldown)
    {
        if (!this.CanSupport(farmer))
            return false;
        if (!ignoreCooldown && !this.CooldownReady)
            return false;
        if (farmer.health <= 0)
            return false;

        int vitalLevel = this.Skills.GetLevel(ChaChaSkillService.VitalSkillId);
        int heal = Math.Max(1, (int)Math.Ceiling(farmer.maxHealth * GetVitalHealPercent(vitalLevel)));
        int beforeHealth = farmer.health;
        farmer.health = Math.Min(farmer.maxHealth, farmer.health + heal);
        this.LastHeal = Math.Max(0, farmer.health - beforeHealth);

        bool shield = this.Skills.HasSkill(ChaChaSkillService.GuardSkillId);
        if (shield)
        {
            int guardLevel = this.Skills.GetLevel(ChaChaSkillService.GuardSkillId);
            this.ShieldReduction = GetShieldReduction(guardLevel);
            this.ShieldUntilMs = Environment.TickCount64 + ShieldDurationMs;
        }

        bool spirit = false;
        this.LastStamina = 0f;
        if (this.Skills.HasSkill(ChaChaSkillService.SpiritSkillId) && this.NextRoll() < SpiritProcChance)
        {
            int spiritLevel = this.Skills.GetLevel(ChaChaSkillService.SpiritSkillId);
            float max = Math.Max(1f, farmer.MaxStamina);
            float restore = (float)Math.Ceiling(max * GetStaminaRestorePercent(spiritLevel));
            float before = farmer.Stamina;
            farmer.Stamina = Math.Min(max, farmer.Stamina + restore);
            this.LastStamina = Math.Max(0f, farmer.Stamina - before);
            spirit = true;
            this.SpiritProcCount++;
        }

        bool luck = false;
        if (this.Skills.HasSkill(ChaChaSkillService.LuckSkillId) && this.NextRoll() < LuckProcChance)
        {
            this.ApplyLuckBuff(farmer);
            luck = true;
            this.LuckProcCount++;
        }

        this.Skills.TriggerCastPresentation();
        this.ModuleVisualUntilMs = Environment.TickCount64 + CastModuleVisualMs;
        this.LastVisualShield = shield;
        this.LastVisualSpirit = spirit;
        this.LastVisualLuck = luck;
        this.LastTrigger = trigger;
        this.CastCount++;
        this.CooldownReadyAtMs = Environment.TickCount64 + GetCooldownSeconds(vitalLevel) * 1000L;

        if (trigger.Contains("emergency", StringComparison.OrdinalIgnoreCase))
            Game1.playSound("yoba");
        else
            Game1.playSound("discoverMineral");

        this.Monitor.Log(
            $"ChaCha Support Cast: trigger={trigger}, vitalLv={vitalLevel}, heal={this.LastHeal}, shield={shield}, spirit={spirit}, luck={luck}, cooldown={GetCooldownSeconds(vitalLevel)}s.",
            LogLevel.Trace
        );
        return true;
    }

    private bool CanSupport(Farmer? farmer)
        => Context.IsWorldReady
           && farmer?.IsLocalPlayer == true
           && this.Save.Data.ChaChaLoaned
           && this.Skills.HasSkill(ChaChaSkillService.VitalSkillId)
           && !this.IsBossFormActive();

    private void ApplyLuckBuff(Farmer farmer)
    {
        BuffEffects effects = new();
        effects.LuckLevel.Value = LuckBuffAmount;
        Buff buff = new(
            id: LuckBuffId,
            displayName: "ChaCha",
            iconTexture: Game1.mouseCursors,
            iconSheetIndex: 0,
            duration: LuckDurationMs,
            effects: effects
        );
        buff.visible = false;
        farmer.applyBuff(buff);
    }

    private double NextRoll()
        => this.DebugForcedRolls is { Count: > 0 }
            ? this.DebugForcedRolls.Dequeue()
            : Game1.random.NextDouble();

    private void ResetRuntime(bool removeLuckBuff)
    {
        this.CooldownReadyAtMs = 0;
        this.ShieldUntilMs = 0;
        this.ShieldReduction = 0d;
        this.ModuleVisualUntilMs = 0;
        this.LastVisualShield = false;
        this.LastVisualSpirit = false;
        this.LastVisualLuck = false;
        this.LastTrigger = "none";
        this.LastHeal = 0;
        this.LastStamina = 0f;
        this.DebugForcedRolls = null;
        if (removeLuckBuff && Context.IsWorldReady && Game1.player?.hasBuff(LuckBuffId) == true)
            Game1.player.buffs.Remove(LuckBuffId);
    }

    private void TryLoadIcons()
    {
        if (this.SkillIcons is not null || this.SkillIconsFailed)
            return;
        try
        {
            this.SkillIcons = Game1.content.Load<Texture2D>(ItemAssetService.ChaChaSkillIconsTextureAsset);
        }
        catch
        {
            this.SkillIconsFailed = true;
        }
    }

    private static int LevelIndex(int level) => Math.Clamp(level, 1, 5) - 1;

    private static void DrawBorder(SpriteBatch batch, Rectangle rect, Color color, int thickness)
    {
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, rect.Width, thickness), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Bottom - thickness, rect.Width, thickness), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, thickness, rect.Height), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.Right - thickness, rect.Y, thickness, rect.Height), color);
    }

    private static void DrawDiamond(SpriteBatch batch, Vector2 center, float radius, Color color)
    {
        int r = Math.Max(2, (int)Math.Round(radius));
        for (int y = -r; y <= r; y += Math.Max(2, r / 7))
        {
            int half = Math.Max(1, r - Math.Abs(y));
            batch.Draw(Game1.staminaRect, new Rectangle((int)center.X - half, (int)center.Y + y, half * 2, 2), color * 0.34f);
        }
    }
}

from pathlib import Path
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.4'


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'missing anchor: {label}')
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# Version
# -----------------------------------------------------------------------------
manifest = json.loads(read('manifest.json'))
manifest['Version'] = VERSION
write('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

s = read('Cardcha.csproj')
s = re.sub(r'<Version>[^<]+</Version>', f'<Version>{VERSION}</Version>', s, count=1)
write('Cardcha.csproj', s)

s = read('Directory.Build.targets')
s = re.sub(r'0\.3\.0-alpha\.28\.0\.4\.14\.4\.3', VERSION, s)
write('Directory.Build.targets', s)


# -----------------------------------------------------------------------------
# Canon docs: the user approved the outstanding balance pass.
# -----------------------------------------------------------------------------
canon = '''# ChaCha Support Cast Canon\n\nTarget phase: `0.3.0-alpha.28.0.4.14.4.4`\n\nChaCha has **one normal-form Support Cast**. The four Region skills are modular upgrades to this same cast, never four independent active skills or four cooldowns. Boss Form / Mythic Echo remains separate.\n\n## Shared trigger level\n\nThe Support Cast trigger table uses **Vital Blessing level** (Lv1-Lv5).\n\n| Level | Kill Cast after a monster kill | Lucky Cast when taking damage | Shared cooldown | Vital heal |\n| --- | ---: | ---: | ---: | ---: |\n| Lv1 | 6% | 4% | 40s | 10% Max HP |\n| Lv2 | 9% | 5% | 35s | 13% Max HP |\n| Lv3 | 12% | 6% | 30s | 16% Max HP |\n| Lv4 | 15% | 7% | 25s | 20% Max HP |\n| Lv5 | 18% | 8% | 20s | 25% Max HP |\n\n### Kill Cast\n- Roll after the local player kills a monster.\n- Requires the shared cooldown to be ready.\n- A failed roll does not start cooldown.\n\n### Lucky Cast on damage\n- Roll on every **actual health-damaging hit**.\n- A successful roll casts immediately regardless of HP or cooldown.\n\n### Emergency Cast\n- If HP was **above 30% before the hit** and becomes **30% or lower after the hit**, cast once with 100% certainty.\n- Emergency Cast ignores cooldown.\n- If the player was already at or below 30%, later hits do not retrigger Emergency until HP first returns above 30%.\n\n### Deduplication\nA single damage event can satisfy Lucky + Emergency together, but creates **one cast only**. After any successful cast, the shared cooldown restarts from the current Vital level's full duration.\n\n## Region modules\n\n### Region I: Phúc Lành Sinh Khí / Vital Blessing\nEvery Support Cast heals the player by the Vital heal table above. Material: **Giọt Sương Sinh Khí / Vital Dewdrop**.\n\n### Region II: Hộ Mệnh Thỏ Tiên / Bunny Aegis\nOnce learned, every Support Cast refreshes a **20 second shield**. Incoming damage reduction by Aegis level: **20 / 25 / 30 / 35 / 40%**. Material: **Mảnh Khiên Ánh Trăng / Moonshield Shard**.\n\n### Region III: Tinh Linh Tiếp Sức / Spirit Aid\nOnce learned, every Support Cast rolls **30%** to restore stamina. Restore by Spirit Aid level: **10 / 15 / 20 / 25 / 30% Max Stamina**. Material: **Lông Vũ Gió Nhẹ / Breeze Feather**.\n\n### Region IV: Phúc Vận Thỏ Tiên / Lucky Echo\nOnce learned, every Support Cast rolls **50%** to apply a **+1 Luck buff for 10 seconds**. Material: **Đồng Xu Phúc Tinh / Fortune Coin**. The 50% proc chance and 10s duration do not fragment into another cooldown.\n\n## Visual / input contract\n- One automatic Support Cast action from ChaCha.\n- One HUD icon and one cooldown.\n- No new combat button.\n- Base heal pulse always appears. Shield, stamina and luck visuals layer onto the same cast only when learned/procced.\n- Normal-form Support Cast is disabled while Boss Form is active.\n\n## Regression locks\n- Save schema stays 19; cooldown/buffs are runtime-only.\n- Airship Resonance Pedestal + four upgrade materials remain.\n- `card_icons.png` SHA-256 stays `c5ff456e9a0a697a10537a391ec5abf2f90966de89299799fd2153356b1e6e41`.\n- Airship visual SHA-256 stays `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.\n- Boss Form duration stays 10 seconds and existing activation controls stay unchanged.\n- Forest collision/map edits remain NONE.\n- Card auto audit remains 76/76 PASS.\n'''
Path('docs/chacha-support-cast-canon.md').write_text(canon, encoding='utf-8')


# -----------------------------------------------------------------------------
# Runtime service
# -----------------------------------------------------------------------------
support = r'''using Microsoft.Xna.Framework;
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
'''
write('Services/ChaChaSupportCastService.cs', support)


# -----------------------------------------------------------------------------
# Farmer damage hook: shield before damage; Lucky/Emergency after actual hit.
# -----------------------------------------------------------------------------
s = read('Patches/FarmerDamagePatch.cs')
if 'ChaChaSupportCastService? Support' not in s:
    s = s.replace(
        '    private static CombatService? Combat;\n    private static CardTestArenaService? TestArena;\n',
        '    private static CombatService? Combat;\n    private static ChaChaSupportCastService? Support;\n    private static CardTestArenaService? TestArena;\n'
    )
    s = s.replace(
        '    public static void Apply(Harmony harmony, CombatService combat, CardTestArenaService? testArena = null)\n    {\n        Combat = combat;\n        TestArena = testArena;\n',
        '    public static void Apply(Harmony harmony, CombatService combat, ChaChaSupportCastService support, CardTestArenaService? testArena = null)\n    {\n        Combat = combat;\n        Support = support;\n        TestArena = testArena;\n'
    )
    s = s.replace(
        '            if (Combat is not null)\n                damage = Combat.ModifyFarmerDamage(damage, __instance, damager);\n',
        '            if (Combat is not null)\n                damage = Combat.ModifyFarmerDamage(damage, __instance, damager);\n            if (Support is not null)\n                damage = Support.ModifyIncomingDamage(damage, __instance);\n'
    )
    s = s.replace(
        '        try\n        {\n            Combat?.AfterFarmerTakesDamage(__instance, __state);\n            TestArena?.AfterFarmerDamage(__instance);\n',
        '        try\n        {\n            int healthAfterHit = __instance.health;\n            Combat?.AfterFarmerTakesDamage(__instance, __state);\n            Support?.AfterFarmerTakesDamage(__instance, __state, healthAfterHit);\n            TestArena?.AfterFarmerDamage(__instance);\n'
    )
write('Patches/FarmerDamagePatch.cs', s)


# -----------------------------------------------------------------------------
# Monster death pipeline: one deduplicated kill roll.
# -----------------------------------------------------------------------------
s = read('Services/MonsterDeathService.cs')
if 'private readonly ChaChaSupportCastService Support;' not in s:
    s = s.replace(
        '    private readonly ChaChaSkillMaterialService Materials;\n',
        '    private readonly ChaChaSkillMaterialService Materials;\n    private readonly ChaChaSupportCastService Support;\n'
    )
    s = s.replace(
        '    public MonsterDeathService(DropService drops, CombatService combat, ChaChaSkillMaterialService materials)\n    {\n        this.Drops = drops;\n        this.Combat = combat;\n        this.Materials = materials;\n',
        '    public MonsterDeathService(DropService drops, CombatService combat, ChaChaSkillMaterialService materials, ChaChaSupportCastService support)\n    {\n        this.Drops = drops;\n        this.Combat = combat;\n        this.Materials = materials;\n        this.Support = support;\n'
    )
    s = s.replace(
        '        this.Materials.TryDrop(resolvedLocation, monster.Position, who, scale);\n',
        '        this.Materials.TryDrop(resolvedLocation, monster.Position, who, scale);\n        this.Support.OnMonsterKilled(who);\n',
        1
    )
    s = s.replace(
        '        this.Materials.TryDrop(location, position, who, scale);\n',
        '        this.Materials.TryDrop(location, position, who, scale);\n        this.Support.OnMonsterKilled(who);\n',
        1
    )
write('Services/MonsterDeathService.cs', s)


# -----------------------------------------------------------------------------
# ChaCha skill foundation wording: modules are all learned-on-discovery, not active slots.
# Keep legacy ActiveChaChaSkillId only for save compatibility.
# -----------------------------------------------------------------------------
s = read('Services/ChaChaSkillService.cs')
s = s.replace(
    '/// Persistent ChaCha normal-form skill foundation.\n/// Skills are exploration rewards, independent from Mythic Echo/Boss Form.\n/// This pass deliberately leaves the first skill\'s healing balance uncommitted until the\n/// previously-agreed values are recovered/confirmed; discovery, equip, level persistence and\n/// ChaCha cast presentation are real and testable now.',
    '/// Persistent ChaCha normal-form skill/module foundation.\n/// Skills are exploration rewards and modules on one Support Cast, independent from Mythic Echo/Boss Form.\n/// ActiveChaChaSkillId remains only as a legacy save field; learned modules no longer compete for an active slot.'
)
s = s.replace(
    '           "SkillEffects=DESIGN_LOCK_PENDING (normal-form runtime effects are not enabled yet)";',
    '           "SupportCastRuntime=ENABLED (learned Region skills are modules on one shared cast)";'
)
write('Services/ChaChaSkillService.cs', s)


# -----------------------------------------------------------------------------
# Resonance UI: learned modules, no equip/select model. Replace old collection Support tab.
# -----------------------------------------------------------------------------
s = read('UI/ChaChaResonanceMenu.cs')
old = '''        if (this.CurrentTab == ResonanceTab.Abilities)\n        {\n            ChaChaSkillService? skills = ModEntry.StaticChaChaSkills;\n            string skillId = ChaChaSkillMaterialService.GetSkillIdForIndex(index);\n            if (skills is not null && skills.HasSkill(skillId))\n            {\n                skills.SetActive(skillId);\n                this.Status = ModEntry.T("resonance.ability.equipped", new { name = ModEntry.T($"chacha.skill.{skillId}.name") });\n                return;\n            }\n\n            this.Status = ModEntry.T("resonance.ability.find-region", new { region = index + 1 });\n            Game1.playSound("cancel");\n            return;\n        }\n'''
new = '''        if (this.CurrentTab == ResonanceTab.Abilities)\n        {\n            ChaChaSkillService? skills = ModEntry.StaticChaChaSkills;\n            string skillId = ChaChaSkillMaterialService.GetSkillIdForIndex(index);\n            if (skills is not null && skills.HasSkill(skillId))\n            {\n                this.Status = ModEntry.T("resonance.ability.module-active", new { name = ModEntry.T($"chacha.skill.{skillId}.name") });\n                Game1.playSound("smallSelect");\n                return;\n            }\n\n            this.Status = ModEntry.T("resonance.ability.find-region", new { region = index + 1 });\n            Game1.playSound("cancel");\n            return;\n        }\n'''
if old in s:
    s = s.replace(old, new, 1)

s = s.replace('            bool active = skills?.IsActive(skillId) == true;\n', '')
s = s.replace(
    '            string bottom = found\n                ? active ? ModEntry.T("resonance.ability.active") : ModEntry.T("resonance.ability.select")\n                : ModEntry.T("resonance.ability.normal-form");',
    '            string bottom = found\n                ? ModEntry.T("resonance.ability.module-on")\n                : ModEntry.T("resonance.ability.normal-form");'
)
s = s.replace(
    '                active ? CardchaUi.Gold : Color.White * 0.56f,',
    '                found ? CardchaUi.Gold : Color.White * 0.56f,'
)

# Replace SupportProgress with live Support Cast data.
start = s.find('    private void DrawSupportProgress(SpriteBatch b, Color pink)')
end = s.find('    private void DrawSupportBlock(', start)
if start < 0 or end < 0:
    raise RuntimeError('missing DrawSupportProgress block')
new_support_ui = r'''    private void DrawSupportProgress(SpriteBatch b, Color pink)
    {
        if (this.EntryButtons.Count < 3)
            return;

        ChaChaSkillService? skills = ModEntry.StaticChaChaSkills;
        ChaChaSupportCastService? support = ModEntry.StaticChaChaSupport;
        int vital = skills?.GetLevel(ChaChaSkillService.VitalSkillId) ?? 0;
        double kill = vital > 0 ? ChaChaSupportCastService.GetKillChance(vital) : 0d;
        double lucky = vital > 0 ? ChaChaSupportCastService.GetLuckyDamageChance(vital) : 0d;
        int cooldown = vital > 0 ? ChaChaSupportCastService.GetCooldownSeconds(vital) : 0;
        double heal = vital > 0 ? ChaChaSupportCastService.GetVitalHealPercent(vital) : 0d;

        this.DrawSupportBlock(
            b,
            this.EntryButtons[0],
            ModEntry.T("resonance.support.cast.title"),
            ModEntry.T("resonance.support.cast.body", new
            {
                level = vital,
                kill = Math.Round(kill * 100d),
                cooldown,
                heal = Math.Round(heal * 100d),
                remaining = support?.CooldownSecondsRemaining.ToString("0.0") ?? "0.0"
            }),
            new Color(91, 87, 132),
            pink
        );

        this.DrawSupportBlock(
            b,
            this.EntryButtons[1],
            ModEntry.T("resonance.support.rescue.title"),
            ModEntry.T("resonance.support.rescue.body", new { lucky = Math.Round(lucky * 100d) }),
            new Color(80, 88, 128),
            pink
        );

        int learned = ChaChaSkillService.SkillIds.Count(id => skills?.HasSkill(id) == true);
        this.DrawSupportBlock(
            b,
            this.EntryButtons[2],
            ModEntry.T("resonance.support.modules.title"),
            ModEntry.T("resonance.support.modules.body", new { learned }),
            new Color(103, 75, 112),
            pink
        );
    }

'''
s = s[:start] + new_support_ui + s[end:]
write('UI/ChaChaResonanceMenu.cs', s)


# -----------------------------------------------------------------------------
# ModEntry wiring. BossForm is instantiated before Support so normal-form guard is available.
# -----------------------------------------------------------------------------
s = read('ModEntry.cs')
if 'internal static ChaChaSupportCastService? StaticChaChaSupport;' not in s:
    s = s.replace(
        '    internal static ChaChaSkillService? StaticChaChaSkills;\n',
        '    internal static ChaChaSkillService? StaticChaChaSkills;\n    internal static ChaChaSupportCastService? StaticChaChaSupport;\n'
    )
if 'private ChaChaSupportCastService ChaChaSupport = null!;' not in s:
    s = s.replace(
        '    private ChaChaSkillService ChaChaSkills = null!;\n',
        '    private ChaChaSkillService ChaChaSkills = null!;\n    private ChaChaSupportCastService ChaChaSupport = null!;\n'
    )

old_init = '''        this.WorldActors = new WorldActorService(this.Monitor);\n        this.ChaChaSkills = new ChaChaSkillService(helper, this.Monitor, this.Save, this.WorldActors);\n        StaticChaChaSkills = this.ChaChaSkills;\n        this.ChaChaMaterials = new ChaChaSkillMaterialService(helper, this.Monitor, this.Save, this.ChaChaSkills, this.Controller);\n        this.Progression = new ProgressionService(helper, this.Monitor, this.Save);\n'''
new_init = '''        this.WorldActors = new WorldActorService(this.Monitor);\n        this.ChaChaSkills = new ChaChaSkillService(helper, this.Monitor, this.Save, this.WorldActors);\n        StaticChaChaSkills = this.ChaChaSkills;\n        this.ChaChaBossForm = new ChaChaBossFormService(\n            helper, this.Monitor, this.Save, this.BossEnergy, this.WorldActors, this.Controller\n        );\n        this.ChaChaSupport = new ChaChaSupportCastService(this.Monitor, this.Save, this.ChaChaSkills, () => this.ChaChaBossForm.IsActive);\n        StaticChaChaSupport = this.ChaChaSupport;\n        this.ChaChaMaterials = new ChaChaSkillMaterialService(helper, this.Monitor, this.Save, this.ChaChaSkills, this.Controller);\n        this.Progression = new ProgressionService(helper, this.Monitor, this.Save);\n'''
if old_init in s:
    s = s.replace(old_init, new_init, 1)

s = s.replace(
    '        this.Deaths = new MonsterDeathService(this.Drops, this.Combat, this.ChaChaMaterials);\n',
    '        this.Deaths = new MonsterDeathService(this.Drops, this.Combat, this.ChaChaMaterials, this.ChaChaSupport);\n',
    1
)

# Remove old later BossForm initialization if still present.
old_boss = '''        this.ChaChaBossForm = new ChaChaBossFormService(\n            helper, this.Monitor, this.Save, this.BossEnergy, this.WorldActors, this.Controller\n        );\n'''
first = s.find(old_boss)
if first >= 0:
    second = s.find(old_boss, first + 1)
    if second >= 0:
        s = s[:second] + s[second + len(old_boss):]

if 'this.ChaChaSupport.OnDayStarted' not in s:
    s = s.replace(
        '        helper.Events.GameLoop.DayStarted += this.ChaChaBossForm.OnDayStarted;\n',
        '        helper.Events.GameLoop.DayStarted += this.ChaChaBossForm.OnDayStarted;\n        helper.Events.GameLoop.DayStarted += this.ChaChaSupport.OnDayStarted;\n'
    )
if 'this.ChaChaSupport.OnReturnedToTitle' not in s:
    s = s.replace(
        '        helper.Events.GameLoop.ReturnedToTitle += this.ChaChaSkills.OnReturnedToTitle;\n',
        '        helper.Events.GameLoop.ReturnedToTitle += this.ChaChaSkills.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.ChaChaSupport.OnReturnedToTitle;\n'
    )
if 'this.ChaChaSupport.OnRenderedHud' not in s:
    s = s.replace(
        '        helper.Events.Display.RenderedHud += this.ChaChaBossForm.OnRenderedHud;\n',
        '        helper.Events.Display.RenderedHud += this.ChaChaBossForm.OnRenderedHud;\n        helper.Events.Display.RenderedHud += this.ChaChaSupport.OnRenderedHud;\n'
    )
if 'this.ChaChaSupport.OnRenderedWorld' not in s:
    s = s.replace(
        '        helper.Events.Display.RenderedWorld += this.ChaChaSkills.OnRenderedWorld;\n',
        '        helper.Events.Display.RenderedWorld += this.ChaChaSkills.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.ChaChaSupport.OnRenderedWorld;\n'
    )

s = s.replace(
    '        FarmerDamagePatch.Apply(harmony, this.Combat, this.CardArena);\n',
    '        FarmerDamagePatch.Apply(harmony, this.Combat, this.ChaChaSupport, this.CardArena);\n',
    1
)

if 'cardcha_chacha_support_status' not in s:
    anchor = '        helper.ConsoleCommands.Add("cardcha_chacha_material_status", "Show ChaCha region-material and Airship station state.", this.CommandChaChaMaterialStatus);\n'
    addition = anchor + '''        helper.ConsoleCommands.Add("cardcha_chacha_support_status", "Show ChaCha one-cast support runtime state.", (_, _) => this.Monitor.Log("===== CHACHA SUPPORT CAST =====\\n" + this.ChaChaSupport.Describe(), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_chacha_support_force", "TEST ONLY: force one ChaCha Support Cast, bypassing cooldown.", (_, args) =>\n        {\n            if (!Context.IsWorldReady) return;\n            bool ok = this.ChaChaSupport.DebugForceCast(args.FirstOrDefault() ?? "debug");\n            this.Monitor.Log(ok ? "TEST: ChaCha Support Cast forced." : "TEST: Support Cast unavailable (unlock Vital/ChaCha or leave Boss Form).", ok ? LogLevel.Alert : LogLevel.Warn);\n        });\n'''
    s = replace_once(s, anchor, addition, 'support console commands')

s = re.sub(
    r'Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14\.4\.3 CHACHA SKILL MATERIALS \+ AIRSHIP STATION TEST',
    f'Cardcha! v{VERSION} CHACHA SUPPORT CAST RUNTIME TEST',
    s
)
write('ModEntry.cs', s)


# -----------------------------------------------------------------------------
# i18n
# -----------------------------------------------------------------------------
for rel, values in [
    ('i18n/default.json', {
        'resonance.ability.module-active': '{{name}} is learned and automatically joins ChaCha Support Cast.',
        'resonance.ability.module-on': 'LEARNED • Module joins the same Support Cast',
        'resonance.support.cast.title': 'ChaCha Support Cast',
        'resonance.support.cast.body': 'Vital Lv{{level}} • Kill Cast {{kill}}% • Heal {{heal}}% Max HP • Cooldown {{cooldown}}s • Remaining {{remaining}}s',
        'resonance.support.rescue.title': 'Damage Rescue',
        'resonance.support.rescue.body': 'Every damaging hit rolls {{lucky}}% Lucky Cast. Crossing from above 30% HP to 30% or lower guarantees one Emergency Cast. Both ignore cooldown.',
        'resonance.support.modules.title': 'One Cast • Growing Modules',
        'resonance.support.modules.body': '{{learned}}/4 Region modules learned. Aegis: shield 20s. Spirit Aid: 30% stamina proc. Lucky Echo: 50% chance for +1 Luck for 10s. No separate cooldowns.'
    }),
    ('i18n/vi.json', {
        'resonance.ability.module-active': '{{name}} đã học và tự động ghép vào Hỗ Trợ ChaCha.',
        'resonance.ability.module-on': 'ĐÃ HỌC • Tự ghép vào cùng một lần cast',
        'resonance.support.cast.title': 'Hỗ Trợ ChaCha',
        'resonance.support.cast.body': 'Sinh Khí Lv{{level}} • Cast khi hạ quái {{kill}}% • Hồi {{heal}}% Máu tối đa • Cooldown {{cooldown}}s • Còn {{remaining}}s',
        'resonance.support.rescue.title': 'Cứu Nguy Khi Nhận Sát Thương',
        'resonance.support.rescue.body': 'Mỗi hit gây mất máu roll {{lucky}}% Lucky Cast. Từ trên 30% tụt xuống ≤30% Máu sẽ chắc chắn Emergency Cast 1 lần. Cả hai bỏ qua cooldown.',
        'resonance.support.modules.title': 'Một Cast • Nhiều Module',
        'resonance.support.modules.body': 'Đã học {{learned}}/4 module. Khiên: 20s. Tiếp Sức: 30% hồi thể lực. Phúc Vận: 50% nhận +1 Luck trong 10s. Không có cooldown riêng.'
    })
]:
    data = json.loads(read(rel))
    data.update(values)
    write(rel, json.dumps(data, ensure_ascii=False, indent=2) + '\n')

print(f'Applied ChaCha Support Cast runtime {VERSION}; save schema remains 19')

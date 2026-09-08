from pathlib import Path
from PIL import Image, ImageDraw
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.28'

# ---------------- version bump ----------------
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.12\.27', VERSION, s)
    p.write_text(s, encoding='utf-8')

# ---------------- boss-card icon ----------------
asset_dir = ROOT / 'assets' / 'boss_cards'
asset_dir.mkdir(parents=True, exist_ok=True)
icon = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
d = ImageDraw.Draw(icon)
# Outer living-ring silhouette.
d.ellipse((5, 5, 58, 58), fill=(24, 62, 43, 235), outline=(155, 225, 126, 255), width=3)
d.ellipse((11, 11, 52, 52), fill=(15, 40, 31, 245), outline=(77, 157, 89, 255), width=2)
# Four broad leaves around the core.
leaf = (92, 184, 95, 255)
d.polygon([(31, 9), (24, 25), (31, 30), (38, 25)], fill=leaf)
d.polygon([(55, 31), (39, 24), (34, 31), (39, 38)], fill=leaf)
d.polygon([(31, 55), (24, 39), (31, 34), (38, 39)], fill=leaf)
d.polygon([(9, 31), (25, 24), (30, 31), (25, 38)], fill=leaf)
# Crystalline Verdant Core.
d.polygon([(32, 17), (43, 29), (39, 43), (32, 49), (25, 43), (21, 29)], fill=(126, 242, 116, 255), outline=(218, 255, 179, 255))
d.polygon([(32, 21), (38, 30), (35, 39), (32, 44), (29, 39), (26, 30)], fill=(67, 182, 88, 255))
d.ellipse((29, 27, 35, 33), fill=(235, 255, 187, 255))
icon.save(asset_dir / 'verdant_core_icon.png')

# ---------------- runtime service ----------------
service = r'''using Microsoft.Xna.Framework;
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
'''
(ROOT / 'Services' / 'BossCardService.cs').write_text(service, encoding='utf-8')

# ---------------- hook incoming damage ----------------
damage_path = ROOT / 'Patches' / 'FarmerDamagePatch.cs'
damage = damage_path.read_text(encoding='utf-8')
damage = damage.replace(
    '    private static CardTestArenaService? TestArena;\n',
    '    private static CardTestArenaService? TestArena;\n    private static BossCardService? BossCards;\n',
    1
)
damage = damage.replace(
    '    public static void Apply(Harmony harmony, CombatService combat, ChaChaSupportCastService support, CardTestArenaService? testArena = null)\n',
    '    public static void Apply(Harmony harmony, CombatService combat, ChaChaSupportCastService support, CardTestArenaService? testArena, BossCardService bossCards)\n',
    1
)
damage = damage.replace(
    '        TestArena = testArena;\n',
    '        TestArena = testArena;\n        BossCards = bossCards;\n',
    1
)
damage = damage.replace(
    '            if (Support is not null)\n                damage = Support.ModifyIncomingDamage(damage, __instance);\n',
    '            if (Support is not null)\n                damage = Support.ModifyIncomingDamage(damage, __instance);\n            if (BossCards is not null)\n                damage = BossCards.ModifyIncomingDamage(damage, __instance);\n',
    1
)
damage_path.write_text(damage, encoding='utf-8')

# ---------------- wire service into ModEntry ----------------
mod_path = ROOT / 'ModEntry.cs'
mod = mod_path.read_text(encoding='utf-8')
mod = mod.replace(
    '    private BossEnergyService BossEnergy = null!;\n',
    '    private BossEnergyService BossEnergy = null!;\n    private BossCardService BossCards = null!;\n',
    1
)
mod = mod.replace(
    '        this.BossEnergy = new BossEnergyService(this.Loadout, this.Cards, this.Upgrades);\n',
    '        this.BossEnergy = new BossEnergyService(this.Loadout, this.Cards, this.Upgrades);\n        this.BossCards = new BossCardService(helper, this.Monitor, this.Save, this.Config);\n',
    1
)
mod = mod.replace(
    '        helper.Events.GameLoop.SaveLoaded += this.CardArena.OnSaveLoaded;\n',
    '        helper.Events.GameLoop.SaveLoaded += this.CardArena.OnSaveLoaded;\n        helper.Events.GameLoop.SaveLoaded += this.BossCards.OnSaveLoaded;\n',
    1
)
mod = mod.replace(
    '        helper.Events.GameLoop.DayStarted += this.BossEnergy.OnDayStarted;\n',
    '        helper.Events.GameLoop.DayStarted += this.BossEnergy.OnDayStarted;\n        helper.Events.GameLoop.DayStarted += this.BossCards.OnDayStarted;\n',
    1
)
mod = mod.replace(
    '        helper.Events.GameLoop.UpdateTicked += this.CardArena.OnUpdateTicked;\n',
    '        helper.Events.GameLoop.UpdateTicked += this.CardArena.OnUpdateTicked;\n        helper.Events.GameLoop.UpdateTicked += this.BossCards.OnUpdateTicked;\n',
    1
)
mod = mod.replace(
    '        helper.Events.GameLoop.ReturnedToTitle += this.BossEnergy.OnReturnedToTitle;\n',
    '        helper.Events.GameLoop.ReturnedToTitle += this.BossEnergy.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.BossCards.OnReturnedToTitle;\n',
    1
)
mod = mod.replace(
    '        helper.Events.Display.RenderedHud += this.CardLabOverlay.OnRenderedHud;\n',
    '        helper.Events.Display.RenderedHud += this.CardLabOverlay.OnRenderedHud;\n        helper.Events.Display.RenderedHud += this.BossCards.OnRenderedHud;\n',
    1
)
mod = mod.replace(
    '        helper.Events.Display.RenderedWorld += this.Story.OnRenderedWorld;\n',
    '        helper.Events.Display.RenderedWorld += this.Story.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.BossCards.OnRenderedWorld;\n',
    1
)
mod = mod.replace(
    '        FarmerDamagePatch.Apply(harmony, this.Combat, this.ChaChaSupport, this.CardArena);\n',
    '        FarmerDamagePatch.Apply(harmony, this.Combat, this.ChaChaSupport, this.CardArena, this.BossCards);\n',
    1
)

marker = '        helper.ConsoleCommands.Add("cardcha_boss1_visual_status"'
pos = mod.find(marker)
if pos < 0:
    raise RuntimeError('cardcha_boss1_visual_status command anchor missing')
line_end = mod.find('\n', pos)
insert = '''        helper.ConsoleCommands.Add("cardcha_boss_card_status", "Show dedicated Boss Card slot/runtime state.", (_, _) => this.Monitor.Log(this.BossCards.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_unlock", "TEST ONLY: unlock Verdant Core without changing Boss I clear state.", (_, _) => this.Monitor.Log(this.BossCards.DebugUnlock(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_equip", "Equip a Boss Card: cardcha_boss_card_equip verdant_core|none", (_, args) => this.Monitor.Log(this.BossCards.DebugEquip(args.FirstOrDefault()), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_trigger", "TEST ONLY: force Verdant Guard active for visual/gameplay verification.", (_, _) => this.Monitor.Log(this.BossCards.DebugTrigger(), LogLevel.Alert));
'''
mod = mod[:line_end + 1] + insert + mod[line_end + 1:]
mod = mod.replace(
    '0.3.0-alpha.28.0.4.14.4.5.12.27 VERDANT GUARDIAN VISUAL COMPLETE + COLOSSUS TEST',
    '0.3.0-alpha.28.0.4.14.4.5.12.28 VERDANT CORE BOSS CARD RUNTIME TEST',
    1
)
mod_path.write_text(mod, encoding='utf-8')

# ---------------- i18n ----------------
def add_i18n(path: Path, values: dict):
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

add_i18n(ROOT / 'i18n' / 'default.json', {
    'boss.card.verdant_core.name': 'Verdant Core',
    'boss.card.verdant_core.desc': 'When a hit would leave you at or below 50% HP, Verdant Guard awakens for 6s: take 35% less damage and recover 2 HP each second. 24s cooldown.',
    'boss.card.verdant_core.unlocked': 'BOSS CARD AWAKENED: Verdant Core. It has been placed in your dedicated Boss Card slot.',
    'boss.card.verdant_core.activated': 'Verdant Core awakened: roots harden around you.',
    'boss.card.state.ready': 'READY',
    'boss.card.state.active': 'VERDANT GUARD  {{seconds}}s',
    'boss.card.state.cooldown': 'ROOTS RECOVERING  {{seconds}}s'
})
add_i18n(ROOT / 'i18n' / 'vi.json', {
    'boss.card.verdant_core.name': 'Verdant Core',
    'boss.card.verdant_core.desc': 'Khi một đòn đánh sắp khiến HP còn 50% hoặc thấp hơn, Verdant Guard thức tỉnh trong 6 giây: giảm 35% sát thương nhận vào và hồi 2 HP mỗi giây. Hồi chiêu 24 giây.',
    'boss.card.verdant_core.unlocked': 'BOSS CARD THỨC TỈNH: Verdant Core. Lá bài đã được đặt vào ô Boss Card riêng.',
    'boss.card.verdant_core.activated': 'Verdant Core thức tỉnh: rễ cây siết lại thành lớp giáp quanh bạn.',
    'boss.card.state.ready': 'SẴN SÀNG',
    'boss.card.state.active': 'VERDANT GUARD  {{seconds}}s',
    'boss.card.state.cooldown': 'RỄ ĐANG HỒI PHỤC  {{seconds}}s'
})

# ---------------- handoff ----------------
handoff = Path('handoff/ALPHA28_0661_VERDANT_CORE_BOSS_CARD_RUNTIME.md')
handoff.write_text(f'''# Alpha28 0661 - Verdant Core Boss Card Runtime\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0661-verdant-core-boss-card-runtime`\nStatus: implementation candidate, in-game acceptance pending. 0660 visual acceptance is still pending because the user continued before testing it.\n\n## Boss Card architecture\n- Boss Cards are a separate system from the normal 76-card pool.\n- Save schema remains 19 and reuses `BossCardsUnlocked` + `EquippedBossCardId`.\n- Boss I first clear already unlocks `verdant_core` and auto-equips it if the dedicated Boss Card slot is empty.\n- 0661 adds the first real runtime effect, HUD state, world feedback, debug equip/unlock/trigger commands, and an authored Verdant Core icon.\n\n## Verdant Core effect\n- Trigger: an incoming hit would leave the local player at or below 50% Max HP.\n- The triggering hit is protected too.\n- Verdant Guard duration: 6 seconds.\n- Incoming damage reduction while active: 35%.\n- Recovery: 2 HP each second while active.\n- Cooldown: 24 seconds from activation.\n- Runtime state is transient; unlock/equip persistence remains in existing save fields.\n\n## Debug\n- `cardcha_boss_card_status`\n- `cardcha_boss_card_unlock`\n- `cardcha_boss_card_equip verdant_core|none`\n- `cardcha_boss_card_trigger`\n\n## Locked systems preserved\nSave schema 19, 20/40/60/80 milestones, 76/76 normal card audit, Boss Form 10 sec, Boss Energy x1/3, 0659 MiMi stair resolver, MiMi profile/CC continuity, Region I Hunt Run 4-of-6, Verdant Guardian 0660 Colossus visuals/combat/reward timing, Airship route/upgrades, controller mapping and Forest gate are unchanged.\n''', encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0661-verdant-core-boss-card-runtime`\nCurrent build: `{VERSION}`\n\nContinue from:\n`handoff/ALPHA28_0661_VERDANT_CORE_BOSS_CARD_RUNTIME.md`\n\n0660 Verdant Guardian visual acceptance is still pending. Do not resume from stale `main`.\n''', encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'bossCard': 'verdant_core',
    'triggerHp': '50%',
    'damageReduction': '35%',
    'durationSeconds': 6,
    'regenHpPerSecond': 2,
    'cooldownSeconds': 24,
    'schema': 19
}, indent=2))

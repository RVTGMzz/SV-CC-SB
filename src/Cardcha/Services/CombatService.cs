
using Cardcha.Models;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Buffs;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// Runtime combat behavior for the Cardcha prototype set.
/// Card ownership and levels live in SaveData; transient combat state intentionally does not.
/// </summary>
internal sealed class CombatService
{
    private const string ThickHideBuffId = "Ronvotri.Cardcha_ThickHide";
    private const string SwiftFeetBuffId = "Ronvotri.Cardcha_SwiftFeet";
    private const string LastStandBuffId = "Ronvotri.Cardcha_LastStand";

    private readonly ModConfig Config;
    private readonly LoadoutService Loadout;
    private readonly SaveService Save;
    private readonly CardRegistry Cards;
    private readonly CardUpgradeService Upgrades;

    private int ChainHunterStacks;
    private long ChainHunterExpiresAt;
    private long BloodFangReadyAt;
    private long SwiftFeetExpiresAt;

    // v0.1.13 visual combat feedback. These are transient and never saved.
    private string HudToastText = "";
    private string HudToastCardId = "";
    private long HudToastExpiresAt;

    // verification telemetry. Never written to the save.
    private long DamageHookCalls;
    private long DamageModifiedCalls;
    private long CritHookCalls;
    private long CritModifiedCalls;
    private long KillHookCalls;
    private long BloodFangProcs;
    private long ChainHunterProcs;
    private long PhoenixHeartProcs;
    private int LastDamageBefore;
    private int LastDamageAfter;
    private float LastCritBefore;
    private float LastCritAfter;

    public CombatService(ModConfig config, LoadoutService loadout, SaveService save, CardRegistry cards, CardUpgradeService upgrades)
    {
        this.Config = config;
        this.Loadout = loadout;
        this.Save = save;
        this.Cards = cards;
        this.Upgrades = upgrades;
    }

    public int CurrentChainHunterStacks
    {
        get
        {
            this.ExpireChainIfNeeded();
            return this.ChainHunterStacks;
        }
    }

    public double CurrentChainSecondsRemaining
    {
        get
        {
            this.ExpireChainIfNeeded();
            if (this.ChainHunterStacks <= 0)
                return 0;

            return Math.Max(0, (this.ChainHunterExpiresAt - Environment.TickCount64) / 1000d);
        }
    }

    public bool IsThickHideActive
        => Context.IsWorldReady && Game1.player?.hasBuff(ThickHideBuffId) == true;

    public bool IsSwiftFeetActive
        => Context.IsWorldReady && Game1.player?.hasBuff(SwiftFeetBuffId) == true;

    public bool IsLastStandActive
        => Context.IsWorldReady && Game1.player?.hasBuff(LastStandBuffId) == true;

    public bool IsPhoenixReady
        => this.Loadout.CardEffectsActive
           && this.Loadout.IsEquipped("phoenix_heart")
           && !this.Save.Data.PhoenixHeartUsedToday;

    public double BloodFangCooldownSecondsRemaining
        => Math.Max(0, (this.BloodFangReadyAt - Environment.TickCount64) / 1000d);

    public double BloodFangCooldownTotalSeconds
    {
        get
        {
            CardDefinition? card = this.Cards.Get("blood_fang");
            return Math.Max(0.25, this.Upgrades.GetStats(card).DurationMs / 1000d);
        }
    }

    public double CurrentChainDurationSeconds
    {
        get
        {
            CardDefinition? card = this.Cards.Get("chain_hunter");
            return Math.Max(0.25, this.Upgrades.GetStats(card).DurationMs / 1000d);
        }
    }

    public string CurrentHudToast
    {
        get
        {
            if (string.IsNullOrWhiteSpace(this.HudToastText))
                return "";

            if (Environment.TickCount64 >= this.HudToastExpiresAt)
            {
                this.HudToastText = "";
                this.HudToastCardId = "";
                this.HudToastExpiresAt = 0;
                return "";
            }

            return this.HudToastText;
        }
    }

    public string CurrentHudToastCardId
    {
        get
        {
            _ = this.CurrentHudToast;
            return this.HudToastCardId;
        }
    }

    public int ModifyMonsterDamage(Monster monster, int damage, bool isBomb, Farmer? who)
    {
        if (!this.Config.EnableCombatCards || !IsLocalPlayer(who) || isBomb || damage <= 0)
            return damage;

        this.DamageHookCalls++;
        this.LastDamageBefore = damage;

        double bonus = 0;

        if (this.Loadout.IsEquipped("iron_edge"))
            bonus += this.GetStats("iron_edge").Primary;

        CardLevelStats executioner = this.GetStats("executioner");
        if (this.Loadout.IsEquipped("executioner")
            && monster.MaxHealth > 0
            && monster.Health <= monster.MaxHealth * Math.Max(0.01, executioner.Threshold))
        {
            bonus += executioner.Primary;
        }

        if (this.Loadout.IsEquipped("chain_hunter"))
            bonus += this.CurrentChainHunterStacks * this.GetStats("chain_hunter").Primary;

        CardLevelStats lastStand = this.GetStats("last_stand");
        if (this.Loadout.IsEquipped("last_stand")
            && IsLowHealth(who!, Math.Max(0.01, lastStand.Threshold)))
        {
            bonus += lastStand.Primary;
        }

        if (bonus <= 0)
        {
            this.LastDamageAfter = damage;
            return damage;
        }

        int modified = Math.Max(1, (int)Math.Ceiling(damage * (1d + bonus)));
        this.LastDamageAfter = modified;
        if (modified != damage)
            this.DamageModifiedCalls++;

        return modified;
    }

    public float ModifyCriticalChance(float critChance, bool isBomb, Farmer? who)
    {
        if (!this.Config.EnableCombatCards || !IsLocalPlayer(who) || isBomb)
            return critChance;

        this.CritHookCalls++;
        this.LastCritBefore = critChance;

        if (this.Loadout.IsEquipped("keen_eye"))
            critChance += (float)this.GetStats("keen_eye").Primary;

        float modified = Math.Max(0f, critChance);
        this.LastCritAfter = modified;
        if (Math.Abs(this.LastCritAfter - this.LastCritBefore) > 0.0001f)
            this.CritModifiedCalls++;

        return modified;
    }

    public void OnMonsterKilled(Monster monster, Farmer? who)
        => this.OnEnemyKilled(who);

    public void OnEnemyKilled(Farmer? who)
    {
        if (!this.Config.EnableCombatCards || !IsLocalPlayer(who))
            return;

        this.KillHookCalls++;

        Farmer player = who!;
        long now = Environment.TickCount64;

        if (this.Loadout.IsEquipped("blood_fang") && now >= this.BloodFangReadyAt && player.health > 0 && player.health < player.maxHealth)
        {
            CardLevelStats bloodFang = this.GetStats("blood_fang");
            int heal = Math.Max(1, (int)Math.Ceiling(player.maxHealth * bloodFang.Primary));
            player.health = Math.Min(player.maxHealth, player.health + heal);
            this.BloodFangReadyAt = now + Math.Max(250, bloodFang.DurationMs);
            this.BloodFangProcs++;
            this.PushHudToast("blood_fang", ModEntry.T("hud.toast.blood-fang", new { heal }));

            if (this.Config.VerboseLogging)
                ModEntry.StaticMonitor?.Log($"Blood Fang healed {heal} HP.", LogLevel.Trace);
        }

        if (this.Loadout.IsEquipped("chain_hunter"))
        {
            CardLevelStats chain = this.GetStats("chain_hunter");
            this.ChainHunterStacks = Math.Min(Math.Max(1, this.Config.ChainHunterMaxStacks), this.CurrentChainHunterStacks + 1);
            this.ChainHunterExpiresAt = now + Math.Max(250, chain.DurationMs);
            this.ChainHunterProcs++;

            // Chain Hunter already has a persistent HUD row with stack count + timer.
            // Don't duplicate the same information in the lower toast area.
        }
        else
        {
            this.ClearChain();
        }
    }

    public void AfterFarmerTakesDamage(Farmer farmer)
    {
        if (!this.Config.EnableCombatCards || !IsLocalPlayer(farmer))
            return;

        if (farmer.health > 0 || !this.Loadout.IsEquipped("phoenix_heart") || this.Save.Data.PhoenixHeartUsedToday)
            return;

        farmer.health = 1;
        farmer.temporarilyInvincible = true;
        farmer.flashDuringThisTemporaryInvincibility = true;
        farmer.temporaryInvincibilityTimer = 0;

        CardLevelStats phoenix = this.GetStats("phoenix_heart");
        farmer.currentTemporaryInvincibilityDuration = Math.Max(1200, phoenix.DurationMs);

        this.Save.Data.PhoenixHeartUsedToday = true;
        this.PhoenixHeartProcs++;
        this.Save.Save();

        Game1.playSound("yoba");
        this.PushHudToast("phoenix_heart", ModEntry.T("hud.toast.phoenix"), 2600);
    }

    public void SyncPassiveBuffs()
    {
        if (!Context.IsWorldReady || !this.Config.EnableCombatCards)
            return;

        Farmer player = Game1.player;
        if (player is null)
            return;

        // Story hard-gate: old test saves may still have an equipped loadout and
        // lingering hidden buffs. Until MiMi + Wizard actually hand over the Binder,
        // Cardcha combat effects must be completely dormant.
        if (!this.Loadout.CardEffectsActive)
        {
            TryRemoveBuff(player, ThickHideBuffId);
            TryRemoveBuff(player, SwiftFeetBuffId);
            TryRemoveBuff(player, LastStandBuffId);
            this.SwiftFeetExpiresAt = 0;
            this.BloodFangReadyAt = 0;
            this.ClearChain();
            this.HudToastText = "";
            this.HudToastCardId = "";
            this.HudToastExpiresAt = 0;
            return;
        }

        CardLevelStats thickHide = this.GetStats("thick_hide");
        if (this.Loadout.IsEquipped("thick_hide"))
            ApplyHiddenBuff(player, ThickHideBuffId, defense: Math.Max(0, (int)Math.Round(thickHide.Primary)), speed: 0);
        else
            TryRemoveBuff(player, ThickHideBuffId);

        bool hasLivingMonster = Game1.currentLocation?.characters
            .OfType<Monster>()
            .Any(m => m.IsMonster && m.Health > 0) == true;

        CardLevelStats swift = this.GetStats("swift_feet");
        long now = Environment.TickCount64;

        if (this.Loadout.IsEquipped("swift_feet") && hasLivingMonster)
            this.SwiftFeetExpiresAt = now + Math.Max(0, swift.DurationMs);

        bool swiftActive =
            this.Loadout.IsEquipped("swift_feet")
            && (hasLivingMonster || (swift.DurationMs > 0 && now < this.SwiftFeetExpiresAt));

        if (swiftActive)
            ApplyHiddenBuff(player, SwiftFeetBuffId, defense: 0, speed: Math.Max(0, (int)Math.Round(swift.Primary)));
        else
            TryRemoveBuff(player, SwiftFeetBuffId);

        CardLevelStats lastStand = this.GetStats("last_stand");
        if (this.Loadout.IsEquipped("last_stand")
            && IsLowHealth(player, Math.Max(0.01, lastStand.Threshold)))
        {
            ApplyHiddenBuff(
                player,
                LastStandBuffId,
                defense: Math.Max(0, (int)Math.Round(lastStand.Secondary)),
                speed: 0
            );
        }
        else
        {
            TryRemoveBuff(player, LastStandBuffId);
        }

        if (!this.Loadout.IsEquipped("chain_hunter"))
            this.ClearChain();
        else
            this.ExpireChainIfNeeded();
    }

    public string BuildVerificationReport()
    {
        string damage = this.DamageHookCalls == 0
            ? "no eligible weapon hit observed yet"
            : $"{this.DamageModifiedCalls}/{this.DamageHookCalls} modified; last {this.LastDamageBefore}->{this.LastDamageAfter}";

        string crit = this.CritHookCalls == 0
            ? "no eligible crit roll observed yet"
            : $"{this.CritModifiedCalls}/{this.CritHookCalls} modified; last {this.LastCritBefore:0.000}->{this.LastCritAfter:0.000}";

        string passive = Context.IsWorldReady
            ? $"ThickHide={(Game1.player.hasBuff(ThickHideBuffId) ? "ON" : "off")}, SwiftFeet={(Game1.player.hasBuff(SwiftFeetBuffId) ? "ON" : "off")}, LastStand={(Game1.player.hasBuff(LastStandBuffId) ? "ON" : "off")}" 
            : "world not ready";

        return
            $"Damage: {damage}\n" +
            $"Crit: {crit}\n" +
            $"Kills observed: {this.KillHookCalls} | Blood Fang heals: {this.BloodFangProcs} | Chain Hunter procs: {this.ChainHunterProcs}\n" +
            $"Chain Hunter now: {this.CurrentChainHunterStacks}/{this.Config.ChainHunterMaxStacks} ({this.CurrentChainSecondsRemaining:0.0}s)\n" +
            $"Phoenix Heart procs this session: {this.PhoenixHeartProcs} | used today: {this.Save.Data.PhoenixHeartUsedToday}\n" +
            $"Passive buffs: {passive}";
    }

    public void ResetVerificationTelemetry()
    {
        this.DamageHookCalls = 0;
        this.DamageModifiedCalls = 0;
        this.CritHookCalls = 0;
        this.CritModifiedCalls = 0;
        this.KillHookCalls = 0;
        this.BloodFangProcs = 0;
        this.ChainHunterProcs = 0;
        this.PhoenixHeartProcs = 0;
        this.LastDamageBefore = 0;
        this.LastDamageAfter = 0;
        this.LastCritBefore = 0;
        this.LastCritAfter = 0;
    }

    public void ResetRuntime()
    {
        this.ClearChain();
        this.BloodFangReadyAt = 0;
        this.SwiftFeetExpiresAt = 0;
        this.HudToastText = "";
        this.HudToastCardId = "";
        this.HudToastExpiresAt = 0;
    }

    private CardLevelStats GetStats(string id)
    {
        CardDefinition? card = this.Cards.Get(id);
        return this.Upgrades.GetStats(card);
    }

    private static bool IsLocalPlayer(Farmer? who)
        => who is not null && who.IsLocalPlayer;

    private static bool IsLowHealth(Farmer farmer, double threshold)
        => farmer.maxHealth > 0 && farmer.health > 0 && farmer.health <= farmer.maxHealth * threshold;

    private static void ApplyHiddenBuff(Farmer player, string id, int defense, int speed)
    {
        BuffEffects effects = new();
        if (defense != 0)
            effects.Defense.Value = defense;
        if (speed != 0)
            effects.Speed.Value = speed;

        Buff buff = new(
            id: id,
            displayName: "Cardcha!",
            iconTexture: Game1.mouseCursors,
            iconSheetIndex: 0,
            duration: 1200,
            effects: effects
        );
        buff.visible = false;
        player.applyBuff(buff);
    }

    private static void TryRemoveBuff(Farmer player, string id)
    {
        if (player.hasBuff(id))
            player.buffs.Remove(id);
    }

    private void PushHudToast(string cardId, string text, int ms = 1800)
    {
        this.HudToastCardId = cardId;
        this.HudToastText = text;
        this.HudToastExpiresAt = Environment.TickCount64 + Math.Max(500, ms);
    }

    private void ExpireChainIfNeeded()
    {
        if (this.ChainHunterStacks <= 0)
            return;

        if (Environment.TickCount64 >= this.ChainHunterExpiresAt)
            this.ClearChain();
    }

    private void ClearChain()
    {
        this.ChainHunterStacks = 0;
        this.ChainHunterExpiresAt = 0;
    }
}

using Cardcha.Models;
using Microsoft.Xna.Framework;
using StardewValley;
using StardewValley.Buffs;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// Alpha.26.5 completion pass for Base Set cards whose text existed before their runtime hooks.
/// This deliberately keeps state transient; daily one-shot effects use SaveData so reloads cannot refresh them.
/// </summary>
internal sealed class CoreCardEffectsService
{
    private const string RuntimeBuffId = "Ronvotri.Cardcha_CoreCompletion";

    private readonly LoadoutService Loadout;
    private readonly SaveService Save;
    private readonly CardRegistry Cards;
    private readonly CardUpgradeService Upgrades;

    private readonly HashSet<Monster> HitTargets = new();
    private readonly Dictionary<Monster, int> TargetHits = new();
    private readonly HashSet<string> MonsterTypesToday = new(StringComparer.OrdinalIgnoreCase);

    private long LastOutgoingHitAt;
    private long LastTakenHitAt;
    private bool CounterforceReady;
    private int RhythmHitCount;
    private int BattleTranceHitCount;
    private int FieldMedicKills;
    private int NoHitKillStreak;
    private bool TookHitSinceLastKill;

    private int PredatorStacks;
    private long PredatorExpiresAt;
    private int WarDrumStacks;
    private long WarDrumExpiresAt;
    private long WarDrumBurstUntil;
    private long ApexPredatorBuffUntil;

    private long SecondBreathReadyAt;
    private long GuardStepUntil;
    private long BackstepUntil;
    private long ExplorerUntil;
    private long MomentumUntil;
    private long AdrenalineUntil;
    private long FleetHunterUntil;
    private long BattleTranceUntil;
    private long OverclockUntil;
    private long VoidPhaseUntil;
    private long VoidReadyAt;
    private long UnyieldingReadyAt;
    private bool MirrorGuardArmed;
    private long MirrorGuardReadyAt;

    private Monster? MarkedPreyTarget;
    private long MarkedPreyUntil;

    private int VanguardShield;
    private int GuardianShield;
    private string VanguardLocation = "";
    private bool VanguardSawMonsters;

    private Vector2 LastStationaryPosition;
    private long StationarySince;

    private long CalmHeartNextHealAt;
    private long LifeStealWindowAt;
    private double LifeStealThisWindow;

    // alpha.26.5 completion telemetry for cards whose mechanics need a little context
    // around a hit instead of a flat percentage modifier. All of this is transient.
    private double TypicalRawHitDamage;
    private int PendingRawHitDamage;
    private bool PendingCritLikeHit;
    private bool PhantomCritArmed;
    private Vector2 PhantomSamplePosition;
    private long PhantomSampleAt;
    private long PhantomReadyAt;
    private long TimeBreakerUntil;
    private long TimeBreakerReadyAt;

    public CoreCardEffectsService(LoadoutService loadout, SaveService save, CardRegistry cards, CardUpgradeService upgrades)
    {
        this.Loadout = loadout;
        this.Save = save;
        this.Cards = cards;
        this.Upgrades = upgrades;
    }

    public int CurrentNoHitKillStreak => Math.Max(0, this.NoHitKillStreak);

    /// <summary>
    /// Record the raw Stardew hit before Cardcha multipliers. This provides a conservative
    /// crit heuristic for mechanics which need to react to an actual high-damage hit, and
    /// lets Steady Grip reduce ordinary damage variance without flattening likely crits.
    /// </summary>
    public int PrepareOutgoingDamage(int damage)
    {
        if (!this.Loadout.CardEffectsActive || damage <= 0)
        {
            this.PendingRawHitDamage = 0;
            this.PendingCritLikeHit = false;
            return damage;
        }

        this.PendingRawHitDamage = damage;
        this.PendingCritLikeHit = this.TypicalRawHitDamage >= 1d
            && damage >= this.TypicalRawHitDamage * 1.65d;

        if (!this.Loadout.IsEquipped("steady_grip")
            || this.PendingCritLikeHit
            || this.TypicalRawHitDamage < 1d)
            return damage;

        double reduction = this.LevelValue("steady_grip", .15, .22, .30, .38, .45);
        double stabilized = this.TypicalRawHitDamage
            + (damage - this.TypicalRawHitDamage) * (1d - reduction);
        return Math.Max(1, (int)Math.Round(stabilized));
    }

    public double GetPendingCrushingImpactKnockbackMultiplier()
    {
        if (!this.Loadout.CardEffectsActive
            || !this.PendingCritLikeHit
            || !this.Loadout.IsEquipped("crushing_impact"))
            return 1d;

        return 1d + this.LevelValue("crushing_impact", .30, .40, .50, .60);
    }

    public double GetOutgoingDamageBonus(Monster monster, Farmer player)
    {
        if (!this.Loadout.CardEffectsActive)
            return 0;

        long now = Environment.TickCount64;
        double bonus = 0;
        bool firstHit = !this.HitTargets.Contains(monster);
        double targetHealth = monster.MaxHealth > 0 ? monster.Health / (double)monster.MaxHealth : 1d;

        if (this.Loadout.IsEquipped("first_strike") && firstHit)
            bonus += this.LevelValue("first_strike", .08, .10, .12, .14, .16);
        if (this.Loadout.IsEquipped("opening_gambit") && firstHit)
            bonus += this.LevelValue("opening_gambit", .18, .21, .24, .27);
        if (this.Loadout.IsEquipped("finisher") && targetHealth < .20)
            bonus += this.LevelValue("finisher", .08, .10, .12, .14, .16);
        if (this.Loadout.IsEquipped("hunters_focus") && targetHealth > .80)
            bonus += this.LevelValue("hunters_focus", .05, .06, .07, .08, .10);
        if (this.Loadout.IsEquipped("last_push") && player.maxHealth > 0 && player.health <= player.maxHealth * .30)
            bonus += this.LevelValue("last_push", .05, .07, .09, .11, .13);

        if (this.Loadout.IsEquipped("bruiser") && monster.MaxHealth >= 300)
            bonus += this.LevelValue("bruiser", .04, .05, .06, .07, .08);

        this.ExpireTimedStacks(now);
        if (this.Loadout.IsEquipped("predator"))
            bonus += this.PredatorStacks * this.LevelValue("predator", .03, .035, .04, .045);

        if (this.Loadout.IsEquipped("counterforce") && this.CounterforceReady)
        {
            bonus += this.LevelValue("counterforce", .15, .20, .25, .30);
            this.CounterforceReady = false;
        }

        int priorHits = this.TargetHits.TryGetValue(monster, out int hitCount) ? hitCount : 0;
        if (this.Loadout.IsEquipped("armor_breaker"))
            bonus += Math.Min(5, priorHits) * this.LevelValue("armor_breaker", .02, .025, .03, .035);

        if (this.Loadout.IsEquipped("relentless"))
        {
            int level = this.Level("relentless");
            int max = level switch { 1 => 5, 2 => 6, _ => 7 };
            bonus += Math.Min(max, priorHits) * this.LevelValue("relentless", .02, .025, .03);
        }

        if (this.Loadout.IsEquipped("berserker_soul") && player.maxHealth > 0)
        {
            double missing = Math.Clamp(1d - player.health / (double)player.maxHealth, 0d, 1d);
            int tens = (int)Math.Floor(missing * 10d + 0.0001d);
            double perTen = this.LevelValue("berserker_soul", .01, .012, .014);
            double cap = this.LevelValue("berserker_soul", .08, .10, .12);
            bonus += Math.Min(cap, tens * perTen);
        }

        if (this.Loadout.IsEquipped("rhythm") && this.RhythmHitCount >= 3)
        {
            bonus += this.LevelValue("rhythm", .04, .05, .06, .07, .08);
            this.RhythmHitCount = 0;
        }

        if (this.Loadout.IsEquipped("reapers_mark") && priorHits >= 4)
            bonus += this.LevelValue("reapers_mark", .08, .10, .12);

        if (this.Loadout.IsEquipped("marked_prey"))
        {
            if (now - this.LastOutgoingHitAt >= 3000 && (this.MarkedPreyTarget is null || now >= this.MarkedPreyUntil))
            {
                this.MarkedPreyTarget = monster;
                this.MarkedPreyUntil = now + 5000;
            }
            if (ReferenceEquals(this.MarkedPreyTarget, monster) && now < this.MarkedPreyUntil)
                bonus += this.LevelValue("marked_prey", .10, .13, .16, .19);
        }

        if (this.Loadout.IsEquipped("war_drum") && now < this.WarDrumBurstUntil && this.WarDrumStacks >= 4)
            bonus += this.LevelValue("war_drum", .08, .10, .12);

        if (this.Loadout.IsEquipped("titans_grip"))
            bonus += this.LevelValue("titans_grip", .25, .30, .35);

        if (this.Loadout.IsEquipped("apex_predator"))
        {
            if (IsBossLike(monster))
                bonus += this.LevelValue("apex_predator", .10, .15, .20);
            if (now < this.ApexPredatorBuffUntil)
                bonus += this.LevelValue("apex_predator", .08, .10, .12);
        }

        return Math.Max(0, bonus);
    }

    public float ModifyCritChance(float current, Farmer player)
    {
        if (!this.Loadout.CardEffectsActive)
            return current;

        long now = Environment.TickCount64;
        if (this.Loadout.IsEquipped("patient_hunter") && now - this.LastOutgoingHitAt >= 2000)
            current += (float)this.LevelValue("patient_hunter", .03, .04, .05, .06, .07);

        if (this.Loadout.IsEquipped("perfect_hunter") && this.NoHitKillStreak > 0)
            current += (float)(Math.Min(5, this.NoHitKillStreak) * this.LevelValue("perfect_hunter", .02, .025, .03));

        // Phantom Step uses a movement-based dodge heuristic. A quick displacement while
        // monsters are present and without taking damage arms exactly one boosted crit roll.
        if (this.Loadout.IsEquipped("phantom_step") && this.PhantomCritArmed)
        {
            current += (float)this.LevelValue("phantom_step", .15, .20, .25);
            this.PhantomCritArmed = false;
        }

        return Math.Max(0, current);
    }

    public int ModifyIncomingDamage(int damage, Farmer player, Monster? attacker)
    {
        if (!this.Loadout.CardEffectsActive || damage <= 0 || player.health <= 0)
            return damage;

        long now = Environment.TickCount64;
        double multiplier = 1d;

        if (this.Loadout.IsEquipped("guard_step") && now < this.GuardStepUntil)
            multiplier *= 1d - this.LevelValue("guard_step", .08, .10, .12, .14);

        if (this.Loadout.IsEquipped("stoneheart") && player.maxHealth > 0 && player.health > player.maxHealth * .80)
            multiplier *= 1d - this.LevelValue("stoneheart", .10, .12, .15);

        if (this.Loadout.IsEquipped("mirror_guard") && this.MirrorGuardArmed && now >= this.MirrorGuardReadyAt)
        {
            multiplier *= 1d - this.LevelValue("mirror_guard", .30, .40, .50);
            this.MirrorGuardArmed = false;
            this.MirrorGuardReadyAt = now + this.LevelInt("mirror_guard", 12000, 10000, 8000);
        }

        if (this.Loadout.IsEquipped("void_walker") && now >= this.VoidReadyAt)
        {
            double proc = this.LevelValue("void_walker", .15, .20, .25);
            if (Game1.random.NextDouble() < proc)
            {
                multiplier *= 1d - this.LevelValue("void_walker", .40, .50, .60);
                this.VoidPhaseUntil = now + this.LevelInt("void_walker", 1500, 1750, 2000);
                this.VoidReadyAt = now + this.LevelInt("void_walker", 20000, 18000, 16000);
            }
        }

        int modified = Math.Max(0, (int)Math.Ceiling(damage * multiplier));

        // Encounter/daily shields absorb after percentage reductions.
        modified = this.AbsorbShield(ref this.VanguardShield, modified);
        modified = this.AbsorbShield(ref this.GuardianShield, modified);

        if (this.Loadout.IsEquipped("unyielding") && now >= this.UnyieldingReadyAt && player.maxHealth > 0)
        {
            double fraction = this.LevelValue("unyielding", .45, .40, .35);
            int cap = Math.Max(1, (int)Math.Ceiling(player.maxHealth * fraction));
            if (modified > cap)
            {
                modified = cap;
                this.UnyieldingReadyAt = now + this.LevelInt("unyielding", 20000, 18000, 16000);
            }
        }

        if (this.Loadout.IsEquipped("guardian_angel")
            && !this.Save.Data.GuardianAngelUsedToday
            && modified >= player.health)
        {
            modified = Math.Max(0, player.health - 1);
            this.GuardianShield = Math.Max(this.GuardianShield,
                Math.Max(1, (int)Math.Ceiling(player.maxHealth * this.LevelValue("guardian_angel", .25, .35, .45))));
            this.Save.Data.GuardianAngelUsedToday = true;
            this.Save.Save();
            Game1.playSound("yoba");
        }

        return Math.Max(0, modified);
    }

    public void AfterMonsterTakesDamage(Monster monster, Farmer? who, int healthBefore)
    {
        if (who?.IsLocalPlayer != true || !this.Loadout.CardEffectsActive)
            return;

        int actual = Math.Max(0, healthBefore - Math.Max(0, monster.Health));
        if (actual <= 0)
        {
            this.PendingRawHitDamage = 0;
            this.PendingCritLikeHit = false;
            return;
        }

        long now = Environment.TickCount64;
        bool critLike = this.PendingCritLikeHit;
        int rawHit = this.PendingRawHitDamage > 0 ? this.PendingRawHitDamage : actual;

        // Keep a slowly moving ordinary-hit baseline. Likely crits are deliberately excluded
        // so they don't teach the heuristic that a crit is normal damage.
        if (!critLike)
        {
            this.TypicalRawHitDamage = this.TypicalRawHitDamage < 1d
                ? rawHit
                : this.TypicalRawHitDamage * .82d + rawHit * .18d;
        }

        if (critLike
            && this.Loadout.IsEquipped("time_breaker")
            && now >= this.TimeBreakerReadyAt)
        {
            double proc = this.LevelValue("time_breaker", .10, .12, .15);
            if (Game1.random.NextDouble() < proc)
            {
                this.TimeBreakerUntil = now + 3000;
                this.TimeBreakerReadyAt = now + this.LevelInt("time_breaker", 12000, 10000, 8000);
                Game1.playSound("crit");
            }
        }

        this.PendingRawHitDamage = 0;
        this.PendingCritLikeHit = false;

        this.HitTargets.Add(monster);
        this.TargetHits[monster] = Math.Min(1000, (this.TargetHits.TryGetValue(monster, out int hits) ? hits : 0) + 1);
        this.LastOutgoingHitAt = now;

        if (this.Loadout.IsEquipped("rhythm"))
            this.RhythmHitCount = Math.Min(3, this.RhythmHitCount + 1);
        else
            this.RhythmHitCount = 0;

        if (this.Loadout.IsEquipped("battle_trance"))
        {
            this.BattleTranceHitCount++;
            if (this.BattleTranceHitCount >= 4)
            {
                this.BattleTranceHitCount = 0;
                this.BattleTranceUntil = now + 2000;
            }
        }
        else
            this.BattleTranceHitCount = 0;

        if (this.Loadout.IsEquipped("soul_siphon") && who.health > 0 && who.health < who.maxHealth)
        {
            if (now - this.LifeStealWindowAt >= 1000)
            {
                this.LifeStealWindowAt = now;
                this.LifeStealThisWindow = 0;
            }

            double cap = this.LevelValue("soul_siphon", 3, 4, 5);
            double healFraction = this.LevelValue("soul_siphon", .010, .0125, .015);
            double room = Math.Max(0, cap - this.LifeStealThisWindow);
            int heal = Math.Max(0, (int)Math.Floor(Math.Min(room, actual * healFraction)));
            if (heal > 0)
            {
                who.health = Math.Min(who.maxHealth, who.health + heal);
                this.LifeStealThisWindow += heal;
            }
        }
    }

    public void AfterFarmerTakesDamage(Farmer player, int healthBefore)
    {
        if (!this.Loadout.CardEffectsActive)
            return;

        int lost = Math.Max(0, healthBefore - Math.Max(0, player.health));
        if (lost <= 0)
            return;

        long now = Environment.TickCount64;
        this.LastTakenHitAt = now;
        this.TookHitSinceLastKill = true;
        this.NoHitKillStreak = 0;
        this.CounterforceReady = this.Loadout.IsEquipped("counterforce");

        if (this.Loadout.IsEquipped("guard_step"))
            this.GuardStepUntil = now + this.LevelInt("guard_step", 600, 700, 800, 900);
        if (this.Loadout.IsEquipped("backstep"))
            this.BackstepUntil = now + this.LevelInt("backstep", 1000, 1100, 1200, 1300);

        if (this.Loadout.IsEquipped("mirror_guard") && player.maxHealth > 0 && lost >= player.maxHealth * .25)
            this.MirrorGuardArmed = true;

        if (this.Loadout.IsEquipped("lifeline")
            && !this.Save.Data.LifelineUsedToday
            && player.health > 0
            && player.maxHealth > 0
            && player.health <= player.maxHealth * .25)
        {
            int heal = this.LevelInt("lifeline", 12, 16, 20);
            player.health = Math.Min(player.maxHealth, player.health + heal);
            this.Save.Data.LifelineUsedToday = true;
            this.Save.Save();
            Game1.playSound("healSound");
        }
    }

    public void OnMonsterKilled(Monster monster, Farmer player)
    {
        if (!this.Loadout.CardEffectsActive)
            return;

        long now = Environment.TickCount64;
        string monsterType = monster.GetType().FullName ?? monster.GetType().Name;
        this.MonsterTypesToday.Add(monsterType);

        if (!this.TookHitSinceLastKill)
            this.NoHitKillStreak = Math.Min(20, this.NoHitKillStreak + 1);
        else
            this.NoHitKillStreak = 0;
        this.TookHitSinceLastKill = false;

        if (this.Loadout.IsEquipped("second_breath") && now >= this.SecondBreathReadyAt && player.health > 0 && player.health < player.maxHealth)
        {
            int heal = this.LevelInt("second_breath", 1, 2, 3);
            player.health = Math.Min(player.maxHealth, player.health + heal);
            this.SecondBreathReadyAt = now + 2500;
        }

        if (this.Loadout.IsEquipped("field_medic"))
        {
            this.FieldMedicKills++;
            if (this.FieldMedicKills >= 8)
            {
                this.FieldMedicKills = 0;
                int heal = this.LevelInt("field_medic", 8, 10, 12, 15);
                if (player.health > 0)
                    player.health = Math.Min(player.maxHealth, player.health + heal);
            }
        }
        else
            this.FieldMedicKills = 0;

        if (this.Loadout.IsEquipped("predator"))
        {
            this.PredatorStacks = Math.Min(3, this.PredatorStacks + 1);
            this.PredatorExpiresAt = now + 6000;
        }
        else
            this.PredatorStacks = 0;

        if (this.Loadout.IsEquipped("explorer"))
            this.ExplorerUntil = now + 3000;
        if (this.Loadout.IsEquipped("momentum"))
            this.MomentumUntil = now + 2000;
        if (this.Loadout.IsEquipped("adrenaline"))
            this.AdrenalineUntil = now + 3000;
        if (this.Loadout.IsEquipped("fleet_hunter"))
            this.FleetHunterUntil = now + 2500;

        if (this.Loadout.IsEquipped("war_drum"))
        {
            this.WarDrumStacks = Math.Min(4, this.WarDrumStacks + 1);
            this.WarDrumExpiresAt = now + 6000;
            if (this.WarDrumStacks >= 4)
                this.WarDrumBurstUntil = now + 3000;
        }
        else
            this.WarDrumStacks = 0;

        if (IsBossLike(monster))
        {
            if (this.Loadout.IsEquipped("overclock"))
                this.OverclockUntil = now + 5000;
            if (this.Loadout.IsEquipped("apex_predator"))
                this.ApexPredatorBuffUntil = now + 6000;
        }

        this.HitTargets.Remove(monster);
        this.TargetHits.Remove(monster);
        if (ReferenceEquals(this.MarkedPreyTarget, monster))
        {
            this.MarkedPreyTarget = null;
            this.MarkedPreyUntil = 0;
        }
    }

    public void Sync(Farmer player, bool hasLivingMonster)
    {
        if (!this.Loadout.CardEffectsActive)
        {
            TryRemoveBuff(player, RuntimeBuffId);
            return;
        }

        long now = Environment.TickCount64;
        this.ExpireTimedStacks(now);

        // Vanguard is once per encounter/location entry. It refreshes only after the area was clear.
        string locationName = Game1.currentLocation?.NameOrUniqueName ?? "";
        if (!string.Equals(locationName, this.VanguardLocation, StringComparison.OrdinalIgnoreCase))
        {
            this.VanguardLocation = locationName;
            this.VanguardSawMonsters = false;
            this.VanguardShield = 0;
        }
        if (!hasLivingMonster)
            this.VanguardSawMonsters = false;
        else if (!this.VanguardSawMonsters)
        {
            this.VanguardSawMonsters = true;
            if (this.Loadout.IsEquipped("vanguard"))
                this.VanguardShield = this.LevelInt("vanguard", 5, 8, 11, 14);
        }

        // Calm Heart: begin five seconds after all combat activity, then use the card's cadence.
        if (this.Loadout.IsEquipped("calm_heart") && !hasLivingMonster && now - Math.Max(this.LastTakenHitAt, this.LastOutgoingHitAt) >= 5000)
        {
            int level = this.Level("calm_heart");
            int amount = level >= 4 ? 2 : 1;
            int cadence = level switch { 1 => 3000, 2 => 2500, _ => 2000 };
            if (this.CalmHeartNextHealAt <= 0)
                this.CalmHeartNextHealAt = now + cadence;
            if (now >= this.CalmHeartNextHealAt)
            {
                if (player.health > 0 && player.health < player.maxHealth)
                    player.health = Math.Min(player.maxHealth, player.health + amount);
                this.CalmHeartNextHealAt = now + cadence;
            }
        }
        else
            this.CalmHeartNextHealAt = 0;

        // Phantom Step: infer an evasive movement from a quick displacement while combat is
        // active and no damage was taken in the immediately preceding half-second. This is
        // intentionally controller/keyboard agnostic and only arms one future crit roll.
        if (this.Loadout.IsEquipped("phantom_step") && hasLivingMonster)
        {
            if (this.PhantomSampleAt <= 0)
            {
                this.PhantomSampleAt = now;
                this.PhantomSamplePosition = player.Position;
            }
            else if (now - this.PhantomSampleAt >= 250)
            {
                float moved = Vector2.Distance(player.Position, this.PhantomSamplePosition);
                if (moved >= 48f
                    && now - this.LastTakenHitAt >= 500
                    && now >= this.PhantomReadyAt)
                {
                    this.PhantomCritArmed = true;
                    this.PhantomReadyAt = now + this.LevelInt("phantom_step", 8000, 7000, 6000);
                }
                this.PhantomSampleAt = now;
                this.PhantomSamplePosition = player.Position;
            }
        }
        else
        {
            this.PhantomCritArmed = false;
            this.PhantomSampleAt = now;
            this.PhantomSamplePosition = player.Position;
        }

        // Stalwart checks real player position, not input, so controller/keyboard behavior is identical.
        if (this.Loadout.IsEquipped("stalwart"))
        {
            if (Vector2.DistanceSquared(player.Position, this.LastStationaryPosition) > 4f)
            {
                this.LastStationaryPosition = player.Position;
                this.StationarySince = now;
            }
        }
        else
            this.StationarySince = now;

        int defense = 0;
        if (this.Loadout.IsEquipped("resilient") && player.maxHealth > 0 && player.health <= player.maxHealth * .50)
            defense += this.LevelInt("resilient", 1, 2, 3);
        if (this.Loadout.IsEquipped("iron_will") && player.maxHealth > 0 && player.health <= player.maxHealth * .35)
            defense += this.LevelInt("iron_will", 2, 3, 4);
        if (this.Loadout.IsEquipped("stalwart"))
        {
            int level = this.Level("stalwart");
            int required = level switch { 1 => 1500, 2 or 3 => 1250, _ => 1000 };
            int bonus = level >= 3 ? 2 : 1;
            if (now - this.StationarySince >= required)
                defense += bonus;
        }
        if (this.Loadout.IsEquipped("battle_scholar") && this.MonsterTypesToday.Count >= 3 && this.Level("battle_scholar") >= 3)
            defense += 1;

        double weaponSpeed = 0;
        if (this.Loadout.IsEquipped("quick_hands"))
            weaponSpeed += this.LevelValue("quick_hands", .04, .05, .06, .07, .08);
        if (this.Loadout.IsEquipped("momentum") && now < this.MomentumUntil)
            weaponSpeed += this.LevelValue("momentum", .05, .07, .09, .11);
        if (this.Loadout.IsEquipped("adrenaline") && now < this.AdrenalineUntil)
            weaponSpeed += this.LevelValue("adrenaline", .08, .10, .12, .14);
        if (this.Loadout.IsEquipped("battle_trance") && now < this.BattleTranceUntil)
            weaponSpeed += this.LevelValue("battle_trance", .06, .08, .10, .12);
        if (this.Loadout.IsEquipped("war_drum") && this.WarDrumStacks > 0)
            weaponSpeed += this.WarDrumStacks * this.LevelValue("war_drum", .03, .04, .05);
        if (this.Loadout.IsEquipped("overclock") && now < this.OverclockUntil)
            weaponSpeed += this.LevelValue("overclock", .15, .20, .25);
        if (this.Loadout.IsEquipped("time_breaker") && now < this.TimeBreakerUntil)
            weaponSpeed += this.LevelValue("time_breaker", .30, .35, .40);
        if (this.Loadout.IsEquipped("titans_grip"))
            weaponSpeed -= this.LevelValue("titans_grip", .10, .08, .06);
        if (this.Loadout.IsEquipped("battle_scholar") && this.MonsterTypesToday.Count >= 3)
            weaponSpeed += this.LevelValue("battle_scholar", .02, .03, .04);

        double movePercent = 0;
        if (this.Loadout.IsEquipped("backstep") && now < this.BackstepUntil)
            movePercent += this.LevelValue("backstep", .10, .12, .14, .16);
        if (this.Loadout.IsEquipped("explorer") && now < this.ExplorerUntil)
            movePercent += this.LevelValue("explorer", .05, .06, .07, .08, .10);
        if (this.Loadout.IsEquipped("adrenaline") && now < this.AdrenalineUntil)
            movePercent += this.LevelValue("adrenaline", .05, .06, .07, .08);
        if (this.Loadout.IsEquipped("fleet_hunter") && now < this.FleetHunterUntil)
            movePercent += this.LevelValue("fleet_hunter", .12, .15, .18, .21);
        if (this.Loadout.IsEquipped("void_walker") && now < this.VoidPhaseUntil)
            movePercent += this.LevelValue("void_walker", .15, .20, .25);

        double knockback = this.Loadout.IsEquipped("heavy_blow")
            ? this.LevelValue("heavy_blow", .10, .15, .20, .25, .30)
            : 0;
        double critPower = this.Loadout.IsEquipped("deadeye")
            ? this.LevelValue("deadeye", .12, .16, .20, .24)
            : 0;
        int magnet = this.Loadout.IsEquipped("treasure_magnet")
            ? this.LevelInt("treasure_magnet", 32, 48, 64, 80, 96)
            : 0;

        // Battle Scholar's damage component is applied as AttackMultiplier so it also works
        // with unusual compatible weapon paths which don't call our Monster.takeDamage hook.
        double attackMultiplier = this.Loadout.IsEquipped("battle_scholar") && this.MonsterTypesToday.Count >= 3
            ? this.LevelValue("battle_scholar", .03, .04, .05)
            : 0;

        BuffEffects effects = new();
        effects.Defense.Value = defense;
        effects.WeaponSpeedMultiplier.Value = (float)weaponSpeed;
        effects.Speed.Value = (float)(movePercent * 10d); // Stardew +1 movement speed is roughly a 10% tier.
        effects.KnockbackMultiplier.Value = (float)knockback;
        effects.CriticalPowerMultiplier.Value = (float)critPower;
        effects.MagneticRadius.Value = magnet;
        effects.AttackMultiplier.Value = (float)attackMultiplier;

        Buff buff = new(
            id: RuntimeBuffId,
            displayName: "Cardcha!",
            iconTexture: Game1.mouseCursors,
            iconSheetIndex: 0,
            duration: 1200,
            effects: effects
        );
        buff.visible = false;
        player.applyBuff(buff);
    }

    public void ResetRuntime()
    {
        this.HitTargets.Clear();
        this.TargetHits.Clear();
        this.MonsterTypesToday.Clear();
        this.LastOutgoingHitAt = 0;
        this.LastTakenHitAt = 0;
        this.CounterforceReady = false;
        this.RhythmHitCount = 0;
        this.BattleTranceHitCount = 0;
        this.FieldMedicKills = 0;
        this.NoHitKillStreak = 0;
        this.TookHitSinceLastKill = false;
        this.PredatorStacks = 0;
        this.WarDrumStacks = 0;
        this.VanguardShield = 0;
        this.GuardianShield = 0;
        this.VanguardLocation = "";
        this.VanguardSawMonsters = false;
        this.MarkedPreyTarget = null;
        this.CalmHeartNextHealAt = 0;
        this.LifeStealWindowAt = 0;
        this.LifeStealThisWindow = 0;
        this.SecondBreathReadyAt = 0;
        this.GuardStepUntil = 0;
        this.BackstepUntil = 0;
        this.ExplorerUntil = 0;
        this.MomentumUntil = 0;
        this.AdrenalineUntil = 0;
        this.FleetHunterUntil = 0;
        this.BattleTranceUntil = 0;
        this.OverclockUntil = 0;
        this.VoidPhaseUntil = 0;
        this.VoidReadyAt = 0;
        this.UnyieldingReadyAt = 0;
        this.MirrorGuardArmed = false;
        this.MirrorGuardReadyAt = 0;
        this.PredatorExpiresAt = 0;
        this.WarDrumExpiresAt = 0;
        this.WarDrumBurstUntil = 0;
        this.ApexPredatorBuffUntil = 0;
        this.TypicalRawHitDamage = 0;
        this.PendingRawHitDamage = 0;
        this.PendingCritLikeHit = false;
        this.PhantomCritArmed = false;
        this.PhantomSampleAt = 0;
        this.PhantomReadyAt = 0;
        this.TimeBreakerUntil = 0;
        this.TimeBreakerReadyAt = 0;
        this.StationarySince = Environment.TickCount64;
        if (Game1.player is not null)
            TryRemoveBuff(Game1.player, RuntimeBuffId);
    }

    private void ExpireTimedStacks(long now)
    {
        if (this.PredatorStacks > 0 && now >= this.PredatorExpiresAt)
            this.PredatorStacks = 0;
        if (this.WarDrumStacks > 0 && now >= this.WarDrumExpiresAt)
            this.WarDrumStacks = 0;
    }

    private int AbsorbShield(ref int shield, int damage)
    {
        if (shield <= 0 || damage <= 0)
            return damage;
        int absorbed = Math.Min(shield, damage);
        shield -= absorbed;
        return damage - absorbed;
    }

    private int Level(string id)
        => this.Upgrades.GetLevel(this.Cards.Get(id));

    private double LevelValue(string id, params double[] values)
    {
        if (values.Length == 0)
            return 0;
        int level = Math.Clamp(this.Level(id), 1, values.Length);
        return values[level - 1];
    }

    private int LevelInt(string id, params int[] values)
    {
        if (values.Length == 0)
            return 0;
        int level = Math.Clamp(this.Level(id), 1, values.Length);
        return values[level - 1];
    }

    private static bool IsBossLike(Monster monster)
    {
        string name = string.IsNullOrWhiteSpace(monster.Name) ? monster.GetType().Name : monster.Name;
        string source = monster.GetType().FullName ?? monster.GetType().Name;
        return DropService.ClassifyEnemy(name, source, monster.modData?.Pairs) == EnemyLootScale.BossLike;
    }

    private static void TryRemoveBuff(Farmer player, string id)
    {
        if (player.hasBuff(id))
            player.buffs.Remove(id);
    }
}

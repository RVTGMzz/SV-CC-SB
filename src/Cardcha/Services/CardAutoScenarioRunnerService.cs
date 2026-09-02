using Cardcha.Models;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Services;

internal enum CardAutoScenarioStatus
{
    NotRun,
    Pass,
    Fail,
    Blocked,
    Error
}

internal sealed class CardAutoScenarioResult
{
    public string CardId { get; init; } = "";
    public CardAutoScenarioStatus Status { get; init; }
    public int PassedLevels { get; init; }
    public int TotalLevels { get; init; }
    public string Summary { get; init; } = "";
    public string Detail { get; init; } = "";
}

internal readonly record struct CardScenarioCounts(int Pass, int Fail, int Blocked, int Error, int NotRun);

/// <summary>
/// TEST-only runtime scenario runner. It exercises the real Cardcha services with deterministic
/// synthetic monsters / forced RNG seams, compares expected design values against actual runtime
/// results, and restores SaveData + player state after every level. Results are RAM-only.
/// </summary>
internal sealed class CardAutoScenarioRunnerService
{
    private readonly IMonitor Monitor;
    private readonly ModConfig Config;
    private readonly CardRegistry Cards;
    private readonly SaveService Save;
    private readonly CardUpgradeService Upgrades;
    private readonly CombatService Combat;
    private readonly DropService Drops;
    private readonly GachaService Gacha;
    private readonly Dictionary<string, CardAutoScenarioResult> Results = new(StringComparer.OrdinalIgnoreCase);

    public CardAutoScenarioRunnerService(
        IMonitor monitor,
        ModConfig config,
        CardRegistry cards,
        SaveService save,
        CardUpgradeService upgrades,
        CombatService combat,
        DropService drops,
        GachaService gacha)
    {
        this.Monitor = monitor;
        this.Config = config;
        this.Cards = cards;
        this.Save = save;
        this.Upgrades = upgrades;
        this.Combat = combat;
        this.Drops = drops;
        this.Gacha = gacha;
    }

    public IReadOnlyList<CardDefinition> ActiveCards
        => this.Cards.All
            .Where(card => card.StableBaseId is >= 1 and <= 76)
            .OrderBy(card => card.StableBaseId)
            .ToList();

    public CardAutoScenarioResult Get(CardDefinition card)
        => this.Results.TryGetValue(card.Id, out CardAutoScenarioResult? result)
            ? result
            : new CardAutoScenarioResult
            {
                CardId = card.Id,
                Status = CardAutoScenarioStatus.NotRun,
                TotalLevels = Math.Max(1, card.MaxLevel),
                Summary = "Not run yet.",
                Detail = "Press AUTO RUN ALL."
            };

    public CardScenarioCounts Counts()
    {
        IReadOnlyList<CardDefinition> cards = this.ActiveCards;
        int pass = cards.Count(card => this.Get(card).Status == CardAutoScenarioStatus.Pass);
        int fail = cards.Count(card => this.Get(card).Status == CardAutoScenarioStatus.Fail);
        int blocked = cards.Count(card => this.Get(card).Status == CardAutoScenarioStatus.Blocked);
        int error = cards.Count(card => this.Get(card).Status == CardAutoScenarioStatus.Error);
        int notRun = cards.Count - pass - fail - blocked - error;
        return new(pass, fail, blocked, error, notRun);
    }

    public CardScenarioCounts RunAll()
    {
        if (!Context.IsWorldReady || Game1.player is null || Game1.currentLocation is null)
            return this.Counts();

        bool combatBefore = this.Config.EnableCombatCards;
        bool dropsBefore = this.Config.EnableMonsterDrops;
        double multiplierBefore = this.Config.PrototypeDropMultiplier;

        this.Config.EnableCombatCards = true;
        this.Config.EnableMonsterDrops = true;
        this.Config.PrototypeDropMultiplier = 1d;
        this.Results.Clear();

        try
        {
            foreach (CardDefinition card in this.ActiveCards)
                this.Results[card.Id] = this.RunCardInternal(card);
        }
        finally
        {
            this.Combat.ResetRuntime();
            this.Config.EnableCombatCards = combatBefore;
            this.Config.EnableMonsterDrops = dropsBefore;
            this.Config.PrototypeDropMultiplier = multiplierBefore;
        }

        CardScenarioCounts counts = this.Counts();
        this.Monitor.Log(
            $"AUTO SCENARIO RUNNER complete: PASS={counts.Pass} FAIL={counts.Fail} BLOCKED={counts.Blocked} ERROR={counts.Error} NOTRUN={counts.NotRun}.",
            counts.Fail > 0 || counts.Error > 0 ? LogLevel.Warn : LogLevel.Alert
        );
        return counts;
    }

    public CardAutoScenarioResult RunCard(CardDefinition card)
    {
        if (!Context.IsWorldReady || Game1.player is null || Game1.currentLocation is null)
            return this.Get(card);

        CardAutoScenarioResult result = this.RunCardInternal(card);
        this.Results[card.Id] = result;
        return result;
    }

    private CardAutoScenarioResult RunCardInternal(CardDefinition card)
    {
        if (card.Id.Equals("victory_charge", StringComparison.OrdinalIgnoreCase))
        {
            return new CardAutoScenarioResult
            {
                CardId = card.Id,
                Status = CardAutoScenarioStatus.Blocked,
                TotalLevels = Math.Max(1, card.MaxLevel),
                Summary = "BLOCKED: Boss Energy subsystem does not exist yet.",
                Detail = "No substitute effect is accepted."
            };
        }

        int max = Math.Max(1, card.MaxLevel);
        int passed = 0;
        List<string> details = new();

        for (int level = 1; level <= max; level++)
        {
            try
            {
                LevelScenarioCheck check = this.RunLevel(card, level);
                details.Add($"Lv{level}: {check.Detail}");
                if (check.Pass)
                    passed++;
                else
                {
                    return new CardAutoScenarioResult
                    {
                        CardId = card.Id,
                        Status = CardAutoScenarioStatus.Fail,
                        PassedLevels = passed,
                        TotalLevels = max,
                        Summary = $"{passed}/{max} levels matched. FAIL at Lv{level}.",
                        Detail = check.Detail
                    };
                }
            }
            catch (Exception ex)
            {
                return new CardAutoScenarioResult
                {
                    CardId = card.Id,
                    Status = CardAutoScenarioStatus.Error,
                    PassedLevels = passed,
                    TotalLevels = max,
                    Summary = $"Runner error at Lv{level}: {ex.GetType().Name}",
                    Detail = ex.Message
                };
            }
        }

        return new CardAutoScenarioResult
        {
            CardId = card.Id,
            Status = CardAutoScenarioStatus.Pass,
            PassedLevels = passed,
            TotalLevels = max,
            Summary = $"{passed}/{max} levels matched runtime scenarios.",
            Detail = details.Count == 0 ? "PASS" : details[^1]
        };
    }

    private LevelScenarioCheck RunLevel(CardDefinition card, int level)
    {
        using IDisposable saveScope = this.Save.BeginTransientTestScope();
        using IDisposable dropScope = this.Drops.BeginScenarioTestScope();
        using IDisposable gachaScope = this.Gacha.BeginScenarioTestScope();

        Farmer player = Game1.player;
        PlayerSnapshot playerSnapshot = new(player);

        try
        {
            this.Prepare(card, level);
            return card.Id switch
            {
                "iron_edge" => this.CheckFlatDamage(level, .04, .05, .06, .07, .08),
                "quick_hands" => this.CheckPassiveWeaponSpeed(level, .04, .05, .06, .07, .08),
                "keen_eye" => this.CheckCrit(level, .02, .025, .03, .035, .04),
                "heavy_blow" => this.CheckPassiveKnockback(level, .10, .15, .20, .25, .30),
                "first_strike" => this.CheckFirstStrike(level),
                "finisher" => this.CheckTargetHealthDamage(level, 0.19, .08, .10, .12, .14, .16),
                "hunters_focus" => this.CheckTargetHealthDamage(level, 1.00, .05, .06, .07, .08, .10),
                "steady_grip" => this.CheckSteadyGrip(level),
                "thick_hide" => this.CheckThickHide(level),
                "vitality" => this.CheckVitality(level),
                "second_breath" => this.CheckSecondBreath(level),
                "guard_step" => this.CheckGuardStep(level),
                "swift_feet" => this.CheckSwiftFeet(level),
                "backstep" => this.CheckBackstep(level),
                "stalwart" => this.CheckStalwart(level),
                "last_push" => this.CheckLowHealthDamage(level, .30, .05, .07, .09, .11, .13),
                "calm_heart" => this.CheckCalmHeart(level),
                "scavenger" => this.CheckDropBonus(level, "scavenger"),
                "essence_finder" => this.CheckEssenceFinder(level),
                "lucky_pocket" => this.CheckLuckyPocket(level),
                "treasure_magnet" => this.CheckTreasureMagnet(level),
                "explorer" => this.CheckKillPassiveMove(level, "explorer", .05, .06, .07, .08, .10),
                "patient_hunter" => this.CheckPatientHunter(level),
                "rhythm" => this.CheckRhythm(level),
                "bruiser" => this.CheckBruiser(level),
                "resilient" => this.CheckLowHealthDefense(level, .50, 1, 2, 3),
                "momentum" => this.CheckKillPassiveWeapon(level, "momentum", .05, .07, .09, .11),
                "blood_fang" => this.CheckBloodFang(level),
                "executioner" => this.CheckExecutioner(level),
                "opening_gambit" => this.CheckOpeningGambit(level),
                "deadeye" => this.CheckDeadeye(level),
                "predator" => this.CheckPredator(level),
                "adrenaline" => this.CheckAdrenaline(level),
                "counterforce" => this.CheckCounterforce(level),
                "iron_will" => this.CheckLowHealthDefense(level, .35, 2, 3, 4),
                "field_medic" => this.CheckFieldMedic(level),
                "lifeline" => this.CheckLifeline(level),
                "armor_breaker" => this.CheckComboReset(level, false),
                "crushing_impact" => this.CheckCrushingImpact(level),
                "fleet_hunter" => this.CheckKillPassiveMove(level, "fleet_hunter", .12, .15, .18, .21),
                "treasure_eye" => this.CheckDropBonus(level, "treasure_eye"),
                "card_seeker" => this.CheckCardSeeker(level),
                "dust_collector" => this.CheckDustCollector(level),
                "fortune_chain" => this.CheckFortuneChain(level),
                "battle_trance" => this.CheckBattleTrance(level),
                "vanguard" => this.CheckVanguard(level),
                "marked_prey" => this.CheckMarkedPrey(level),
                "unyielding" => this.CheckUnyielding(level),
                "collectors_instinct" => this.CheckBossDropBonus(level, "collectors_instinct"),
                "berserker_soul" => this.CheckBerserker(level),
                "chain_hunter" => this.CheckChainHunter(level),
                "soul_siphon" => this.CheckSoulSiphon(level),
                "phantom_step" => this.CheckPhantomStep(level),
                "reapers_mark" => this.CheckReapersMark(level),
                "stoneheart" => this.CheckStoneheart(level),
                "last_stand" => this.CheckLastStand(level),
                "war_drum" => this.CheckWarDrum(level),
                "treasure_hunter" => this.CheckBossDropBonus(level, "treasure_hunter"),
                "golden_hand" => this.CheckGoldenHand(level),
                "arcane_recycler" => this.CheckArcaneRecycler(level),
                "mirror_guard" => this.CheckMirrorGuard(level),
                "relentless" => this.CheckComboReset(level, true),
                "overclock" => this.CheckOverclock(level),
                "lucky_break" => this.CheckLuckyBreak(level),
                "battle_scholar" => this.CheckBattleScholar(level),
                "phoenix_heart" => this.CheckPhoenixHeart(level),
                "void_walker" => this.CheckVoidWalker(level),
                "soul_eater" => this.CheckSoulEater(level),
                "time_breaker" => this.CheckTimeBreaker(level),
                "titans_grip" => this.CheckTitansGrip(level),
                "perfect_hunter" => this.CheckPerfectHunter(level),
                "kings_ransom" => this.CheckKingsRansom(level),
                "cardmaster" => this.CheckCardmaster(level),
                "guardian_angel" => this.CheckGuardianAngel(level),
                "apex_predator" => this.CheckApexPredator(level),
                _ => LevelScenarioCheck.Fail($"No runtime scenario adapter for {card.Id}.")
            };
        }
        finally
        {
            this.Combat.ResetRuntime();
            playerSnapshot.Restore(player);
        }
    }

    private void Prepare(CardDefinition card, int level)
    {
        this.Combat.ResetRuntime();
        this.Combat.ResetVerificationTelemetry();
        this.Combat.DebugCompletion.DebugClearForcedChanceRoll();

        SaveData data = this.Save.Data;
        data.MachineDelivered = true;
        data.BinderUnlocked = true;
        data.MimiMeetupCompleted = true;
        data.OwnedCards.Add(card.Id);
        data.EquippedCards.Clear();
        data.EquippedCards.Add(card.Id);
        data.CardLevels[card.Id] = Math.Clamp(level, 1, Math.Max(1, card.MaxLevel));
        data.PhoenixHeartUsedToday = false;
        data.LifelineUsedToday = false;
        data.GuardianAngelUsedToday = false;
        data.BattleScholarMonsterTypesToday.Clear();
        data.FirstScrapTriggered = true;
        data.CardboardScraps = 0;
        data.ShinyScraps = 0;
        data.SuspiciousDust = 0;
        data.PullIndex = 0;
        data.StandardPullIndex = 0;
        data.DuplicatePullStreak = 0;
        data.StandardSinceRare = 0;
        data.StandardSinceEpic = 0;
        data.StandardSinceLegendary = 0;
        data.PremiumSinceEpic = 0;
        data.PremiumSinceLegendary = 0;

        Farmer player = Game1.player;
        player.maxHealth = 100;
        player.health = 100;
        player.Money = 1000;
        player.Stamina = player.MaxStamina;
    }

    private LevelScenarioCheck CheckFlatDamage(int level, params double[] bonus)
        => this.CheckDamageExpected(100, At(level, bonus));

    private LevelScenarioCheck CheckCrit(int level, params double[] bonus)
    {
        float before = .10f;
        float actual = this.Combat.ModifyCriticalChance(before, false, Game1.player);
        double expected = before + At(level, bonus);
        return Near(actual, expected)
            ? LevelScenarioCheck.Ok($"crit {before:0.###}->{actual:0.###}, expected {expected:0.###}")
            : LevelScenarioCheck.Fail($"crit actual {actual:0.###}, expected {expected:0.###}");
    }

    private LevelScenarioCheck CheckPassiveWeaponSpeed(int level, params double[] values)
    {
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expected = At(level, values);
        return Near(snap.WeaponSpeed, expected)
            ? LevelScenarioCheck.Ok($"weapon speed +{snap.WeaponSpeed:P1}, expected +{expected:P1}")
            : LevelScenarioCheck.Fail($"weapon speed {snap.WeaponSpeed:P1}, expected {expected:P1}");
    }

    private LevelScenarioCheck CheckPassiveKnockback(int level, params double[] values)
    {
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expected = At(level, values);
        return Near(snap.Knockback, expected)
            ? LevelScenarioCheck.Ok($"knockback +{snap.Knockback:P0}, expected +{expected:P0}")
            : LevelScenarioCheck.Fail($"knockback {snap.Knockback:P0}, expected {expected:P0}");
    }

    private LevelScenarioCheck CheckFirstStrike(int level)
    {
        double bonus = At(level, .08, .10, .12, .14, .16);
        Monster monster = NewMonster(1000, 1d);
        int first = this.Combat.ModifyMonsterDamage(monster, 100, false, Game1.player);
        ApplyHit(monster, first);
        this.Combat.AfterMonsterTakesDamage(monster, Game1.player, monster.Health + first);
        int second = this.Combat.ModifyMonsterDamage(monster, 100, false, Game1.player);
        int expectedFirst = DamageExpected(100, bonus);
        return first == expectedFirst && second == 100
            ? LevelScenarioCheck.Ok($"first {first}, second {second}; expected {expectedFirst}/100")
            : LevelScenarioCheck.Fail($"first/second {first}/{second}, expected {expectedFirst}/100");
    }

    private LevelScenarioCheck CheckTargetHealthDamage(int level, double fraction, params double[] values)
    {
        Monster monster = NewMonster(1000, fraction);
        double bonus = At(level, values);
        int actual = this.Combat.ModifyMonsterDamage(monster, 100, false, Game1.player);
        int expected = DamageExpected(100, bonus);
        return actual == expected
            ? LevelScenarioCheck.Ok($"damage 100->{actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"damage {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckSteadyGrip(int level)
    {
        Monster monster = NewMonster(2000, 1d);
        int before1 = monster.Health;
        int first = this.Combat.ModifyMonsterDamage(monster, 100, false, Game1.player);
        monster.Health -= first;
        this.Combat.AfterMonsterTakesDamage(monster, Game1.player, before1);

        double reduction = At(level, .15, .22, .30, .38, .45);
        int actual = this.Combat.ModifyMonsterDamage(monster, 140, false, Game1.player);
        int expected = Math.Max(1, (int)Math.Round(100d + 40d * (1d - reduction)));
        return actual == expected
            ? LevelScenarioCheck.Ok($"raw variance 140->{actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"stabilized {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckThickHide(int level)
    {
        this.Combat.SyncPassiveBuffs();
        int expected = (int)At(level, 1d, 2d, 3d);
        int actual = this.Combat.DebugThickHideDefense;
        return actual == expected
            ? LevelScenarioCheck.Ok($"defense +{actual}, expected +{expected}")
            : LevelScenarioCheck.Fail($"defense {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckVitality(int level)
    {
        this.Combat.SyncPassiveBuffs();
        int expectedBonus = (int)At(level, 10d, 15d, 20d, 25d, 30d);
        int actual = Game1.player.maxHealth;
        return actual == 100 + expectedBonus && this.Combat.DebugVitalityAppliedBonus == expectedBonus
            ? LevelScenarioCheck.Ok($"max HP 100->{actual}, expected {100 + expectedBonus}")
            : LevelScenarioCheck.Fail($"max HP {actual}, expected {100 + expectedBonus}");
    }

    private LevelScenarioCheck CheckSecondBreath(int level)
    {
        Game1.player.health = 50;
        int heal = (int)At(level, 1d, 2d, 3d);
        this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        return Game1.player.health == 50 + heal
            ? LevelScenarioCheck.Ok($"kill heal +{heal} HP")
            : LevelScenarioCheck.Fail($"HP {Game1.player.health}, expected {50 + heal}");
    }

    private LevelScenarioCheck CheckGuardStep(int level)
    {
        Game1.player.health = 90;
        this.Combat.AfterFarmerTakesDamage(Game1.player, 100);
        double reduction = At(level, .08, .10, .12, .14);
        int actual = this.Combat.ModifyFarmerDamage(100, Game1.player, NewMonster());
        int expected = ReducedExpected(100, reduction);
        return actual == expected
            ? LevelScenarioCheck.Ok($"incoming 100->{actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"incoming {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckSwiftFeet(int level)
    {
        double expected = At(level, .03, .04, .05, .06, .07);
        double actual = 0;
        WithTemporaryLivingMonster(_ =>
        {
            this.Combat.SyncPassiveBuffs();
            actual = this.Combat.DebugSwiftFeetSpeed;
        });
        return Near(actual, expected)
            ? LevelScenarioCheck.Ok($"move speed +{actual:P1}, expected +{expected:P1}")
            : LevelScenarioCheck.Fail($"move speed {actual:P1}, expected {expected:P1}");
    }

    private LevelScenarioCheck CheckBackstep(int level)
    {
        Game1.player.health = 90;
        this.Combat.AfterFarmerTakesDamage(Game1.player, 100);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expected = At(level, .10, .12, .14, .16);
        return Near(snap.MovePercent, expected)
            ? LevelScenarioCheck.Ok($"move +{snap.MovePercent:P0}, expected +{expected:P0}")
            : LevelScenarioCheck.Fail($"move {snap.MovePercent:P0}, expected {expected:P0}");
    }

    private LevelScenarioCheck CheckStalwart(int level)
    {
        long now = Environment.TickCount64;
        SetCoreField("LastStationaryPosition", Game1.player.Position);
        SetCoreField("StationarySince", now - 5000L);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        int expected = level >= 3 ? 2 : 1;
        return snap.Defense == expected
            ? LevelScenarioCheck.Ok($"stationary defense +{snap.Defense}, expected +{expected}")
            : LevelScenarioCheck.Fail($"defense {snap.Defense}, expected {expected}");
    }

    private LevelScenarioCheck CheckLowHealthDamage(int level, double healthFraction, params double[] values)
    {
        Game1.player.health = Math.Max(1, (int)Math.Floor(Game1.player.maxHealth * healthFraction));
        return this.CheckDamageExpected(100, At(level, values));
    }

    private LevelScenarioCheck CheckCalmHeart(int level)
    {
        Game1.player.health = 50;
        long now = Environment.TickCount64;
        SetCoreField("LastTakenHitAt", now - 10000L);
        SetCoreField("LastOutgoingHitAt", now - 10000L);
        SetCoreField("CalmHeartNextHealAt", now - 1L);
        this.Combat.DebugSyncCompletion(false);
        int expectedHeal = level >= 4 ? 2 : 1;
        return Game1.player.health == 50 + expectedHeal
            ? LevelScenarioCheck.Ok($"idle heal +{expectedHeal}")
            : LevelScenarioCheck.Fail($"HP {Game1.player.health}, expected {50 + expectedHeal}");
    }

    private LevelScenarioCheck CheckDropBonus(int level, string id)
    {
        int before = this.Save.Data.CardboardScraps;
        this.Drops.DebugSetForcedRolls(1d, 1d, 0d);
        this.Drops.TryDrop(Game1.currentLocation, Game1.player.Position, "Scenario Slime", 100, Game1.player, EnemyLootScale.Regular);
        int gained = this.Save.Data.CardboardScraps - before;
        return gained == 1
            ? LevelScenarioCheck.Ok($"{id} forced proc awarded +1 Scrap")
            : LevelScenarioCheck.Fail($"{id} awarded {gained}, expected 1");
    }

    private LevelScenarioCheck CheckEssenceFinder(int level)
    {
        int before = this.Save.Data.CardboardScraps;
        this.Drops.DebugSetForcedRolls(0d, 0d, 1d);
        this.Drops.TryDrop(Game1.currentLocation, Game1.player.Position, "Scenario Slime", 100, Game1.player, EnemyLootScale.Regular);
        int gained = this.Save.Data.CardboardScraps - before;
        return gained == 2 && this.Drops.LastNormalAmount == 2
            ? LevelScenarioCheck.Ok("normal Scrap 1 + Essence Finder 1 = 2")
            : LevelScenarioCheck.Fail($"Scrap gained {gained}, LastNormalAmount={this.Drops.LastNormalAmount}, expected 2");
    }

    private LevelScenarioCheck CheckLuckyPocket(int level)
    {
        int before = Game1.player.Money;
        this.Drops.DebugSetForcedRolls(1d, 1d, 0d);
        this.Drops.TryDrop(Game1.currentLocation, Game1.player.Position, "Scenario Slime", 100, Game1.player, EnemyLootScale.Regular);
        int gained = Game1.player.Money - before;
        return gained == 25
            ? LevelScenarioCheck.Ok("forced proc +25g")
            : LevelScenarioCheck.Fail($"money +{gained}, expected +25g");
    }

    private LevelScenarioCheck CheckTreasureMagnet(int level)
    {
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        int expected = (int)At(level, 32d, 48d, 64d, 80d, 96d);
        return snap.MagneticRadius == expected
            ? LevelScenarioCheck.Ok($"magnet +{snap.MagneticRadius}, expected {expected}")
            : LevelScenarioCheck.Fail($"magnet {snap.MagneticRadius}, expected {expected}");
    }

    private LevelScenarioCheck CheckKillPassiveMove(int level, string id, params double[] values)
    {
        this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expected = At(level, values);
        return Near(snap.MovePercent, expected)
            ? LevelScenarioCheck.Ok($"{id} move +{snap.MovePercent:P0}, expected +{expected:P0}")
            : LevelScenarioCheck.Fail($"{id} move {snap.MovePercent:P0}, expected {expected:P0}");
    }

    private LevelScenarioCheck CheckPatientHunter(int level)
    {
        SetCoreField("LastOutgoingHitAt", Environment.TickCount64 - 5000L);
        float actual = this.Combat.ModifyCriticalChance(.10f, false, Game1.player);
        double expected = .10 + At(level, .03, .04, .05, .06, .07);
        return Near(actual, expected)
            ? LevelScenarioCheck.Ok($"crit {actual:P1}, expected {expected:P1}")
            : LevelScenarioCheck.Fail($"crit {actual:P1}, expected {expected:P1}");
    }

    private LevelScenarioCheck CheckRhythm(int level)
    {
        Monster monster = NewMonster(3000, 1d);
        for (int i = 0; i < 3; i++)
            PerformHit(monster, 10);
        int actual = this.Combat.ModifyMonsterDamage(monster, 100, false, Game1.player);
        int expected = DamageExpected(100, At(level, .04, .05, .06, .07, .08));
        return actual == expected
            ? LevelScenarioCheck.Ok($"4th-hit rhythm damage {actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"rhythm damage {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckBruiser(int level)
    {
        Monster monster = NewMonster(300, 1d);
        int actual = this.Combat.ModifyMonsterDamage(monster, 100, false, Game1.player);
        int expected = DamageExpected(100, At(level, .04, .05, .06, .07, .08));
        return actual == expected
            ? LevelScenarioCheck.Ok($"300-HP target damage {actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"damage {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckLowHealthDefense(int level, double threshold, params int[] values)
    {
        Game1.player.health = Math.Max(1, (int)Math.Floor(100d * threshold));
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        int expected = AtInt(level, values);
        return snap.Defense == expected
            ? LevelScenarioCheck.Ok($"defense +{snap.Defense}, expected +{expected}")
            : LevelScenarioCheck.Fail($"defense {snap.Defense}, expected {expected}");
    }

    private LevelScenarioCheck CheckKillPassiveWeapon(int level, string id, params double[] values)
    {
        this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expected = At(level, values);
        return Near(snap.WeaponSpeed, expected)
            ? LevelScenarioCheck.Ok($"{id} weapon speed +{snap.WeaponSpeed:P0}, expected +{expected:P0}")
            : LevelScenarioCheck.Fail($"{id} weapon speed {snap.WeaponSpeed:P0}, expected {expected:P0}");
    }

    private LevelScenarioCheck CheckBloodFang(int level)
    {
        Game1.player.health = 50;
        this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        int expectedHeal = Math.Max(1, (int)Math.Ceiling(100d * At(level, .020, .025, .030, .035)));
        return Game1.player.health == 50 + expectedHeal
            ? LevelScenarioCheck.Ok($"kill heal +{expectedHeal} HP")
            : LevelScenarioCheck.Fail($"HP {Game1.player.health}, expected {50 + expectedHeal}");
    }

    private LevelScenarioCheck CheckExecutioner(int level)
        => this.CheckTargetHealthDamage(level, .19, .15, .18, .21, .24);

    private LevelScenarioCheck CheckOpeningGambit(int level)
    {
        Monster monster = NewMonster(1000, 1d);
        int actual = this.Combat.ModifyMonsterDamage(monster, 100, false, Game1.player);
        int expected = DamageExpected(100, At(level, .18, .21, .24, .27));
        return actual == expected
            ? LevelScenarioCheck.Ok($"opening hit {actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"opening hit {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckDeadeye(int level)
    {
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expected = At(level, .12, .16, .20, .24);
        return Near(snap.CriticalPower, expected)
            ? LevelScenarioCheck.Ok($"crit power +{snap.CriticalPower:P0}, expected +{expected:P0}")
            : LevelScenarioCheck.Fail($"crit power {snap.CriticalPower:P0}, expected {expected:P0}");
    }

    private LevelScenarioCheck CheckPredator(int level)
    {
        this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        int actual = this.Combat.ModifyMonsterDamage(NewMonster(1000), 100, false, Game1.player);
        int expected = DamageExpected(100, At(level, .03, .035, .04, .045));
        return actual == expected
            ? LevelScenarioCheck.Ok($"1 stack damage {actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"damage {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckAdrenaline(int level)
    {
        this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expectedWeapon = At(level, .08, .10, .12, .14);
        double expectedMove = At(level, .05, .06, .07, .08);
        return Near(snap.WeaponSpeed, expectedWeapon) && Near(snap.MovePercent, expectedMove)
            ? LevelScenarioCheck.Ok($"weapon {snap.WeaponSpeed:P0}, move {snap.MovePercent:P0}")
            : LevelScenarioCheck.Fail($"weapon/move {snap.WeaponSpeed:P0}/{snap.MovePercent:P0}, expected {expectedWeapon:P0}/{expectedMove:P0}");
    }

    private LevelScenarioCheck CheckCounterforce(int level)
    {
        Game1.player.health = 90;
        this.Combat.AfterFarmerTakesDamage(Game1.player, 100);
        Monster monster = NewMonster(1000);
        int first = this.Combat.ModifyMonsterDamage(monster, 100, false, Game1.player);
        int second = this.Combat.ModifyMonsterDamage(monster, 100, false, Game1.player);
        int expected = DamageExpected(100, At(level, .15, .20, .25, .30));
        return first == expected && second == 100
            ? LevelScenarioCheck.Ok($"armed hit {first}, next {second}; expected {expected}/100")
            : LevelScenarioCheck.Fail($"hits {first}/{second}, expected {expected}/100");
    }

    private LevelScenarioCheck CheckFieldMedic(int level)
    {
        Game1.player.health = 50;
        for (int i = 0; i < 8; i++)
            this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        int heal = AtInt(level, 8, 10, 12, 15);
        return Game1.player.health == 50 + heal
            ? LevelScenarioCheck.Ok($"8 kills heal +{heal}")
            : LevelScenarioCheck.Fail($"HP {Game1.player.health}, expected {50 + heal}");
    }

    private LevelScenarioCheck CheckLifeline(int level)
    {
        Game1.player.health = 20;
        this.Combat.AfterFarmerTakesDamage(Game1.player, 40);
        int heal = AtInt(level, 12, 16, 20);
        int expected = Math.Min(100, 20 + heal);
        return Game1.player.health == expected && this.Save.Data.LifelineUsedToday
            ? LevelScenarioCheck.Ok($"threshold heal to {expected}, daily flag set")
            : LevelScenarioCheck.Fail($"HP/flag {Game1.player.health}/{this.Save.Data.LifelineUsedToday}, expected {expected}/true");
    }

    private LevelScenarioCheck CheckComboReset(int level, bool relentless)
    {
        double per = relentless
            ? At(level, .02, .025, .03)
            : At(level, .02, .025, .03, .035);
        Monster a = NewMonster(3000);
        Monster b = NewMonster(3000);
        PerformHit(a, 10);
        int stacked = this.Combat.ModifyMonsterDamage(a, 100, false, Game1.player);
        PerformHit(b, 10);
        int returned = this.Combat.ModifyMonsterDamage(a, 100, false, Game1.player);
        int expectedStacked = DamageExpected(100, per);
        return stacked == expectedStacked && returned == 100
            ? LevelScenarioCheck.Ok($"same-target {stacked}; A→B→A reset {returned}")
            : LevelScenarioCheck.Fail($"same/reset {stacked}/{returned}, expected {expectedStacked}/100");
    }

    private LevelScenarioCheck CheckCrushingImpact(int level)
    {
        Monster monster = NewMonster(5000);
        PerformHit(monster, 100);

        int before = monster.Health;
        int damage = this.Combat.ModifyMonsterDamage(monster, 180, false, Game1.player);
        int x = 100;
        int y = 0;
        this.Combat.ModifyMonsterTrajectory(ref x, ref y, false, Game1.player);
        monster.Health = Math.Max(1, monster.Health - damage);
        this.Combat.AfterMonsterTakesDamage(monster, Game1.player, before);

        double knock = At(level, .30, .40, .50, .60);
        int expectedX = (int)Math.Round(100d * (1d + knock));
        int expectedStun = AtInt(level, 200, 250, 300, 350);
        int actualStun = ReadWrappedIntField(monster, "stunTime");
        bool stunSupported = actualStun >= expectedStun;
        return x == expectedX && stunSupported
            ? LevelScenarioCheck.Ok($"crit-like trajectory 100->{x}, stagger {actualStun}ms")
            : LevelScenarioCheck.Fail($"trajectory/stun {x}/{actualStun}, expected {expectedX}/≥{expectedStun}");
    }

    private LevelScenarioCheck CheckCardSeeker(int level)
    {
        this.Drops.DebugSetForcedRolls(1d, 1d);
        this.Drops.TryDrop(Game1.currentLocation, Game1.player.Position, "Scenario Slime", 100, Game1.player, EnemyLootScale.Regular);
        double expectedNormal = .12 * (1d + At(level, .15, .18, .21, .24));
        return Near(this.Drops.LastNormalChance, expectedNormal) && Near(this.Drops.LastShinyChance, .03)
            ? LevelScenarioCheck.Ok($"normal {this.Drops.LastNormalChance:P2}, shiny unchanged {this.Drops.LastShinyChance:P0}")
            : LevelScenarioCheck.Fail($"normal/shiny {this.Drops.LastNormalChance:P2}/{this.Drops.LastShinyChance:P2}, expected {expectedNormal:P2}/3%");
    }

    private LevelScenarioCheck CheckDustCollector(int level)
    {
        PrepareGachaPool(maxed: true);
        this.Save.Data.EquippedCards.Clear();
        this.Save.Data.EquippedCards.Add("dust_collector");
        this.Save.Data.CardLevels["dust_collector"] = level;
        this.Gacha.DebugSetForcedRolls(.50, 0d);
        PullResult result = this.Gacha.Pull(PullType.Premium);
        return result.DustAwarded == 2
            ? LevelScenarioCheck.Ok($"maxed duplicate dust {result.DustAwarded} (1 base +1 forced extra)")
            : LevelScenarioCheck.Fail($"dust {result.DustAwarded}, expected 2");
    }

    private LevelScenarioCheck CheckFortuneChain(int level)
    {
        for (int i = 0; i < 5; i++)
            this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        int before = this.Save.Data.CardboardScraps;
        this.Drops.DebugSetForcedRolls(1d, 1d, 0d);
        this.Drops.TryDrop(Game1.currentLocation, Game1.player.Position, "Scenario Slime", 100, Game1.player, EnemyLootScale.Regular);
        int gained = this.Save.Data.CardboardScraps - before;
        return this.Combat.CurrentNoHitKillStreak >= 5 && gained == 1
            ? LevelScenarioCheck.Ok($"no-hit streak {this.Combat.CurrentNoHitKillStreak}, forced +1 Scrap")
            : LevelScenarioCheck.Fail($"streak/scrap {this.Combat.CurrentNoHitKillStreak}/{gained}, expected ≥5/1");
    }

    private LevelScenarioCheck CheckBattleTrance(int level)
    {
        Monster monster = NewMonster(5000);
        for (int i = 0; i < 4; i++)
            PerformHit(monster, 10);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expected = At(level, .06, .08, .10, .12);
        return Near(snap.WeaponSpeed, expected)
            ? LevelScenarioCheck.Ok($"4-hit burst weapon speed +{snap.WeaponSpeed:P0}")
            : LevelScenarioCheck.Fail($"weapon speed {snap.WeaponSpeed:P0}, expected {expected:P0}");
    }

    private LevelScenarioCheck CheckVanguard(int level)
    {
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        int expectedShield = AtInt(level, 5, 8, 11, 14);
        int actualIncoming = this.Combat.ModifyFarmerDamage(10, Game1.player, NewMonster());
        int expectedIncoming = Math.Max(0, 10 - expectedShield);
        return snap.VanguardShield == expectedShield && actualIncoming == expectedIncoming
            ? LevelScenarioCheck.Ok($"encounter shield {snap.VanguardShield}; hit 10->{actualIncoming}")
            : LevelScenarioCheck.Fail($"shield/hit {snap.VanguardShield}/{actualIncoming}, expected {expectedShield}/{expectedIncoming}");
    }

    private LevelScenarioCheck CheckMarkedPrey(int level)
    {
        SetCoreField("LastOutgoingHitAt", Environment.TickCount64 - 5000L);
        int actual = this.Combat.ModifyMonsterDamage(NewMonster(1000), 100, false, Game1.player);
        int expected = DamageExpected(100, At(level, .10, .13, .16, .19));
        return actual == expected
            ? LevelScenarioCheck.Ok($"marked target damage {actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"damage {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckUnyielding(int level)
    {
        double capFraction = At(level, .45, .40, .35);
        int actual = this.Combat.ModifyFarmerDamage(100, Game1.player, NewMonster());
        int expected = Math.Max(1, (int)Math.Ceiling(100d * capFraction));
        return actual == expected
            ? LevelScenarioCheck.Ok($"big hit capped 100->{actual}")
            : LevelScenarioCheck.Fail($"incoming {actual}, expected cap {expected}");
    }

    private LevelScenarioCheck CheckBossDropBonus(int level, string id)
    {
        int before = this.Save.Data.CardboardScraps;
        this.Drops.DebugSetForcedRolls(1d, 1d, 0d);
        this.Drops.TryDrop(Game1.currentLocation, Game1.player.Position, "Scenario Boss", 1000, Game1.player, EnemyLootScale.BossLike);
        int gained = this.Save.Data.CardboardScraps - before;
        return gained == 1
            ? LevelScenarioCheck.Ok($"{id} boss forced proc +1 Scrap")
            : LevelScenarioCheck.Fail($"{id} Scrap +{gained}, expected 1");
    }

    private LevelScenarioCheck CheckBerserker(int level)
    {
        Game1.player.health = 50;
        double perTen = At(level, .01, .012, .014);
        double cap = At(level, .08, .10, .12);
        double bonus = Math.Min(cap, 5d * perTen);
        int actual = this.Combat.ModifyMonsterDamage(NewMonster(1000), 100, false, Game1.player);
        int expected = DamageExpected(100, bonus);
        return actual == expected
            ? LevelScenarioCheck.Ok($"50% missing HP damage {actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"damage {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckChainHunter(int level)
    {
        this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        int actual = this.Combat.ModifyMonsterDamage(NewMonster(1000), 100, false, Game1.player);
        int expected = DamageExpected(100, At(level, .04, .05, .06));
        return this.Combat.CurrentChainHunterStacks == 1 && actual == expected
            ? LevelScenarioCheck.Ok($"1 stack; damage {actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"stack/damage {this.Combat.CurrentChainHunterStacks}/{actual}, expected 1/{expected}");
    }

    private LevelScenarioCheck CheckSoulSiphon(int level)
    {
        Game1.player.health = 50;
        Monster monster = NewMonster(3000);
        PerformHit(monster, 50);
        PerformHit(monster, 50);
        int healed = Game1.player.health - 50;
        return healed == 1
            ? LevelScenarioCheck.Ok("fractional lifesteal: two 50-damage hits accumulated to +1 HP")
            : LevelScenarioCheck.Fail($"healed {healed}, expected 1 from fractional carry");
    }

    private LevelScenarioCheck CheckPhantomStep(int level)
    {
        long now = Environment.TickCount64;
        SetCoreField("PhantomSamplePosition", Game1.player.Position);
        SetCoreField("PhantomSampleAt", now - 300L);
        SetCoreField("LastTakenHitAt", now - 1000L);
        SetCoreField("PhantomReadyAt", 0L);
        Game1.player.Position += new Vector2(64f, 0f);
        this.Combat.DebugSyncCompletion(true);
        float actual = this.Combat.ModifyCriticalChance(.10f, false, Game1.player);
        double expected = .10 + At(level, .15, .20, .25);
        return Near(actual, expected)
            ? LevelScenarioCheck.Ok($"evasive displacement armed crit {actual:P0}")
            : LevelScenarioCheck.Fail($"crit {actual:P0}, expected {expected:P0}");
    }

    private LevelScenarioCheck CheckReapersMark(int level)
    {
        Monster monster = NewMonster(5000);
        for (int i = 0; i < 4; i++)
            PerformHit(monster, 10);
        int actual = this.Combat.ModifyMonsterDamage(monster, 100, false, Game1.player);
        int expected = DamageExpected(100, At(level, .08, .10, .12));
        return actual == expected
            ? LevelScenarioCheck.Ok($"4-hit mark damage {actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"marked damage {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckStoneheart(int level)
    {
        Game1.player.health = 100;
        double reduction = At(level, .10, .12, .15);
        int actual = this.Combat.ModifyFarmerDamage(100, Game1.player, NewMonster());
        int expected = ReducedExpected(100, reduction);
        return actual == expected
            ? LevelScenarioCheck.Ok($"high-HP incoming 100->{actual}")
            : LevelScenarioCheck.Fail($"incoming {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckLastStand(int level)
    {
        Game1.player.health = 20;
        bool active = false;
        int actual = 0;
        WithTemporaryLivingMonster(_ =>
        {
            this.Combat.SyncPassiveBuffs();
            active = this.Combat.IsLastStandActive;
            actual = this.Combat.ModifyMonsterDamage(NewMonster(1000), 100, false, Game1.player);
        });
        int expected = DamageExpected(100, At(level, .12, .16, .20));
        return active && actual == expected
            ? LevelScenarioCheck.Ok($"low-HP encounter active; damage {actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"active/damage {active}/{actual}, expected true/{expected}");
    }

    private LevelScenarioCheck CheckWarDrum(int level)
    {
        for (int i = 0; i < 4; i++)
            this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        int actualDamage = this.Combat.ModifyMonsterDamage(NewMonster(1000), 100, false, Game1.player);
        double expectedWeapon = 4d * At(level, .03, .04, .05);
        int expectedDamage = DamageExpected(100, At(level, .08, .10, .12));
        return Near(snap.WeaponSpeed, expectedWeapon) && actualDamage == expectedDamage
            ? LevelScenarioCheck.Ok($"4 stacks weapon {snap.WeaponSpeed:P0}; burst damage {actualDamage}")
            : LevelScenarioCheck.Fail($"weapon/damage {snap.WeaponSpeed:P0}/{actualDamage}, expected {expectedWeapon:P0}/{expectedDamage}");
    }

    private LevelScenarioCheck CheckGoldenHand(int level)
    {
        this.Save.Data.OwnedCards.Clear();
        this.Save.Data.CardLevels.Clear();
        this.Save.Data.EquippedCards.Clear();
        this.Save.Data.EquippedCards.Add("golden_hand");
        this.Save.Data.CardLevels["golden_hand"] = level;
        this.Save.Data.PullIndex = 9;
        this.Save.Data.StandardPullIndex = 0;
        this.Save.Data.SuspiciousDust = 0;
        this.Gacha.DebugSetForcedRolls(.90);
        PullResult result = this.Gacha.Pull(PullType.Standard);
        int expected = AtInt(level, 5, 7, 10);
        return this.Save.Data.SuspiciousDust == expected && result.DustAwarded == expected
            ? LevelScenarioCheck.Ok($"10th pull +{expected} Dust")
            : LevelScenarioCheck.Fail($"dust {this.Save.Data.SuspiciousDust}/{result.DustAwarded}, expected {expected}");
    }

    private LevelScenarioCheck CheckArcaneRecycler(int level)
    {
        PrepareGachaPool(maxed: false);
        this.Save.Data.EquippedCards.Clear();
        this.Save.Data.EquippedCards.Add("arcane_recycler");
        this.Save.Data.CardLevels["arcane_recycler"] = level;
        this.Save.Data.ShinyScraps = 0;
        this.Gacha.DebugSetForcedRolls(.50, 0d);
        _ = this.Gacha.Pull(PullType.Premium);
        double rate = At(level, .05, .075, .10);
        double expectedRaw = Math.Max(0, this.Config.PremiumPullCost) * rate;
        int expected = (int)Math.Floor(expectedRaw);
        if (expectedRaw - expected > 0)
            expected++;
        return this.Save.Data.ShinyScraps == expected
            ? LevelScenarioCheck.Ok($"forced fractional refund +{expected} Shiny Scrap")
            : LevelScenarioCheck.Fail($"refund {this.Save.Data.ShinyScraps}, expected {expected}");
    }

    private LevelScenarioCheck CheckMirrorGuard(int level)
    {
        Game1.player.health = 70;
        this.Combat.AfterFarmerTakesDamage(Game1.player, 100);
        Game1.player.health = 100;
        double reduction = At(level, .30, .40, .50);
        int actual = this.Combat.ModifyFarmerDamage(100, Game1.player, NewMonster());
        int expected = ReducedExpected(100, reduction);
        return actual == expected
            ? LevelScenarioCheck.Ok($"armed next hit 100->{actual}")
            : LevelScenarioCheck.Fail($"incoming {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckOverclock(int level)
    {
        this.Combat.OnCustomEnemyKilled(Game1.player, "ScenarioBoss", true);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expected = At(level, .15, .20, .25);
        return Near(snap.WeaponSpeed, expected)
            ? LevelScenarioCheck.Ok($"boss kill weapon speed +{snap.WeaponSpeed:P0}")
            : LevelScenarioCheck.Fail($"weapon speed {snap.WeaponSpeed:P0}, expected {expected:P0}");
    }

    private LevelScenarioCheck CheckLuckyBreak(int level)
    {
        int before = this.Save.Data.CardboardScraps;
        this.Drops.DebugSetForcedRolls(
            1d, 1d,
            1d, 1d,
            1d, 1d,
            1d, 1d, 0d
        );
        for (int i = 0; i < 4; i++)
            this.Drops.TryDrop(Game1.currentLocation, Game1.player.Position, "Scenario Slime", 100, Game1.player, EnemyLootScale.Regular);
        int gained = this.Save.Data.CardboardScraps - before;
        return gained == 1
            ? LevelScenarioCheck.Ok("3 failed kills built streak; 4th forced bonus +1 Scrap")
            : LevelScenarioCheck.Fail($"bonus Scrap {gained}, expected 1");
    }

    private LevelScenarioCheck CheckBattleScholar(int level)
    {
        this.Combat.OnCustomEnemyKilled(Game1.player, "Scenario.TypeA", false);
        this.Combat.OnCustomEnemyKilled(Game1.player, "Scenario.TypeB", false);
        this.Combat.OnCustomEnemyKilled(Game1.player, "Scenario.TypeC", false);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expectedWeapon = At(level, .02, .03, .04);
        double expectedAttack = At(level, .03, .04, .05);
        int expectedDefense = level >= 3 ? 1 : 0;
        return this.Save.Data.BattleScholarMonsterTypesToday.Count >= 3
            && Near(snap.WeaponSpeed, expectedWeapon)
            && Near(snap.AttackMultiplier, expectedAttack)
            && snap.Defense == expectedDefense
            ? LevelScenarioCheck.Ok($"3 types; weapon {snap.WeaponSpeed:P0}, attack {snap.AttackMultiplier:P0}, defense {snap.Defense}")
            : LevelScenarioCheck.Fail($"types/weapon/attack/def {this.Save.Data.BattleScholarMonsterTypesToday.Count}/{snap.WeaponSpeed:P0}/{snap.AttackMultiplier:P0}/{snap.Defense}");
    }

    private LevelScenarioCheck CheckPhoenixHeart(int level)
    {
        Game1.player.health = 0;
        this.Combat.AfterFarmerTakesDamage(Game1.player, 50);
        int expectedDuration = Math.Max(1200, AtInt(level, 1000, 1500, 2000));
        return Game1.player.health == 1
            && this.Save.Data.PhoenixHeartUsedToday
            && Game1.player.currentTemporaryInvincibilityDuration == expectedDuration
            ? LevelScenarioCheck.Ok($"lethal rescue to 1 HP; invincibility {expectedDuration}ms")
            : LevelScenarioCheck.Fail($"HP/flag/inv {Game1.player.health}/{this.Save.Data.PhoenixHeartUsedToday}/{Game1.player.currentTemporaryInvincibilityDuration}, expected 1/true/{expectedDuration}");
    }

    private LevelScenarioCheck CheckVoidWalker(int level)
    {
        this.Combat.DebugCompletion.DebugForceNextChanceRoll(0d);
        Game1.player.health = 90;
        this.Combat.AfterFarmerTakesDamage(Game1.player, 100);
        Game1.player.health = 100;
        double reduction = At(level, .40, .50, .60);
        int actual = this.Combat.ModifyFarmerDamage(100, Game1.player, NewMonster());
        int expected = ReducedExpected(100, reduction);
        return actual == expected
            ? LevelScenarioCheck.Ok($"triggering hit unmodified; subsequent phase hit 100->{actual}")
            : LevelScenarioCheck.Fail($"phase incoming {actual}, expected {expected}");
    }

    private LevelScenarioCheck CheckSoulEater(int level)
    {
        Game1.player.health = 50;
        int target = AtInt(level, 6, 5, 4);
        for (int i = 0; i < target; i++)
            this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        int heal = (int)Math.Ceiling(100d * At(level, .10, .12, .15));
        int expectedHealth = Math.Min(100, 50 + heal);
        int actualDamage = this.Combat.ModifyMonsterDamage(NewMonster(1000), 100, false, Game1.player);
        int expectedDamage = DamageExpected(100, At(level, .10, .12, .15));
        return this.Combat.IsSoulEaterActive && Game1.player.health == expectedHealth && actualDamage == expectedDamage
            ? LevelScenarioCheck.Ok($"{target} kills; HP {expectedHealth}; buff damage {actualDamage}")
            : LevelScenarioCheck.Fail($"active/HP/dmg {this.Combat.IsSoulEaterActive}/{Game1.player.health}/{actualDamage}, expected true/{expectedHealth}/{expectedDamage}");
    }

    private LevelScenarioCheck CheckTimeBreaker(int level)
    {
        Monster monster = NewMonster(5000);
        PerformHit(monster, 100);
        this.Combat.DebugCompletion.DebugForceNextChanceRoll(0d);
        PerformHit(monster, 180);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double expected = At(level, .30, .35, .40);
        return Near(snap.WeaponSpeed, expected)
            ? LevelScenarioCheck.Ok($"forced crit-like proc weapon speed +{snap.WeaponSpeed:P0}")
            : LevelScenarioCheck.Fail($"weapon speed {snap.WeaponSpeed:P0}, expected {expected:P0}");
    }

    private LevelScenarioCheck CheckTitansGrip(int level)
    {
        int actualDamage = this.Combat.ModifyMonsterDamage(NewMonster(2000), 100, false, Game1.player);
        CardPassiveDebugSnapshot snap = this.Combat.DebugSyncCompletion(true);
        double damage = At(level, .25, .30, .35);
        double speedPenalty = At(level, .10, .08, .06);
        int expectedDamage = DamageExpected(100, damage);
        return actualDamage == expectedDamage && Near(snap.WeaponSpeed, -speedPenalty)
            ? LevelScenarioCheck.Ok($"damage {actualDamage}; weapon speed {snap.WeaponSpeed:P0}")
            : LevelScenarioCheck.Fail($"damage/speed {actualDamage}/{snap.WeaponSpeed:P0}, expected {expectedDamage}/{(-speedPenalty):P0}");
    }

    private LevelScenarioCheck CheckPerfectHunter(int level)
    {
        for (int i = 0; i < 5; i++)
            this.Combat.OnMonsterKilled(NewMonster(), Game1.player);
        float actual = this.Combat.ModifyCriticalChance(.10f, false, Game1.player);
        double expected = .10 + 5d * At(level, .02, .025, .03);
        return Near(actual, expected)
            ? LevelScenarioCheck.Ok($"5 no-hit kills crit {actual:P1}, expected {expected:P1}")
            : LevelScenarioCheck.Fail($"crit {actual:P1}, expected {expected:P1}");
    }

    private LevelScenarioCheck CheckKingsRansom(int level)
    {
        int normalBefore = this.Save.Data.CardboardScraps;
        int shinyBefore = this.Save.Data.ShinyScraps;
        if (level <= 1)
            this.Drops.DebugSetForcedRolls(1d, 1d);
        else
            this.Drops.DebugSetForcedRolls(1d, 1d, 0d);
        this.Drops.TryDrop(Game1.currentLocation, Game1.player.Position, "Scenario Boss", 1000, Game1.player, EnemyLootScale.BossLike);
        int normal = this.Save.Data.CardboardScraps - normalBefore;
        int shiny = this.Save.Data.ShinyScraps - shinyBefore;
        bool pass = level <= 1 ? normal == 1 && shiny == 0 : normal == 0 && shiny == 1;
        return pass
            ? LevelScenarioCheck.Ok(level <= 1 ? "boss reward +1 normal Scrap" : "forced upgrade converted reward to +1 Shiny")
            : LevelScenarioCheck.Fail($"normal/shiny +{normal}/+{shiny}, expected {(level <= 1 ? "1/0" : "0/1")}");
    }

    private LevelScenarioCheck CheckCardmaster(int level)
    {
        this.Save.Data.OwnedCards.Clear();
        this.Save.Data.CardLevels.Clear();
        this.Save.Data.EquippedCards.Clear();
        this.Save.Data.EquippedCards.Add("cardmaster");
        this.Save.Data.CardLevels["cardmaster"] = level;
        this.Save.Data.StandardPullIndex = 9;
        this.Save.Data.PullIndex = 0;
        this.Save.Data.SuspiciousDust = 0;
        this.Gacha.DebugSetForcedRolls(.90);
        PullResult tenth = this.Gacha.Pull(PullType.Standard);
        int expectedDust = AtInt(level, 5, 7, 10);
        bool dustOk = this.Save.Data.SuspiciousDust == expectedDust && tenth.DustAwarded == expectedDust;

        this.Save.Data.StandardSinceRare = 0;
        this.Save.Data.StandardSinceEpic = 0;
        this.Save.Data.StandardSinceLegendary = 0;
        this.Gacha.DebugSetForcedRolls(.455);
        PullResult boosted = this.Gacha.Pull(PullType.Standard);
        bool rarityOk = boosted.Card.Rarity >= CardRarity.Rare;

        return dustOk && rarityOk
            ? LevelScenarioCheck.Ok($"10th Standard +{expectedDust} Dust; next forced 45.5% roll => {boosted.Card.Rarity}")
            : LevelScenarioCheck.Fail($"dust/rarity {this.Save.Data.SuspiciousDust}/{boosted.Card.Rarity}, expected {expectedDust}/Rare+");
    }

    private LevelScenarioCheck CheckGuardianAngel(int level)
    {
        Game1.player.health = 15;
        this.Combat.AfterFarmerTakesDamage(Game1.player, 100);
        Game1.player.health = 15;
        int actual = this.Combat.ModifyFarmerDamage(20, Game1.player, NewMonster());
        int expectedShield = (int)Math.Ceiling(100d * At(level, .25, .35, .45));
        bool expectedAbsorb = expectedShield >= 20;
        return this.Save.Data.GuardianAngelUsedToday && actual == (expectedAbsorb ? 0 : 20 - expectedShield)
            ? LevelScenarioCheck.Ok($"≤20% HP shield {expectedShield}; next 20 damage -> {actual}")
            : LevelScenarioCheck.Fail($"flag/hit {this.Save.Data.GuardianAngelUsedToday}/{actual}, expected true/{Math.Max(0, 20 - expectedShield)}");
    }

    private LevelScenarioCheck CheckApexPredator(int level)
    {
        Monster boss = NewMonster(3000);
        boss.modData["rank"] = "boss";
        int bossDamage = this.Combat.ModifyMonsterDamage(boss, 100, false, Game1.player);
        int expectedBoss = DamageExpected(100, At(level, .10, .15, .20));
        this.Combat.OnCustomEnemyKilled(Game1.player, "ScenarioBoss", true);
        int afterKill = this.Combat.ModifyMonsterDamage(NewMonster(1000), 100, false, Game1.player);
        int expectedAfter = DamageExpected(100, At(level, .08, .10, .12));
        return bossDamage == expectedBoss && afterKill == expectedAfter
            ? LevelScenarioCheck.Ok($"boss damage {bossDamage}; post-boss buff damage {afterKill}")
            : LevelScenarioCheck.Fail($"boss/post {bossDamage}/{afterKill}, expected {expectedBoss}/{expectedAfter}");
    }

    private LevelScenarioCheck CheckDamageExpected(int raw, double bonus)
    {
        int actual = this.Combat.ModifyMonsterDamage(NewMonster(5000), raw, false, Game1.player);
        int expected = DamageExpected(raw, bonus);
        return actual == expected
            ? LevelScenarioCheck.Ok($"damage {raw}->{actual}, expected {expected}")
            : LevelScenarioCheck.Fail($"damage {actual}, expected {expected}");
    }

    private void PrepareGachaPool(bool maxed)
    {
        foreach (CardDefinition card in this.ActiveCards)
        {
            this.Save.Data.OwnedCards.Add(card.Id);
            this.Save.Data.CardLevels[card.Id] = maxed ? Math.Max(1, card.MaxLevel) : 1;
        }
        this.Save.Data.DuplicatePullStreak = 0;
        this.Save.Data.StandardSinceRare = 0;
        this.Save.Data.StandardSinceEpic = 0;
        this.Save.Data.StandardSinceLegendary = 0;
        this.Save.Data.PremiumSinceEpic = 0;
        this.Save.Data.PremiumSinceLegendary = 0;
    }

    private int PerformHit(Monster monster, int rawDamage)
    {
        int healthBefore = monster.Health;
        int actual = this.Combat.ModifyMonsterDamage(monster, rawDamage, false, Game1.player);
        monster.Health = Math.Max(1, monster.Health - actual);
        this.Combat.AfterMonsterTakesDamage(monster, Game1.player, healthBefore);
        return actual;
    }

    private static void ApplyHit(Monster monster, int damage)
        => monster.Health = Math.Max(1, monster.Health - Math.Max(0, damage));

    private void WithTemporaryLivingMonster(Action<Monster> action)
    {
        GameLocation location = Game1.currentLocation;
        Monster monster = NewMonster(1000);
        location.characters.Add(monster);
        try
        {
            action(monster);
        }
        finally
        {
            location.characters.Remove(monster);
        }
    }

    private Monster NewMonster(int maxHealth = 1000, double healthFraction = 1d)
    {
        GreenSlime slime = new(Vector2.Zero, 0)
        {
            MaxHealth = Math.Max(1, maxHealth),
            Health = Math.Max(1, Math.Min(maxHealth, (int)Math.Round(maxHealth * Math.Clamp(healthFraction, .01, 1d)))),
            Speed = 0
        };
        return slime;
    }

    private void SetCoreField(string fieldName, object value)
    {
        FieldInfo? field = typeof(CoreCardEffectsService).GetField(fieldName, BindingFlags.Instance | BindingFlags.NonPublic);
        if (field is null)
            throw new MissingFieldException(typeof(CoreCardEffectsService).Name, fieldName);
        field.SetValue(this.Combat.DebugCompletion, value);
    }

    private static int ReadWrappedIntField(object target, string fieldName)
    {
        FieldInfo? field = target.GetType().GetField(fieldName, BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
            ?? typeof(Monster).GetField(fieldName, BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        if (field is null)
            return -1;
        object? value = field.GetValue(target);
        if (value is int i)
            return i;
        PropertyInfo? prop = value?.GetType().GetProperty("Value");
        return prop?.GetValue(value) is int wrapped ? wrapped : -1;
    }

    private static int DamageExpected(int raw, double bonus)
        => Math.Max(1, (int)Math.Ceiling(raw * (1d + Math.Max(0d, bonus))));

    private static int ReducedExpected(int raw, double reduction)
        => Math.Max(0, (int)Math.Ceiling(raw * (1d - Math.Clamp(reduction, 0d, .99d))));

    private static double At(int level, params double[] values)
        => values[Math.Clamp(level, 1, values.Length) - 1];

    private static int AtInt(int level, params int[] values)
        => values[Math.Clamp(level, 1, values.Length) - 1];

    private static bool Near(double actual, double expected, double tolerance = .0005)
        => Math.Abs(actual - expected) <= tolerance;

    private readonly record struct LevelScenarioCheck(bool Pass, string Detail)
    {
        public static LevelScenarioCheck Ok(string detail) => new(true, detail);
        public static LevelScenarioCheck Fail(string detail) => new(false, detail);
    }

    private readonly struct PlayerSnapshot
    {
        private readonly int MaxHealth;
        private readonly int Health;
        private readonly int Money;
        private readonly Vector2 Position;
        private readonly float Stamina;
        private readonly bool TemporarilyInvincible;
        private readonly bool FlashDuringInvincibility;
        private readonly int TemporaryInvincibilityTimer;
        private readonly int TemporaryInvincibilityDuration;

        public PlayerSnapshot(Farmer player)
        {
            this.MaxHealth = player.maxHealth;
            this.Health = player.health;
            this.Money = player.Money;
            this.Position = player.Position;
            this.Stamina = player.Stamina;
            this.TemporarilyInvincible = player.temporarilyInvincible;
            this.FlashDuringInvincibility = player.flashDuringThisTemporaryInvincibility;
            this.TemporaryInvincibilityTimer = player.temporaryInvincibilityTimer;
            this.TemporaryInvincibilityDuration = player.currentTemporaryInvincibilityDuration;
        }

        public void Restore(Farmer player)
        {
            player.maxHealth = Math.Max(1, this.MaxHealth);
            player.health = Math.Clamp(this.Health, 1, player.maxHealth);
            player.Money = this.Money;
            player.Position = this.Position;
            player.Stamina = this.Stamina;
            player.temporarilyInvincible = this.TemporarilyInvincible;
            player.flashDuringThisTemporaryInvincibility = this.FlashDuringInvincibility;
            player.temporaryInvincibilityTimer = this.TemporaryInvincibilityTimer;
            player.currentTemporaryInvincibilityDuration = this.TemporaryInvincibilityDuration;
        }
    }
}

from pathlib import Path

ROOT = Path('src/Cardcha')


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    (ROOT / rel).write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'{label}: anchor not found')
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# SaveService: suppress disk writes + restore exact SaveData after each scenario.
# -----------------------------------------------------------------------------
s = read('Services/SaveService.cs')
s = replace_once(
    s,
    '    private readonly IModHelper Helper;\n',
    '    private readonly IModHelper Helper;\n    private int TransientTestDepth;\n',
    'SaveService transient depth'
)

scope_code = r'''    internal IDisposable BeginTransientTestScope()
    {
        SaveData snapshot = CloneData(this.Data);
        this.TransientTestDepth++;
        return new TransientScope(() =>
        {
            this.Data = snapshot;
            this.TransientTestDepth = Math.Max(0, this.TransientTestDepth - 1);
        });
    }

    private static SaveData CloneData(SaveData d)
        => new()
        {
            SchemaVersion = d.SchemaVersion,
            OwnedCards = new HashSet<string>(d.OwnedCards ?? new HashSet<string>(), StringComparer.OrdinalIgnoreCase),
            EquippedCards = new List<string>(d.EquippedCards ?? new List<string>()),
            CardLevels = new Dictionary<string, int>(d.CardLevels ?? new Dictionary<string, int>(), StringComparer.OrdinalIgnoreCase),
            CardCopies = new Dictionary<string, int>(d.CardCopies ?? new Dictionary<string, int>(), StringComparer.OrdinalIgnoreCase),
            FavoriteCardIds = new HashSet<string>(d.FavoriteCardIds ?? new HashSet<string>(), StringComparer.OrdinalIgnoreCase),
            ActiveCardSlotCount = d.ActiveCardSlotCount,
            SuspiciousDust = d.SuspiciousDust,
            PullIndex = d.PullIndex,
            GachaSeed = d.GachaSeed,
            StandardSinceRare = d.StandardSinceRare,
            StandardSinceEpic = d.StandardSinceEpic,
            StandardSinceLegendary = d.StandardSinceLegendary,
            PremiumSinceEpic = d.PremiumSinceEpic,
            PremiumSinceLegendary = d.PremiumSinceLegendary,
            DuplicatePullStreak = d.DuplicatePullStreak,
            StandardPullIndex = d.StandardPullIndex,
            BattleScholarMonsterTypesToday = new HashSet<string>(d.BattleScholarMonsterTypesToday ?? new HashSet<string>(), StringComparer.OrdinalIgnoreCase),
            PhoenixHeartUsedToday = d.PhoenixHeartUsedToday,
            LifelineUsedToday = d.LifelineUsedToday,
            GuardianAngelUsedToday = d.GuardianAngelUsedToday,
            CardboardScraps = d.CardboardScraps,
            ShinyScraps = d.ShinyScraps,
            FirstScrapTriggered = d.FirstScrapTriggered,
            FirstScrapDay = d.FirstScrapDay,
            MachineLetterQueued = d.MachineLetterQueued,
            MachineDelivered = d.MachineDelivered,
            BinderUnlocked = d.BinderUnlocked,
            MimiIntroSeen = d.MimiIntroSeen,
            MimiMeetupPending = d.MimiMeetupPending,
            MimiMeetupCompleted = d.MimiMeetupCompleted,
            ChaChaLoaned = d.ChaChaLoaned,
            FirstPullQuestActive = d.FirstPullQuestActive,
            FirstPullCompleted = d.FirstPullCompleted,
            Chapter1Completed = d.Chapter1Completed,
            CardchaStoryChapter = d.CardchaStoryChapter,
            CardchaStoryStage = d.CardchaStoryStage,
            MimiMerchantUnlockedDay = d.MimiMerchantUnlockedDay,
            MimiFirstMerchantPepTalkShown = d.MimiFirstMerchantPepTalkShown,
            FirstScrapPickupNoticeShown = d.FirstScrapPickupNoticeShown,
            MimiMeetupOfferedDay = d.MimiMeetupOfferedDay,
            PortableMachinePurchased = d.PortableMachinePurchased,
            PortableMachineGifted = d.PortableMachineGifted,
            AirshipFlybySeen = d.AirshipFlybySeen,
            AirshipUnlocked = d.AirshipUnlocked,
            AirshipUnlockedDay = d.AirshipUnlockedDay,
            AirshipHighestRegionUnlocked = d.AirshipHighestRegionUnlocked,
            AirshipFlightsTaken = d.AirshipFlightsTaken,
            AirshipTotalFarePaid = d.AirshipTotalFarePaid,
            AirshipEngineLevel = d.AirshipEngineLevel,
            AirshipNavigationLevel = d.AirshipNavigationLevel,
            AirshipHullLevel = d.AirshipHullLevel,
            AirshipReactorLevel = d.AirshipReactorLevel,
            LastStateFingerprint = d.LastStateFingerprint ?? ""
        };

    private sealed class TransientScope : IDisposable
    {
        private Action? OnDispose;
        public TransientScope(Action onDispose) => this.OnDispose = onDispose;
        public void Dispose()
        {
            Action? action = this.OnDispose;
            this.OnDispose = null;
            action?.Invoke();
        }
    }

'''
s = replace_once(s, '    public void Save()\n    {\n', scope_code + '    public void Save()\n    {\n        if (this.TransientTestDepth > 0)\n            return;\n\n', 'SaveService transient scope')
write('Services/SaveService.cs', s)

# -----------------------------------------------------------------------------
# CoreCardEffectsService: deterministic chance seam + passive snapshot.
# -----------------------------------------------------------------------------
s = read('Services/CoreCardEffectsService.cs')
s = replace_once(
    s,
    'namespace Cardcha.Services;\n\ninternal sealed class CoreCardEffectsService\n',
    '''namespace Cardcha.Services;\n\ninternal readonly record struct CardPassiveDebugSnapshot(\n    int Defense,\n    double WeaponSpeed,\n    double MovePercent,\n    double Knockback,\n    double CriticalPower,\n    int MagneticRadius,\n    double AttackMultiplier,\n    int VanguardShield,\n    int GuardianShield\n);\n\ninternal sealed class CoreCardEffectsService\n''',
    'Core passive snapshot type'
)
s = replace_once(
    s,
    '    private long TimeBreakerReadyAt;\n',
    '    private long TimeBreakerReadyAt;\n    private CardPassiveDebugSnapshot DebugLastPassive;\n    private double? DebugForcedNextChanceRoll;\n',
    'Core debug fields'
)
s = replace_once(
    s,
    '    public int CurrentNoHitKillStreak => Math.Max(0, this.NoHitKillStreak);\n',
    '''    public int CurrentNoHitKillStreak => Math.Max(0, this.NoHitKillStreak);\n    internal CardPassiveDebugSnapshot DebugPassiveSnapshot => this.DebugLastPassive;\n\n    internal void DebugForceNextChanceRoll(double value)\n        => this.DebugForcedNextChanceRoll = Math.Clamp(value, 0d, 0.999999999d);\n\n    internal void DebugClearForcedChanceRoll()\n        => this.DebugForcedNextChanceRoll = null;\n\n    private double NextChanceRoll()\n    {\n        if (this.DebugForcedNextChanceRoll is double forced)\n        {\n            this.DebugForcedNextChanceRoll = null;\n            return forced;\n        }\n        return Game1.random.NextDouble();\n    }\n''',
    'Core chance methods'
)
s = s.replace('Game1.random.NextDouble() < proc', 'this.NextChanceRoll() < proc')

passive_anchor = '''        double attackMultiplier = this.Loadout.IsEquipped("battle_scholar") && this.Save.Data.BattleScholarMonsterTypesToday.Count >= 3\n            ? this.LevelValue("battle_scholar", .03, .04, .05)\n            : 0;\n\n        BuffEffects effects = new();\n'''
passive_new = '''        double attackMultiplier = this.Loadout.IsEquipped("battle_scholar") && this.Save.Data.BattleScholarMonsterTypesToday.Count >= 3\n            ? this.LevelValue("battle_scholar", .03, .04, .05)\n            : 0;\n\n        this.DebugLastPassive = new CardPassiveDebugSnapshot(\n            defense, weaponSpeed, movePercent, knockback, critPower, magnet, attackMultiplier,\n            this.VanguardShield, this.GuardianShield\n        );\n\n        BuffEffects effects = new();\n'''
s = replace_once(s, passive_anchor, passive_new, 'Core passive snapshot assignment')
s = replace_once(
    s,
    '        this.TimeBreakerReadyAt = 0;\n        this.StationarySince = Environment.TickCount64;\n',
    '        this.TimeBreakerReadyAt = 0;\n        this.DebugLastPassive = default;\n        this.DebugForcedNextChanceRoll = null;\n        this.StationarySince = Environment.TickCount64;\n',
    'Core reset debug'
)
write('Services/CoreCardEffectsService.cs', s)

# -----------------------------------------------------------------------------
# CombatService: expose exact test-only passive values without parsing Buff internals.
# -----------------------------------------------------------------------------
s = read('Services/CombatService.cs')
s = replace_once(
    s,
    '    private int LastDamageAfter;\n',
    '    private int LastDamageAfter;\n    internal int DebugThickHideDefense { get; private set; }\n    internal double DebugSwiftFeetSpeed { get; private set; }\n',
    'Combat debug fields'
)
s = replace_once(
    s,
    '    public int CurrentNoHitKillStreak => this.Completion.CurrentNoHitKillStreak;\n',
    '''    public int CurrentNoHitKillStreak => this.Completion.CurrentNoHitKillStreak;\n    internal int DebugVitalityAppliedBonus => this.VitalityAppliedBonus;\n    internal CoreCardEffectsService DebugCompletion => this.Completion;\n\n    internal CardPassiveDebugSnapshot DebugSyncCompletion(bool hasLivingMonster)\n    {\n        if (Context.IsWorldReady && Game1.player is not null)\n            this.Completion.Sync(Game1.player, hasLivingMonster);\n        return this.Completion.DebugPassiveSnapshot;\n    }\n''',
    'Combat debug accessors'
)
s = replace_once(
    s,
    '            this.SwiftFeetExpiresAt = 0;\n            this.BloodFangReadyAt = 0;\n',
    '            this.SwiftFeetExpiresAt = 0;\n            this.DebugThickHideDefense = 0;\n            this.DebugSwiftFeetSpeed = 0;\n            this.BloodFangReadyAt = 0;\n',
    'Combat hardgate debug reset'
)
s = replace_once(
    s,
    '''        CardLevelStats thickHide = this.GetStats("thick_hide");\n        if (this.Loadout.IsEquipped("thick_hide"))\n            ApplyHiddenBuff(player, ThickHideBuffId, defense: Math.Max(0, (int)Math.Round(thickHide.Primary)), speed: 0);\n        else\n            TryRemoveBuff(player, ThickHideBuffId);\n''',
    '''        CardLevelStats thickHide = this.GetStats("thick_hide");\n        this.DebugThickHideDefense = this.Loadout.IsEquipped("thick_hide")\n            ? Math.Max(0, (int)Math.Round(thickHide.Primary))\n            : 0;\n        if (this.DebugThickHideDefense > 0)\n            ApplyHiddenBuff(player, ThickHideBuffId, defense: this.DebugThickHideDefense, speed: 0);\n        else\n            TryRemoveBuff(player, ThickHideBuffId);\n''',
    'Combat thick hide debug'
)
s = replace_once(
    s,
    '''        if (swiftActive)\n            ApplyHiddenBuff(player, SwiftFeetBuffId, defense: 0, speed: Math.Max(0, swift.Primary));\n        else\n            TryRemoveBuff(player, SwiftFeetBuffId);\n''',
    '''        this.DebugSwiftFeetSpeed = swiftActive ? Math.Max(0, swift.Primary) : 0d;\n        if (swiftActive)\n            ApplyHiddenBuff(player, SwiftFeetBuffId, defense: 0, speed: this.DebugSwiftFeetSpeed);\n        else\n            TryRemoveBuff(player, SwiftFeetBuffId);\n''',
    'Combat swift debug'
)
s = replace_once(
    s,
    '        this.SwiftFeetExpiresAt = 0;\n        this.HudToastText = "";\n',
    '        this.SwiftFeetExpiresAt = 0;\n        this.DebugThickHideDefense = 0;\n        this.DebugSwiftFeetSpeed = 0;\n        this.HudToastText = "";\n',
    'Combat reset runtime debug'
)
write('Services/CombatService.cs', s)

# -----------------------------------------------------------------------------
# DropService: deterministic forced-roll queue + reversible transient diagnostics.
# -----------------------------------------------------------------------------
s = read('Services/DropService.cs')
s = replace_once(
    s,
    '    private int LuckyBreakFailStreak;\n',
    '    private int LuckyBreakFailStreak;\n    private Queue<double>? DebugForcedRolls;\n',
    'Drop forced rolls field'
)
s = s.replace('rng.NextDouble()', 'this.NextRoll(rng)')

drop_scope = r'''    internal void DebugSetForcedRolls(params double[] rolls)
        => this.DebugForcedRolls = new Queue<double>((rolls ?? Array.Empty<double>()).Select(value => Math.Clamp(value, 0d, 0.999999999d)));

    private double NextRoll(Random rng)
        => this.DebugForcedRolls is { Count: > 0 }
            ? this.DebugForcedRolls.Dequeue()
            : rng.NextDouble();

    internal IDisposable BeginScenarioTestScope()
    {
        int kills = this.KillsSinceNormalScrap;
        int lucky = this.LuckyBreakFailStreak;
        long eligible = this.EligibleDeaths;
        long normalEvents = this.NormalDropEvents;
        long shinyEvents = this.ShinyDropEvents;
        double normalChance = this.LastNormalChance;
        double shinyChance = this.LastShinyChance;
        bool forced = this.LastNormalForced;
        string scale = this.LastLootScale;
        int normalAmount = this.LastNormalAmount;
        int shinyAmount = this.LastShinyAmount;
        string enemy = this.LastEnemyName;
        int rawHp = this.LastRawMaxHealth;
        Queue<double>? queue = this.DebugForcedRolls is null ? null : new Queue<double>(this.DebugForcedRolls);

        this.KillsSinceNormalScrap = 0;
        this.LuckyBreakFailStreak = 0;
        this.EligibleDeaths = 0;
        this.NormalDropEvents = 0;
        this.ShinyDropEvents = 0;
        this.LastNormalChance = 0;
        this.LastShinyChance = 0;
        this.LastNormalForced = false;
        this.LastLootScale = "none";
        this.LastNormalAmount = 0;
        this.LastShinyAmount = 0;
        this.LastEnemyName = "none";
        this.LastRawMaxHealth = 0;
        this.DebugForcedRolls = null;

        return new ScenarioScope(() =>
        {
            this.KillsSinceNormalScrap = kills;
            this.LuckyBreakFailStreak = lucky;
            this.EligibleDeaths = eligible;
            this.NormalDropEvents = normalEvents;
            this.ShinyDropEvents = shinyEvents;
            this.LastNormalChance = normalChance;
            this.LastShinyChance = shinyChance;
            this.LastNormalForced = forced;
            this.LastLootScale = scale;
            this.LastNormalAmount = normalAmount;
            this.LastShinyAmount = shinyAmount;
            this.LastEnemyName = enemy;
            this.LastRawMaxHealth = rawHp;
            this.DebugForcedRolls = queue;
        });
    }

    private sealed class ScenarioScope : IDisposable
    {
        private Action? OnDispose;
        public ScenarioScope(Action onDispose) => this.OnDispose = onDispose;
        public void Dispose()
        {
            Action? action = this.OnDispose;
            this.OnDispose = null;
            action?.Invoke();
        }
    }

'''
s = replace_once(s, '    public static EnemyLootScale ClassifyEnemy(\n', drop_scope + '    public static EnemyLootScale ClassifyEnemy(\n', 'Drop test scope')
write('Services/DropService.cs', s)

# -----------------------------------------------------------------------------
# GachaService: deterministic forced-roll queue. SaveData itself is restored by SaveService.
# -----------------------------------------------------------------------------
s = read('Services/GachaService.cs')
s = replace_once(
    s,
    '    private readonly ModConfig Config;\n',
    '    private readonly ModConfig Config;\n    private Queue<double>? DebugForcedRolls;\n',
    'Gacha forced rolls field'
)
s = s.replace('rng.NextDouble()', 'this.NextRoll(rng)')
gacha_scope = r'''    internal void DebugSetForcedRolls(params double[] rolls)
        => this.DebugForcedRolls = new Queue<double>((rolls ?? Array.Empty<double>()).Select(value => Math.Clamp(value, 0d, 0.999999999d)));

    private double NextRoll(DeterministicRng rng)
        => this.DebugForcedRolls is { Count: > 0 }
            ? this.DebugForcedRolls.Dequeue()
            : rng.NextDouble();

    internal IDisposable BeginScenarioTestScope()
    {
        Queue<double>? queue = this.DebugForcedRolls is null ? null : new Queue<double>(this.DebugForcedRolls);
        this.DebugForcedRolls = null;
        return new ScenarioScope(() => this.DebugForcedRolls = queue);
    }

    private sealed class ScenarioScope : IDisposable
    {
        private Action? OnDispose;
        public ScenarioScope(Action onDispose) => this.OnDispose = onDispose;
        public void Dispose()
        {
            Action? action = this.OnDispose;
            this.OnDispose = null;
            action?.Invoke();
        }
    }

'''
s = replace_once(s, '    private IEnumerable<CardDefinition> GetEligibleUnowned(PullType type, SaveData data)\n', gacha_scope + '    private IEnumerable<CardDefinition> GetEligibleUnowned(PullType type, SaveData data)\n', 'Gacha test scope')
write('Services/GachaService.cs', s)

# -----------------------------------------------------------------------------
# ModEntry: construct runner, expose command, pass it to menu.
# -----------------------------------------------------------------------------
s = read('ModEntry.cs')
s = replace_once(
    s,
    '    private CardTestLabOverlayService CardLabOverlay = null!;\n',
    '    private CardTestLabOverlayService CardLabOverlay = null!;\n    private CardAutoScenarioRunnerService CardAutoRunner = null!;\n',
    'ModEntry runner field'
)
s = replace_once(
    s,
    '        this.CardLabOverlay = new CardTestLabOverlayService(helper, this.CardLab, this.CardArena, this.OpenCardTestLab, this.EndCardTestLabSession);\n',
    '''        this.CardLabOverlay = new CardTestLabOverlayService(helper, this.CardLab, this.CardArena, this.OpenCardTestLab, this.EndCardTestLabSession);\n        this.CardAutoRunner = new CardAutoScenarioRunnerService(\n            this.Monitor, this.Config, this.Cards, this.Save, this.Upgrades, this.Combat, this.Drops, this.Gacha\n        );\n''',
    'ModEntry runner init'
)
s = replace_once(
    s,
    '        helper.ConsoleCommands.Add("cardcha_card_test_stop", "TEST ONLY: stop Card Test Lab, exit arena, and restore the real loadout.", this.CommandCardTestStop);\n',
    '''        helper.ConsoleCommands.Add("cardcha_card_test_stop", "TEST ONLY: stop Card Test Lab, exit arena, and restore the real loadout.", this.CommandCardTestStop);\n        helper.ConsoleCommands.Add("cardcha_card_auto_run", "TEST ONLY: run deterministic runtime scenarios for all 76 active cards.", this.CommandCardAutoRun);\n''',
    'ModEntry runner command registration'
)
s = replace_once(
    s,
    '        Game1.activeClickableMenu = new CardTestLabMenu(this.CardLab, this.Renderer, this.CardArena);\n',
    '        Game1.activeClickableMenu = new CardTestLabMenu(this.CardLab, this.Renderer, this.CardArena, this.CardAutoRunner);\n',
    'ModEntry menu ctor'
)
command_method = r'''    private void CommandCardAutoRun(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save before running Card Auto Scenario Runner.", LogLevel.Warn);
            return;
        }

        CardScenarioCounts counts = this.CardAutoRunner.RunAll();
        this.Monitor.Log(
            $"===== CARD AUTO SCENARIO RUNNER =====\nPASS {counts.Pass} | FAIL {counts.Fail} | BLOCKED {counts.Blocked} | ERROR {counts.Error} | NOT RUN {counts.NotRun}",
            counts.Fail > 0 || counts.Error > 0 ? LogLevel.Warn : LogLevel.Alert
        );
    }

'''
s = replace_once(s, '    private void CommandVersion(string command, string[] args)\n', command_method + '    private void CommandVersion(string command, string[] args)\n', 'ModEntry auto run method')
write('ModEntry.cs', s)

# -----------------------------------------------------------------------------
# Card Test Lab menu: one-click all-card runtime run + visible result markers.
# -----------------------------------------------------------------------------
s = read('UI/CardTestLabMenu.cs')
s = replace_once(
    s,
    '    private readonly CardTestArenaService Arena;\n',
    '    private readonly CardTestArenaService Arena;\n    private readonly CardAutoScenarioRunnerService AutoRunner;\n',
    'Menu runner field'
)
s = replace_once(s, '    private Rectangle CloseRect;\n', '    private Rectangle CloseRect;\n    private Rectangle AutoRunRect;\n', 'Menu auto rect field')
s = replace_once(
    s,
    '    public CardTestLabMenu(CardTestLabService lab, CardRenderer renderer, CardTestArenaService arena)\n',
    '    public CardTestLabMenu(CardTestLabService lab, CardRenderer renderer, CardTestArenaService arena, CardAutoScenarioRunnerService autoRunner)\n',
    'Menu ctor signature'
)
s = replace_once(
    s,
    '        this.Arena = arena;\n        this.Cards = lab.ActiveCards;\n',
    '        this.Arena = arena;\n        this.AutoRunner = autoRunner;\n        this.Cards = lab.ActiveCards;\n',
    'Menu ctor assign'
)
s = replace_once(
    s,
    '            case Keys.F7:\n                this.Arena.ResetDummy(1.0);\n',
    '            case Keys.F5:\n                this.RunAutoScenarios();\n                return;\n            case Keys.F7:\n                this.Arena.ResetDummy(1.0);\n',
    'Menu F5'
)
s = replace_once(
    s,
    '            case Buttons.RightStick:\n                this.Arena.ResetDummy(0.19);\n                return;\n',
    '            case Buttons.RightStick:\n                this.Arena.ResetDummy(0.19);\n                return;\n            case Buttons.LeftStick:\n                this.RunAutoScenarios();\n                return;\n',
    'Menu L3'
)
s = replace_once(
    s,
    '        if (this.TrySelectCardRowAt(x, y))\n            return;\n\n        if (this.PrevRect.Contains(x, y))',
    '        if (this.TrySelectCardRowAt(x, y))\n            return;\n\n        if (this.AutoRunRect.Contains(x, y)) this.RunAutoScenarios();\n        else if (this.PrevRect.Contains(x, y))',
    'Menu mouse auto'
)

old_progress = '''        string guide = "↑↓ CHỌN LÁ   •   ←→ LEVEL   •   A EQUIP   •   X BASELINE   •   RT ARENA   •   B THU NHỎ   •   F8 / R-STICK MỞ LẠI";\n        Vector2 guideSize = Game1.smallFont.MeasureString(guide);\n        float guideScale = Math.Min(0.86f, (outer.Width - 80f) / Math.Max(1f, guideSize.X));\n        b.DrawString(Game1.smallFont, guide, new Vector2(outer.Center.X - guideSize.X * guideScale / 2f, outer.Y + 116), new Color(255, 218, 116), 0f, Vector2.Zero, guideScale, SpriteEffects.None, 1f);\n\n        int contentTop = outer.Y + 158;\n'''
new_progress = '''        CardScenarioCounts scenarioCounts = this.AutoRunner.Counts();\n        string scenarioProgress = $"AUTO SCENARIO: {scenarioCounts.Pass} PASS   {scenarioCounts.Fail} FAIL   {scenarioCounts.Blocked} BLOCKED   {scenarioCounts.Error} ERROR   {scenarioCounts.NotRun} NOT RUN";\n        Vector2 scenarioSize = Game1.smallFont.MeasureString(scenarioProgress);\n        float scenarioScale = Math.Min(0.88f, (outer.Width - 420f) / Math.Max(1f, scenarioSize.X));\n        b.DrawString(Game1.smallFont, scenarioProgress, new Vector2(outer.Center.X - scenarioSize.X * scenarioScale / 2f, outer.Y + 114), new Color(137, 236, 169), 0f, Vector2.Zero, scenarioScale, SpriteEffects.None, 1f);\n\n        string guide = "↑↓ CHỌN LÁ   •   ←→ LEVEL   •   L3/F5 AUTO RUN ALL   •   A EQUIP   •   RT ARENA   •   B THU NHỎ";\n        Vector2 guideSize = Game1.smallFont.MeasureString(guide);\n        float guideScale = Math.Min(0.86f, (outer.Width - 80f) / Math.Max(1f, guideSize.X));\n        b.DrawString(Game1.smallFont, guide, new Vector2(outer.Center.X - guideSize.X * guideScale / 2f, outer.Y + 142), new Color(255, 218, 116), 0f, Vector2.Zero, guideScale, SpriteEffects.None, 1f);\n\n        int contentTop = outer.Y + 184;\n'''
s = replace_once(s, old_progress, new_progress, 'Menu scenario progress')

old_marker = '''            CardLabVerdict verdict = this.Lab.GetVerdict(card);\n            string marker = verdict switch\n            {\n                CardLabVerdict.Pass => "PASS",\n                CardLabVerdict.Fail => "FAIL",\n                _ => " • "\n            };\n            Color markerColor = verdict switch\n            {\n                CardLabVerdict.Pass => new Color(122, 221, 153),\n                CardLabVerdict.Fail => new Color(240, 118, 130),\n                _ => new Color(172, 164, 191)\n            };\n'''
new_marker = '''            CardAutoScenarioResult scenario = this.AutoRunner.Get(card);\n            string marker = scenario.Status switch\n            {\n                CardAutoScenarioStatus.Pass => "AUTO",\n                CardAutoScenarioStatus.Fail => "FAIL",\n                CardAutoScenarioStatus.Blocked => "BLK",\n                CardAutoScenarioStatus.Error => "ERR",\n                _ => " • "\n            };\n            Color markerColor = scenario.Status switch\n            {\n                CardAutoScenarioStatus.Pass => new Color(122, 221, 153),\n                CardAutoScenarioStatus.Fail => new Color(240, 118, 130),\n                CardAutoScenarioStatus.Blocked => new Color(255, 199, 96),\n                CardAutoScenarioStatus.Error => new Color(245, 116, 190),\n                _ => new Color(172, 164, 191)\n            };\n'''
s = replace_once(s, old_marker, new_marker, 'Menu list scenario marker')

s = replace_once(
    s,
    '        CardAutoAuditEntry autoAudit = GeneratedCardAutoAudit.Get(card);\n',
    '        CardAutoAuditEntry autoAudit = GeneratedCardAutoAudit.Get(card);\n        CardAutoScenarioResult scenario = this.AutoRunner.Get(card);\n',
    'Menu detail scenario result'
)

scenario_detail_anchor = '''        b.DrawString(Game1.smallFont, runState, new Vector2(nameX, panel.Y + 166), runColor, 0f, Vector2.Zero, 0.90f, SpriteEffects.None, 1f);\n\n        string verdictText = verdict == CardLabVerdict.Untested ? "MANUAL: UNTESTED" : $"MANUAL: {verdict.ToString().ToUpperInvariant()}";\n'''
scenario_detail_new = '''        b.DrawString(Game1.smallFont, runState, new Vector2(nameX, panel.Y + 166), runColor, 0f, Vector2.Zero, 0.90f, SpriteEffects.None, 1f);\n\n        Color scenarioColor = scenario.Status switch\n        {\n            CardAutoScenarioStatus.Pass => new Color(122, 221, 153),\n            CardAutoScenarioStatus.Fail => new Color(240, 118, 130),\n            CardAutoScenarioStatus.Blocked => new Color(255, 199, 96),\n            CardAutoScenarioStatus.Error => new Color(245, 116, 190),\n            _ => new Color(190, 183, 206)\n        };\n        b.DrawString(Game1.smallFont, $"AUTO SCENARIO: {scenario.Status.ToString().ToUpperInvariant()} • {scenario.PassedLevels}/{scenario.TotalLevels} levels", new Vector2(nameX, panel.Y + 190), scenarioColor, 0f, Vector2.Zero, 0.88f, SpriteEffects.None, 1f);\n\n        string verdictText = verdict == CardLabVerdict.Untested ? "MANUAL: UNTESTED" : $"MANUAL: {verdict.ToString().ToUpperInvariant()}";\n'''
s = replace_once(s, scenario_detail_anchor, scenario_detail_new, 'Menu scenario detail line')

s = replace_once(
    s,
    '        b.DrawString(Game1.smallFont, "SELECTED LEVEL EFFECT", new Vector2(panel.X + 20, panel.Y + 204), new Color(255, 218, 116), 0f, Vector2.Zero, 1.0f, SpriteEffects.None, 1f);\n',
    '        DrawClippedText(b, Game1.smallFont, scenario.Summary, new Rectangle(panel.X + 20, panel.Y + 218, panel.Width - 40, 30), scenarioColor, 0.88f);\n        b.DrawString(Game1.smallFont, "SELECTED LEVEL EFFECT", new Vector2(panel.X + 20, panel.Y + 250), new Color(255, 218, 116), 0f, Vector2.Zero, 1.0f, SpriteEffects.None, 1f);\n',
    'Menu scenario summary'
)
s = s.replace('Rectangle descriptionArea = new(panel.X + 20, panel.Y + 238, panel.Width - 40, 76);', 'Rectangle descriptionArea = new(panel.X + 20, panel.Y + 282, panel.Width - 40, 70);')
s = s.replace('new Vector2(panel.X + 20, panel.Y + 324)', 'new Vector2(panel.X + 20, panel.Y + 360)')
s = s.replace('Rectangle instructionArea = new(panel.X + 20, panel.Y + 358, panel.Width - 40, 78);', 'Rectangle instructionArea = new(panel.X + 20, panel.Y + 394, panel.Width - 40, 70);')
s = s.replace('new Vector2(panel.X + 20, panel.Y + 446)', 'new Vector2(panel.X + 20, panel.Y + 472)')
s = s.replace('Rectangle telemetryArea = new(panel.X + 20, panel.Y + 482, panel.Width - 40, Math.Max(70, panel.Bottom - (panel.Y + 494)));', 'Rectangle telemetryArea = new(panel.X + 20, panel.Y + 508, panel.Width - 40, Math.Max(70, panel.Bottom - (panel.Y + 520)));')

s = replace_once(
    s,
    '        DrawButton(b, this.CloseRect, "RETURN [B/Q]", new Color(68, 64, 79));\n',
    '        DrawButton(b, this.CloseRect, "RETURN [B/Q]", new Color(68, 64, 79));\n        DrawButton(b, this.AutoRunRect, "AUTO RUN ALL [L3/F5]", new Color(52, 142, 99));\n',
    'Menu auto button draw'
)
run_method = r'''    private void RunAutoScenarios()
    {
        Game1.playSound("wand");
        CardScenarioCounts counts = this.AutoRunner.RunAll();
        Game1.showGlobalMessage($"AUTO SCENARIO • PASS {counts.Pass} • FAIL {counts.Fail} • BLOCKED {counts.Blocked} • ERROR {counts.Error}");
    }

'''
s = replace_once(s, '    private void MoveSelection(int delta, bool force = false)\n', run_method + '    private void MoveSelection(int delta, bool force = false)\n', 'Menu run method')
s = replace_once(
    s,
    '        this.CloseRect = new Rectangle(this.xPositionOnScreen + this.width - 164, this.yPositionOnScreen + 18, 142, 42);\n',
    '        this.CloseRect = new Rectangle(this.xPositionOnScreen + this.width - 164, this.yPositionOnScreen + 18, 142, 42);\n        this.AutoRunRect = new Rectangle(this.CloseRect.X - 282, this.CloseRect.Y, 270, 42);\n',
    'Menu auto rect layout'
)

# Card row click panel must use the same shifted content top as draw().
s = s.replace('        int contentTop = outer.Y + 132;\n', '        int contentTop = outer.Y + 184;\n')
write('UI/CardTestLabMenu.cs', s)

# Tighten Crushing Impact's vanilla scenario: the base GreenSlime should expose a real stun timer.
runner = read('Services/CardAutoScenarioRunnerService.cs')
runner = runner.replace(
    '        bool stunSupported = actualStun < 0 || actualStun >= expectedStun;\n        return x == expectedX && stunSupported\n',
    '        bool stunSupported = actualStun >= expectedStun;\n        return x == expectedX && stunSupported\n'
)
write('Services/CardAutoScenarioRunnerService.cs', runner)

print('Applied alpha28.0.4.14.3.7 Auto Scenario Runner integration')

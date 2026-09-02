from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.3.8'


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
# Version
# -----------------------------------------------------------------------------
manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8'))
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

csproj = ROOT / 'Cardcha.csproj'
s = csproj.read_text(encoding='utf-8')
s = re.sub(r'<Version>[^<]+</Version>', f'<Version>{VERSION}</Version>', s, count=1)
csproj.write_text(s, encoding='utf-8')

(ROOT / 'Directory.Build.targets').write_text(f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .4.14.3.8 Boss Energy + Victory Charge runtime. -->\n  <Target Name="CardchaAlpha28041438Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n''', encoding='utf-8')


# -----------------------------------------------------------------------------
# Card data + translations
# -----------------------------------------------------------------------------
cards_path = ROOT / 'assets/cards.json'
cards = json.loads(cards_path.read_text(encoding='utf-8'))
vc = next(card for card in cards if card.get('Id') == 'victory_charge')
vc['Description'] = 'Boss Energy nhận từ hạ quái +10%; không tăng phần Energy nhận từ sát thương hoặc đòn chí mạng.'
vc['StarRules'] = [
    'Boss Energy nhận từ hạ quái +10%.',
    'Boss Energy nhận từ hạ quái +15%.',
    'Boss Energy nhận từ hạ quái +20%.',
    'Boss Energy nhận từ hạ quái +25%.',
    'Boss Energy nhận từ hạ quái +30%.',
]
cards_path.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for lang, values in {
    'default.json': {
        'card.victory_charge.desc': 'Boss Energy gained from kills +10%; does not increase Energy gained from damage or crit-like hits.',
        'card.victory_charge.star.1': 'Boss Energy gained from kills +10%.',
        'card.victory_charge.star.2': 'Boss Energy gained from kills +15%.',
        'card.victory_charge.star.3': 'Boss Energy gained from kills +20%.',
        'card.victory_charge.star.4': 'Boss Energy gained from kills +25%.',
        'card.victory_charge.star.5': 'Boss Energy gained from kills +30%.',
        'hud.boss-energy': 'Boss Energy',
        'binder.level-effect.victory-charge': 'Boss Energy from kills +{{bonus}}%. Damage/crit-like Energy is unchanged.',
    },
    'vi.json': {
        'card.victory_charge.desc': 'Boss Energy nhận từ hạ quái +10%; không tăng phần Energy nhận từ sát thương hoặc đòn chí mạng.',
        'card.victory_charge.star.1': 'Boss Energy nhận từ hạ quái +10%.',
        'card.victory_charge.star.2': 'Boss Energy nhận từ hạ quái +15%.',
        'card.victory_charge.star.3': 'Boss Energy nhận từ hạ quái +20%.',
        'card.victory_charge.star.4': 'Boss Energy nhận từ hạ quái +25%.',
        'card.victory_charge.star.5': 'Boss Energy nhận từ hạ quái +30%.',
        'hud.boss-energy': 'Năng Lượng Trùm',
        'binder.level-effect.victory-charge': 'Boss Energy từ hạ quái +{{bonus}}%. Energy từ sát thương/chí mạng không đổi.',
    },
}.items():
    path = ROOT / 'i18n' / lang
    obj = json.loads(path.read_text(encoding='utf-8'))
    obj.update(values)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


# -----------------------------------------------------------------------------
# CardUpgradeService: canonical per-level value and Binder level effect.
# -----------------------------------------------------------------------------
s = read('Services/CardUpgradeService.cs')
if '"victory_charge" => new CardLevelStats' not in s:
    s = replace_once(
        s,
        '''            "vitality" => new CardLevelStats\n            {\n                Primary = Pick(level, 10, 15, 20, 25, 30)\n            },\n\n''',
        '''            "vitality" => new CardLevelStats\n            {\n                Primary = Pick(level, 10, 15, 20, 25, 30)\n            },\n\n            "victory_charge" => new CardLevelStats\n            {\n                Primary = Pick(level, 0.10, 0.15, 0.20, 0.25, 0.30)\n            },\n\n''',
        'Victory Charge stats'
    )
if 'binder.level-effect.victory-charge' not in s:
    s = replace_once(
        s,
        '''            "thick_hide" => ModEntry.T(\n                "binder.level-effect.thick-hide",\n                new { defense = (int)Math.Round(s.Primary) }\n            ),\n\n''',
        '''            "thick_hide" => ModEntry.T(\n                "binder.level-effect.thick-hide",\n                new { defense = (int)Math.Round(s.Primary) }\n            ),\n\n            "victory_charge" => ModEntry.T(\n                "binder.level-effect.victory-charge",\n                new { bonus = Percent(s.Primary) }\n            ),\n\n''',
        'Victory Charge Binder effect'
    )
write('Services/CardUpgradeService.cs', s)


# -----------------------------------------------------------------------------
# CoreCardEffectsService: expose actual/crit-like outcome after the real hit.
# -----------------------------------------------------------------------------
s = read('Services/CoreCardEffectsService.cs')
if 'LastProcessedActualDamage' not in s:
    s = replace_once(
        s,
        '    internal CardPassiveDebugSnapshot DebugPassiveSnapshot => this.DebugLastPassive;\n',
        '    internal CardPassiveDebugSnapshot DebugPassiveSnapshot => this.DebugLastPassive;\n    internal int LastProcessedActualDamage { get; private set; }\n    internal bool LastProcessedCritLike { get; private set; }\n',
        'Boss Energy hit outcome properties'
    )
    s = replace_once(
        s,
        '''        if (actual <= 0)\n        {\n            this.PendingRawHitDamage = 0;\n            this.PendingCritLikeHit = false;\n            return;\n        }\n\n        long now = Environment.TickCount64;\n        bool critLike = this.PendingCritLikeHit;\n''',
        '''        if (actual <= 0)\n        {\n            this.LastProcessedActualDamage = 0;\n            this.LastProcessedCritLike = false;\n            this.PendingRawHitDamage = 0;\n            this.PendingCritLikeHit = false;\n            return;\n        }\n\n        long now = Environment.TickCount64;\n        bool critLike = this.PendingCritLikeHit;\n        this.LastProcessedActualDamage = actual;\n        this.LastProcessedCritLike = critLike;\n''',
        'Boss Energy hit outcome capture'
    )
write('Services/CoreCardEffectsService.cs', s)


# -----------------------------------------------------------------------------
# CombatService: route real hit/kill events into Boss Energy.
# -----------------------------------------------------------------------------
s = read('Services/CombatService.cs')
if 'private readonly BossEnergyService BossEnergy;' not in s:
    s = replace_once(
        s,
        '    private readonly CardUpgradeService Upgrades;\n    private readonly CoreCardEffectsService Completion;\n',
        '    private readonly CardUpgradeService Upgrades;\n    private readonly BossEnergyService BossEnergy;\n    private readonly CoreCardEffectsService Completion;\n',
        'Combat BossEnergy field'
    )
    s = replace_once(
        s,
        '    public CombatService(ModConfig config, LoadoutService loadout, SaveService save, CardRegistry cards, CardUpgradeService upgrades)\n',
        '    public CombatService(ModConfig config, LoadoutService loadout, SaveService save, CardRegistry cards, CardUpgradeService upgrades, BossEnergyService bossEnergy)\n',
        'Combat ctor signature'
    )
    s = replace_once(
        s,
        '        this.Upgrades = upgrades;\n        this.Completion = new CoreCardEffectsService(loadout, save, cards, upgrades);\n',
        '        this.Upgrades = upgrades;\n        this.BossEnergy = bossEnergy;\n        this.Completion = new CoreCardEffectsService(loadout, save, cards, upgrades);\n',
        'Combat ctor assignment'
    )

s = replace_once(
    s,
    '''    public void OnMonsterKilled(Monster monster, Farmer? who)\n    {\n        if (who?.IsLocalPlayer == true)\n            this.Completion.OnMonsterKilled(monster, who);\n        this.OnEnemyKilled(who);\n    }\n''',
    '''    public void OnMonsterKilled(Monster monster, Farmer? who)\n    {\n        if (who?.IsLocalPlayer == true)\n        {\n            this.Completion.OnMonsterKilled(monster, who);\n            string name = string.IsNullOrWhiteSpace(monster.Name) ? monster.GetType().Name : monster.Name;\n            string source = monster.GetType().FullName ?? monster.GetType().Name;\n            bool bossLike = DropService.ClassifyEnemy(name, source, monster.modData?.Pairs) == EnemyLootScale.BossLike;\n            this.BossEnergy.OnKill(bossLike, who);\n        }\n        this.OnEnemyKilled(who);\n    }\n''',
    'Boss Energy vanilla kill hook'
)

s = replace_once(
    s,
    '''    public void OnCustomEnemyKilled(Farmer? who, string sourceType, bool bossLike)\n    {\n        if (who?.IsLocalPlayer == true)\n            this.Completion.OnCustomMonsterKilled(sourceType, who, bossLike);\n        this.OnEnemyKilled(who);\n    }\n''',
    '''    public void OnCustomEnemyKilled(Farmer? who, string sourceType, bool bossLike)\n    {\n        if (who?.IsLocalPlayer == true)\n        {\n            this.Completion.OnCustomMonsterKilled(sourceType, who, bossLike);\n            this.BossEnergy.OnKill(bossLike, who);\n        }\n        this.OnEnemyKilled(who);\n    }\n''',
    'Boss Energy custom kill hook'
)

s = replace_once(
    s,
    '''    public void AfterMonsterTakesDamage(Monster monster, Farmer? who, int healthBefore)\n        => this.Completion.AfterMonsterTakesDamage(monster, who, healthBefore);\n''',
    '''    public void AfterMonsterTakesDamage(Monster monster, Farmer? who, int healthBefore)\n    {\n        this.Completion.AfterMonsterTakesDamage(monster, who, healthBefore);\n        if (who?.IsLocalPlayer == true)\n            this.BossEnergy.OnDamageDealt(this.Completion.LastProcessedActualDamage, this.Completion.LastProcessedCritLike);\n    }\n''',
    'Boss Energy damage hook'
)

if 'Boss Energy: {this.BossEnergy.Describe()}' not in s:
    s = replace_once(
        s,
        '            $"Passive buffs: {passive}";\n',
        '            $"Passive buffs: {passive}\\n" +\n            $"Boss Energy: {this.BossEnergy.Describe()}";\n',
        'Boss Energy telemetry'
    )
write('Services/CombatService.cs', s)


# -----------------------------------------------------------------------------
# Combat HUD: visible Boss Energy meter, low priority so critical card states win.
# -----------------------------------------------------------------------------
s = read('UI/CombatHudRenderer.cs')
if 'private readonly BossEnergyService BossEnergy;' not in s:
    s = replace_once(
        s,
        '    private readonly CombatService Combat;\n    private readonly LoadoutService Loadout;\n',
        '    private readonly CombatService Combat;\n    private readonly BossEnergyService BossEnergy;\n    private readonly LoadoutService Loadout;\n',
        'HUD BossEnergy field'
    )
    s = replace_once(
        s,
        '''        ModConfig config,\n        CombatService combat,\n        LoadoutService loadout,\n''',
        '''        ModConfig config,\n        CombatService combat,\n        BossEnergyService bossEnergy,\n        LoadoutService loadout,\n''',
        'HUD ctor signature'
    )
    s = replace_once(
        s,
        '        this.Config = config;\n        this.Combat = combat;\n        this.Loadout = loadout;\n',
        '        this.Config = config;\n        this.Combat = combat;\n        this.BossEnergy = bossEnergy;\n        this.Loadout = loadout;\n',
        'HUD ctor assignment'
    )

if 'Key: "boss_energy"' not in s:
    s = replace_once(
        s,
        '''        List<HudEntry> entries = new();\n\n        string toast = this.Combat.CurrentHudToast;\n''',
        '''        List<HudEntry> entries = new();\n\n        if (this.BossEnergy.CurrentEnergy > 0.001d || this.Loadout.IsEquipped("victory_charge"))\n        {\n            entries.Add(new HudEntry(\n                Key: "boss_energy",\n                CardId: "victory_charge",\n                Label: ModEntry.T("hud.boss-energy"),\n                Value: $"{this.BossEnergy.CurrentEnergy:0.#}/{BossEnergyService.MaxEnergy:0}",\n                RemainingSeconds: null,\n                TotalSeconds: null,\n                Timing: HudTiming.None,\n                StackText: "",\n                Kind: HudKind.Ready,\n                Priority: 5\n            ));\n        }\n\n        string toast = this.Combat.CurrentHudToast;\n''',
        'HUD Boss Energy entry'
    )
write('UI/CombatHudRenderer.cs', s)


# -----------------------------------------------------------------------------
# ModEntry wiring.
# -----------------------------------------------------------------------------
s = read('ModEntry.cs')
if 'private BossEnergyService BossEnergy = null!;' not in s:
    s = replace_once(
        s,
        '    private ResourceService Resources = null!;\n    private CombatService Combat = null!;\n',
        '    private ResourceService Resources = null!;\n    private BossEnergyService BossEnergy = null!;\n    private CombatService Combat = null!;\n',
        'ModEntry BossEnergy field'
    )
    s = replace_once(
        s,
        '''        this.Items = new ItemAssetService(helper);\n        this.Resources = new ResourceService(this.Save);\n        this.Combat = new CombatService(this.Config, this.Loadout, this.Save, this.Cards, this.Upgrades);\n''',
        '''        this.Items = new ItemAssetService(helper);\n        this.Resources = new ResourceService(this.Save);\n        this.BossEnergy = new BossEnergyService(this.Loadout, this.Cards, this.Upgrades);\n        this.Combat = new CombatService(this.Config, this.Loadout, this.Save, this.Cards, this.Upgrades, this.BossEnergy);\n''',
        'ModEntry BossEnergy construction'
    )
    s = replace_once(
        s,
        '''            this.Config,\n            this.Combat,\n            this.Loadout,\n''',
        '''            this.Config,\n            this.Combat,\n            this.BossEnergy,\n            this.Loadout,\n''',
        'Combat HUD BossEnergy injection'
    )
    s = replace_once(
        s,
        '''        this.CardAutoRunner = new CardAutoScenarioRunnerService(\n            this.Monitor, this.Config, this.Cards, this.Save, this.Upgrades, this.Combat, this.Drops, this.Gacha\n        );\n''',
        '''        this.CardAutoRunner = new CardAutoScenarioRunnerService(\n            this.Monitor, this.Config, this.Cards, this.Save, this.Upgrades, this.Combat, this.Drops, this.Gacha, this.BossEnergy\n        );\n''',
        'Auto Runner BossEnergy injection'
    )
    s = replace_once(
        s,
        '        helper.Events.GameLoop.DayStarted += this.OnDayStarted;\n',
        '        helper.Events.GameLoop.DayStarted += this.OnDayStarted;\n        helper.Events.GameLoop.DayStarted += this.BossEnergy.OnDayStarted;\n',
        'BossEnergy day reset event'
    )
    s = replace_once(
        s,
        '        helper.Events.GameLoop.ReturnedToTitle += this.OnReturnedToTitle;\n',
        '        helper.Events.GameLoop.ReturnedToTitle += this.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.BossEnergy.OnReturnedToTitle;\n',
        'BossEnergy title reset event'
    )

s = re.sub(
    r'Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14\.3\.\d+ CARD AUTO SCENARIO TEST',
    f'Cardcha! v{VERSION} BOSS ENERGY + VICTORY CHARGE TEST',
    s
)
write('ModEntry.cs', s)


# -----------------------------------------------------------------------------
# Card Test Lab instruction now describes a real, visible meter.
# -----------------------------------------------------------------------------
s = read('Services/CardTestLabService.cs')
s = s.replace(
    '            "victory_charge" => "BLOCKED: Boss Energy does not exist yet. Do not mark PASS based on a substitute effect.",',
    '            "victory_charge" => "EQUIP & PLAY and defeat a kill target. Boss Energy should gain more from the kill at higher star levels; damage/crit-like Energy must stay unchanged.",'
)
write('Services/CardTestLabService.cs', s)


# -----------------------------------------------------------------------------
# Auto Scenario Runner: test all five Victory Charge levels against the real meter.
# -----------------------------------------------------------------------------
s = read('Services/CardAutoScenarioRunnerService.cs')
if 'private readonly BossEnergyService BossEnergy;' not in s:
    s = replace_once(
        s,
        '    private readonly GachaService Gacha;\n',
        '    private readonly GachaService Gacha;\n    private readonly BossEnergyService BossEnergy;\n',
        'Runner BossEnergy field'
    )
    s = replace_once(
        s,
        '''        CardUpgradeService upgrades,\n        CombatService combat,\n        DropService drops,\n        GachaService gacha)\n''',
        '''        CardUpgradeService upgrades,\n        CombatService combat,\n        DropService drops,\n        GachaService gacha,\n        BossEnergyService bossEnergy)\n''',
        'Runner BossEnergy ctor signature'
    )
    s = replace_once(
        s,
        '        this.Drops = drops;\n        this.Gacha = gacha;\n',
        '        this.Drops = drops;\n        this.Gacha = gacha;\n        this.BossEnergy = bossEnergy;\n',
        'Runner BossEnergy assignment'
    )

blocked_pattern = re.compile(
    r'\n        if \(card\.Id\.Equals\("victory_charge", StringComparison\.OrdinalIgnoreCase\)\)\n        \{.*?\n        \}\n\n        int max =',
    re.S
)
if blocked_pattern.search(s):
    s = blocked_pattern.sub('\n        int max =', s, count=1)

if '"victory_charge" => this.CheckVictoryCharge(level),' not in s:
    s = replace_once(
        s,
        '                "essence_finder" => this.CheckEssenceFinder(level),\n',
        '                "essence_finder" => this.CheckEssenceFinder(level),\n                "victory_charge" => this.CheckVictoryCharge(level),\n',
        'Runner Victory Charge adapter'
    )

if 'this.BossEnergy.DebugSetEnergy(0d);' not in s:
    s = replace_once(
        s,
        '        this.Combat.DebugCompletion.DebugClearForcedChanceRoll();\n\n        SaveData data = this.Save.Data;\n',
        '        this.Combat.DebugCompletion.DebugClearForcedChanceRoll();\n        this.BossEnergy.DebugSetEnergy(0d);\n\n        SaveData data = this.Save.Data;\n',
        'Runner energy reset in Prepare'
    )

if 'private LevelScenarioCheck CheckVictoryCharge' not in s:
    s = replace_once(
        s,
        '    private LevelScenarioCheck CheckFlatDamage(int level, params double[] bonus)\n',
        '''    private LevelScenarioCheck CheckVictoryCharge(int level)\n    {\n        double bonus = At(level, .10, .15, .20, .25, .30);\n\n        this.BossEnergy.DebugSetEnergy(0d);\n        this.BossEnergy.OnDamageDealt(100, false);\n        this.BossEnergy.OnDamageDealt(170, true);\n        double nonKillActual = this.BossEnergy.CurrentEnergy;\n        double nonKillExpected = 1d + 1.7d + BossEnergyService.CritLikeEnergy;\n\n        this.BossEnergy.DebugSetEnergy(0d);\n        this.BossEnergy.OnKill(false, Game1.player);\n        double regularActual = this.BossEnergy.CurrentEnergy;\n        double regularExpected = BossEnergyService.RegularKillEnergy * (1d + bonus);\n\n        this.BossEnergy.DebugSetEnergy(0d);\n        this.BossEnergy.OnKill(true, Game1.player);\n        double bossActual = this.BossEnergy.CurrentEnergy;\n        double bossExpected = BossEnergyService.BossLikeKillEnergy * (1d + bonus);\n\n        bool pass = Near(nonKillActual, nonKillExpected)\n                    && Near(regularActual, regularExpected)\n                    && Near(bossActual, bossExpected);\n\n        return pass\n            ? LevelScenarioCheck.Ok($"damage/crit {nonKillActual:0.##} unchanged; kill {regularActual:0.##}/{bossActual:0.##}, expected {regularExpected:0.##}/{bossExpected:0.##}")\n            : LevelScenarioCheck.Fail($"energy damage/crit {nonKillActual:0.##} exp {nonKillExpected:0.##}; kill {regularActual:0.##}/{bossActual:0.##} exp {regularExpected:0.##}/{bossExpected:0.##}");\n    }\n\n    private LevelScenarioCheck CheckFlatDamage(int level, params double[] bonus)\n''',
        'Runner Victory Charge scenario'
    )

# Reset RAM-only Energy after every scenario level and after RunAll.
if 'this.BossEnergy.Reset();\n            playerSnapshot.Restore(player);' not in s:
    s = replace_once(
        s,
        '            this.Combat.ResetRuntime();\n            playerSnapshot.Restore(player);\n',
        '            this.Combat.ResetRuntime();\n            this.BossEnergy.Reset();\n            playerSnapshot.Restore(player);\n',
        'Runner per-level energy cleanup'
    )
if 'this.BossEnergy.Reset();\n            this.Config.EnableCombatCards = combatBefore;' not in s:
    s = replace_once(
        s,
        '            this.Combat.ResetRuntime();\n            this.Config.EnableCombatCards = combatBefore;\n',
        '            this.Combat.ResetRuntime();\n            this.BossEnergy.Reset();\n            this.Config.EnableCombatCards = combatBefore;\n',
        'Runner final energy cleanup'
    )
write('Services/CardAutoScenarioRunnerService.cs', s)


# -----------------------------------------------------------------------------
# Static audit: Victory Charge is no longer structurally blocked.
# -----------------------------------------------------------------------------
audit_tool = Path('tools/alpha28_41436_auto_audit.py')
s = audit_tool.read_text(encoding='utf-8')
s = s.replace("    blocked = card_id.lower() == 'victory_charge'\n", "    blocked = False\n")
audit_tool.write_text(s, encoding='utf-8')

print(f'Applied Boss Energy + Victory Charge runtime for {VERSION}')

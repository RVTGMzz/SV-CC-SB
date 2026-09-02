from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.3'


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
# Version only. Save schema remains 19 from .4.14.4.2.
# -----------------------------------------------------------------------------
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

csproj = ROOT / 'Cardcha.csproj'
s = csproj.read_text(encoding='utf-8')
s = re.sub(r'<Version>[^<]+</Version>', f'<Version>{VERSION}</Version>', s, count=1)
csproj.write_text(s, encoding='utf-8')

(ROOT / 'Directory.Build.targets').write_text(f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .4.14.4.3 ChaCha skill materials + Airship Resonance Pedestal. -->\n  <Target Name="CardchaAlpha28041443Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n''', encoding='utf-8')


# -----------------------------------------------------------------------------
# ChaChaSkillService: lock four IDs/namespaces, station level apply and debug discovery.
# Gameplay effects remain deliberately disabled in this pass.
# -----------------------------------------------------------------------------
s = read('Services/ChaChaSkillService.cs')
if 'public const string GuardSkillId' not in s:
    s = replace_once(
        s,
        '    public const string VitalSkillId = "vital_blessing";\n    public const int MaxSkillLevel = 5;\n',
        '''    public const string VitalSkillId = "vital_blessing";\n    public const string GuardSkillId = "bunny_aegis";\n    public const string SpiritSkillId = "spirit_aid";\n    public const string LuckSkillId = "lucky_echo";\n    public const int MaxSkillLevel = 5;\n\n    public static IReadOnlyList<string> SkillIds { get; } = new[]\n    {\n        VitalSkillId, GuardSkillId, SpiritSkillId, LuckSkillId\n    };\n''',
        'ChaCha four skill IDs'
    )

if 'public bool DebugDiscoverSkill' not in s:
    s = replace_once(
        s,
        '''    public bool SetActive(string id)\n    {\n        if (!this.HasSkill(id))\n            return false;\n\n        this.Save.Data.ActiveChaChaSkillId = id;\n        this.Save.Save();\n        Game1.playSound("smallSelect");\n        return true;\n    }\n\n''',
        '''    public bool SetActive(string id)\n    {\n        if (!this.HasSkill(id))\n            return false;\n\n        this.Save.Data.ActiveChaChaSkillId = id;\n        this.Save.Save();\n        Game1.playSound("smallSelect");\n        return true;\n    }\n\n    internal bool ApplyUpgradeFromStation(string id)\n    {\n        if (!this.HasSkill(id))\n            return false;\n\n        int level = this.GetLevel(id);\n        if (level <= 0 || level >= MaxSkillLevel)\n            return false;\n\n        this.Save.Data.ChaChaSkillLevels[id] = level + 1;\n        return true;\n    }\n\n    public bool DebugDiscoverSkill(string id, bool showPresentation = true)\n    {\n        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned || !SkillIds.Contains(id, StringComparer.OrdinalIgnoreCase))\n            return false;\n\n        bool fresh = this.Save.Data.ChaChaSkillsFound.Add(id);\n        if (!this.Save.Data.ChaChaSkillLevels.ContainsKey(id))\n            this.Save.Data.ChaChaSkillLevels[id] = 1;\n        if (string.IsNullOrWhiteSpace(this.Save.Data.ActiveChaChaSkillId))\n            this.Save.Data.ActiveChaChaSkillId = id;\n        this.Save.Save();\n\n        if (showPresentation)\n            this.TriggerCastPresentation();\n        return fresh;\n    }\n\n''',
        'ChaCha station upgrade + debug discovery'
    )

# Generalize DebugSetLevel to all four known skills; still test-only.
s = s.replace(
    '        if (!this.HasSkill(id))\n            return false;\n\n        this.Save.Data.ChaChaSkillLevels[id] = Math.Clamp(level, 1, MaxSkillLevel);',
    '        if (!this.HasSkill(id) || !SkillIds.Contains(id, StringComparer.OrdinalIgnoreCase))\n            return false;\n\n        this.Save.Data.ChaChaSkillLevels[id] = Math.Clamp(level, 1, MaxSkillLevel);',
    1
)

# Richer status, still explicitly says effects aren't enabled.
old_desc = '''    public string Describe()\n        => $"Found=[{string.Join(',', this.Save.Data.ChaChaSkillsFound.OrderBy(p => p, StringComparer.OrdinalIgnoreCase))}] | " +\n           $"Active={this.ActiveSkillId} | VitalLv={this.GetLevel(VitalSkillId)}/{MaxSkillLevel} | " +\n           "HealBalance=UNLOCKED_FOR_DESIGN (runtime heal not enabled yet)";\n'''
new_desc = '''    public string Describe()\n        => $"Found=[{string.Join(',', this.Save.Data.ChaChaSkillsFound.OrderBy(p => p, StringComparer.OrdinalIgnoreCase))}] | " +\n           $"Active={this.ActiveSkillId} | Levels=" +\n           $"Vital:{this.GetLevel(VitalSkillId)},Guard:{this.GetLevel(GuardSkillId)},Spirit:{this.GetLevel(SpiritSkillId)},Luck:{this.GetLevel(LuckSkillId)} | " +\n           "SkillEffects=DESIGN_LOCK_PENDING (normal-form runtime effects are not enabled yet)";\n'''
if old_desc in s:
    s = s.replace(old_desc, new_desc, 1)
write('Services/ChaChaSkillService.cs', s)


# -----------------------------------------------------------------------------
# ItemAssetService: four real object IDs + two UI sheets.
# -----------------------------------------------------------------------------
s = read('Services/ItemAssetService.cs')
if 'ChaChaSkillMaterialsTextureAsset' not in s:
    s = replace_once(
        s,
        '    public const string PortableMachineTextureAsset = "Mods/Ronvotri.Cardcha/PortableMachine";\n',
        '''    public const string PortableMachineTextureAsset = "Mods/Ronvotri.Cardcha/PortableMachine";\n    public const string ChaChaSkillMaterialsTextureAsset = "Mods/Ronvotri.Cardcha/ChaChaSkillMaterials";\n    public const string ChaChaSkillIconsTextureAsset = "Mods/Ronvotri.Cardcha/ChaChaSkillIcons";\n''',
        'ChaCha icon texture assets'
    )

if 'assets/chacha_skill_materials.png' not in s:
    s = replace_once(
        s,
        '''        if (e.Name.IsEquivalentTo(PortableMachineTextureAsset))\n        {\n            e.LoadFromModFile<Texture2D>("assets/portable_machine.png", AssetLoadPriority.Medium);\n            return;\n        }\n\n''',
        '''        if (e.Name.IsEquivalentTo(PortableMachineTextureAsset))\n        {\n            e.LoadFromModFile<Texture2D>("assets/portable_machine.png", AssetLoadPriority.Medium);\n            return;\n        }\n\n        if (e.Name.IsEquivalentTo(ChaChaSkillMaterialsTextureAsset))\n        {\n            e.LoadFromModFile<Texture2D>("assets/chacha_skill_materials.png", AssetLoadPriority.Medium);\n            return;\n        }\n\n        if (e.Name.IsEquivalentTo(ChaChaSkillIconsTextureAsset))\n        {\n            e.LoadFromModFile<Texture2D>("assets/chacha_skill_icons.png", AssetLoadPriority.Medium);\n            return;\n        }\n\n''',
        'ChaCha texture asset loads'
    )

if 'ChaChaSkillMaterialService.VitalDewdropId' not in s:
    s = replace_once(
        s,
        '''                data[SuspiciousDustId] = MakeObject(\n                    this.Helper.Translation.Get("item.dust.name").ToString(),\n                    this.Helper.Translation.Get("item.dust.desc").ToString(),\n                    2\n                );\n''',
        '''                data[SuspiciousDustId] = MakeObject(\n                    this.Helper.Translation.Get("item.dust.name").ToString(),\n                    this.Helper.Translation.Get("item.dust.desc").ToString(),\n                    2\n                );\n                data[ChaChaSkillMaterialService.VitalDewdropId] = MakeObject(\n                    this.Helper.Translation.Get("item.chacha-material.1.name").ToString(),\n                    this.Helper.Translation.Get("item.chacha-material.1.desc").ToString(),\n                    3\n                );\n                data[ChaChaSkillMaterialService.MoonshieldShardId] = MakeObject(\n                    this.Helper.Translation.Get("item.chacha-material.2.name").ToString(),\n                    this.Helper.Translation.Get("item.chacha-material.2.desc").ToString(),\n                    4\n                );\n                data[ChaChaSkillMaterialService.BreezeFeatherId] = MakeObject(\n                    this.Helper.Translation.Get("item.chacha-material.3.name").ToString(),\n                    this.Helper.Translation.Get("item.chacha-material.3.desc").ToString(),\n                    5\n                );\n                data[ChaChaSkillMaterialService.FortuneCoinId] = MakeObject(\n                    this.Helper.Translation.Get("item.chacha-material.4.name").ToString(),\n                    this.Helper.Translation.Get("item.chacha-material.4.desc").ToString(),\n                    6\n                );\n''',
        'ChaCha material objects'
    )
write('Services/ItemAssetService.cs', s)


# -----------------------------------------------------------------------------
# MonsterDeathService: route Cardcha custom-region kills to material drop service.
# -----------------------------------------------------------------------------
s = read('Services/MonsterDeathService.cs')
if 'private readonly ChaChaSkillMaterialService Materials;' not in s:
    s = replace_once(
        s,
        '    private readonly DropService Drops;\n    private readonly CombatService Combat;\n',
        '    private readonly DropService Drops;\n    private readonly CombatService Combat;\n    private readonly ChaChaSkillMaterialService Materials;\n',
        'MonsterDeath materials field'
    )
    s = replace_once(
        s,
        '''    public MonsterDeathService(DropService drops, CombatService combat)\n    {\n        this.Drops = drops;\n        this.Combat = combat;\n    }\n''',
        '''    public MonsterDeathService(DropService drops, CombatService combat, ChaChaSkillMaterialService materials)\n    {\n        this.Drops = drops;\n        this.Combat = combat;\n        this.Materials = materials;\n    }\n''',
        'MonsterDeath materials ctor'
    )

if 'this.Materials.TryDrop(resolvedLocation' not in s:
    s = replace_once(
        s,
        '''        this.Combat.OnMonsterKilled(monster, who);\n        this.Drops.TryDrop(resolvedLocation, monster, who);\n''',
        '''        this.Combat.OnMonsterKilled(monster, who);\n        this.Drops.TryDrop(resolvedLocation, monster, who);\n        EnemyLootScale scale = DropService.ClassifyEnemy(this.LastMonsterName, this.LastDeathSource, monster.modData?.Pairs);\n        this.Materials.TryDrop(resolvedLocation, monster.Position, who, scale);\n''',
        'MonsterDeath material regular drop'
    )
if 'this.Materials.TryDrop(location, position, who, scale);' not in s:
    s = replace_once(
        s,
        '''        this.Drops.TryDrop(\n            location,\n            position,\n            this.LastMonsterName,\n            this.LastMonsterMaxHealth,\n            who,\n            scale\n        );\n''',
        '''        this.Drops.TryDrop(\n            location,\n            position,\n            this.LastMonsterName,\n            this.LastMonsterMaxHealth,\n            who,\n            scale\n        );\n        this.Materials.TryDrop(location, position, who, scale);\n''',
        'MonsterDeath material custom drop'
    )
write('Services/MonsterDeathService.cs', s)


# -----------------------------------------------------------------------------
# ChaCha Resonance menu: use official four icon sheet, known names, region locks.
# -----------------------------------------------------------------------------
s = read('UI/ChaChaResonanceMenu.cs')
if 'private Texture2D? SkillIconTexture;' not in s:
    s = replace_once(
        s,
        '    private Texture2D? ChaChaPortraitTexture;\n',
        '    private Texture2D? ChaChaPortraitTexture;\n    private Texture2D? SkillIconTexture;\n',
        'Resonance skill icon texture field'
    )

# Generalize abilities activation.
old = '''        if (this.CurrentTab == ResonanceTab.Abilities)\n        {\n            ChaChaSkillService? skills = ModEntry.StaticChaChaSkills;\n            if (index == 0 && skills is not null && skills.HasSkill(ChaChaSkillService.VitalSkillId))\n            {\n                skills.SetActive(ChaChaSkillService.VitalSkillId);\n                this.Status = ModEntry.T("resonance.ability.vital.equipped");\n                return;\n            }\n\n            this.Status = index == 0\n                ? ModEntry.T("resonance.ability.vital.find-region1")\n                : ModEntry.T("resonance.ability.region.future", new { region = index + 1 });\n            Game1.playSound("cancel");\n            return;\n        }\n'''
new = '''        if (this.CurrentTab == ResonanceTab.Abilities)\n        {\n            ChaChaSkillService? skills = ModEntry.StaticChaChaSkills;\n            string skillId = ChaChaSkillMaterialService.GetSkillIdForIndex(index);\n            if (skills is not null && skills.HasSkill(skillId))\n            {\n                skills.SetActive(skillId);\n                this.Status = ModEntry.T("resonance.ability.equipped", new { name = ModEntry.T($"chacha.skill.{skillId}.name") });\n                return;\n            }\n\n            this.Status = ModEntry.T("resonance.ability.find-region", new { region = index + 1 });\n            Game1.playSound("cancel");\n            return;\n        }\n'''
if old in s:
    s = s.replace(old, new, 1)

start = s.find('    private void DrawAbilities(SpriteBatch b, Color pink)')
end = s.find('    private void DrawSupportProgress(SpriteBatch b, Color pink)', start)
if start < 0 or end < 0:
    raise RuntimeError('Resonance DrawAbilities boundary not found')
new_method = r'''    private void DrawAbilities(SpriteBatch b, Color pink)
    {
        ChaChaSkillService? skills = ModEntry.StaticChaChaSkills;

        for (int i = 0; i < this.EntryButtons.Count && i < 4; i++)
        {
            Rectangle r = this.EntryButtons[i].bounds;
            string skillId = ChaChaSkillMaterialService.GetSkillIdForIndex(i);
            bool found = skills?.HasSkill(skillId) == true;
            bool active = skills?.IsActive(skillId) == true;
            int level = skills?.GetLevel(skillId) ?? 0;
            bool focused = this.currentlySnappedComponent?.myID == this.EntryButtons[i].myID;
            Color accent = i switch
            {
                0 => new Color(124, 238, 178),
                1 => new Color(131, 187, 255),
                2 => new Color(106, 223, 249),
                _ => new Color(255, 204, 91)
            };

            CardchaUi.DrawRoundedPanel(
                b,
                r,
                new Color(47, 35, 55),
                focused ? Color.White : found ? accent : new Color(111, 83, 117),
                thickness: focused ? 4 : 3,
                radius: 10
            );

            Rectangle sourceRect = new(r.X + 16, r.Y + 12, r.Width - 32, 34);
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                ModEntry.T("resonance.ability.region-source", new { region = i + 1, range = GetAbilityLevelRange(i) }),
                sourceRect,
                accent * (found ? 0.94f : 0.55f),
                centerX: true,
                centerY: true,
                padding: 2,
                maxScale: 0.86f
            );

            int emblemSize = Math.Min(82, Math.Max(58, r.Height / 3));
            Rectangle emblem = new(r.Center.X - emblemSize / 2, r.Y + 53, emblemSize, emblemSize);
            CardchaUi.DrawRoundedPanel(b, emblem, new Color(28, 24, 35), accent * (found ? 0.65f : 0.28f), thickness: 2, radius: 22);
            if (this.SkillIconTexture is not null)
            {
                Rectangle source = new(i * 32, 0, 32, 32);
                b.Draw(this.SkillIconTexture, Inflate(emblem, -5), source, found ? Color.White : Color.White * 0.30f);
            }
            else
            {
                CardchaUi.DrawScaledText(b, Game1.dialogueFont, "?", emblem, accent * (found ? 1f : 0.45f), centerX: true, centerY: true, padding: 7, maxScale: 0.8f);
            }

            Rectangle nameRect = new(r.X + 14, emblem.Bottom + 7, r.Width - 28, 31);
            CardchaUi.DrawScaledText(
                b,
                Game1.dialogueFont,
                ModEntry.T($"chacha.skill.{skillId}.name"),
                nameRect,
                found ? Color.White : Color.White * 0.64f,
                centerX: true,
                centerY: true,
                padding: 2,
                maxScale: 0.70f
            );

            Rectangle infoRect = new(r.X + 17, nameRect.Bottom + 2, r.Width - 34, 28);
            string info = found
                ? ModEntry.T("resonance.ability.level", new { level, max = ChaChaSkillService.MaxSkillLevel })
                : ModEntry.T("resonance.ability.find-region", new { region = i + 1 });
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                info,
                infoRect,
                found ? accent : Color.White * 0.48f,
                centerX: true,
                centerY: true,
                padding: 2,
                maxScale: 0.80f
            );

            Rectangle bottomRect = new(r.X + 18, r.Bottom - 48, r.Width - 36, 36);
            string bottom = found
                ? active ? ModEntry.T("resonance.ability.active") : ModEntry.T("resonance.ability.select")
                : ModEntry.T("resonance.ability.normal-form");
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                bottom,
                bottomRect,
                active ? CardchaUi.Gold : Color.White * 0.56f,
                centerX: true,
                centerY: true,
                padding: 3,
                maxScale: 0.76f
            );
        }
    }

    private static string GetAbilityLevelRange(int index)
        => index switch
        {
            0 => "0–20",
            1 => "21–40",
            2 => "41–60",
            _ => "61–80"
        };

'''
s = s[:start] + new_method + s[end:]

if 'this.SkillIconTexture = Game1.content.Load<Texture2D>(ItemAssetService.ChaChaSkillIconsTextureAsset);' not in s:
    anchor = '''        try\n        {\n            this.ChaChaPortraitTexture = ModEntry.StaticHelper.ModContent.Load<Texture2D>("assets/chacha_portrait.png");\n        }\n        catch\n        {\n            this.ChaChaPortraitTexture = null;\n        }\n'''
    if anchor not in s:
        # Actual source uses normal newlines; keep a second anchor.
        anchor = '''        try
        {
            this.ChaChaPortraitTexture = ModEntry.StaticHelper.ModContent.Load<Texture2D>("assets/chacha_portrait.png");
        }
        catch
        {
            this.ChaChaPortraitTexture = null;
        }
'''
    addition = anchor + '''
        try
        {
            this.SkillIconTexture = Game1.content.Load<Texture2D>(ItemAssetService.ChaChaSkillIconsTextureAsset);
        }
        catch
        {
            this.SkillIconTexture = null;
        }
'''
    s = replace_once(s, anchor, addition, 'Resonance skill icon texture load')
write('UI/ChaChaResonanceMenu.cs', s)


# -----------------------------------------------------------------------------
# ModEntry wiring. Build world actors/skills/materials before death pipeline.
# -----------------------------------------------------------------------------
s = read('ModEntry.cs')
if 'private ChaChaSkillMaterialService ChaChaMaterials = null!;' not in s:
    s = replace_once(
        s,
        '    private ChaChaSkillService ChaChaSkills = null!;\n',
        '    private ChaChaSkillService ChaChaSkills = null!;\n    private ChaChaSkillMaterialService ChaChaMaterials = null!;\n',
        'ModEntry materials field'
    )

# Move/init block before Progression and remove old duplicate actor/skill block.
old_init = '''        this.Combat = new CombatService(this.Config, this.Loadout, this.Save, this.Cards, this.Upgrades, this.BossEnergy);\n        this.Renderer = new CardRenderer(helper);\n        this.Progression = new ProgressionService(helper, this.Monitor, this.Save);\n'''
new_init = '''        this.Combat = new CombatService(this.Config, this.Loadout, this.Save, this.Cards, this.Upgrades, this.BossEnergy);\n        this.Renderer = new CardRenderer(helper);\n        this.WorldActors = new WorldActorService(this.Monitor);\n        this.ChaChaSkills = new ChaChaSkillService(helper, this.Monitor, this.Save, this.WorldActors);\n        StaticChaChaSkills = this.ChaChaSkills;\n        this.ChaChaMaterials = new ChaChaSkillMaterialService(helper, this.Monitor, this.Save, this.ChaChaSkills, this.Controller);\n        this.Progression = new ProgressionService(helper, this.Monitor, this.Save);\n'''
s = replace_once(s, old_init, new_init, 'ModEntry early ChaCha initialization')

s = s.replace(
    '        this.Deaths = new MonsterDeathService(this.Drops, this.Combat);\n',
    '        this.Deaths = new MonsterDeathService(this.Drops, this.Combat, this.ChaChaMaterials);\n',
    1
)
old_duplicate = '''        this.WorldActors = new WorldActorService(this.Monitor);\n        this.ChaChaSkills = new ChaChaSkillService(helper, this.Monitor, this.Save, this.WorldActors);\n        StaticChaChaSkills = this.ChaChaSkills;\n'''
# Remove only if it occurs after BookTab; now there will be two occurrences until removed.
first = s.find(old_duplicate)
if first >= 0:
    second = s.find(old_duplicate, first + 1)
    if second >= 0:
        s = s[:second] + s[second + len(old_duplicate):]

if 'this.ChaChaMaterials.OnRenderedWorld' not in s:
    s = replace_once(
        s,
        '        helper.Events.Display.RenderedWorld += this.ChaChaSkills.OnRenderedWorld;\n',
        '        helper.Events.Display.RenderedWorld += this.ChaChaSkills.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.ChaChaMaterials.OnRenderedWorld;\n',
        'Materials render event'
    )
if 'this.ChaChaMaterials.OnButtonPressed' not in s:
    s = replace_once(
        s,
        '        helper.Events.Input.ButtonPressed += this.ChaChaSkills.OnButtonPressed;\n',
        '        helper.Events.Input.ButtonPressed += this.ChaChaSkills.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.ChaChaMaterials.OnButtonPressed;\n',
        'Materials input event'
    )

if 'cardcha_chacha_materials' not in s:
    s = replace_once(
        s,
        '        helper.ConsoleCommands.Add("cardcha_chacha_skill_status", "Show persistent ChaCha normal-form skill state.", this.CommandChaChaSkillStatus);\n',
        '''        helper.ConsoleCommands.Add("cardcha_chacha_skill_status", "Show persistent ChaCha normal-form skill state.", this.CommandChaChaSkillStatus);\n        helper.ConsoleCommands.Add("cardcha_chacha_materials", "TEST ONLY: give all four ChaCha region upgrade materials: cardcha_chacha_materials [amount]", this.CommandChaChaMaterials);\n        helper.ConsoleCommands.Add("cardcha_chacha_station", "TEST ONLY: open the Airship ChaCha Resonance Pedestal UI directly.", this.CommandChaChaStation);\n        helper.ConsoleCommands.Add("cardcha_chacha_material_status", "Show ChaCha region-material and Airship station state.", this.CommandChaChaMaterialStatus);\n''',
        'Materials debug commands'
    )

# Extend existing skill unlock debug command to accept vital/guard/spirit/luck/all.
pattern = re.compile(r'    private void CommandChaChaSkillUnlock\(string command, string\[\] args\)\n    \{.*?\n    \}\n\n    private void CommandChaChaSkillLevel', re.S)
match = pattern.search(s)
if match:
    replacement = '''    private void CommandChaChaSkillUnlock(string command, string[] args)\n    {\n        if (!Context.IsWorldReady)\n        {\n            this.Monitor.Log("Load a save before testing ChaCha skills.", LogLevel.Warn);\n            return;\n        }\n        if (!this.Save.Data.ChaChaLoaned)\n        {\n            this.Monitor.Log("ChaCha has not joined the player yet; normal-form skills stay story-gated.", LogLevel.Warn);\n            return;\n        }\n\n        string arg = args.FirstOrDefault()?.Trim().ToLowerInvariant() ?? "vital";\n        IEnumerable<string> ids = arg == "all"\n            ? ChaChaSkillService.SkillIds\n            : new[]\n            {\n                arg switch\n                {\n                    "guard" or "aegis" or "bunny_aegis" => ChaChaSkillService.GuardSkillId,\n                    "spirit" or "spirit_aid" => ChaChaSkillService.SpiritSkillId,\n                    "luck" or "lucky" or "lucky_echo" => ChaChaSkillService.LuckSkillId,\n                    _ => ChaChaSkillService.VitalSkillId\n                }\n            };\n\n        int fresh = 0;\n        foreach (string id in ids)\n            if (this.ChaChaSkills.DebugDiscoverSkill(id, showPresentation: false))\n                fresh++;\n        this.ChaChaSkills.TriggerCastPresentation();\n        this.Monitor.Log($"TEST: discovered {fresh} new ChaCha skill(s). Found=[{string.Join(",", this.Save.Data.ChaChaSkillsFound)}]", LogLevel.Alert);\n    }\n\n    private void CommandChaChaSkillLevel'''
    s = s[:match.start()] + replacement + s[match.end():]

# Generalize level debug command to optional skill selector.
pattern = re.compile(r'    private void CommandChaChaSkillLevel\(string command, string\[\] args\)\n    \{.*?\n    \}\n\n    private void CommandChaChaSkillCast', re.S)
match = pattern.search(s)
if match:
    replacement = '''    private void CommandChaChaSkillLevel(string command, string[] args)\n    {\n        if (!Context.IsWorldReady)\n            return;\n\n        int level = args.Length > 0 && int.TryParse(args[0], out int parsed)\n            ? Math.Clamp(parsed, 1, ChaChaSkillService.MaxSkillLevel)\n            : 1;\n        string selector = args.Length > 1 ? args[1].Trim().ToLowerInvariant() : "vital";\n        string skillId = selector switch\n        {\n            "guard" or "aegis" => ChaChaSkillService.GuardSkillId,\n            "spirit" => ChaChaSkillService.SpiritSkillId,\n            "luck" or "lucky" => ChaChaSkillService.LuckSkillId,\n            _ => ChaChaSkillService.VitalSkillId\n        };\n\n        if (!this.ChaChaSkills.DebugSetLevel(skillId, level))\n        {\n            this.Monitor.Log("Discover that ChaCha skill first. Use cardcha_chacha_skill_unlock <vital|guard|spirit|luck|all> for TEST.", LogLevel.Warn);\n            return;\n        }\n        this.Monitor.Log($"TEST: {skillId} set to Lv {level}/{ChaChaSkillService.MaxSkillLevel}. No materials or Magic Dust were spent.", LogLevel.Alert);\n    }\n\n    private void CommandChaChaSkillCast'''
    s = s[:match.start()] + replacement + s[match.end():]

if 'private void CommandChaChaMaterials' not in s:
    anchor = '''    private void CommandChaChaSkillStatus(string command, string[] args)\n    {\n        this.Monitor.Log("===== CHACHA NORMAL-FORM SKILLS =====\\n" + this.ChaChaSkills.Describe(), LogLevel.Alert);\n    }\n\n'''
    addition = anchor + '''    private void CommandChaChaMaterials(string command, string[] args)\n    {\n        if (!Context.IsWorldReady)\n            return;\n        int amount = args.Length > 0 && int.TryParse(args[0], out int parsed) ? Math.Clamp(parsed, 1, 999) : 20;\n        this.ChaChaMaterials.GiveAllForDebug(amount);\n        this.Monitor.Log($"TEST: gave {amount} of each ChaCha skill material to the backpack.", LogLevel.Alert);\n    }\n\n    private void CommandChaChaStation(string command, string[] args)\n    {\n        if (!Context.IsWorldReady || Game1.activeClickableMenu is not null)\n            return;\n        Game1.activeClickableMenu = new ChaChaSkillUpgradeMenu(this.Save, this.ChaChaSkills, this.ChaChaMaterials, this.Controller);\n    }\n\n    private void CommandChaChaMaterialStatus(string command, string[] args)\n    {\n        this.Monitor.Log("===== CHACHA SKILL MATERIALS =====\\n" + this.ChaChaMaterials.Describe(), LogLevel.Alert);\n    }\n\n'''
    s = replace_once(s, anchor, addition, 'Materials command methods')

s = re.sub(
    r'Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14\.4\.2 CHACHA SKILL FOUNDATION TEST',
    f'Cardcha! v{VERSION} CHACHA SKILL MATERIALS + AIRSHIP STATION TEST',
    s
)
write('ModEntry.cs', s)


# -----------------------------------------------------------------------------
# i18n. Four names are now design-locked; effects for II-IV remain future.
# -----------------------------------------------------------------------------
updates = {
    'default.json': {
        'item.chacha-material.1.name': 'Vital Dewdrop',
        'item.chacha-material.1.desc': 'A luminous dewdrop carrying gentle life resonance. Found in Region I and used at ChaCha’s Airship Resonance Pedestal.',
        'item.chacha-material.2.name': 'Moonshield Shard',
        'item.chacha-material.2.desc': 'A moonlit protective crystal fragment tied to Region II. Used to strengthen ChaCha’s protective support skill.',
        'item.chacha-material.3.name': 'Breeze Feather',
        'item.chacha-material.3.desc': 'A feather filled with light wind resonance from Region III. Used to strengthen ChaCha’s support skill.',
        'item.chacha-material.4.name': 'Fortune Coin',
        'item.chacha-material.4.desc': 'A lucky magical coin resonating with Region IV. Used to strengthen ChaCha’s fortune support skill.',
        'chacha.skill.vital_blessing.name': 'Vital Blessing',
        'chacha.skill.bunny_aegis.name': 'Bunny Aegis',
        'chacha.skill.spirit_aid.name': 'Spirit Aid',
        'chacha.skill.lucky_echo.name': 'Lucky Echo',
        'chacha.station.world-label': 'ChaCha Resonance Pedestal',
        'chacha.station.title': 'ChaCha Resonance Pedestal',
        'chacha.station.subtitle': 'Bring region materials back to the Airship • Magic Dust: {{dust}}',
        'chacha.station.back': 'Back',
        'chacha.station.region': 'Region {{region}} • Lv {{range}}',
        'chacha.station.level': 'Skill Lv {{level}}/{{max}}',
        'chacha.station.locked': 'Skill not discovered',
        'chacha.station.material-count': '{{name}} × {{count}}',
        'chacha.station.find-first': 'Find the skill in Region {{region}} before upgrading it.',
        'chacha.station.max': 'MAX LEVEL',
        'chacha.station.upgrade-cost': 'Upgrade to Lv {{next}} • {{material}} material + {{dust}} Magic Dust',
        'chacha.station.status.ready': 'Choose a discovered ChaCha skill to upgrade.',
        'chacha.station.status.load-save': 'Load a save first.',
        'chacha.station.status.skill-locked': 'This skill must be discovered in Region {{region}} first.',
        'chacha.station.status.max': 'This ChaCha skill is already max level.',
        'chacha.station.status.not-enough': 'Need {{materialNeed}} material (have {{material}}) and {{dustNeed}} Magic Dust (have {{dust}}).',
        'chacha.station.status.consume-failed': 'Upgrade transaction failed safely; resources were not lost.',
        'chacha.station.status.upgraded': 'ChaCha skill upgraded to Lv {{level}}!',
        'resonance.ability.region-source': 'REGION {{region}} • Lv {{range}}',
        'resonance.ability.level': 'Lv {{level}}/{{max}} • Upgrade on the Airship',
        'resonance.ability.find-region': 'Find this skill while exploring Region {{region}}.',
        'resonance.ability.equipped': '{{name}} equipped for ChaCha’s normal form.',
        'resonance.ability.active': 'ACTIVE • Normal-form support',
        'resonance.ability.select': 'Select to use this normal-form skill',
        'resonance.ability.normal-form': 'Normal-form passive • Skill not discovered yet',
    },
    'vi.json': {
        'item.chacha-material.1.name': 'Giọt Sương Sinh Khí',
        'item.chacha-material.1.desc': 'Giọt sương phát sáng chứa cộng hưởng sinh khí dịu nhẹ. Tìm thấy ở Khu Vực I và dùng tại Bệ Cộng Hưởng ChaCha trên tàu bay.',
        'item.chacha-material.2.name': 'Mảnh Khiên Ánh Trăng',
        'item.chacha-material.2.desc': 'Mảnh pha lê hộ mệnh phủ ánh trăng của Khu Vực II. Dùng để cường hóa kỹ năng bảo hộ của ChaCha.',
        'item.chacha-material.3.name': 'Lông Vũ Gió Nhẹ',
        'item.chacha-material.3.desc': 'Chiếc lông vũ mang cộng hưởng gió nhẹ từ Khu Vực III. Dùng để cường hóa kỹ năng hỗ trợ của ChaCha.',
        'item.chacha-material.4.name': 'Đồng Xu Phúc Tinh',
        'item.chacha-material.4.desc': 'Đồng xu ma pháp mang vận may của Khu Vực IV. Dùng để cường hóa kỹ năng phúc vận của ChaCha.',
        'chacha.skill.vital_blessing.name': 'Phúc Lành Sinh Khí',
        'chacha.skill.bunny_aegis.name': 'Hộ Mệnh Thỏ Tiên',
        'chacha.skill.spirit_aid.name': 'Tinh Linh Tiếp Sức',
        'chacha.skill.lucky_echo.name': 'Phúc Vận Thỏ Tiên',
        'chacha.station.world-label': 'Bệ Cộng Hưởng ChaCha',
        'chacha.station.title': 'Bệ Cộng Hưởng ChaCha',
        'chacha.station.subtitle': 'Mang nguyên liệu từ Khu Vực về tàu bay • Bụi Ma Thuật: {{dust}}',
        'chacha.station.back': 'Quay lại',
        'chacha.station.region': 'Khu Vực {{region}} • Lv {{range}}',
        'chacha.station.level': 'Kỹ năng Lv {{level}}/{{max}}',
        'chacha.station.locked': 'Chưa khám phá kỹ năng',
        'chacha.station.material-count': '{{name}} × {{count}}',
        'chacha.station.find-first': 'Hãy tìm kỹ năng ở Khu Vực {{region}} trước khi nâng cấp.',
        'chacha.station.max': 'CẤP TỐI ĐA',
        'chacha.station.upgrade-cost': 'Nâng lên Lv {{next}} • {{material}} nguyên liệu + {{dust}} Bụi Ma Thuật',
        'chacha.station.status.ready': 'Chọn một kỹ năng ChaCha đã khám phá để nâng cấp.',
        'chacha.station.status.load-save': 'Hãy vào một file save trước.',
        'chacha.station.status.skill-locked': 'Cần khám phá kỹ năng này ở Khu Vực {{region}} trước.',
        'chacha.station.status.max': 'Kỹ năng ChaCha này đã đạt cấp tối đa.',
        'chacha.station.status.not-enough': 'Cần {{materialNeed}} nguyên liệu (đang có {{material}}) và {{dustNeed}} Bụi Ma Thuật (đang có {{dust}}).',
        'chacha.station.status.consume-failed': 'Giao dịch nâng cấp đã dừng an toàn; không mất nguyên liệu.',
        'chacha.station.status.upgraded': 'Kỹ năng ChaCha đã lên Lv {{level}}!',
        'resonance.ability.region-source': 'KHU VỰC {{region}} • Lv {{range}}',
        'resonance.ability.level': 'Lv {{level}}/{{max}} • Nâng trên tàu bay',
        'resonance.ability.find-region': 'Tìm kỹ năng này khi khám phá Khu Vực {{region}}.',
        'resonance.ability.equipped': 'Đã chọn {{name}} cho form thường của ChaCha.',
        'resonance.ability.active': 'ĐANG DÙNG • Hỗ trợ form thường',
        'resonance.ability.select': 'Chọn để dùng kỹ năng form thường này',
        'resonance.ability.normal-form': 'Passive form thường • Chưa khám phá kỹ năng',
    }
}
for lang, kv in updates.items():
    p = ROOT / 'i18n' / lang
    obj = json.loads(p.read_text(encoding='utf-8'))
    obj.update(kv)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(f'Applied ChaCha skill materials + Airship station {VERSION}; save schema remains 19')

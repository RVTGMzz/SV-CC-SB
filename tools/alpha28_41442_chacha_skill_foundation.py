from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.2'
SCHEMA = 19


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

(ROOT / 'Directory.Build.targets').write_text(f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .4.14.4.2 ChaCha normal-form skill discovery foundation. -->\n  <Target Name="CardchaAlpha28041442Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n''', encoding='utf-8')


# -----------------------------------------------------------------------------
# Save schema 19: persistent discovered normal-form ChaCha skills.
# -----------------------------------------------------------------------------
s = read('Models/SaveData.cs')
s = re.sub(r'public int SchemaVersion \{ get; set; \} = \d+;', f'public int SchemaVersion {{ get; set; }} = {SCHEMA};', s, count=1)
if 'ChaChaSkillsFound' not in s:
    s = replace_once(
        s,
        '''    public int CardchaStoryStage { get; set; }\n\n''',
        '''    public int CardchaStoryStage { get; set; }\n\n    // alpha.28.0.4.14.4.2 — persistent ChaCha normal-form skills found while exploring\n    // Cardcha custom regions. Boss Forms / Mythic Echoes are intentionally separate.\n    public HashSet<string> ChaChaSkillsFound { get; set; } = new(StringComparer.OrdinalIgnoreCase);\n    public Dictionary<string, int> ChaChaSkillLevels { get; set; } = new(StringComparer.OrdinalIgnoreCase);\n    public string ActiveChaChaSkillId { get; set; } = "";\n\n''',
        'SaveData ChaCha skill fields'
    )
write('Models/SaveData.cs', s)

s = read('Services/SaveService.cs')
s = re.sub(r'private const int CurrentSchemaVersion = \d+;', f'private const int CurrentSchemaVersion = {SCHEMA};', s, count=1)

if 'if (loadedSchema < 19)' not in s:
    s = replace_once(
        s,
        '''        if (loadedSchema < CurrentSchemaVersion)\n        {\n''',
        '''        // v19: ChaCha normal-form exploration skill foundation. Existing saves begin\n        // with no discovered ChaCha skills; no Magic Dust or card state is changed.\n        if (loadedSchema < 19)\n        {\n            this.Data.ChaChaSkillsFound = new HashSet<string>(\n                this.Data.ChaChaSkillsFound ?? new HashSet<string>(),\n                StringComparer.OrdinalIgnoreCase\n            );\n            this.Data.ChaChaSkillLevels = new Dictionary<string, int>(\n                this.Data.ChaChaSkillLevels ?? new Dictionary<string, int>(),\n                StringComparer.OrdinalIgnoreCase\n            );\n            this.Data.ActiveChaChaSkillId ??= "";\n        }\n\n        if (loadedSchema < CurrentSchemaVersion)\n        {\n''',
        'SaveService v19 migration'
    )

if 'ChaChaSkillsFound = new HashSet<string>' not in s[s.find('private static SaveData CloneData'):]:
    s = replace_once(
        s,
        '''            CardchaStoryStage = d.CardchaStoryStage,\n            MimiMerchantUnlockedDay = d.MimiMerchantUnlockedDay,\n''',
        '''            CardchaStoryStage = d.CardchaStoryStage,\n            ChaChaSkillsFound = new HashSet<string>(d.ChaChaSkillsFound ?? new HashSet<string>(), StringComparer.OrdinalIgnoreCase),\n            ChaChaSkillLevels = new Dictionary<string, int>(d.ChaChaSkillLevels ?? new Dictionary<string, int>(), StringComparer.OrdinalIgnoreCase),\n            ActiveChaChaSkillId = d.ActiveChaChaSkillId ?? "",\n            MimiMerchantUnlockedDay = d.MimiMerchantUnlockedDay,\n''',
        'SaveService CloneData skills'
    )

if 'this.Data.ChaChaSkillsFound ??=' not in s:
    s = replace_once(
        s,
        '''        this.Data.FavoriteCardIds ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);\n        this.Data.LastStateFingerprint ??= "";\n''',
        '''        this.Data.FavoriteCardIds ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);\n        this.Data.ChaChaSkillsFound ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);\n        this.Data.ChaChaSkillLevels ??= new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);\n        this.Data.ActiveChaChaSkillId ??= "";\n        this.Data.LastStateFingerprint ??= "";\n''',
        'SaveService normalize init skills'
    )

if 'normalizedChaChaSkillLevels' not in s:
    s = replace_once(
        s,
        '''        this.Data.CardCopies = copies;\n    }\n\n    private static string ComputeFingerprint(SaveData data)\n''',
        '''        this.Data.CardCopies = copies;\n\n        this.Data.ChaChaSkillsFound = new HashSet<string>(\n            this.Data.ChaChaSkillsFound.Where(p => !string.IsNullOrWhiteSpace(p)),\n            StringComparer.OrdinalIgnoreCase\n        );\n        Dictionary<string, int> normalizedChaChaSkillLevels = new(StringComparer.OrdinalIgnoreCase);\n        foreach (string skillId in this.Data.ChaChaSkillsFound)\n        {\n            int level = this.Data.ChaChaSkillLevels.TryGetValue(skillId, out int storedLevel) ? storedLevel : 1;\n            normalizedChaChaSkillLevels[skillId] = Math.Clamp(level, 1, ChaChaSkillService.MaxSkillLevel);\n        }\n        this.Data.ChaChaSkillLevels = normalizedChaChaSkillLevels;\n        if (!string.IsNullOrWhiteSpace(this.Data.ActiveChaChaSkillId)\n            && !this.Data.ChaChaSkillsFound.Contains(this.Data.ActiveChaChaSkillId))\n        {\n            this.Data.ActiveChaChaSkillId = "";\n        }\n    }\n\n    private static string ComputeFingerprint(SaveData data)\n''',
        'SaveService normalize skills'
    )

if 'string chachaSkills =' not in s:
    s = replace_once(
        s,
        '''        string battleScholarTypes = string.Join(",", (data.BattleScholarMonsterTypesToday ?? new HashSet<string>())\n            .Where(p => !string.IsNullOrWhiteSpace(p))\n            .OrderBy(p => p, StringComparer.OrdinalIgnoreCase));\n\n''',
        '''        string battleScholarTypes = string.Join(",", (data.BattleScholarMonsterTypesToday ?? new HashSet<string>())\n            .Where(p => !string.IsNullOrWhiteSpace(p))\n            .OrderBy(p => p, StringComparer.OrdinalIgnoreCase));\n\n        string chachaSkills = string.Join(",", (data.ChaChaSkillsFound ?? new HashSet<string>())\n            .Where(p => !string.IsNullOrWhiteSpace(p))\n            .OrderBy(p => p, StringComparer.OrdinalIgnoreCase));\n        string chachaSkillLevels = string.Join(",", (data.ChaChaSkillLevels ?? new Dictionary<string, int>())\n            .OrderBy(p => p.Key, StringComparer.OrdinalIgnoreCase)\n            .Select(p => $"{p.Key}:{p.Value}"));\n\n''',
        'SaveService fingerprint skill strings'
    )
    s = replace_once(
        s,
        '''            data.CardchaStoryChapter,\n            data.CardchaStoryStage,\n            data.MimiMerchantUnlockedDay,\n''',
        '''            data.CardchaStoryChapter,\n            data.CardchaStoryStage,\n            chachaSkills,\n            chachaSkillLevels,\n            data.ActiveChaChaSkillId ?? "",\n            data.MimiMerchantUnlockedDay,\n''',
        'SaveService fingerprint skill fields'
    )
write('Services/SaveService.cs', s)


# -----------------------------------------------------------------------------
# ChaCha Resonance: Abilities now come from custom maps, not card milestones.
# -----------------------------------------------------------------------------
s = read('UI/ChaChaResonanceMenu.cs')

# Replace activation behavior for Abilities.
old = '''        if (this.CurrentTab == ResonanceTab.Abilities)\n        {\n            int milestone = new[] { 20, 40, 60, 80 }[Math.Clamp(index, 0, 3)];\n            this.Status = ModEntry.T("resonance.ability.status.future", new { milestone });\n            Game1.playSound("cancel");\n            return;\n        }\n'''
new = '''        if (this.CurrentTab == ResonanceTab.Abilities)\n        {\n            ChaChaSkillService? skills = ModEntry.StaticChaChaSkills;\n            if (index == 0 && skills is not null && skills.HasSkill(ChaChaSkillService.VitalSkillId))\n            {\n                skills.SetActive(ChaChaSkillService.VitalSkillId);\n                this.Status = ModEntry.T("resonance.ability.vital.equipped");\n                return;\n            }\n\n            this.Status = index == 0\n                ? ModEntry.T("resonance.ability.vital.find-region1")\n                : ModEntry.T("resonance.ability.region.future", new { region = index + 1 });\n            Game1.playSound("cancel");\n            return;\n        }\n'''
s = replace_once(s, old, new, 'Resonance ability activation')

# Replace DrawAbilities wholesale using method boundary.
start = s.find('    private void DrawAbilities(SpriteBatch b, Color pink)')
end = s.find('    private void DrawSupportProgress(SpriteBatch b, Color pink)', start)
if start < 0 or end < 0:
    raise RuntimeError('DrawAbilities method boundary not found')
new_method = r'''    private void DrawAbilities(SpriteBatch b, Color pink)
    {
        ChaChaSkillService? skills = ModEntry.StaticChaChaSkills;
        bool vitalFound = skills?.HasSkill(ChaChaSkillService.VitalSkillId) == true;
        bool vitalActive = skills?.IsActive(ChaChaSkillService.VitalSkillId) == true;
        int vitalLevel = skills?.GetLevel(ChaChaSkillService.VitalSkillId) ?? 0;

        for (int i = 0; i < this.EntryButtons.Count && i < 4; i++)
        {
            Rectangle r = this.EntryButtons[i].bounds;
            bool focused = this.currentlySnappedComponent?.myID == this.EntryButtons[i].myID;
            bool first = i == 0;
            bool found = first && vitalFound;

            Color border = focused
                ? Color.White
                : found
                    ? new Color(124, 238, 178)
                    : new Color(111, 83, 117);
            CardchaUi.DrawRoundedPanel(
                b,
                r,
                new Color(47, 35, 55),
                border,
                thickness: focused ? 4 : 3,
                radius: 10
            );

            Rectangle sourceRect = new(r.X + 16, r.Y + 13, r.Width - 32, 38);
            CardchaUi.DrawScaledText(
                b,
                Game1.dialogueFont,
                first ? ModEntry.T("resonance.ability.region1.source") : ModEntry.T("resonance.ability.region.source", new { region = i + 1 }),
                sourceRect,
                first ? new Color(174, 244, 205) : new Color(242, 190, 222) * 0.62f,
                centerX: true,
                centerY: true,
                padding: 3,
                maxScale: 0.68f
            );

            int emblemSize = Math.Min(78, Math.Max(54, r.Height / 3));
            Rectangle emblem = new(r.Center.X - emblemSize / 2, r.Y + 61, emblemSize, emblemSize);
            Color emblemBorder = found ? new Color(132, 255, 194) : pink * 0.38f;
            CardchaUi.DrawRoundedPanel(b, emblem, new Color(28, 24, 35), emblemBorder, thickness: 2, radius: 30);
            CardchaUi.DrawScaledText(
                b,
                Game1.dialogueFont,
                found ? "+" : "?",
                emblem,
                found ? new Color(159, 255, 203) : pink,
                centerX: true,
                centerY: true,
                padding: 8,
                maxScale: 0.86f
            );

            Rectangle nameRect = new(r.X + 14, emblem.Bottom + 9, r.Width - 28, 31);
            string name = first
                ? found ? ModEntry.T("resonance.ability.vital.name") : ModEntry.T("resonance.ability.undiscovered")
                : ModEntry.T("resonance.ability.future-name");
            CardchaUi.DrawScaledText(
                b,
                Game1.dialogueFont,
                name,
                nameRect,
                found ? Color.White : Color.White * 0.72f,
                centerX: true,
                centerY: true,
                padding: 2,
                maxScale: 0.72f
            );

            Rectangle infoRect = new(r.X + 17, nameRect.Bottom + 2, r.Width - 34, 28);
            string info = first
                ? found
                    ? ModEntry.T("resonance.ability.vital.level", new { level = vitalLevel, max = ChaChaSkillService.MaxSkillLevel })
                    : ModEntry.T("resonance.ability.vital.find-region1")
                : ModEntry.T("resonance.ability.region.future", new { region = i + 1 });
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                info,
                infoRect,
                found ? new Color(169, 244, 201) : Color.White * 0.50f,
                centerX: true,
                centerY: true,
                padding: 2,
                maxScale: 0.82f
            );

            Rectangle bottomRect = new(r.X + 18, r.Bottom - 50, r.Width - 36, 38);
            string bottom = first && found
                ? vitalActive
                    ? ModEntry.T("resonance.ability.vital.active")
                    : ModEntry.T("resonance.ability.vital.select")
                : first
                    ? ModEntry.T("resonance.ability.normal-form")
                    : ModEntry.T("resonance.ability.not-designed");
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                bottom,
                bottomRect,
                first && vitalActive ? CardchaUi.Gold : Color.White * 0.56f,
                centerX: true,
                centerY: true,
                padding: 3,
                maxScale: 0.78f
            );
        }
    }

'''
s = s[:start] + new_method + s[end:]
write('UI/ChaChaResonanceMenu.cs', s)


# -----------------------------------------------------------------------------
# ModEntry wiring + test commands.
# -----------------------------------------------------------------------------
s = read('ModEntry.cs')
if 'internal static ChaChaSkillService? StaticChaChaSkills;' not in s:
    s = replace_once(
        s,
        '    internal static IModHelper? StaticHelper;\n',
        '    internal static IModHelper? StaticHelper;\n    internal static ChaChaSkillService? StaticChaChaSkills;\n',
        'ModEntry static skills bridge'
    )
if 'private ChaChaSkillService ChaChaSkills = null!;' not in s:
    s = replace_once(
        s,
        '    private BossEnergyService BossEnergy = null!;\n    private ChaChaBossFormService ChaChaBossForm = null!;\n',
        '    private BossEnergyService BossEnergy = null!;\n    private ChaChaBossFormService ChaChaBossForm = null!;\n    private ChaChaSkillService ChaChaSkills = null!;\n',
        'ModEntry skill field'
    )
if 'this.ChaChaSkills = new ChaChaSkillService' not in s:
    s = replace_once(
        s,
        '''        this.WorldActors = new WorldActorService(this.Monitor);\n        this.ChaChaBossForm = new ChaChaBossFormService(\n''',
        '''        this.WorldActors = new WorldActorService(this.Monitor);\n        this.ChaChaSkills = new ChaChaSkillService(helper, this.Monitor, this.Save, this.WorldActors);\n        StaticChaChaSkills = this.ChaChaSkills;\n        this.ChaChaBossForm = new ChaChaBossFormService(\n''',
        'ModEntry skill construction'
    )

# Hook events once.
if 'this.ChaChaSkills.OnRenderedWorld' not in s:
    s = replace_once(s, '        helper.Events.Display.RenderedWorld += this.Story.OnRenderedWorld;\n', '        helper.Events.Display.RenderedWorld += this.Story.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.ChaChaSkills.OnRenderedWorld;\n', 'skill render hook')
if 'this.ChaChaSkills.OnButtonPressed' not in s:
    s = replace_once(s, '        helper.Events.Input.ButtonPressed += this.Story.OnButtonPressed;\n', '        helper.Events.Input.ButtonPressed += this.Story.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.ChaChaSkills.OnButtonPressed;\n', 'skill input hook')
if 'this.ChaChaSkills.OnWarped' not in s:
    s = replace_once(s, '        helper.Events.Player.Warped += this.Story.OnWarped;\n', '        helper.Events.Player.Warped += this.Story.OnWarped;\n        helper.Events.Player.Warped += this.ChaChaSkills.OnWarped;\n', 'skill warp hook')
if 'this.ChaChaSkills.OnReturnedToTitle' not in s:
    s = replace_once(s, '        helper.Events.GameLoop.ReturnedToTitle += this.OnReturnedToTitle;\n', '        helper.Events.GameLoop.ReturnedToTitle += this.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.ChaChaSkills.OnReturnedToTitle;\n', 'skill title hook')

if 'cardcha_chacha_skill_unlock' not in s:
    s = replace_once(
        s,
        '''        helper.ConsoleCommands.Add("cardcha_chacha_boss_status", "Show ChaCha Boss Form runtime state.", this.CommandChaChaBossStatus);\n''',
        '''        helper.ConsoleCommands.Add("cardcha_chacha_boss_status", "Show ChaCha Boss Form runtime state.", this.CommandChaChaBossStatus);\n        helper.ConsoleCommands.Add("cardcha_chacha_skill_unlock", "TEST ONLY: discover the Region I ChaCha skill.", this.CommandChaChaSkillUnlock);\n        helper.ConsoleCommands.Add("cardcha_chacha_skill_level", "TEST ONLY: set the Region I ChaCha skill level 1-5 without spending Magic Dust.", this.CommandChaChaSkillLevel);\n        helper.ConsoleCommands.Add("cardcha_chacha_skill_cast", "TEST ONLY: replay the normal-form ChaCha skill cast visual.", this.CommandChaChaSkillCast);\n        helper.ConsoleCommands.Add("cardcha_chacha_skill_status", "Show persistent ChaCha normal-form skill state.", this.CommandChaChaSkillStatus);\n''',
        'skill commands registration'
    )

if 'private void CommandChaChaSkillUnlock' not in s:
    anchor = '''    private void CommandChaChaBossStatus(string command, string[] args)\n    {\n        this.Monitor.Log("===== CHACHA BOSS FORM =====\\n" + this.ChaChaBossForm.Describe(), LogLevel.Alert);\n    }\n\n'''
    addition = '''    private void CommandChaChaBossStatus(string command, string[] args)\n    {\n        this.Monitor.Log("===== CHACHA BOSS FORM =====\\n" + this.ChaChaBossForm.Describe(), LogLevel.Alert);\n    }\n\n    private void CommandChaChaSkillUnlock(string command, string[] args)\n    {\n        if (!Context.IsWorldReady)\n        {\n            this.Monitor.Log("Load a save before testing ChaCha skills.", LogLevel.Warn);\n            return;\n        }\n        if (!this.Save.Data.ChaChaLoaned)\n        {\n            this.Monitor.Log("ChaCha has not joined the player yet; normal-form skills stay story-gated.", LogLevel.Warn);\n            return;\n        }\n\n        bool fresh = this.ChaChaSkills.DiscoverVitalSkill(showPresentation: true);\n        this.Monitor.Log(fresh ? "TEST: discovered Region I ChaCha skill." : "TEST: Region I ChaCha skill was already discovered.", LogLevel.Alert);\n    }\n\n    private void CommandChaChaSkillLevel(string command, string[] args)\n    {\n        if (!Context.IsWorldReady)\n            return;\n        int level = args.Length > 0 && int.TryParse(args[0], out int parsed) ? Math.Clamp(parsed, 1, ChaChaSkillService.MaxSkillLevel) : 1;\n        if (!this.ChaChaSkills.DebugSetLevel(ChaChaSkillService.VitalSkillId, level))\n        {\n            this.Monitor.Log("Discover the Region I ChaCha skill first. Use cardcha_chacha_skill_unlock for TEST.", LogLevel.Warn);\n            return;\n        }\n        this.Monitor.Log($"TEST: Region I ChaCha skill set to Lv {level}/{ChaChaSkillService.MaxSkillLevel}. No Magic Dust was spent; balance is not locked yet.", LogLevel.Alert);\n    }\n\n    private void CommandChaChaSkillCast(string command, string[] args)\n    {\n        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned)\n            return;\n        this.ChaChaSkills.TriggerCastPresentation();\n        this.Monitor.Log("TEST: replayed ChaCha normal-form skill cast visual. No healing value is applied in this foundation.", LogLevel.Alert);\n    }\n\n    private void CommandChaChaSkillStatus(string command, string[] args)\n    {\n        this.Monitor.Log("===== CHACHA NORMAL-FORM SKILLS =====\\n" + this.ChaChaSkills.Describe(), LogLevel.Alert);\n    }\n\n'''
    s = replace_once(s, anchor, addition, 'skill command methods')

# Fix stale .4.14.4 debug copy and bump version strings.
s = s.replace(
    'ChaCha Boss Form TEST primed to 100 Boss Energy. Use the flashing button or Select/View x3.',
    'ChaCha Boss Form TEST primed to 100 ChaCha Energy. Use controller Confirm+Deselect (Switch B+Y), Left Shift+A, or click the READY ChaCha Energy bar.'
)
s = re.sub(r'Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14\.4\.1 CHACHA ENERGY AURA \+ CHORD TEST', f'Cardcha! v{VERSION} CHACHA SKILL FOUNDATION TEST', s)
write('ModEntry.cs', s)


# -----------------------------------------------------------------------------
# i18n: map-source skill UI; no made-up heal/cost numbers.
# -----------------------------------------------------------------------------
strings = {
    'default.json': {
        'resonance.ability.region1.source': 'REGION I • Lv 0–20',
        'resonance.ability.region.source': 'REGION {{region}} • Future map',
        'resonance.ability.future-name': 'Skill not designed yet',
        'resonance.ability.region.future': 'Reserved for the Region {{region}} exploration skill.',
        'resonance.ability.not-designed': 'Effect and balance intentionally not designed yet.',
        'resonance.ability.normal-form': 'Normal-form passive • ChaCha visibly casts when triggered.',
        'resonance.ability.vital.name': 'Vital Blessing',
        'resonance.ability.vital.level': 'Lv {{level}}/{{max}} • Upgraded with Magic Dust',
        'resonance.ability.vital.find-region1': 'Find this skill while exploring Region I.',
        'resonance.ability.vital.active': 'ACTIVE • Normal-form support',
        'resonance.ability.vital.select': 'Select to use this normal-form skill.',
        'resonance.ability.vital.equipped': 'Vital Blessing equipped. Healing values/costs are still waiting for the approved balance table.',
        'chacha.skill.vital.found': 'ChaCha discovered Vital Blessing! The normal-form skill has been equipped.',
        'chacha.skill.vital.already': 'ChaCha already knows Vital Blessing.',
    },
    'vi.json': {
        'resonance.ability.region1.source': 'KHU VỰC I • Lv 0–20',
        'resonance.ability.region.source': 'KHU VỰC {{region}} • Map tương lai',
        'resonance.ability.future-name': 'Kỹ năng chưa thiết kế',
        'resonance.ability.region.future': 'Dành cho kỹ năng khám phá ở Khu Vực {{region}}.',
        'resonance.ability.not-designed': 'Hiệu ứng và cân bằng chưa được thiết kế.',
        'resonance.ability.normal-form': 'Passive form thường • ChaCha sẽ hiện hiệu ứng cast khi kích hoạt.',
        'resonance.ability.vital.name': 'Phúc Lành Sinh Khí',
        'resonance.ability.vital.level': 'Lv {{level}}/{{max}} • Nâng bằng Bụi Ma Thuật',
        'resonance.ability.vital.find-region1': 'Tìm kỹ năng này khi khám phá Khu Vực I.',
        'resonance.ability.vital.active': 'ĐANG DÙNG • Hỗ trợ form thường',
        'resonance.ability.vital.select': 'Chọn để dùng kỹ năng form thường này.',
        'resonance.ability.vital.equipped': 'Đã dùng Phúc Lành Sinh Khí. Chỉ số hồi máu/chi phí đang chờ bảng cân bằng đã chốt.',
        'chacha.skill.vital.found': 'ChaCha đã tìm thấy Phúc Lành Sinh Khí! Kỹ năng form thường đã được trang bị.',
        'chacha.skill.vital.already': 'ChaCha đã biết Phúc Lành Sinh Khí rồi.',
    }
}
for lang, updates in strings.items():
    p = ROOT / 'i18n' / lang
    obj = json.loads(p.read_text(encoding='utf-8'))
    obj.update(updates)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(f'Applied ChaCha skill discovery foundation {VERSION}, schema {SCHEMA}')

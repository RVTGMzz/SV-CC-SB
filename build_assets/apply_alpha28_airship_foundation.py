from pathlib import Path
import json

ROOT = Path('src/Cardcha')
OLD = '0.3.0-alpha.27.0.7.9.0'
NEW = '0.3.0-alpha.28.0.1.0'


def replace_once(path: Path, old: str, new: str):
    text = path.read_text(encoding='utf-8')
    if new in text and old not in text:
        return
    if old not in text:
        raise RuntimeError(f'Expected marker not found in {path}: {old[:120]!r}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


def insert_once(path: Path, marker: str, insertion: str, sentinel: str):
    text = path.read_text(encoding='utf-8')
    if sentinel in text:
        return
    if marker not in text:
        raise RuntimeError(f'Insert marker not found in {path}: {marker[:120]!r}')
    path.write_text(text.replace(marker, insertion + marker, 1), encoding='utf-8')


# Version sync.
for rel in ['Cardcha.csproj', 'Directory.Build.targets', 'manifest.json', 'ModEntry.cs']:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    if OLD in text:
        p.write_text(text.replace(OLD, NEW), encoding='utf-8')

# Save data/schema.
save_data = ROOT / 'Models/SaveData.cs'
text = save_data.read_text(encoding='utf-8')
text = text.replace('public int SchemaVersion { get; set; } = 14;', 'public int SchemaVersion { get; set; } = 15;')
if 'public bool AirshipFlybySeen' not in text:
    marker = '    public string LastStateFingerprint { get; set; } = "";\n'
    addition = '''    // alpha.28 — Cardcha-owned Airship progression.\n    public bool AirshipFlybySeen { get; set; }\n    public bool AirshipUnlocked { get; set; }\n    public int AirshipUnlockedDay { get; set; } = -1;\n    public int AirshipHighestRegionUnlocked { get; set; }\n\n'''
    if marker not in text:
        raise RuntimeError('SaveData insertion marker missing')
    text = text.replace(marker, addition + marker, 1)
save_data.write_text(text, encoding='utf-8')

save_service = ROOT / 'Services/SaveService.cs'
text = save_service.read_text(encoding='utf-8')
text = text.replace('private const int CurrentSchemaVersion = 14;', 'private const int CurrentSchemaVersion = 15;')
if 'Alpha.28 Airship migration' not in text:
    marker = '        if (loadedSchema < CurrentSchemaVersion)\n'
    block = '''        // v15: Airship foundation. Existing saves that already completed the MiMi/Wizard\n        // handoff receive Region I access immediately instead of replaying onboarding.\n        if (loadedSchema < 15)\n        {\n            if (this.Data.MimiMeetupCompleted || this.Data.MachineDelivered || this.Data.BinderUnlocked)\n            {\n                this.Data.AirshipUnlocked = true;\n                this.Data.AirshipHighestRegionUnlocked = Math.Max(1, this.Data.AirshipHighestRegionUnlocked);\n                if (this.Data.AirshipUnlockedDay < 0)\n                    this.Data.AirshipUnlockedDay = Game1.Date.TotalDays;\n            }\n        }\n\n'''
    if marker not in text:
        raise RuntimeError('SaveService migration marker missing')
    text = text.replace(marker, block + marker, 1)
if 'this.Data.AirshipHighestRegionUnlocked = Math.Clamp' not in text:
    marker = '        this.Data.DuplicatePullStreak = Math.Max(0, this.Data.DuplicatePullStreak);\n\n'
    extra = '''        this.Data.AirshipHighestRegionUnlocked = Math.Clamp(this.Data.AirshipHighestRegionUnlocked, 0, 4);\n        this.Data.AirshipUnlockedDay = Math.Max(-1, this.Data.AirshipUnlockedDay);\n\n'''
    if marker not in text:
        raise RuntimeError('SaveService normalize marker missing')
    text = text.replace(marker, marker + extra, 1)
if 'data.AirshipFlybySeen ? 1 : 0' not in text:
    marker = '            data.PortableMachineGifted ? 1 : 0\n'
    repl = '''            data.PortableMachineGifted ? 1 : 0,\n            data.AirshipFlybySeen ? 1 : 0,\n            data.AirshipUnlocked ? 1 : 0,\n            data.AirshipUnlockedDay,\n            data.AirshipHighestRegionUnlocked\n'''
    if marker not in text:
        raise RuntimeError('SaveService fingerprint marker missing')
    text = text.replace(marker, repl, 1)
save_service.write_text(text, encoding='utf-8')

# Story progression unlock at the existing MiMi/Wizard handoff.
progression = ROOT / 'Services/ProgressionService.cs'
text = progression.read_text(encoding='utf-8')
if 'this.Save.Data.AirshipUnlocked = true;' not in text:
    marker = '            this.Save.Data.ChaChaLoaned = true;\n'
    addition = '''            this.Save.Data.AirshipUnlocked = true;\n            this.Save.Data.AirshipHighestRegionUnlocked = Math.Max(1, this.Save.Data.AirshipHighestRegionUnlocked);\n            if (this.Save.Data.AirshipUnlockedDay < 0)\n                this.Save.Data.AirshipUnlockedDay = Game1.Date.TotalDays;\n'''
    if marker not in text:
        raise RuntimeError('Progression existing-machine marker missing')
    text = text.replace(marker, marker + addition, 1)

    marker2 = '        this.Save.Data.MimiMerchantUnlockedDay = Game1.Date.TotalDays;\n\n'
    addition2 = '''        this.Save.Data.AirshipUnlocked = true;\n        this.Save.Data.AirshipHighestRegionUnlocked = Math.Max(1, this.Save.Data.AirshipHighestRegionUnlocked);\n        this.Save.Data.AirshipUnlockedDay = Game1.Date.TotalDays;\n\n'''
    if marker2 not in text:
        raise RuntimeError('Progression meetup marker missing')
    text = text.replace(marker2, marker2 + addition2, 1)

if 'airship.unlocked' not in text:
    marker = '        this.Save.Save();\n\n        this.Monitor.Log(\n            "Cardcha Story Chapter 1 handoff completed: MiMi introduced the player and the Wizard delivered the Machine + Binder.",\n'
    replacement = '''        this.Save.Save();\n        Game1.showGlobalMessage(this.Helper.Translation.Get("airship.unlocked").ToString());\n\n        this.Monitor.Log(\n            "Cardcha Story Chapter 1 handoff completed: MiMi introduced the player, the Wizard delivered the Machine + Binder, and Region I Airship access was unlocked.",\n'''
    if marker not in text:
        raise RuntimeError('Progression unlock message marker missing')
    text = text.replace(marker, replacement, 1)
progression.write_text(text, encoding='utf-8')

# ModEntry wiring.
mod = ROOT / 'ModEntry.cs'
text = mod.read_text(encoding='utf-8')
if 'private AirshipFoundationService Airship' not in text:
    text = text.replace(
        '    private PortableMachineService PortableMachine = null!;\n',
        '    private PortableMachineService PortableMachine = null!;\n    private AirshipFoundationService Airship = null!;\n',
        1
    )
if 'this.Airship = new AirshipFoundationService' not in text:
    text = text.replace(
        '        this.AtticVisual = new MimiAtticVisualService(helper, this.Save);\n',
        '        this.AtticVisual = new MimiAtticVisualService(helper, this.Save);\n        this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save);\n',
        1
    )
if 'this.Airship.OnAssetRequested' not in text:
    text = text.replace(
        '        helper.Events.Content.AssetRequested += this.AtticVisual.OnAssetRequested;\n',
        '        helper.Events.Content.AssetRequested += this.AtticVisual.OnAssetRequested;\n        helper.Events.Content.AssetRequested += this.Airship.OnAssetRequested;\n',
        1
    )
if 'this.Airship.OnRenderedWorld' not in text:
    text = text.replace(
        '        helper.Events.Display.RenderedWorld += this.AtticVisual.OnRenderedWorld;\n',
        '        helper.Events.Display.RenderedWorld += this.AtticVisual.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.Airship.OnRenderedWorld;\n',
        1
    )
if 'this.Airship.OnButtonPressed' not in text:
    text = text.replace(
        '        helper.Events.Input.ButtonPressed += this.PortableMachine.OnButtonPressed;\n',
        '        helper.Events.Input.ButtonPressed += this.PortableMachine.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.Airship.OnButtonPressed;\n',
        1
    )
if 'cardcha_test_airship' not in text:
    text = text.replace(
        '        helper.ConsoleCommands.Add("cardcha_test_attic", "TEST ONLY: toggle direct MiMi attic access without changing friendship/story progression.", this.CommandTestAttic);\n',
        '        helper.ConsoleCommands.Add("cardcha_test_attic", "TEST ONLY: toggle direct MiMi attic access without changing friendship/story progression.", this.CommandTestAttic);\n        helper.ConsoleCommands.Add("cardcha_airship_status", "Show alpha.28 Airship foundation state.", this.CommandAirshipStatus);\n        helper.ConsoleCommands.Add("cardcha_test_airship", "TEST ONLY: toggle direct Airship deck access without changing story progression.", this.CommandTestAirship);\n        helper.ConsoleCommands.Add("cardcha_test_airship_flyby", "TEST ONLY: replay the pre-MiMi Farm Airship flyby without changing save progression.", this.CommandTestAirshipFlyby);\n',
        1
    )
if 'this.Airship.OnSaveLoaded();' not in text:
    text = text.replace('        this.PortableMachine.OnSaveLoaded();\n', '        this.PortableMachine.OnSaveLoaded();\n        this.Airship.OnSaveLoaded();\n', 1)
if 'this.Airship.OnDayStarted();' not in text:
    text = text.replace('        this.Progression.OnDayStarted();\n', '        this.Progression.OnDayStarted();\n        this.Airship.OnDayStarted();\n', 1)
if 'this.Airship.OnUpdateTicked(e);' not in text:
    text = text.replace('        this.Social.OnUpdateTicked(e);\n', '        this.Social.OnUpdateTicked(e);\n        this.Airship.OnUpdateTicked(e);\n', 1)
if 'this.Airship.OnReturnedToTitle();' not in text:
    text = text.replace('        this.Home.OnReturnedToTitle();\n', '        this.Home.OnReturnedToTitle();\n        this.Airship.OnReturnedToTitle();\n', 1)
if 'this.Airship.Describe()' not in text:
    text = text.replace(
        '            this.Home.Describe() + "\\n" +\n            this.PortableMachine.Describe(),\n',
        '            this.Home.Describe() + "\\n" +\n            this.PortableMachine.Describe() + "\\n" +\n            this.Airship.Describe(),\n',
        1
    )
if 'private void CommandAirshipStatus' not in text:
    marker = '    private void CommandVersion(string command, string[] args)\n'
    methods = '''    private void CommandAirshipStatus(string command, string[] args)\n    {\n        this.Monitor.Log("===== CARDCHA AIRSHIP STATUS =====\\n" + this.Airship.Describe(), LogLevel.Alert);\n    }\n\n    private void CommandTestAirship(string command, string[] args)\n    {\n        this.Monitor.Log(this.Airship.DebugToggleDeck(), LogLevel.Alert);\n    }\n\n    private void CommandTestAirshipFlyby(string command, string[] args)\n    {\n        this.Monitor.Log(this.Airship.DebugReplayFlyby(), LogLevel.Alert);\n    }\n\n'''
    if marker not in text:
        raise RuntimeError('ModEntry command insertion marker missing')
    text = text.replace(marker, methods + marker, 1)
text = text.replace('ATTIC ACCEPTANCE POLISH TEST', 'AIRSHIP FOUNDATION TEST')
mod.write_text(text, encoding='utf-8')

# Localization.
translations = {
    'default.json': {
        'airship.unlocked': 'MiMi has granted you access to the Cardcha Airship. Region I is now available.',
        'airship.deck.unavailable': 'The Airship route is unstable right now. Try again after reloading the day.',
        'airship.route.region1.foundation': 'REGION I // Route survey in progress. Your Binder currently resonates with {{cards}} unique cards. The hunting grounds and 20-card Boss Gate are the next construction step.',
        'airship.route.locked': 'The route console is still dormant.'
    },
    'vi.json': {
        'airship.unlocked': 'MiMi đã cho bạn quyền sử dụng Tàu Bay Cardcha. Khu Vực I đã được mở.',
        'airship.deck.unavailable': 'Tuyến Tàu Bay đang không ổn định. Hãy thử lại sau khi tải lại ngày.',
        'airship.route.region1.foundation': 'KHU VỰC I // Tuyến đường đang được khảo sát. Binder của bạn hiện cộng hưởng với {{cards}} lá bài khác nhau. Khu săn quái và Cổng Boss 20 lá sẽ được xây ở bước tiếp theo.',
        'airship.route.locked': 'Bảng điều khiển tuyến đường vẫn chưa hoạt động.'
    }
}
for filename, additions in translations.items():
    path = ROOT / 'i18n' / filename
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(additions)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print('alpha.28.0.1.0 Airship foundation patch applied')

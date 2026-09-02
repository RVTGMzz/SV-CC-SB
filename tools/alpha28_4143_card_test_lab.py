from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.3'


def replace_once(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'Missing patch anchor: {old[:120]!r}')
    return text.replace(old, new, 1)


# manifest.json
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Cardcha.csproj
csproj_path = ROOT / 'Cardcha.csproj'
csproj = csproj_path.read_text(encoding='utf-8')
csproj = re.sub(r'<Version>[^<]+</Version>', f'<Version>{VERSION}</Version>', csproj, count=1)
csproj_path.write_text(csproj, encoding='utf-8')

# Directory.Build.targets
build_targets_path = ROOT / 'Directory.Build.targets'
build_targets = f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .4.14.3 Card Test Lab is materialized by CI before compilation.\n       Keep this hook version-only so repeated local builds cannot reapply source patches. -->\n  <Target Name="CardchaAlpha2804143Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n'''
build_targets_path.write_text(build_targets, encoding='utf-8')

# ModEntry.cs
entry_path = ROOT / 'ModEntry.cs'
entry = entry_path.read_text(encoding='utf-8')
entry = replace_once(
    entry,
    '    private AirshipFoundationService Airship = null!;\n',
    '    private AirshipFoundationService Airship = null!;\n    private CardTestLabService CardLab = null!;\n'
)
entry = replace_once(
    entry,
    '        this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save, this.Controller);\n',
    '        this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save, this.Controller);\n        this.CardLab = new CardTestLabService(this.Cards, this.Save, this.Combat);\n'
)
entry = replace_once(
    entry,
    '        helper.ConsoleCommands.Add("cardcha_test_airship_flyby", "TEST ONLY: replay the pre-MiMi Farm Airship flyby without changing save progression.", this.CommandTestAirshipFlyby);\n',
    '        helper.ConsoleCommands.Add("cardcha_test_airship_flyby", "TEST ONLY: replay the pre-MiMi Farm Airship flyby without changing save progression.", this.CommandTestAirshipFlyby);\n        helper.ConsoleCommands.Add("cardcha_card_test", "TEST ONLY: open the visual 76-card Card Test Lab.", this.CommandCardTest);\n'
)
entry = replace_once(
    entry,
    '        this.Airship.OnReturnedToTitle();\n        this.Save.Clear();\n',
    '        this.Airship.OnReturnedToTitle();\n        this.CardLab.EndSession();\n        this.Save.Clear();\n'
)
entry = replace_once(
    entry,
    '    private void CommandVersion(string command, string[] args)\n',
    '''    private void CommandCardTest(string command, string[] args)\n    {\n        if (!Context.IsWorldReady)\n        {\n            this.Monitor.Log("Load a save before opening Card Test Lab.", LogLevel.Warn);\n            return;\n        }\n\n        if (Game1.activeClickableMenu is not null)\n        {\n            this.Monitor.Log("Close the current menu first, then run cardcha_card_test again.", LogLevel.Warn);\n            return;\n        }\n\n        Game1.activeClickableMenu = new CardTestLabMenu(this.CardLab, this.Renderer);\n        this.Monitor.Log("Card Test Lab opened. Temporary test loadout will be restored when the Lab closes.", LogLevel.Alert);\n    }\n\n    private void CommandVersion(string command, string[] args)\n'''
)
entry = entry.replace(
    'Cardcha! v0.3.0-alpha.28.0.4.14.2 CARD RUNTIME AUDIT TEST',
    f'Cardcha! v{VERSION} CARD TEST LAB TEST'
)
entry_path.write_text(entry, encoding='utf-8')

print(f'Applied {VERSION} Card Test Lab finalizer')

from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.3.1'


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
build_targets = f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .4.14.3.1 Card Test Lab UX is materialized by CI before compilation.\n       Keep this hook version-only so repeated local builds cannot reapply source patches. -->\n  <Target Name="CardchaAlpha28041431Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n'''
build_targets_path.write_text(build_targets, encoding='utf-8')

# ModEntry.cs
entry_path = ROOT / 'ModEntry.cs'
entry = entry_path.read_text(encoding='utf-8')

if '    private CardTestLabService CardLab = null!;\n' not in entry:
    entry = replace_once(
        entry,
        '    private AirshipFoundationService Airship = null!;\n',
        '    private AirshipFoundationService Airship = null!;\n    private CardTestLabService CardLab = null!;\n'
    )

if '        this.CardLab = new CardTestLabService(this.Cards, this.Save, this.Combat);\n' not in entry:
    entry = replace_once(
        entry,
        '        this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save, this.Controller);\n',
        '        this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save, this.Controller);\n        this.CardLab = new CardTestLabService(this.Cards, this.Save, this.Combat);\n'
    )

if 'helper.ConsoleCommands.Add("cardcha_card_test"' not in entry:
    entry = replace_once(
        entry,
        '        helper.ConsoleCommands.Add("cardcha_test_airship_flyby", "TEST ONLY: replay the pre-MiMi Farm Airship flyby without changing save progression.", this.CommandTestAirshipFlyby);\n',
        '        helper.ConsoleCommands.Add("cardcha_test_airship_flyby", "TEST ONLY: replay the pre-MiMi Farm Airship flyby without changing save progression.", this.CommandTestAirshipFlyby);\n        helper.ConsoleCommands.Add("cardcha_card_test", "TEST ONLY: open/reopen the visual 76-card Card Test Lab.", this.CommandCardTest);\n'
    )

if '    private void CommandCardTest(string command, string[] args)\n' not in entry:
    entry = replace_once(
        entry,
        '    private void CommandVersion(string command, string[] args)\n',
        '''    private void CommandCardTest(string command, string[] args)\n    {\n        if (!Context.IsWorldReady)\n        {\n            this.Monitor.Log("Load a save before opening Card Test Lab.", LogLevel.Warn);\n            return;\n        }\n\n        if (Game1.activeClickableMenu is not null)\n        {\n            this.Monitor.Log("Close the current menu first, then run cardcha_card_test again.", LogLevel.Warn);\n            return;\n        }\n\n        Game1.activeClickableMenu = new CardTestLabMenu(this.CardLab, this.Renderer);\n        this.Monitor.Log("Card Test Lab opened. EQUIP/UNEQUIP & PLAY keeps the temporary Lab session active; END LAB restores the real loadout.", LogLevel.Alert);\n    }\n\n    private void CommandVersion(string command, string[] args)\n'''
    )
else:
    entry = entry.replace(
        'Card Test Lab opened. Temporary test loadout will be restored when the Lab closes.',
        'Card Test Lab opened. EQUIP/UNEQUIP & PLAY keeps the temporary Lab session active; END LAB restores the real loadout.'
    )

# Returning to title always restores the temporary Lab snapshot.
if '        this.Airship.OnReturnedToTitle();\n        this.CardLab.EndSession();\n        this.Save.Clear();\n' not in entry:
    entry = replace_once(
        entry,
        '        this.Airship.OnReturnedToTitle();\n        this.Save.Clear();\n',
        '        this.Airship.OnReturnedToTitle();\n        this.CardLab.EndSession();\n        this.Save.Clear();\n'
    )

# Critical save safety: a Lab session can now stay alive while gameplay resumes, so restore the
# real snapshot before any Stardew save is serialized. This deliberately ends the Lab session.
on_saving_old = '''    private void OnSaving(object? sender, SavingEventArgs e)\n    {\n        this.Combat.PrepareForGameSave();\n'''
on_saving_new = '''    private void OnSaving(object? sender, SavingEventArgs e)\n    {\n        this.CardLab.EndSession();\n        this.Combat.PrepareForGameSave();\n'''
entry = replace_once(entry, on_saving_old, on_saving_new)

# Normalize visible version strings without depending on which earlier test suffix is present.
entry = re.sub(
    r'Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14(?:\.\d+)* [A-Z0-9 ]+ TEST',
    f'Cardcha! v{VERSION} CARD TEST LAB UX TEST',
    entry
)
entry_path.write_text(entry, encoding='utf-8')

# Menu compatibility + responsive vertical spacing.
menu_path = ROOT / 'UI/CardTestLabMenu.cs'
menu = menu_path.read_text(encoding='utf-8')
menu = menu.replace('    public override void cleanupBeforeExit()\n', '    protected override void cleanupBeforeExit()\n', 1)
menu = menu.replace(
    'b.Draw(Game1.fadeToBlackRect, Game1.uiViewport.Bounds, Color.Black * 0.72f);',
    'b.Draw(Game1.fadeToBlackRect, new Microsoft.Xna.Framework.Rectangle(0, 0, Game1.uiViewport.Width, Game1.uiViewport.Height), Color.Black * 0.72f);'
)
menu = menu.replace(
    'b.Draw(Game1.fadeToBlackRect, Game1.uiViewport, Color.Black * 0.72f);',
    'b.Draw(Game1.fadeToBlackRect, new Microsoft.Xna.Framework.Rectangle(0, 0, Game1.uiViewport.Width, Game1.uiViewport.Height), Color.Black * 0.72f);'
)
menu = menu.replace('Rectangle descriptionArea = new(panel.X + 20, panel.Y + 170, panel.Width - 40, 86);', 'Rectangle descriptionArea = new(panel.X + 20, panel.Y + 168, panel.Width - 40, 68);')
menu = menu.replace('new Vector2(panel.X + 20, panel.Y + 266)', 'new Vector2(panel.X + 20, panel.Y + 244)')
menu = menu.replace('Rectangle instructionArea = new(panel.X + 20, panel.Y + 300, panel.Width - 40, 102);', 'Rectangle instructionArea = new(panel.X + 20, panel.Y + 278, panel.Width - 40, 74);')
menu = menu.replace('new Vector2(panel.X + 20, panel.Y + 410)', 'new Vector2(panel.X + 20, panel.Y + 360)')
menu = menu.replace('Rectangle telemetryArea = new(panel.X + 20, panel.Y + 446, panel.Width - 40, Math.Max(70, panel.Bottom - (panel.Y + 460)));', 'Rectangle telemetryArea = new(panel.X + 20, panel.Y + 396, panel.Width - 40, Math.Max(70, panel.Bottom - (panel.Y + 408)));')
menu_path.write_text(menu, encoding='utf-8')

print(f'Applied {VERSION} Card Test Lab UX finalizer')

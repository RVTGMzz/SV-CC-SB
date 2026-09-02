from pathlib import Path
import re

p = Path('src/Cardcha/ModEntry.cs')
s = p.read_text(encoding='utf-8')
VERSION = '0.3.0-alpha.28.0.4.14.3.3'

def once(old, new):
    global s
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'missing anchor: {old[:120]!r}')
    s = s.replace(old, new, 1)

once(
    '    private CardTestLabService CardLab = null!;\n',
    '    private CardTestLabService CardLab = null!;\n    private CardTestArenaService CardArena = null!;\n    private CardTestLabOverlayService CardLabOverlay = null!;\n'
)
once(
    '        this.CardLab = new CardTestLabService(this.Cards, this.Save, this.Combat);\n',
    '        this.CardLab = new CardTestLabService(this.Cards, this.Save, this.Combat);\n        this.CardArena = new CardTestArenaService(helper, this.Monitor, this.CardLab);\n        this.CardLabOverlay = new CardTestLabOverlayService(helper, this.CardLab, this.CardArena, this.OpenCardTestLab, this.EndCardTestLabSession);\n'
)
once(
    '        helper.Events.Content.AssetRequested += this.Airship.OnAssetRequested;\n',
    '        helper.Events.Content.AssetRequested += this.Airship.OnAssetRequested;\n        helper.Events.Content.AssetRequested += this.CardArena.OnAssetRequested;\n'
)
once(
    '        helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;\n',
    '        helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;\n        helper.Events.GameLoop.SaveLoaded += this.CardArena.OnSaveLoaded;\n'
)
once(
    '        helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;\n',
    '        helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;\n        helper.Events.GameLoop.UpdateTicked += this.CardArena.OnUpdateTicked;\n'
)
once(
    '        helper.Events.GameLoop.ReturnedToTitle += this.OnReturnedToTitle;\n',
    '        helper.Events.GameLoop.ReturnedToTitle += this.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.CardArena.OnReturnedToTitle;\n'
)
once(
    '        helper.Events.Display.RenderedHud += this.OnRenderedHud;\n',
    '        helper.Events.Display.RenderedHud += this.OnRenderedHud;\n        helper.Events.Display.RenderedHud += this.CardLabOverlay.OnRenderedHud;\n'
)
once(
    '        helper.Events.Input.ButtonPressed += this.Airship.OnButtonPressed;\n',
    '        helper.Events.Input.ButtonPressed += this.Airship.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.CardLabOverlay.OnButtonPressed;\n'
)
once(
    '        helper.Events.Player.Warped += this.Airship.OnWarped;\n',
    '        helper.Events.Player.Warped += this.Airship.OnWarped;\n        helper.Events.Player.Warped += this.CardArena.OnWarped;\n'
)
if 'cardcha_card_test_stop' not in s:
    once(
        '        helper.ConsoleCommands.Add("cardcha_card_test", "TEST ONLY: open the visual 76-card Card Test Lab.", this.CommandCardTest);\n',
        '        helper.ConsoleCommands.Add("cardcha_card_test", "TEST ONLY: open the visual 76-card Card Test Lab.", this.CommandCardTest);\n        helper.ConsoleCommands.Add("cardcha_card_test_stop", "TEST ONLY: stop Card Test Lab, exit arena, and restore the real loadout.", this.CommandCardTestStop);\n'
    )

s = s.replace('MonsterDamagePatch.Apply(harmony, this.Combat, this.Deaths);', 'MonsterDamagePatch.Apply(harmony, this.Combat, this.Deaths, this.CardArena);')
s = s.replace('FarmerDamagePatch.Apply(harmony, this.Combat);', 'FarmerDamagePatch.Apply(harmony, this.Combat, this.CardArena);')

once(
    '    private void OnSaving(object? sender, SavingEventArgs e)\n    {\n        this.CardLab.EndSession();\n',
    '    private void OnSaving(object? sender, SavingEventArgs e)\n    {\n        this.CardArena.PrepareForSave();\n        this.CardLab.EndSession();\n'
)

s = s.replace(
    '        Game1.activeClickableMenu = new CardTestLabMenu(this.CardLab, this.Renderer);\n        this.Monitor.Log("Card Test Lab opened. EQUIP/UNEQUIP & PLAY keeps the temporary Lab session active; END LAB restores the real loadout.", LogLevel.Alert);',
    '        this.OpenCardTestLab();\n        this.Monitor.Log("Card Test Lab opened. Minimize once, then reopen from CARD LAB tab / F8 / controller right-stick. Arena stays active until END LAB or cardcha_card_test_stop.", LogLevel.Alert);'
)

if '    private void OpenCardTestLab()\n' not in s:
    once(
        '    private void CommandVersion(string command, string[] args)\n',
        '''    private void OpenCardTestLab()\n    {\n        if (!Context.IsWorldReady || Game1.activeClickableMenu is not null)\n            return;\n        Game1.activeClickableMenu = new CardTestLabMenu(this.CardLab, this.Renderer, this.CardArena);\n    }\n\n    private void EndCardTestLabSession()\n    {\n        this.CardArena.ExitArena();\n        this.CardLab.EndSession();\n        if (Game1.activeClickableMenu is CardTestLabMenu)\n            Game1.exitActiveMenu();\n    }\n\n    private void CommandCardTestStop(string command, string[] args)\n    {\n        if (!Context.IsWorldReady)\n            return;\n        this.EndCardTestLabSession();\n        this.Monitor.Log("Card Test Lab stopped. Arena exited and the real loadout was restored.", LogLevel.Alert);\n    }\n\n    private void CommandVersion(string command, string[] args)\n'''
    )

s = re.sub(
    r'Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14(?:\.\d+)* [A-Z0-9 ]+ TEST',
    f'Cardcha! v{VERSION} CARD TEST ARENA TEST',
    s
)
p.write_text(s, encoding='utf-8')
print(f'Applied Card Test Arena ModEntry integration for {VERSION}')

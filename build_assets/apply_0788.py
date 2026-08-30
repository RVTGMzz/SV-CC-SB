from pathlib import Path
import json, re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.8.8'


def set_version(path: Path):
    text = path.read_text()
    text, n = re.subn(r'0\.3\.0-alpha\.27\.0\.7\.8\.\d+', TARGET, text)
    if n == 0 and TARGET not in text:
        raise AssertionError(f'No version replacement in {path}')
    path.write_text(text)


p = ROOT / 'UI/CardchaBinderMenu.cs'
text = p.read_text()

field_marker = '''    private bool ControllerDetailActionLatched;\n    private Buttons ControllerDetailActionButton;\n'''
field_new = '''    private bool ControllerDetailActionLatched;\n    private Buttons ControllerDetailActionButton;\n    // Stardew can synthesize a mouse click at the snapped cursor after receiveGamePadButton.\n    // Favorite/Equip are toggles, so that second path would instantly undo the controller action.\n    // Consume only the matching synthetic click for a very short window; real mouse clicks remain normal.\n    private long SuppressSyntheticDetailClickUntilMs;\n    private int SuppressSyntheticDetailClickActionId = -1;\n'''
if field_new not in text:
    if field_marker not in text:
        raise AssertionError('field marker missing')
    text = text.replace(field_marker, field_new, 1)

old_activate = '''        if (id == FavoriteActionId)\n        {\n            this.ActivateFavoriteAction();\n            return;\n        }\n\n        if (id == EquipActionId)\n        {\n            this.ToggleEquip();\n            return;\n        }\n'''
new_activate = '''        if (id == FavoriteActionId)\n        {\n            if (fromController)\n                this.ArmSyntheticDetailClickSuppression(id);\n            this.ActivateFavoriteAction();\n            return;\n        }\n\n        if (id == EquipActionId)\n        {\n            if (fromController)\n                this.ArmSyntheticDetailClickSuppression(id);\n            this.ToggleEquip();\n            return;\n        }\n'''
if new_activate not in text:
    if old_activate not in text:
        raise AssertionError('favorite/equip activate block missing')
    text = text.replace(old_activate, new_activate, 1)

left_marker = '''    public override void receiveLeftClick(int x, int y, bool playSound = true)\n    {\n        this.LastInputWasController = false;\n'''
left_new = '''    public override void receiveLeftClick(int x, int y, bool playSound = true)\n    {\n        if (this.TryConsumeSyntheticDetailClick(x, y))\n            return;\n\n        this.LastInputWasController = false;\n'''
if left_new not in text:
    if left_marker not in text:
        raise AssertionError('receiveLeftClick marker missing')
    text = text.replace(left_marker, left_new, 1)

helper_marker = '''    private void HandleCollectionActivation(CardDefinition card, bool fromController)\n'''
helpers = '''    private void ArmSyntheticDetailClickSuppression(int actionId)\n    {\n        this.SuppressSyntheticDetailClickActionId = actionId;\n        this.SuppressSyntheticDetailClickUntilMs = Environment.TickCount64 + 220L;\n    }\n\n    private bool TryConsumeSyntheticDetailClick(int x, int y)\n    {\n        if (this.SuppressSyntheticDetailClickActionId < 0)\n            return false;\n\n        long now = Environment.TickCount64;\n        if (now > this.SuppressSyntheticDetailClickUntilMs)\n        {\n            this.SuppressSyntheticDetailClickActionId = -1;\n            this.SuppressSyntheticDetailClickUntilMs = 0L;\n            return false;\n        }\n\n        int hitId = -1;\n        if (Inflate(this.FavoriteActionButton.bounds, 3).Contains(x, y))\n            hitId = FavoriteActionId;\n        else if (Inflate(this.EquipActionButton.bounds, 3).Contains(x, y))\n            hitId = EquipActionId;\n\n        if (hitId != this.SuppressSyntheticDetailClickActionId)\n            return false;\n\n        this.SuppressSyntheticDetailClickActionId = -1;\n        this.SuppressSyntheticDetailClickUntilMs = 0L;\n        return true;\n    }\n\n'''
if 'private void ArmSyntheticDetailClickSuppression' not in text:
    if helper_marker not in text:
        raise AssertionError('helper insertion marker missing')
    text = text.replace(helper_marker, helpers + helper_marker, 1)

p.write_text(text)

for f in [ROOT/'Cardcha.csproj', ROOT/'Directory.Build.targets', ROOT/'ModEntry.cs']:
    set_version(f)
manifest = json.loads((ROOT/'manifest.json').read_text())
manifest['Version'] = TARGET
(ROOT/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

final = p.read_text()
assert 'TryConsumeSyntheticDetailClick(x, y)' in final
assert 'ArmSyntheticDetailClickSuppression(id)' in final
assert 'SuppressSyntheticDetailClickUntilMs' in final
print('0.7.8.8 patch applied')

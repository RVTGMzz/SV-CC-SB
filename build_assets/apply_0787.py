from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.8.7'


def set_version(path: Path) -> None:
    text = path.read_text()
    text, count = re.subn(r'0\.3\.0-alpha\.27\.0\.7\.8\.\d+(?!\.\d)', TARGET, text)
    if count == 0 and TARGET not in text:
        raise AssertionError(f'could not update version in {path}')
    path.write_text(text)


def patch_binder() -> None:
    path = ROOT / 'UI/CardchaBinderMenu.cs'
    text = path.read_text()

    field_marker = '    private bool LastInputWasController;\n'
    field_block = '''    private bool LastInputWasController;\n    // Some controller runtimes can report the same physical Confirm press more than once while\n    // the button is still held. Toggle actions must therefore stay latched until that button is\n    // physically released, otherwise Favorite/Equip execute twice and immediately undo themselves.\n    private bool ControllerDetailActionLatched;\n    private Buttons ControllerDetailActionButton;\n'''
    if 'private bool ControllerDetailActionLatched;' not in text:
        if field_marker not in text:
            raise AssertionError('controller field marker not found')
        text = text.replace(field_marker, field_block, 1)

    receive_marker = '    public override void receiveGamePadButton(Buttons b)\n'
    helper = '''    public override void update(GameTime time)\n    {\n        base.update(time);\n\n        if (this.ControllerDetailActionLatched\n            && !IsGamePadButtonHeld(this.ControllerDetailActionButton))\n        {\n            this.ControllerDetailActionLatched = false;\n        }\n    }\n\n    private static bool IsGamePadButtonHeld(Buttons button)\n    {\n        foreach (PlayerIndex playerIndex in new[] { PlayerIndex.One, PlayerIndex.Two, PlayerIndex.Three, PlayerIndex.Four })\n        {\n            if (GamePad.GetState(playerIndex).IsButtonDown(button))\n                return true;\n        }\n\n        return false;\n    }\n\n'''
    if 'private static bool IsGamePadButtonHeld(Buttons button)' not in text:
        if receive_marker not in text:
            raise AssertionError('receiveGamePadButton marker not found')
        text = text.replace(receive_marker, helper + receive_marker, 1)

    old = '''        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n        if (collectionFocused)\n            this.CaptureControllerActionTarget(focusedId);\n'''
    new = '''        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n        if (collectionFocused)\n            this.CaptureControllerActionTarget(focusedId);\n\n        // One physical Confirm press must produce exactly one detail action. In affected runtimes\n        // the same held press can reach receiveGamePadButton twice, which is especially visible on\n        // toggles: Equip -> Unequip and Favorite -> Unfavorite in the same press. Keep the first\n        // event and ignore repeats until the physical button is released.\n        if (this.Controller.IsConfirm(b) && IsDetailActionId(focusedId))\n        {\n            if (this.ControllerDetailActionLatched)\n                return;\n\n            this.ControllerDetailActionLatched = true;\n            this.ControllerDetailActionButton = b;\n        }\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError('controller receive block not found')

    path.write_text(text)


patch_binder()
for p in [ROOT/'Cardcha.csproj', ROOT/'Directory.Build.targets', ROOT/'ModEntry.cs']:
    set_version(p)
manifest = json.loads((ROOT/'manifest.json').read_text())
manifest['Version'] = TARGET
(ROOT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

binder = (ROOT/'UI/CardchaBinderMenu.cs').read_text()
assert 'private bool ControllerDetailActionLatched;' in binder
assert 'private static bool IsGamePadButtonHeld(Buttons button)' in binder
assert 'if (this.ControllerDetailActionLatched)' in binder
assert 'this.ControllerDetailActionButton = b;' in binder
print('0.7.8.7 patch applied')

from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.8.5'
DECOR = 'alpha.27.0.7.8.5'


def set_versions() -> None:
    pattern = r'0\.3\.0-alpha\.27\.0\.7\.(?:7|8)(?:\.\d+)?'
    for rel in ['Cardcha.csproj', 'Directory.Build.targets', 'ModEntry.cs']:
        path = ROOT / rel
        text = path.read_text()
        text, count = re.subn(pattern, TARGET, text)
        if count == 0 and TARGET not in text:
            raise AssertionError(f'Could not update version in {rel}')
        path.write_text(text)

    manifest = ROOT / 'manifest.json'
    data = json.loads(manifest.read_text())
    data['Version'] = TARGET
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    tmx = ROOT / 'assets/mimi_attic.tmx'
    text = tmx.read_text()
    text = re.sub(
        r'CardchaAtticVersion" value="alpha\.27\.0\.7\.(?:7|8)(?:\.\d+)?"',
        f'CardchaAtticVersion" value="{DECOR}"',
        text,
        count=1,
    )
    tmx.write_text(text)


def patch_binder() -> None:
    path = ROOT / 'UI/CardchaBinderMenu.cs'
    text = path.read_text()

    # 0.7.8.4 tried to simulate mouse clicks after rebinding controller-specific target state.
    # That extra state is exactly what let Favorite/Equip drift away from the card shown on the
    # right page. Controller action buttons now call the same core methods as mouse clicks, with
    # Selected as the canonical visible card.
    synthetic = '''        if (fromController && this.LastInputWasController && IsDetailActionId(id))\n        {\n            this.PrepareControllerActionTargetForMousePath();\n            Rectangle action = focused.bounds;\n            this.receiveLeftClick(action.Center.X, action.Center.Y, playSound: true);\n            this.LastInputWasController = true;\n            return;\n        }\n\n'''
    text = text.replace(synthetic, '')

    text = text.replace(
        '''        if (id == EquipActionId)\n        {\n            this.RestoreLockedSelectionForAction();\n            this.ToggleEquip();\n            return;\n        }\n''',
        '''        if (id == EquipActionId)\n        {\n            this.ToggleEquip();\n            return;\n        }\n''',
        1,
    )
    text = text.replace(
        '''        if (id == UpgradeActionId)\n        {\n            this.RestoreLockedSelectionForAction();\n            this.TryUpgradeSelected();\n            return;\n        }\n''',
        '''        if (id == UpgradeActionId)\n        {\n            this.TryUpgradeSelected();\n            return;\n        }\n''',
        1,
    )

    text = text.replace(
        '''        if (Inflate(this.EquipActionButton.bounds, 3).Contains(x, y))\n        {\n            this.RestoreLockedSelectionForAction();\n            this.ToggleEquip();\n            return;\n        }\n''',
        '''        if (Inflate(this.EquipActionButton.bounds, 3).Contains(x, y))\n        {\n            this.ToggleEquip();\n            return;\n        }\n''',
        1,
    )
    text = text.replace(
        '''        if (Inflate(this.UpgradeActionButton.bounds, 3).Contains(x, y))\n        {\n            this.RestoreLockedSelectionForAction();\n            this.TryUpgradeSelected();\n            return;\n        }\n''',
        '''        if (Inflate(this.UpgradeActionButton.bounds, 3).Contains(x, y))\n        {\n            this.TryUpgradeSelected();\n            return;\n        }\n''',
        1,
    )

    old_sync = '''        if (this.ControllerSelectionLocked && this.LockedCard is not null)\n        {\n            // The detail page can stay locked, but Favorite follows the collection card the\n            // controller actually navigated from instead of an older locked selection.\n            this.Selected = this.LockedCard;\n            return;\n        }\n\n        this.Selected = card;\n'''
    new_sync = '''        // Browsing a new collection card must also move the visible/action card. Keeping\n        // Selected frozen on an older LockedCard was the root cause of "first card works, second\n        // card fails" for both Favorite and Equip on controller.\n        this.Selected = card;\n'''
    if old_sync in text:
        text = text.replace(old_sync, new_sync, 1)

    old_target = '''    private CardDefinition? GetFavoriteTargetCard()\n    {\n        if (this.LastInputWasController\n            && IsDetailActionId(this.currentlySnappedComponent?.myID ?? -1)\n            && this.ControllerActionTarget is not null)\n        {\n            return this.ControllerActionTarget;\n        }\n\n        return this.PreviewCard ?? this.Selected ?? this.LockedCard;\n    }\n'''
    new_target = '''    private CardDefinition? GetFavoriteTargetCard()\n        => this.Selected ?? this.PreviewCard ?? this.LockedCard;\n'''
    if old_target not in text and new_target not in text:
        raise AssertionError('Could not locate Favorite target resolver')
    text = text.replace(old_target, new_target, 1)

    # Equip/unequip feedback belongs in the same 3-second toast used by Favorite. Persistent Status
    # text sits directly above the buttons and was visibly colliding with the detail copy.
    text = text.replace(
        '            this.Status = ModEntry.T("binder.status.not-owned");\n            Game1.playSound("cancel");\n            return;\n        }\n\n        if (this.IsStoredEquipped(this.Selected.Id))',
        '            this.ShowFavoriteToast(ModEntry.T("binder.status.not-owned"));\n            Game1.playSound("cancel");\n            return;\n        }\n\n        if (this.IsStoredEquipped(this.Selected.Id))',
        1,
    )
    text = text.replace(
        '                this.Status = ModEntry.T("binder.status.unequipped", new { name = this.Selected.Name });',
        '                this.ShowFavoriteToast(ModEntry.T("binder.status.unequipped", new { name = this.Selected.Name }));',
        1,
    )
    text = text.replace(
        '            this.Status = ModEntry.T("binder.status.equipped", new { name = this.Selected.Name });',
        '            this.ShowFavoriteToast(ModEntry.T("binder.status.equipped", new { name = this.Selected.Name }));',
        1,
    )
    text = text.replace(
        '            this.Status = ModEntry.T("binder.status.full", new { slots = this.UnlockedSlots });',
        '            this.ShowFavoriteToast(ModEntry.T("binder.status.full", new { slots = this.UnlockedSlots }));',
        1,
    )

    path.write_text(text)


def patch_attic() -> None:
    path = ROOT / 'Services/MimiAtticVisualService.cs'
    text = path.read_text()
    text = re.sub(
        r'private const string DecorVersion = "alpha\.27\.0\.7\.(?:7|8)(?:\.\d+)?";',
        f'private const string DecorVersion = "{DECOR}";',
        text,
        count=1,
    )

    # TV is accepted. Only nudge the lower-right patchwork rug a final 8 px left.
    old = 'TryAddFurniture(attic, "(F)1456", 16, 9, pixelOffsetX: -32);'
    new = 'TryAddFurniture(attic, "(F)1456", 16, 9, pixelOffsetX: -40);'
    if old not in text and new not in text:
        raise AssertionError('Could not locate prototype rug offset')
    text = text.replace(old, new, 1)
    path.write_text(text)


def validate() -> None:
    binder = (ROOT / 'UI/CardchaBinderMenu.cs').read_text()
    visual = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()

    assert 'this.PrepareControllerActionTargetForMousePath();' not in binder
    assert 'private CardDefinition? GetFavoriteTargetCard()\n        => this.Selected ?? this.PreviewCard ?? this.LockedCard;' in binder
    assert 'Keeping\n        // Selected frozen on an older LockedCard' in binder
    assert 'this.ShowFavoriteToast(ModEntry.T("binder.status.unequipped"' in binder
    assert 'this.ShowFavoriteToast(ModEntry.T("binder.status.equipped"' in binder
    assert 'this.Status = ModEntry.T("binder.status.unequipped"' not in binder
    assert 'this.Status = ModEntry.T("binder.status.equipped"' not in binder
    assert '"(F)1456", 16, 9, pixelOffsetX: -40' in visual
    assert '"(F)1466", 4, 7, pixelOffsetX: -32' in visual
    assert DECOR in visual
    assert json.loads((ROOT / 'manifest.json').read_text())['Version'] == TARGET


def main() -> None:
    patch_binder()
    patch_attic()
    set_versions()
    validate()
    print('0.7.8.5 controller top actions + transient equip toast + rug nudge applied')


if __name__ == '__main__':
    main()

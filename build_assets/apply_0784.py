from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.8.4'
DECOR = 'alpha.27.0.7.8.4'


def set_versions() -> None:
    pattern = r'0\.3\.0-alpha\.27\.0\.7\.8(?:\.\d+)?'
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
        r'CardchaAtticVersion" value="alpha\.27\.0\.7\.8(?:\.\d+)?"',
        f'CardchaAtticVersion" value="{DECOR}"',
        text,
        count=1,
    )
    tmx.write_text(text)


def patch_binder() -> None:
    path = ROOT / 'UI/CardchaBinderMenu.cs'
    text = path.read_text()

    if 'private CardDefinition? ControllerActionTarget;' not in text:
        anchor = '    private CardDefinition? LockedCard;\n'
        if anchor not in text:
            raise AssertionError('Could not locate LockedCard field')
        text = text.replace(anchor, anchor + '    private CardDefinition? ControllerActionTarget;\n', 1)

    # Replace the 0.7.8.3 Favorite-only controller bridge with one persistent card target shared by
    # Favorite, Equip, Upgrade and Deselect. The current collection card is captured BEFORE focus
    # leaves the collection grid.
    pattern = re.compile(
        r'''        int focusedId = this\.currentlySnappedComponent\?\.myID \?\? -1;\n'''
        r'''        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId \+ this\.CardButtons\.Count;\n'''
        r'''        if \(collectionFocused\)\n        \{.*?\n        \}\n\n'''
        r'''        if \(focusedId == FavoriteActionId && this\.Controller\.IsConfirm\(b\)\)\n        \{.*?\n        \}\n''',
        re.S,
    )
    replacement = '''        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n        if (collectionFocused)\n            this.CaptureControllerActionTarget(focusedId);\n'''
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1 and 'this.CaptureControllerActionTarget(focusedId);' not in text:
        raise AssertionError('Could not replace controller collection/favorite preamble')

    old_tail = '''        base.receiveGamePadButton(b);\n        this.EnsureControllerFocusValid();\n        this.SyncBrowsePreviewToFocusedCard();\n'''
    new_tail = '''        base.receiveGamePadButton(b);\n        this.EnsureControllerFocusValid();\n        this.SyncBrowsePreviewToFocusedCard();\n        int movedFocusId = this.currentlySnappedComponent?.myID ?? -1;\n        if (movedFocusId >= CardBaseId && movedFocusId < CardBaseId + this.CardButtons.Count)\n            this.CaptureControllerActionTarget(movedFocusId);\n'''
    if new_tail not in text:
        if old_tail not in text:
            raise AssertionError('Could not locate controller navigation tail')
        text = text.replace(old_tail, new_tail, 1)

    # All four detail buttons now use the exact same receiveLeftClick path as mouse input. Before
    # invoking it, synchronize the controller's last collection card into the normal Selected/Lock state.
    activation_anchor = '''        int id = focused.myID;\n        if (id >= CardBaseId && id < CardBaseId + this.CardButtons.Count)\n'''
    activation_new = '''        int id = focused.myID;\n        if (fromController && this.LastInputWasController && IsDetailActionId(id))\n        {\n            this.PrepareControllerActionTargetForMousePath();\n            Rectangle action = focused.bounds;\n            this.receiveLeftClick(action.Center.X, action.Center.Y, playSound: true);\n            this.LastInputWasController = true;\n            return;\n        }\n\n        if (id >= CardBaseId && id < CardBaseId + this.CardButtons.Count)\n'''
    if 'PrepareControllerActionTargetForMousePath();' not in text:
        if activation_anchor not in text:
            raise AssertionError('Could not locate ActivateFocusedComponent ID block')
        text = text.replace(activation_anchor, activation_new, 1)

    # Remove Favorite-only helper and replace with generic controller action target helpers.
    target_pattern = re.compile(
        r'''    private CardDefinition\? GetFavoriteTargetCard\(\)\n        => this\.PreviewCard \?\? this\.Selected \?\? this\.LockedCard;\n\n'''
        r'''    private void ActivateFavoriteThroughMouseHandler\(\)\n    \{.*?\n    \}\n\n''',
        re.S,
    )
    target_replacement = '''    private static bool IsDetailActionId(int id)\n        => id == FavoriteActionId || id == EquipActionId || id == UpgradeActionId || id == DeselectActionId;\n\n    private void CaptureControllerActionTarget(int focusedCardId)\n    {\n        int index = focusedCardId - CardBaseId;\n        if (index < 0 || index >= this.CardButtons.Count)\n            return;\n\n        CardDefinition card = this.CardButtons[index].Card;\n        this.ControllerActionTarget = card;\n        this.PreviewCard = card;\n        this.Selected = card;\n        this.FavoriteActionButton.leftNeighborID = focusedCardId;\n    }\n\n    private void PrepareControllerActionTargetForMousePath()\n    {\n        CardDefinition? target = this.ControllerActionTarget ?? this.PreviewCard ?? this.Selected ?? this.LockedCard;\n        if (target is null)\n            return;\n\n        this.ControllerActionTarget = target;\n        this.PreviewCard = target;\n        this.Selected = target;\n        this.LockedCard = target;\n        this.ControllerSelectionLocked = true;\n    }\n\n    private CardDefinition? GetFavoriteTargetCard()\n    {\n        if (this.LastInputWasController\n            && IsDetailActionId(this.currentlySnappedComponent?.myID ?? -1)\n            && this.ControllerActionTarget is not null)\n        {\n            return this.ControllerActionTarget;\n        }\n\n        return this.PreviewCard ?? this.Selected ?? this.LockedCard;\n    }\n\n'''
    text, count = target_pattern.subn(target_replacement, text, count=1)
    if count != 1 and 'private void CaptureControllerActionTarget(int focusedCardId)' not in text:
        raise AssertionError('Could not replace Favorite-only target helper')

    # Remove old direct Favorite helper call if one remains in ActivateFocusedComponent. The generic
    # controller action branch above catches controller input; mouse/keyboard can use normal action code.
    text = text.replace(
        '''        if (id == FavoriteActionId)\n        {\n            this.ActivateFavoriteThroughMouseHandler();\n            return;\n        }\n''',
        '''        if (id == FavoriteActionId)\n        {\n            this.ActivateFavoriteAction();\n            return;\n        }\n''',
        1,
    )

    # Button labels/colors/stats must read the same target card that controller actions will mutate.
    draw_pattern = re.compile(
        r'''    private void DrawActionButtons\(SpriteBatch b, bool owned\)\n    \{\n'''
        r'''        CardDefinition\? favoriteTarget = this\.GetFavoriteTargetCard\(\);\n'''
        r'''        bool favorite = favoriteTarget is not null\n'''
        r'''            && this\.Save\.Data\.OwnedCards\.Contains\(favoriteTarget\.Id\)\n'''
        r'''            && this\.Save\.Data\.FavoriteCardIds\.Contains\(favoriteTarget\.Id\);\n'''
        r'''        bool equipped = owned && this\.Selected is not null && this\.IsStoredEquipped\(this\.Selected\.Id\);\n'''
        r'''        bool maxed = !owned \|\| this\.Selected is null \|\| this\.Upgrades\.IsMaxLevel\(this\.Selected\);\n'''
        r'''        int have = this\.Selected is null \? 0 : this\.Upgrades\.GetCopies\(this\.Selected\);\n'''
        r'''        int need = this\.Selected is null \? 0 : this\.Upgrades\.GetRequiredCopies\(this\.Selected\);\n''',
        re.S,
    )
    draw_replacement = '''    private void DrawActionButtons(SpriteBatch b, bool owned)\n    {\n        CardDefinition? actionTarget = this.LastInputWasController\n            && IsDetailActionId(this.currentlySnappedComponent?.myID ?? -1)\n            && this.ControllerActionTarget is not null\n                ? this.ControllerActionTarget\n                : this.Selected;\n        bool actionOwned = actionTarget is not null && this.Save.Data.OwnedCards.Contains(actionTarget.Id);\n        bool favorite = actionOwned && this.Save.Data.FavoriteCardIds.Contains(actionTarget!.Id);\n        bool equipped = actionOwned && this.IsStoredEquipped(actionTarget!.Id);\n        bool maxed = !actionOwned || actionTarget is null || this.Upgrades.IsMaxLevel(actionTarget);\n        int have = actionTarget is null ? 0 : this.Upgrades.GetCopies(actionTarget);\n        int need = actionTarget is null ? 0 : this.Upgrades.GetRequiredCopies(actionTarget);\n'''
    text, count = draw_pattern.subn(draw_replacement, text, count=1)
    if count != 1 and 'bool actionOwned = actionTarget is not null' not in text:
        raise AssertionError('Could not replace DrawActionButtons target state')

    # Replace the two old uses of right-page owned state in the top buttons with action target ownership.
    text = text.replace(
        '            owned ? CardchaUi.Gold : new Color(130, 120, 112)\n',
        '            actionOwned ? CardchaUi.Gold : new Color(130, 120, 112)\n',
        1,
    )
    text = text.replace(
        '            owned ? (equipped ? CardchaUi.DangerRed : CardchaUi.GoodGreen) : new Color(130, 120, 112)\n',
        '            actionOwned ? (equipped ? CardchaUi.DangerRed : CardchaUi.GoodGreen) : new Color(130, 120, 112)\n',
        1,
    )

    path.write_text(text)


def patch_attic() -> None:
    path = ROOT / 'Services/MimiAtticVisualService.cs'
    text = path.read_text()
    text = re.sub(
        r'private const string DecorVersion = "alpha\.27\.0\.7\.8(?:\.\d+)?";',
        f'private const string DecorVersion = "{DECOR}";',
        text,
        count=1,
    )

    old_rug = 'TryAddFurniture(attic, "(F)1456", 16, 9, pixelOffsetX: -24);  // Further left nudge requested after in-game 0.7.8.2 acceptance.'
    new_rug = 'TryAddFurniture(attic, "(F)1456", 16, 9, pixelOffsetX: -32);  // Final left nudge: rug visual center under the prototype table.'
    if new_rug not in text:
        if old_rug not in text:
            raise AssertionError('Could not locate 0.7.8.3 prototype rug offset')
        text = text.replace(old_rug, new_rug, 1)

    # TV is accepted in-game at -32px; leave it untouched.
    if '"(F)1466", 4, 7, pixelOffsetX: -32' not in text:
        raise AssertionError('Accepted TV offset was unexpectedly changed')

    path.write_text(text)


def validate() -> None:
    binder = (ROOT / 'UI/CardchaBinderMenu.cs').read_text()
    visual = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()

    assert 'private CardDefinition? ControllerActionTarget;' in binder
    assert 'this.CaptureControllerActionTarget(focusedId);' in binder
    assert 'private void PrepareControllerActionTargetForMousePath()' in binder
    assert 'fromController && this.LastInputWasController && IsDetailActionId(id)' in binder
    assert 'this.receiveLeftClick(action.Center.X, action.Center.Y, playSound: true);' in binder
    assert 'bool actionOwned = actionTarget is not null' in binder
    assert 'ActivateFavoriteThroughMouseHandler' not in binder

    assert '"(F)1456", 16, 9, pixelOffsetX: -32' in visual
    assert '"(F)1466", 4, 7, pixelOffsetX: -32' in visual
    assert DECOR in visual
    assert json.loads((ROOT / 'manifest.json').read_text())['Version'] == TARGET


def main() -> None:
    patch_binder()
    patch_attic()
    set_versions()
    validate()
    print('0.7.8.4 unified controller detail actions + final rug nudge applied')


if __name__ == '__main__':
    main()

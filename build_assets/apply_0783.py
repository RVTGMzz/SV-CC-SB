from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.8.3'
DECOR = 'alpha.27.0.7.8.3'


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

    old_focus = '''        if (focusedId == FavoriteActionId && this.Controller.IsConfirm(b))\n        {\n            this.ActivateFavoriteAction();\n            return;\n        }\n'''
    new_focus = '''        if (focusedId == FavoriteActionId && this.Controller.IsConfirm(b))\n        {\n            // Do literally what a mouse-left click on the visible Favorite button does.\n            // receiveLeftClick temporarily switches LastInputWasController off, so the Favorite\n            // target resolves from the same PreviewCard/Selected state as a real mouse click.\n            this.ActivateFavoriteThroughMouseHandler();\n            return;\n        }\n'''
    if new_focus not in text:
        if old_focus not in text:
            raise AssertionError('Could not locate focused Favorite controller block')
        text = text.replace(old_focus, new_focus, 1)

    old_component = '''        if (id == FavoriteActionId)\n        {\n            this.ActivateFavoriteAction();\n            return;\n        }\n'''
    new_component = '''        if (id == FavoriteActionId)\n        {\n            this.ActivateFavoriteThroughMouseHandler();\n            return;\n        }\n'''
    if new_component not in text:
        if old_component not in text:
            raise AssertionError('Could not locate Favorite action component block')
        text = text.replace(old_component, new_component, 1)

    old_target = '''    private CardDefinition? GetFavoriteTargetCard()\n    {\n        if (this.LastInputWasController && this.currentlySnappedComponent?.myID == FavoriteActionId)\n        {\n            int sourceId = this.FavoriteActionButton.leftNeighborID;\n            int sourceIndex = sourceId - CardBaseId;\n            if (sourceIndex >= 0 && sourceIndex < this.CardButtons.Count)\n                return this.CardButtons[sourceIndex].Card;\n        }\n\n        return this.PreviewCard ?? this.Selected ?? this.LockedCard;\n    }\n\n    private void ActivateFavoriteAction()\n'''
    new_target = '''    private CardDefinition? GetFavoriteTargetCard()\n        => this.PreviewCard ?? this.Selected ?? this.LockedCard;\n\n    private void ActivateFavoriteThroughMouseHandler()\n    {\n        bool restoreControllerState = this.LastInputWasController;\n        Rectangle bounds = this.FavoriteActionButton.bounds;\n        this.receiveLeftClick(bounds.Center.X, bounds.Center.Y, playSound: true);\n        this.LastInputWasController = restoreControllerState;\n    }\n\n    private void ActivateFavoriteAction()\n'''
    if new_target not in text:
        if old_target not in text:
            raise AssertionError('Could not locate Favorite target method')
        text = text.replace(old_target, new_target, 1)

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

    old_rug = 'TryAddFurniture(attic, "(F)1456", 16, 9, pixelOffsetX: -16);  // Small left nudge to center the rug under the prototype table.'
    new_rug = 'TryAddFurniture(attic, "(F)1456", 16, 9, pixelOffsetX: -24);  // Another 8px left after in-game acceptance screenshot.'
    if new_rug not in text:
        if old_rug not in text:
            raise AssertionError('Could not locate prototype rug offset')
        text = text.replace(old_rug, new_rug, 1)

    old_tv = 'TryAddFurniture(attic, "(F)1466", 4, 7, pixelOffsetX: -24); // Final small nudge left: TV visual center matches couch/rug.'
    new_tv = 'TryAddFurniture(attic, "(F)1466", 4, 7, pixelOffsetX: -32); // Another 8px left after in-game acceptance screenshot.'
    if new_tv not in text:
        if old_tv not in text:
            raise AssertionError('Could not locate TV offset')
        text = text.replace(old_tv, new_tv, 1)

    path.write_text(text)


def validate() -> None:
    binder = (ROOT / 'UI/CardchaBinderMenu.cs').read_text()
    visual = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()
    assert 'private void ActivateFavoriteThroughMouseHandler()' in binder
    assert 'this.receiveLeftClick(bounds.Center.X, bounds.Center.Y, playSound: true);' in binder
    assert '=> this.PreviewCard ?? this.Selected ?? this.LockedCard;' in binder
    assert 'sourceId = this.FavoriteActionButton.leftNeighborID' not in binder
    assert 'pixelOffsetX: -32' in visual
    assert 'pixelOffsetX: -24' in visual
    assert DECOR in visual
    assert json.loads((ROOT / 'manifest.json').read_text())['Version'] == TARGET


def main() -> None:
    patch_binder()
    patch_attic()
    set_versions()
    validate()
    print('0.7.8.3 exact mouse Favorite + TV/rug nudges applied')


if __name__ == '__main__':
    main()

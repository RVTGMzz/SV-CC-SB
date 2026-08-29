from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.8.1'
DECOR = 'alpha.27.0.7.8.1'


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

    # Some controller runtimes emit the same Confirm press twice. Favorite is a toggle, so the
    # duplicate event immediately undoes the first event and leaves the misleading "removed" toast.
    field_anchor = '''    private long FavoriteToastExpiresAtMs;\n    private const long FavoriteToastDurationMs = 3000L;\n'''
    field_new = '''    private long FavoriteToastExpiresAtMs;\n    private const long FavoriteToastDurationMs = 3000L;\n    private long LastFavoriteControllerActivationAtMs;\n    private const long FavoriteControllerDebounceMs = 250L;\n'''
    if 'FavoriteControllerDebounceMs' not in text:
        if field_anchor not in text:
            raise AssertionError('Could not locate Favorite toast fields')
        text = text.replace(field_anchor, field_new, 1)

    # Capture the exact collection card before the navigation event moves focus to Favorite.
    # This makes the Favorite action deterministic even when a previous card is still selection-locked.
    nav_anchor = '''        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n\n        if (focusedId == FavoriteActionId\n'''
    nav_new = '''        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n        if (collectionFocused)\n            this.ControllerFavoriteTarget = this.CardButtons[focusedId - CardBaseId].Card;\n\n        if (focusedId == FavoriteActionId\n'''
    if nav_new not in text:
        if nav_anchor not in text:
            raise AssertionError('Could not locate controller focus preamble')
        text = text.replace(nav_anchor, nav_new, 1)

    # Confirm / Favorite while focus is on the Favorite button must be debounced as one physical press.
    old_focus = '''        if (focusedId == FavoriteActionId\n            && (this.Controller.IsConfirm(b) || this.Controller.IsFavorite(b)))\n        {\n            this.ActivateFavoriteAction();\n            return;\n        }\n'''
    new_focus = '''        if (focusedId == FavoriteActionId\n            && (this.Controller.IsConfirm(b) || this.Controller.IsFavorite(b)))\n        {\n            this.TryActivateFavoriteFromController();\n            return;\n        }\n'''
    if new_focus not in text:
        if old_focus not in text:
            raise AssertionError('Could not locate focused Favorite controller action')
        text = text.replace(old_focus, new_focus, 1)

    old_shortcut = '''                this.RestoreLockedSelectionForAction();\n                this.ActivateFavoriteAction();\n'''
    new_shortcut = '''                this.RestoreLockedSelectionForAction();\n                this.TryActivateFavoriteFromController();\n'''
    if new_shortcut not in text:
        if old_shortcut not in text:
            raise AssertionError('Could not locate controller Favorite shortcut action')
        text = text.replace(old_shortcut, new_shortcut, 1)

    helper_anchor = '''    private CardDefinition? GetFavoriteTargetCard()\n        => this.LastInputWasController && this.ControllerFavoriteTarget is not null\n            ? this.ControllerFavoriteTarget\n            : this.PreviewCard ?? this.Selected ?? this.LockedCard;\n\n    private void ActivateFavoriteAction()\n'''
    helper_new = '''    private CardDefinition? GetFavoriteTargetCard()\n        => this.LastInputWasController && this.ControllerFavoriteTarget is not null\n            ? this.ControllerFavoriteTarget\n            : this.PreviewCard ?? this.Selected ?? this.LockedCard;\n\n    private void TryActivateFavoriteFromController()\n    {\n        long now = Environment.TickCount64;\n        if (now - this.LastFavoriteControllerActivationAtMs < FavoriteControllerDebounceMs)\n            return;\n\n        this.LastFavoriteControllerActivationAtMs = now;\n        this.ActivateFavoriteAction();\n    }\n\n    private void ActivateFavoriteAction()\n'''
    if 'private void TryActivateFavoriteFromController()' not in text:
        if helper_anchor not in text:
            raise AssertionError('Could not locate Favorite target/action methods')
        text = text.replace(helper_anchor, helper_new, 1)

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

    # The lower-right rug and prototype table were one whole tile apart. Move the rug one tile
    # right so their visual centers share the same axis, matching the accepted TV/couch treatment.
    old_rug = 'TryAddFurniture(attic, "(F)1456", 15, 9);  // Patchwork Rug — moved beneath the lower prototype table.'
    new_rug = 'TryAddFurniture(attic, "(F)1456", 16, 9);  // Patchwork Rug centered beneath the lower prototype table.'
    if new_rug not in text:
        if old_rug not in text:
            raise AssertionError('Could not locate lower prototype rug')
        text = text.replace(old_rug, new_rug, 1)

    path.write_text(text)


def validate() -> None:
    binder = (ROOT / 'UI/CardchaBinderMenu.cs').read_text()
    visual = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()

    assert 'FavoriteControllerDebounceMs = 250L' in binder
    assert 'this.ControllerFavoriteTarget = this.CardButtons[focusedId - CardBaseId].Card;' in binder
    assert 'this.TryActivateFavoriteFromController();' in binder
    assert 'private void TryActivateFavoriteFromController()' in binder
    assert 'now - this.LastFavoriteControllerActivationAtMs < FavoriteControllerDebounceMs' in binder
    assert '"(F)1456", 16, 9' in visual
    assert 'pixelOffsetX: -16' in visual
    assert DECOR in visual
    assert json.loads((ROOT / 'manifest.json').read_text())['Version'] == TARGET


def main() -> None:
    patch_binder()
    patch_attic()
    set_versions()
    validate()
    print('0.7.8.1 controller favorite debounce + right rug/table alignment applied')


if __name__ == '__main__':
    main()

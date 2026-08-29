from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.8.2'
DECOR = 'alpha.27.0.7.8.2'


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

    # Remove the stale controller-target cache/debounce experiment. The Favorite button now derives
    # its target from its leftNeighborID, i.e. the exact collection cell used to enter the button.
    text = text.replace('    private CardDefinition? ControllerFavoriteTarget;\n', '')
    text = text.replace('    private long LastFavoriteControllerActivationAtMs;\n', '')
    text = text.replace('    private const long FavoriteControllerDebounceMs = 250L;\n', '')

    old_preamble = '''        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n        if (collectionFocused)\n            this.ControllerFavoriteTarget = this.CardButtons[focusedId - CardBaseId].Card;\n\n        if (focusedId == FavoriteActionId\n            && (this.Controller.IsConfirm(b) || this.Controller.IsFavorite(b)))\n        {\n            this.TryActivateFavoriteFromController();\n            return;\n        }\n'''
    new_preamble = '''        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n        if (collectionFocused)\n        {\n            // The Favorite button remembers the exact collection component that led into it.\n            // Both its label and action resolve from this same ID, so they cannot disagree.\n            this.FavoriteActionButton.leftNeighborID = focusedId;\n            this.PreviewCard = this.CardButtons[focusedId - CardBaseId].Card;\n        }\n\n        if (focusedId == FavoriteActionId && this.Controller.IsConfirm(b))\n        {\n            this.ActivateFavoriteAction();\n            return;\n        }\n'''
    if old_preamble not in text:
        raise AssertionError('Could not locate 0.7.8.1 controller preamble')
    text = text.replace(old_preamble, new_preamble, 1)

    # Disable the separate Favorite shortcut inside Binder. The explicit on-screen Favorite button
    # is the single controller path; this prevents mapping/profile shortcuts from mutating another card.
    old_shortcut = '''        if (this.Controller.IsFavorite(b))\n        {\n            if (this.ControllerSelectionLocked && this.LockedCard is not null)\n            {\n                this.RestoreLockedSelectionForAction();\n                this.TryActivateFavoriteFromController();\n            }\n            else\n            {\n                this.ShowFavoriteToast(ModEntry.T("binder.favorite.select-first"));\n                Game1.playSound("cancel");\n            }\n            return;\n        }\n\n'''
    if old_shortcut not in text:
        raise AssertionError('Could not locate controller Favorite shortcut')
    text = text.replace(old_shortcut, '''        // Binder Favorite is intentionally activated only through the focused on-screen button.\n        if (this.Controller.IsFavorite(b))\n            return;\n\n''', 1)

    text = text.replace('        if (fromController)\n            this.ControllerFavoriteTarget = card;\n', '')
    text = text.replace('        if (this.LastInputWasController)\n            this.ControllerFavoriteTarget = card;\n', '')

    old_target = '''    private CardDefinition? GetFavoriteTargetCard()\n        => this.LastInputWasController && this.ControllerFavoriteTarget is not null\n            ? this.ControllerFavoriteTarget\n            : this.PreviewCard ?? this.Selected ?? this.LockedCard;\n\n    private void TryActivateFavoriteFromController()\n    {\n        long now = Environment.TickCount64;\n        if (now - this.LastFavoriteControllerActivationAtMs < FavoriteControllerDebounceMs)\n            return;\n\n        this.LastFavoriteControllerActivationAtMs = now;\n        this.ActivateFavoriteAction();\n    }\n\n'''
    new_target = '''    private CardDefinition? GetFavoriteTargetCard()\n    {\n        if (this.LastInputWasController && this.currentlySnappedComponent?.myID == FavoriteActionId)\n        {\n            int sourceId = this.FavoriteActionButton.leftNeighborID;\n            int sourceIndex = sourceId - CardBaseId;\n            if (sourceIndex >= 0 && sourceIndex < this.CardButtons.Count)\n                return this.CardButtons[sourceIndex].Card;\n        }\n\n        return this.PreviewCard ?? this.Selected ?? this.LockedCard;\n    }\n\n'''
    if old_target not in text:
        raise AssertionError('Could not locate 0.7.8.1 Favorite target/debounce methods')
    text = text.replace(old_target, new_target, 1)

    # The controller hint should no longer advertise a hidden Favorite shortcut which Binder ignores.
    hint = '                new ControlHint(this.Controller.GetLabel(ControllerAction.Favorite), ModEntry.T("binder.hint.favorite"), hasLock),\n'
    text = text.replace(hint, '')

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

    old_tv = 'TryAddFurniture(attic, "(F)1466", 4, 7, pixelOffsetX: -16); // Real -16px shift: measured visual center matches rug + couch.'
    new_tv = 'TryAddFurniture(attic, "(F)1466", 4, 7, pixelOffsetX: -24); // Final small nudge left: TV visual center matches couch/rug.'
    if old_tv not in text:
        raise AssertionError('Could not locate 0.7.8.1 TV placement')
    text = text.replace(old_tv, new_tv, 1)

    old_rug = 'TryAddFurniture(attic, "(F)1456", 16, 9);  // Patchwork Rug centered beneath the lower prototype table.'
    new_rug = 'TryAddFurniture(attic, "(F)1456", 16, 9, pixelOffsetX: -16);  // Small left nudge to center the rug under the prototype table.'
    if old_rug not in text:
        raise AssertionError('Could not locate 0.7.8.1 prototype rug')
    text = text.replace(old_rug, new_rug, 1)

    path.write_text(text)


def validate() -> None:
    binder = (ROOT / 'UI/CardchaBinderMenu.cs').read_text()
    visual = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()
    assert 'ControllerFavoriteTarget' not in binder
    assert 'FavoriteControllerDebounceMs' not in binder
    assert 'focusedId == FavoriteActionId && this.Controller.IsConfirm(b)' in binder
    assert 'this.FavoriteActionButton.leftNeighborID = focusedId;' in binder
    assert 'int sourceId = this.FavoriteActionButton.leftNeighborID;' in binder
    assert 'this.Controller.IsFavorite(b))\n            return;' in binder
    assert 'ControllerAction.Favorite), ModEntry.T("binder.hint.favorite")' not in binder
    assert 'pixelOffsetX: -24' in visual
    assert '"(F)1456", 16, 9, pixelOffsetX: -16' in visual
    assert DECOR in visual
    assert json.loads((ROOT / 'manifest.json').read_text())['Version'] == TARGET


def main() -> None:
    patch_binder()
    patch_attic()
    set_versions()
    validate()
    print('0.7.8.2 exact Favorite source + TV/rug final nudges applied')


if __name__ == '__main__':
    main()

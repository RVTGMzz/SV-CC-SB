from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.8.0'
DECOR = 'alpha.27.0.7.8.0'


def set_versions() -> None:
    pattern = r'0\.3\.0-alpha\.27\.0\.7\.7(?:\.\d+)?|0\.3\.0-alpha\.27\.0\.7\.8(?:\.\d+)?'
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
    text = re.sub(r'CardchaAtticVersion" value="alpha\.27\.0\.7\.(?:7|8)\.\d+"',
                  f'CardchaAtticVersion" value="{DECOR}"', text, count=1)
    tmx.write_text(text)


def patch_binder() -> None:
    path = ROOT / 'UI/CardchaBinderMenu.cs'
    text = path.read_text()

    anchor = '    private CardDefinition? LockedCard;\n'
    insertion = anchor + '    private CardDefinition? ControllerFavoriteTarget;\n'
    if 'private CardDefinition? ControllerFavoriteTarget;' not in text:
        if anchor not in text:
            raise AssertionError('Could not locate LockedCard field')
        text = text.replace(anchor, insertion, 1)

    old_sync = '''    private void SyncBrowsePreviewToFocusedCard()\n    {\n        if (this.ControllerSelectionLocked && this.LockedCard is not null)\n        {\n            // Keep rendering and all action state pinned to the explicit lock.\n            this.Selected = this.LockedCard;\n            return;\n        }\n\n        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        if (focusedId < CardBaseId || focusedId >= CardBaseId + this.CardButtons.Count)\n            return;\n\n        int index = focusedId - CardBaseId;\n        CardDefinition card = this.CardButtons[index].Card;\n        this.PreviewCard = card;\n        this.Selected = card;\n        this.FavoriteActionButton.leftNeighborID = focusedId;\n        this.Status = this.Save.Data.OwnedCards.Contains(card.Id)\n            ? string.Empty\n            : ModEntry.T("binder.status.not-owned");\n    }\n'''
    new_sync = '''    private void SyncBrowsePreviewToFocusedCard()\n    {\n        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        if (focusedId < CardBaseId || focusedId >= CardBaseId + this.CardButtons.Count)\n            return;\n\n        int index = focusedId - CardBaseId;\n        CardDefinition card = this.CardButtons[index].Card;\n        this.PreviewCard = card;\n        this.FavoriteActionButton.leftNeighborID = focusedId;\n        if (this.LastInputWasController)\n            this.ControllerFavoriteTarget = card;\n\n        if (this.ControllerSelectionLocked && this.LockedCard is not null)\n        {\n            // The detail page can stay locked, but Favorite follows the collection card the\n            // controller actually navigated from instead of an older locked selection.\n            this.Selected = this.LockedCard;\n            return;\n        }\n\n        this.Selected = card;\n        this.Status = this.Save.Data.OwnedCards.Contains(card.Id)\n            ? string.Empty\n            : ModEntry.T("binder.status.not-owned");\n    }\n'''
    if new_sync not in text:
        if old_sync not in text:
            raise AssertionError('Could not locate SyncBrowsePreviewToFocusedCard')
        text = text.replace(old_sync, new_sync, 1)

    old_target = '''    private CardDefinition? GetFavoriteTargetCard()\n        => this.ControllerSelectionLocked && this.LockedCard is not null\n            ? this.LockedCard\n            : this.PreviewCard ?? this.Selected;\n'''
    new_target = '''    private CardDefinition? GetFavoriteTargetCard()\n        => this.LastInputWasController && this.ControllerFavoriteTarget is not null\n            ? this.ControllerFavoriteTarget\n            : this.PreviewCard ?? this.Selected ?? this.LockedCard;\n'''
    if new_target not in text:
        if old_target not in text:
            raise AssertionError('Could not locate GetFavoriteTargetCard')
        text = text.replace(old_target, new_target, 1)

    anchor_activation = '''        this.LockedCard = card;\n        this.ControllerSelectionLocked = true;\n        this.PreviewCard = card;\n        this.Selected = card;\n'''
    replacement_activation = '''        this.LockedCard = card;\n        this.ControllerSelectionLocked = true;\n        this.PreviewCard = card;\n        this.Selected = card;\n        if (fromController)\n            this.ControllerFavoriteTarget = card;\n'''
    if replacement_activation not in text:
        if anchor_activation not in text:
            raise AssertionError('Could not locate HandleCollectionActivation lock block')
        text = text.replace(anchor_activation, replacement_activation, 1)

    old_double = '''        if (!string.IsNullOrWhiteSpace(this.FavoriteToast))\n        {\n            if (Environment.TickCount64 < this.FavoriteToastExpiresAtMs)\n            {\n                Rectangle toastArea = new(\n                    this.RightPage.X + 64,\n                    this.FavoriteActionButton.bounds.Y - 46,\n                    this.RightPage.Width - 128,\n                    38\n                );\n                DrawRoundedRect(b, toastArea, new Color(58, 77, 81) * 0.96f, 8);\n                DrawRoundedBorder(b, toastArea, new Color(201, 165, 92), 2, 8);\n                CardchaUi.DrawAutoFitWrappedText(\n                    b, Game1.smallFont, this.FavoriteToast, Inflate(toastArea, -6), Color.White,\n                    maxLines: 1, minScale: 0.72f, centerX: true, maxScale: 0.96f, centerY: true\n                );\n                return;\n            }\n\n            this.FavoriteToast = string.Empty;\n            this.FavoriteToastExpiresAtMs = 0;\n        }\n\n'''
    if old_double in text:
        text = text.replace(old_double, '', 1)
    elif 'Rectangle toastArea = new(' in text:
        raise AssertionError('Unexpected duplicate toast block in DrawStatus')

    path.write_text(text)


def patch_attic() -> None:
    path = ROOT / 'Services/MimiAtticVisualService.cs'
    text = path.read_text()

    text = re.sub(r'private const string DecorVersion = "alpha\.27\.0\.7\.(?:7|8)\.\d+";',
                  f'private const string DecorVersion = "{DECOR}";', text, count=1)

    field_anchor = '    private bool TestAccessActive;\n'
    field_replacement = field_anchor + '    private GameLocation? DecorAppliedLocation;\n'
    if 'private GameLocation? DecorAppliedLocation;' not in text:
        if field_anchor not in text:
            raise AssertionError('Could not locate attic service fields')
        text = text.replace(field_anchor, field_replacement, 1)

    old_sig = '    private static void EnsureVanillaFurniture(GameLocation attic)\n    {\n        if (attic.modData.TryGetValue(DecorMarkerKey, out string? version)\n            && string.Equals(version, DecorVersion, StringComparison.Ordinal))\n        {\n            return;\n        }\n\n'
    new_sig = '    private void EnsureVanillaFurniture(GameLocation attic)\n    {\n        if (ReferenceEquals(this.DecorAppliedLocation, attic))\n            return;\n\n        this.DecorAppliedLocation = attic;\n\n'
    if new_sig not in text:
        if old_sig not in text:
            raise AssertionError('Could not locate EnsureVanillaFurniture version guard')
        text = text.replace(old_sig, new_sig, 1)

    text = text.replace('TryAddFurniture(attic, "(F)1466", 4, 7, pixelOffsetX: 16); // Real +16px draw/collision shift: centered with rug + couch.',
                        'TryAddFurniture(attic, "(F)1466", 4, 7, pixelOffsetX: -16); // Real -16px shift: measured visual center matches rug + couch.')

    path.write_text(text)


def validate() -> None:
    binder = (ROOT / 'UI/CardchaBinderMenu.cs').read_text()
    visual = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()
    assert 'private CardDefinition? ControllerFavoriteTarget;' in binder
    assert 'this.ControllerFavoriteTarget = card;' in binder
    assert 'this.LastInputWasController && this.ControllerFavoriteTarget is not null' in binder
    assert 'Rectangle toastArea = new(' not in binder
    assert binder.count('this.DrawFavoriteToast(b);') == 1
    assert 'private GameLocation? DecorAppliedLocation;' in visual
    assert 'ReferenceEquals(this.DecorAppliedLocation, attic)' in visual
    assert 'private void EnsureVanillaFurniture(GameLocation attic)' in visual
    assert 'pixelOffsetX: -16' in visual
    assert DECOR in visual
    assert json.loads((ROOT / 'manifest.json').read_text())['Version'] == TARGET


def main() -> None:
    patch_binder()
    patch_attic()
    set_versions()
    validate()
    print('0.7.8.0 favorite target + single toast + forced attic refresh applied')


if __name__ == '__main__':
    main()

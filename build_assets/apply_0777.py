from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.7.7'
DECOR = 'alpha.27.0.7.7.7'


def set_versions() -> None:
    pattern = r'0\.3\.0-alpha\.27\.0\.7\.7(?:\.\d+)?(?!\.\d)'
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
    text = re.sub(r'CardchaAtticVersion" value="alpha\.27\.0\.7\.7\.\d+"',
                  f'CardchaAtticVersion" value="{DECOR}"', text, count=1)
    tmx.write_text(text)


def patch_controller_favorite() -> None:
    path = ROOT / 'UI/CardchaBinderMenu.cs'
    text = path.read_text()

    # Controller Confirm on the Favorite action must use the exact same path as a mouse left click.
    # Removing this special-case lets ActivateFocusedComponent fall through to its existing
    # synthetic receiveLeftClick(bounds.Center) call, so favorite/unfavorite behavior cannot drift.
    old = '''        if (id == FavoriteActionId)\n        {\n            this.RestoreLockedSelectionForAction();\n            this.ToggleFavorite();\n            return;\n        }\n\n'''
    if old in text:
        text = text.replace(old, '', 1)
    elif 'if (id == FavoriteActionId)' in text:
        raise AssertionError('Unexpected FavoriteActionId controller special-case')

    # Make the invariant explicit near the generic fallback for future maintenance.
    old_fallback = '''        Rectangle r = focused.bounds;\n        this.receiveLeftClick(r.Center.X, r.Center.Y, playSound: true);\n'''
    new_fallback = '''        // Controller confirm intentionally shares the mouse-left-click handler for action buttons\n        // (including Favorite), so toggles behave identically across input methods.\n        Rectangle r = focused.bounds;\n        this.receiveLeftClick(r.Center.X, r.Center.Y, playSound: true);\n'''
    if new_fallback not in text:
        if old_fallback not in text:
            raise AssertionError('Could not locate ActivateFocusedComponent mouse fallback')
        text = text.replace(old_fallback, new_fallback, 1)

    path.write_text(text)


def patch_attic_alignment_and_ladder_clear() -> None:
    path = ROOT / 'Services/MimiAtticVisualService.cs'
    text = path.read_text()

    text = text.replace('private const string DecorVersion = "alpha.27.0.7.7.6";',
                        f'private const string DecorVersion = "{DECOR}";')

    # Align the green rug and couch on the same x anchor.
    text = text.replace('TryAddFurniture(attic, "(F)1623", 2, 9);   // Green Cottage Rug — TV nook.',
                        'TryAddFurniture(attic, "(F)1623", 3, 9);   // Green Cottage Rug aligned with the couch.')

    # The TV art is visually half a tile right-heavy relative to the 3-tile couch. Give it a
    # half-tile left nudge so TV, rug and couch share one visual center line.
    text = text.replace('TryAddFurniture(attic, "(F)1466", 4, 7);                 // TV shifted right to center with the sofa/rug.',
                        'TryAddFurniture(attic, "(F)1466", 4, 7, offsetX: -0.5f); // TV half-tile left nudge: centered with rug + couch.')

    # Allow a cosmetic half-tile nudge while keeping normal furniture placements unchanged.
    old_sig = '''        int y,\n        int rotation = 0,\n        string? heldId = null)\n'''
    new_sig = '''        int y,\n        int rotation = 0,\n        string? heldId = null,\n        float offsetX = 0f)\n'''
    if new_sig not in text:
        if old_sig not in text:
            raise AssertionError('Could not locate TryAddFurniture signature')
        text = text.replace(old_sig, new_sig, 1)

    old_create = '''            Furniture item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);\n            item.modData[DecorMarkerKey] = DecorVersion;\n'''
    new_create = '''            Furniture item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);\n            if (Math.Abs(offsetX) > 0.001f)\n                item.TileLocation = new Vector2(x + offsetX, y);\n            item.modData[DecorMarkerKey] = DecorVersion;\n'''
    if new_create not in text:
        if old_create not in text:
            raise AssertionError('Could not locate TryAddFurniture creation block')
        text = text.replace(old_create, new_create, 1)

    # The ladder is only one tile wide. Clearing x-1 as well was erasing the neighboring WizardHouse
    # plant's right-side tiles. Clear only the ladder column and preserve adjacent decoration.
    old_clear = '''            for (int x = tile.X - 1; x <= tile.X; x++)\n            {\n                for (int y = tile.Y - 3; y <= tile.Y; y++)\n                {\n                    if (x >= 0 && y >= 0 && x < layer.LayerWidth && y < layer.LayerHeight)\n                        layer.Tiles[x, y] = null;\n                }\n            }\n'''
    new_clear = '''            int x = tile.X;\n            for (int y = tile.Y - 3; y <= tile.Y; y++)\n            {\n                if (x >= 0 && y >= 0 && x < layer.LayerWidth && y < layer.LayerHeight)\n                    layer.Tiles[x, y] = null;\n            }\n'''
    if new_clear not in text:
        if old_clear not in text:
            raise AssertionError('Could not locate Wizard stair clear block')
        text = text.replace(old_clear, new_clear, 1)

    path.write_text(text)


def validate() -> None:
    binder = (ROOT / 'UI/CardchaBinderMenu.cs').read_text()
    visual = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()
    assert 'if (id == FavoriteActionId)' not in binder
    assert 'Controller confirm intentionally shares the mouse-left-click handler' in binder
    assert '"(F)1623", 3, 9' in visual
    assert 'offsetX: -0.5f' in visual
    assert 'item.TileLocation = new Vector2(x + offsetX, y);' in visual
    assert 'for (int x = tile.X - 1; x <= tile.X; x++)' not in visual
    assert 'int x = tile.X;' in visual
    assert DECOR in visual
    assert json.loads((ROOT / 'manifest.json').read_text())['Version'] == TARGET


def main() -> None:
    patch_controller_favorite()
    patch_attic_alignment_and_ladder_clear()
    set_versions()
    validate()
    print('0.7.7.7 controller + TV alignment + ladder plant fix applied')


if __name__ == '__main__':
    main()

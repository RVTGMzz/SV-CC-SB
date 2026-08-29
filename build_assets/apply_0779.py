from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.7.9'
DECOR = 'alpha.27.0.7.7.9'


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


def patch_binder() -> None:
    path = ROOT / 'UI/CardchaBinderMenu.cs'
    text = path.read_text()

    # Horizontal controller navigation should leave the collection through Favorite first,
    # then Equip. This makes Favorite reachable without a diagonal/curved detour.
    old_nav = '''            button.rightNeighborID = col < GridColumns - 1 && i + 1 < this.CardButtons.Count\n                ? CardBaseId + i + 1\n                : EquipActionId;\n'''
    new_nav = '''            button.rightNeighborID = col < GridColumns - 1 && i + 1 < this.CardButtons.Count\n                ? CardBaseId + i + 1\n                : FavoriteActionId;\n'''
    if new_nav not in text:
        if old_nav not in text:
            raise AssertionError('Could not locate collection right-neighbor block')
        text = text.replace(old_nav, new_nav, 1)

    # Remember the exact collection card from which the action row was entered. Going left from
    # Favorite returns to that same card instead of an arbitrary last card on the page.
    old_sync = '''        this.PreviewCard = card;\n        this.Selected = card;\n        this.Status = this.Save.Data.OwnedCards.Contains(card.Id)\n'''
    new_sync = '''        this.PreviewCard = card;\n        this.Selected = card;\n        this.FavoriteActionButton.leftNeighborID = focusedId;\n        this.Status = this.Save.Data.OwnedCards.Contains(card.Id)\n'''
    if new_sync not in text:
        if old_sync not in text:
            raise AssertionError('Could not locate SyncBrowsePreviewToFocusedCard selection block')
        text = text.replace(old_sync, new_sync, 1)

    # Use one target resolver for both the Favorite button label and the Favorite action.
    marker = '''    private void ActivateFavoriteAction()\n    {\n'''
    helper = '''    private CardDefinition? GetFavoriteTargetCard()\n        => this.ControllerSelectionLocked && this.LockedCard is not null\n            ? this.LockedCard\n            : this.PreviewCard ?? this.Selected;\n\n    private void ActivateFavoriteAction()\n    {\n'''
    if 'private CardDefinition? GetFavoriteTargetCard()' not in text:
        if marker not in text:
            raise AssertionError('Could not locate ActivateFavoriteAction')
        text = text.replace(marker, helper, 1)

    text = text.replace('        CardDefinition? card = this.Selected;\n',
                        '        CardDefinition? card = this.GetFavoriteTargetCard();\n', 1)

    old_fav_draw = '''        bool favorite = owned && this.Selected is not null && this.Save.Data.FavoriteCardIds.Contains(this.Selected.Id);\n        bool equipped = owned && this.Selected is not null && this.IsStoredEquipped(this.Selected.Id);\n'''
    new_fav_draw = '''        CardDefinition? favoriteTarget = this.GetFavoriteTargetCard();\n        bool favorite = favoriteTarget is not null\n            && this.Save.Data.OwnedCards.Contains(favoriteTarget.Id)\n            && this.Save.Data.FavoriteCardIds.Contains(favoriteTarget.Id);\n        bool equipped = owned && this.Selected is not null && this.IsStoredEquipped(this.Selected.Id);\n'''
    if new_fav_draw not in text:
        if old_fav_draw not in text:
            raise AssertionError('Could not locate favorite button draw state')
        text = text.replace(old_fav_draw, new_fav_draw, 1)

    # 0.7.7.8 created toast state but forgot to render it. Draw it as a real temporary overlay.
    old_draw = '''        this.DrawRightPage(b);\n        this.DrawResourceTooltipIfNeeded(b);\n'''
    new_draw = '''        this.DrawRightPage(b);\n        this.DrawFavoriteToast(b);\n        this.DrawResourceTooltipIfNeeded(b);\n'''
    if new_draw not in text:
        if old_draw not in text:
            raise AssertionError('Could not locate Binder draw sequence')
        text = text.replace(old_draw, new_draw, 1)

    toast_anchor = '''    private bool IsStoredEquipped(string id)\n        => this.Save.Data.EquippedCards.Contains(id, StringComparer.OrdinalIgnoreCase);\n'''
    toast_method = '''    private void DrawFavoriteToast(SpriteBatch b)\n    {\n        if (string.IsNullOrWhiteSpace(this.FavoriteToast))\n            return;\n\n        long now = Environment.TickCount64;\n        if (now >= this.FavoriteToastExpiresAtMs)\n        {\n            this.FavoriteToast = string.Empty;\n            this.FavoriteToastExpiresAtMs = 0;\n            return;\n        }\n\n        const long fadeMs = 350L;\n        long remaining = this.FavoriteToastExpiresAtMs - now;\n        float alpha = remaining >= fadeMs ? 1f : Math.Clamp(remaining / (float)fadeMs, 0f, 1f);\n        int width = Math.Min(this.RightPage.Width - 96, 520);\n        Rectangle toast = new(\n            this.RightPage.Center.X - width / 2,\n            this.FavoriteActionButton.bounds.Y - 62,\n            width,\n            46\n        );\n        DrawRoundedRect(b, toast, new Color(38, 53, 68) * (0.96f * alpha), 9);\n        DrawRoundedBorder(b, toast, CardchaUi.Gold * alpha, 2, 9);\n        CardchaUi.DrawAutoFitWrappedText(\n            b,\n            Game1.smallFont,\n            this.FavoriteToast,\n            Inflate(toast, -8),\n            Color.White * alpha,\n            maxLines: 1,\n            minScale: 0.72f,\n            centerX: true,\n            maxScale: 1.0f,\n            centerY: true\n        );\n    }\n\n    private bool IsStoredEquipped(string id)\n        => this.Save.Data.EquippedCards.Contains(id, StringComparer.OrdinalIgnoreCase);\n'''
    if 'private void DrawFavoriteToast(SpriteBatch b)' not in text:
        if toast_anchor not in text:
            raise AssertionError('Could not locate toast insertion anchor')
        text = text.replace(toast_anchor, toast_method, 1)

    path.write_text(text)


def patch_furniture_alignment() -> None:
    path = ROOT / 'Services/MimiAtticVisualService.cs'
    text = path.read_text()
    text = text.replace('private const string DecorVersion = "alpha.27.0.7.7.8";',
                        f'private const string DecorVersion = "{DECOR}";')

    # Fractional TileLocation did not affect Furniture.draw because the sprite draw position is
    # derived from boundingBox/drawPosition. Shift the TV's real pixel bounding box by +16 px,
    # then recalculate drawPosition. Screenshot measurement puts the TV ~16 px left of sofa center.
    text = text.replace('TryAddFurniture(attic, "(F)1466", 4, 7, offsetX: -0.25f); // Quarter-tile nudge: visual center matches rug + couch.',
                        'TryAddFurniture(attic, "(F)1466", 4, 7, pixelOffsetX: 16); // Real +16px draw/collision shift: centered with rug + couch.')

    old_sig = '''        int y,\n        int rotation = 0,\n        string? heldId = null,\n        float offsetX = 0f)\n'''
    new_sig = '''        int y,\n        int rotation = 0,\n        string? heldId = null,\n        int pixelOffsetX = 0)\n'''
    if new_sig not in text:
        if old_sig not in text:
            raise AssertionError('Could not locate TryAddFurniture offset signature')
        text = text.replace(old_sig, new_sig, 1)

    old_offset = '''            Furniture item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);\n            if (Math.Abs(offsetX) > 0.001f)\n                item.TileLocation = new Vector2(x + offsetX, y);\n            item.modData[DecorMarkerKey] = DecorVersion;\n'''
    new_offset = '''            Furniture item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);\n            if (pixelOffsetX != 0)\n            {\n                Rectangle box = item.boundingBox.Value;\n                box.X += pixelOffsetX;\n                item.boundingBox.Value = box;\n                item.updateDrawPosition();\n            }\n            item.modData[DecorMarkerKey] = DecorVersion;\n'''
    if new_offset not in text:
        if old_offset not in text:
            raise AssertionError('Could not locate ineffective fractional Furniture offset block')
        text = text.replace(old_offset, new_offset, 1)

    path.write_text(text)


def validate() -> None:
    binder = (ROOT / 'UI/CardchaBinderMenu.cs').read_text()
    visual = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()
    assert ': FavoriteActionId;' in binder
    assert 'this.FavoriteActionButton.leftNeighborID = focusedId;' in binder
    assert 'private CardDefinition? GetFavoriteTargetCard()' in binder
    assert 'this.DrawFavoriteToast(b);' in binder
    assert 'private void DrawFavoriteToast(SpriteBatch b)' in binder
    assert 'pixelOffsetX: 16' in visual
    assert 'item.boundingBox.Value = box;' in visual
    assert 'item.updateDrawPosition();' in visual
    assert 'offsetX: -0.25f' not in visual
    assert DECOR in visual
    assert json.loads((ROOT / 'manifest.json').read_text())['Version'] == TARGET


def main() -> None:
    patch_binder()
    patch_furniture_alignment()
    set_versions()
    validate()
    print('0.7.7.9 controller favorite navigation + rendered toast + real TV pixel alignment applied')


if __name__ == '__main__':
    main()

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

    field_anchor = '    private CardDefinition? LockedCard;\n'
    field_new = field_anchor + '    private CardDefinition? ControllerActionTarget;\n'
    if 'private CardDefinition? ControllerActionTarget;' not in text:
        if field_anchor not in text:
            raise AssertionError('Could not locate LockedCard field')
        text = text.replace(field_anchor, field_new, 1)

    old_preamble = '''        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n        if (collectionFocused)\n        {\n            // The Favorite button remembers the exact collection component that led into it.\n            // Both its label and action resolve from this same ID, so they cannot disagree.\n            this.FavoriteActionButton.leftNeighborID = focusedId;\n            this.PreviewCard = this.CardButtons[focusedId - CardBaseId].Card;\n        }\n\n        if (focusedId == FavoriteActionId && this.Controller.IsConfirm(b))\n        {\n            // Do not maintain a second controller-only Favorite implementation. Synchronize the\n            // controller card into the same state mouse hover uses, then call the exact mouse\n            // left-click path on the visible Favorite button.\n            CardDefinition? target = this.GetFavoriteTargetCard();\n            if (target is not null)\n            {\n                this.PreviewCard = target;\n                this.Selected = target;\n            }\n\n            Rectangle favorite = this.FavoriteActionButton.bounds;\n            this.receiveLeftClick(favorite.Center.X, favorite.Center.Y, playSound: true);\n            return;\n        }\n'''
    new_preamble = '''        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n        if (collectionFocused)\n            this.CaptureControllerActionTarget(focusedId);\n'''
    if new_preamble not in text:
        if old_preamble not in text:
            raise AssertionError('Could not locate 0.7.8.3 controller preamble')
        text = text.replace(old_preamble, new_preamble, 1)

    old_after_base = '''        base.receiveGamePadButton(b);\n        this.EnsureControllerFocusValid();\n        this.SyncBrowsePreviewToFocusedCard();\n'''
    new_after_base = '''        base.receiveGamePadButton(b);\n        this.EnsureControllerFocusValid();\n        this.SyncBrowsePreviewToFocusedCard();\n        int movedFocusId = this.currentlySnappedComponent?.myID ?? -1;\n        if (movedFocusId >= CardBaseId && movedFocusId < CardBaseId + this.CardButtons.Count)\n            this.CaptureControllerActionTarget(movedFocusId);\n'''
    if new_after_base not in text:
        if old_after_base not in text:
            raise AssertionError('Could not locate controller base navigation tail')
        text = text.replace(old_after_base, new_after_base, 1)

    activation_anchor = '''        int id = focused.myID;\n        if (id >= CardBaseId && id < CardBaseId + this.CardButtons.Count)\n'''
    activation_new = '''        int id = focused.myID;\n        if (fromController && this.LastInputWasController && IsDetailActionId(id))\n        {\n            this.PrepareControllerActionTargetForMousePath();\n            Rectangle action = focused.bounds;\n            this.receiveLeftClick(action.Center.X, action.Center.Y, playSound: true);\n            // receiveLeftClick correctly runs the mouse implementation, but it also marks the\n            // latest input as mouse. Restore controller presentation after the synthetic click.\n            this.LastInputWasController = true;\n            return;\n        }\n\n        if (id >= CardBaseId && id < CardBaseId + this.CardButtons.Count)\n'''
    if 'PrepareControllerActionTargetForMousePath();' not in text:
        if activation_anchor not in text:
            raise AssertionError('Could not locate ActivateFocusedComponent ID block')
        text = text.replace(activation_anchor, activation_new, 1)

    old_target = '''    private CardDefinition? GetFavoriteTargetCard()\n    {\n        if (this.LastInputWasController && this.currentlySnappedComponent?.myID == FavoriteActionId)\n        {\n            int sourceId = this.FavoriteActionButton.leftNeighborID;\n            int sourceIndex = sourceId - CardBaseId;\n            if (sourceIndex >= 0 && sourceIndex < this.CardButtons.Count)\n                return this.CardButtons[sourceIndex].Card;\n        }\n\n        return this.PreviewCard ?? this.Selected ?? this.LockedCard;\n    }\n\n'''
    new_target = '''    private static bool IsDetailActionId(int id)\n        => id == FavoriteActionId || id == EquipActionId || id == UpgradeActionId || id == DeselectActionId;\n\n    private void CaptureControllerActionTarget(int focusedCardId)\n    {\n        int index = focusedCardId - CardBaseId;\n        if (index < 0 || index >= this.CardButtons.Count)\n            return;\n\n        CardDefinition card = this.CardButtons[index].Card;\n        this.ControllerActionTarget = card;\n        this.PreviewCard = card;\n        this.Selected = card;\n        this.FavoriteActionButton.leftNeighborID = focusedCardId;\n    }\n\n    private void PrepareControllerActionTargetForMousePath()\n    {\n        CardDefinition? target = this.ControllerActionTarget ?? this.PreviewCard ?? this.Selected ?? this.LockedCard;\n        if (target is null)\n            return;\n\n        // Make every detail action see exactly the same card state that a real mouse click sees.\n        this.ControllerActionTarget = target;\n        this.PreviewCard = target;\n        this.Selected = target;\n        this.LockedCard = target;\n        this.ControllerSelectionLocked = true;\n    }\n\n    private CardDefinition? GetFavoriteTargetCard()\n    {\n        if (this.LastInputWasController\n            && IsDetailActionId(this.currentlySnappedComponent?.myID ?? -1)\n            && this.ControllerActionTarget is not null)\n        {\n            return this.ControllerActionTarget;\n        }\n\n        return this.PreviewCard ?? this.Selected ?? this.LockedCard;\n    }\n\n'''
    if 'private void CaptureControllerActionTarget(int focusedCardId)' not in text:
        if old_target not in text:
            raise AssertionError('Could not locate 0.7.8.3 GetFavoriteTargetCard')
        text = text.replace(old_target, new_target, 1)

    old_draw = '''    private void DrawActionButtons(SpriteBatch b, bool owned)\n    {\n        CardDefinition? favoriteTarget = this.GetFavoriteTargetCard();\n        bool favorite = favoriteTarget is not null\n            && this.Save.Data.OwnedCards.Contains(favoriteTarget.Id)\n            && this.Save.Data.FavoriteCardIds.Contains(favoriteTarget.Id);\n        bool equipped = owned && this.Selected is not null && this.IsStoredEquipped(this.Selected.Id);\n        bool maxed = !owned || this.Selected is null || this.Upgrades.IsMaxLevel(this.Selected);\n        int have = this.Selected is null ? 0 : this.Upgrades.GetCopies(this.Selected);\n        int need = this.Selected is null ? 0 : this.Upgrades.GetRequiredCopies(this.Selected);\n\n        this.DrawSmallButton(\n            b,\n            this.FavoriteActionButton,\n            favorite ? "★ " + ModEntry.T("binder.favorite.remove") : "☆ " + ModEntry.T("binder.favorite.add"),\n            owned ? CardchaUi.Gold : new Color(130, 120, 112)\n        );\n\n        this.DrawSmallButton(\n            b,\n            this.EquipActionButton,\n            equipped ? ModEntry.T("binder.unequip") : ModEntry.T("binder.equip"),\n            owned ? (equipped ? CardchaUi.DangerRed : CardchaUi.GoodGreen) : new Color(130, 120, 112)\n        );\n\n        string upgrade = maxed\n            ? ModEntry.T("binder.upgrade.max")\n            : ModEntry.T("binder.upgrade", new { have, need });\n        Color upgradeColor = !maxed && have >= need ? CardchaUi.PremiumPurple : new Color(130, 120, 112);\n        this.DrawSmallButton(b, this.UpgradeActionButton, upgrade, upgradeColor);\n'''
    new_draw = '''    private void DrawActionButtons(SpriteBatch b, bool owned)\n    {\n        CardDefinition? actionTarget = this.LastInputWasController\n            && IsDetailActionId(this.currentlySnappedComponent?.myID ?? -1)\n            && this.ControllerActionTarget is not null\n                ? this.ControllerActionTarget\n                : this.Selected;\n        bool actionOwned = actionTarget is not null && this.Save.Data.OwnedCards.Contains(actionTarget.Id);\n        bool favorite = actionOwned && this.Save.Data.FavoriteCardIds.Contains(actionTarget!.Id);\n        bool equipped = actionOwned && this.IsStoredEquipped(actionTarget!.Id);\n        bool maxed = !actionOwned || actionTarget is null || this.Upgrades.IsMaxLevel(actionTarget);\n        int have = actionTarget is null ? 0 : this.Upgrades.GetCopies(actionTarget);\n        int need = actionTarget is null ? 0 : this.Upgrades.GetRequiredCopies(actionTarget);\n\n        this.DrawSmallButton(\n            b,\n            this.FavoriteActionButton,\n            favorite ? "★ " + ModEntry.T("binder.favorite.remove") : "☆ " + ModEntry.T("binder.favorite.add"),\n            actionOwned ? CardchaUi.Gold : new Color(130, 120, 112)\n        );\n\n        this.DrawSmallButton(\n            b,\n            this.EquipActionButton,\n            equipped ? ModEntry.T("binder.unequip") : ModEntry.T("binder.equip"),\n            actionOwned ? (equipped ? CardchaUi.DangerRed : CardchaUi.GoodGreen) : new Color(130, 120, 112)\n        );\n\n        string upgrade = maxed\n            ? ModEntry.T("binder.upgrade.max")\n            : ModEntry.T("binder.upgrade", new { have, need });\n        Color upgradeColor = !maxed && have >= need ? CardchaUi.PremiumPurple : new Color(130, 120, 112);\n        this.DrawSmallButton(b, this.UpgradeActionButton, upgrade, upgradeColor);\n'''
    if new_draw not in text:
        if old_draw not in text:
            raise AssertionError('Could not locate DrawActionButtons target logic')
        text = text.replace(old_draw, new_draw, 1)

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

    # TV was accepted by the user in 0.7.8.3; do not move it again.
    if 'pixelOffsetX: -32); // TV accepted' not in text:
        text = text.replace(
            'TryAddFurniture(attic, "(F)1466", 4, 7, pixelOffsetX: -32); // TV accepted visual center after 0.7.8.3 left nudge.',
            'TryAddFurniture(attic, "(F)1466", 4, 7, pixelOffsetX: -32); // TV accepted visual center after 0.7.8.3 left nudge.',
            1,
        )

    path.write_text(text)


def validate() -> None:
    binder = (ROOT / 'UI/CardchaBinderMenu.cs').read_text()
    visual = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()

    assert 'private CardDefinition? ControllerActionTarget;' in binder
    assert 'this.CaptureControllerActionTarget(focusedId);' in binder
    assert 'private void PrepareControllerActionTargetForMousePath()' in binder
    assert 'IsDetailActionId(id)' in binder
    assert 'this.receiveLeftClick(action.Center.X, action.Center.Y, playSound: true);' in binder
    assert 'this.LastInputWasController = true;' in binder
    assert 'bool actionOwned = actionTarget is not null' in binder
    assert 'ControllerFavoriteTarget' not in binder
    assert 'FavoriteControllerDebounceMs' not in binder

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

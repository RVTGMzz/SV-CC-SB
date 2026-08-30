from pathlib import Path
import json, re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.8.9'


def set_version(path: Path):
    text = path.read_text()
    text, n = re.subn(r'0\.3\.0-alpha\.27\.0\.7\.8\.\d+', TARGET, text)
    if n == 0 and TARGET not in text:
        raise AssertionError(f'No version replacement in {path}')
    path.write_text(text)


p = ROOT / 'UI/CardchaBinderMenu.cs'
text = p.read_text()

old_sync = '''    private void SyncBrowsePreviewToFocusedCard()\n    {\n        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        if (focusedId < CardBaseId || focusedId >= CardBaseId + this.CardButtons.Count)\n            return;\n\n        int index = focusedId - CardBaseId;\n        CardDefinition card = this.CardButtons[index].Card;\n        this.PreviewCard = card;\n        this.FavoriteActionButton.leftNeighborID = focusedId;\n\n        // Browsing a new collection card must also move the visible/action card. Keeping\n        // Selected frozen on an older LockedCard was the root cause of \"first card works, second\n        // card fails\" for both Favorite and Equip on controller.\n        this.Selected = card;\n        this.Status = this.Save.Data.OwnedCards.Contains(card.Id)\n            ? string.Empty\n            : ModEntry.T(\"binder.status.not-owned\");\n    }\n'''
new_sync = '''    private void SyncBrowsePreviewToFocusedCard()\n    {\n        int focusedId = this.currentlySnappedComponent?.myID ?? -1;\n        if (focusedId < CardBaseId || focusedId >= CardBaseId + this.CardButtons.Count)\n            return;\n\n        int index = focusedId - CardBaseId;\n        CardDefinition card = this.CardButtons[index].Card;\n        this.PreviewCard = card;\n        this.FavoriteActionButton.leftNeighborID = focusedId;\n\n        // Browsing and selection are intentionally separate states. Once Confirm locks a card,\n        // moving focus over other collection cells may update PreviewCard, but must NOT replace\n        // the selected/action card. This lets controller navigation and Favorite/Equip coexist.\n        if (this.ControllerSelectionLocked && this.LockedCard is not null)\n        {\n            this.Selected = this.LockedCard;\n            this.ControllerActionTarget = this.LockedCard;\n            this.Status = ModEntry.T(\"binder.status.selected\", new { name = this.LockedCard.Name });\n        }\n        else\n        {\n            this.Selected = card;\n            this.ControllerActionTarget = card;\n            this.Status = this.Save.Data.OwnedCards.Contains(card.Id)\n                ? string.Empty\n                : ModEntry.T(\"binder.status.not-owned\");\n        }\n    }\n'''
if new_sync not in text:
    if old_sync not in text:
        raise AssertionError('SyncBrowsePreviewToFocusedCard block missing')
    text = text.replace(old_sync, new_sync, 1)

old_capture = '''    private void CaptureControllerActionTarget(int focusedCardId)\n    {\n        int index = focusedCardId - CardBaseId;\n        if (index < 0 || index >= this.CardButtons.Count)\n            return;\n\n        CardDefinition card = this.CardButtons[index].Card;\n        this.ControllerActionTarget = card;\n        this.PreviewCard = card;\n        this.Selected = card;\n        this.FavoriteActionButton.leftNeighborID = focusedCardId;\n    }\n'''
new_capture = '''    private void CaptureControllerActionTarget(int focusedCardId)\n    {\n        int index = focusedCardId - CardBaseId;\n        if (index < 0 || index >= this.CardButtons.Count)\n            return;\n\n        CardDefinition card = this.CardButtons[index].Card;\n        this.PreviewCard = card;\n        this.FavoriteActionButton.leftNeighborID = focusedCardId;\n\n        if (this.ControllerSelectionLocked && this.LockedCard is not null)\n        {\n            this.ControllerActionTarget = this.LockedCard;\n            this.Selected = this.LockedCard;\n        }\n        else\n        {\n            this.ControllerActionTarget = card;\n            this.Selected = card;\n        }\n    }\n'''
if new_capture not in text:
    if old_capture not in text:
        raise AssertionError('CaptureControllerActionTarget block missing')
    text = text.replace(old_capture, new_capture, 1)

old_prepare = '''    private void PrepareControllerActionTargetForMousePath()\n    {\n        CardDefinition? target = this.ControllerActionTarget ?? this.PreviewCard ?? this.Selected ?? this.LockedCard;\n        if (target is null)\n            return;\n\n        this.ControllerActionTarget = target;\n        this.PreviewCard = target;\n        this.Selected = target;\n        this.LockedCard = target;\n        this.ControllerSelectionLocked = true;\n    }\n\n    private CardDefinition? GetFavoriteTargetCard()\n        => this.Selected ?? this.PreviewCard ?? this.LockedCard;\n'''
new_prepare = '''    private void PrepareControllerActionTargetForMousePath()\n    {\n        CardDefinition? target = this.GetActionTargetCard();\n        if (target is null)\n            return;\n\n        this.ControllerActionTarget = target;\n        this.Selected = target;\n        this.LockedCard = target;\n        this.ControllerSelectionLocked = true;\n    }\n\n    private CardDefinition? GetActionTargetCard()\n        => this.ControllerSelectionLocked && this.LockedCard is not null\n            ? this.LockedCard\n            : this.PreviewCard ?? this.Selected ?? this.ControllerActionTarget;\n\n    private CardDefinition? GetFavoriteTargetCard()\n        => this.GetActionTargetCard();\n'''
if new_prepare not in text:
    if old_prepare not in text:
        raise AssertionError('action target helper block missing')
    text = text.replace(old_prepare, new_prepare, 1)

old_draw = '''        CardDefinition? actionTarget = this.LastInputWasController\n            && IsDetailActionId(this.currentlySnappedComponent?.myID ?? -1)\n            && this.ControllerActionTarget is not null\n                ? this.ControllerActionTarget\n                : this.Selected;\n'''
new_draw = '''        CardDefinition? actionTarget = this.GetActionTargetCard();\n'''
if new_draw not in text:
    if old_draw not in text:
        raise AssertionError('DrawActionButtons target block missing')
    text = text.replace(old_draw, new_draw, 1)

old_toggle = '''    private void ToggleEquip()\n    {\n        if (this.Selected is null || !this.Save.Data.OwnedCards.Contains(this.Selected.Id))\n        {\n            this.ShowFavoriteToast(ModEntry.T(\"binder.status.not-owned\"));\n            Game1.playSound(\"cancel\");\n            return;\n        }\n\n        if (this.IsStoredEquipped(this.Selected.Id))\n        {\n            if (this.Loadout.Unequip(this.Selected.Id))\n            {\n                this.ShowFavoriteToast(ModEntry.T(\"binder.status.unequipped\", new { name = this.Selected.Name }));\n                this.OnLoadoutChanged();\n                Game1.playSound(\"dwop\");\n            }\n            return;\n        }\n\n        if (this.Loadout.Equip(this.Selected.Id))\n        {\n            this.ShowFavoriteToast(ModEntry.T(\"binder.status.equipped\", new { name = this.Selected.Name }));\n            this.OnLoadoutChanged();\n            Game1.playSound(\"coin\");\n        }\n        else\n        {\n            this.ShowFavoriteToast(ModEntry.T(\"binder.status.full\", new { slots = this.UnlockedSlots }));\n            Game1.playSound(\"cancel\");\n        }\n    }\n'''
new_toggle = '''    private void ToggleEquip()\n    {\n        CardDefinition? card = this.GetActionTargetCard();\n        if (card is null || !this.Save.Data.OwnedCards.Contains(card.Id))\n        {\n            this.ShowFavoriteToast(ModEntry.T(\"binder.status.not-owned\"));\n            Game1.playSound(\"cancel\");\n            return;\n        }\n\n        if (this.IsStoredEquipped(card.Id))\n        {\n            if (this.Loadout.Unequip(card.Id))\n            {\n                this.ShowFavoriteToast(ModEntry.T(\"binder.status.unequipped\", new { name = card.Name }));\n                this.OnLoadoutChanged();\n                Game1.playSound(\"dwop\");\n            }\n            return;\n        }\n\n        if (this.Loadout.Equip(card.Id))\n        {\n            this.ShowFavoriteToast(ModEntry.T(\"binder.status.equipped\", new { name = card.Name }));\n            this.OnLoadoutChanged();\n            Game1.playSound(\"coin\");\n        }\n        else\n        {\n            this.ShowFavoriteToast(ModEntry.T(\"binder.status.full\", new { slots = this.UnlockedSlots }));\n            Game1.playSound(\"cancel\");\n        }\n    }\n'''
if new_toggle not in text:
    if old_toggle not in text:
        raise AssertionError('ToggleEquip block missing')
    text = text.replace(old_toggle, new_toggle, 1)

old_upgrade_head = '''    private void TryUpgradeSelected()\n    {\n        if (this.Selected is null || !this.Save.Data.OwnedCards.Contains(this.Selected.Id))\n        {\n            this.Status = ModEntry.T(\"binder.status.not-owned\");\n            Game1.playSound(\"cancel\");\n            return;\n        }\n\n        if (this.Upgrades.IsMaxLevel(this.Selected))\n        {\n            this.Status = ModEntry.T(\"binder.status.card-maxed\", new { name = this.Selected.Name });\n            Game1.playSound(\"cancel\");\n            return;\n        }\n\n        int have = this.Upgrades.GetCopies(this.Selected);\n        int need = this.Upgrades.GetRequiredCopies(this.Selected);\n        if (!this.Upgrades.TryUpgrade(this.Selected, out int newLevel, out int copiesSpent))\n        {\n            this.Status = ModEntry.T(\"binder.status.card-not-enough-copies\", new { have, need });\n            Game1.playSound(\"cancel\");\n            return;\n        }\n\n        this.Status = ModEntry.T(\"binder.status.card-upgraded\", new { name = this.Selected.Name, level = newLevel, copies = copiesSpent });\n        Game1.playSound(\"reward\");\n    }\n'''
new_upgrade_head = '''    private void TryUpgradeSelected()\n    {\n        CardDefinition? card = this.GetActionTargetCard();\n        if (card is null || !this.Save.Data.OwnedCards.Contains(card.Id))\n        {\n            this.Status = ModEntry.T(\"binder.status.not-owned\");\n            Game1.playSound(\"cancel\");\n            return;\n        }\n\n        if (this.Upgrades.IsMaxLevel(card))\n        {\n            this.Status = ModEntry.T(\"binder.status.card-maxed\", new { name = card.Name });\n            Game1.playSound(\"cancel\");\n            return;\n        }\n\n        int have = this.Upgrades.GetCopies(card);\n        int need = this.Upgrades.GetRequiredCopies(card);\n        if (!this.Upgrades.TryUpgrade(card, out int newLevel, out int copiesSpent))\n        {\n            this.Status = ModEntry.T(\"binder.status.card-not-enough-copies\", new { have, need });\n            Game1.playSound(\"cancel\");\n            return;\n        }\n\n        this.Status = ModEntry.T(\"binder.status.card-upgraded\", new { name = card.Name, level = newLevel, copies = copiesSpent });\n        Game1.playSound(\"reward\");\n    }\n'''
if new_upgrade_head not in text:
    if old_upgrade_head not in text:
        raise AssertionError('TryUpgradeSelected block missing')
    text = text.replace(old_upgrade_head, new_upgrade_head, 1)

# The explicit Confirm lock becomes the canonical action target immediately.
needle = '''        this.LockedCard = card;\n        this.ControllerSelectionLocked = true;\n        this.PreviewCard = card;\n        this.Selected = card;\n'''
replacement = '''        this.LockedCard = card;\n        this.ControllerSelectionLocked = true;\n        this.PreviewCard = card;\n        this.Selected = card;\n        this.ControllerActionTarget = card;\n'''
if replacement not in text:
    if needle not in text:
        raise AssertionError('HandleCollectionActivation lock block missing')
    text = text.replace(needle, replacement, 1)

# Releasing the lock must also release the action target; SyncBrowsePreviewToFocusedCard will
# immediately repopulate it from the currently focused card.
needle = '''        this.ControllerSelectionLocked = false;\n        this.LockedCard = null;\n        this.LastQuickToggleCardId = null;\n'''
replacement = '''        this.ControllerSelectionLocked = false;\n        this.LockedCard = null;\n        this.ControllerActionTarget = null;\n        this.LastQuickToggleCardId = null;\n'''
if replacement not in text:
    if needle not in text:
        raise AssertionError('ReleaseSelectionLock clear block missing')
    text = text.replace(needle, replacement, 1)

p.write_text(text)

for f in [ROOT/'Cardcha.csproj', ROOT/'Directory.Build.targets', ROOT/'ModEntry.cs']:
    set_version(f)
manifest = json.loads((ROOT/'manifest.json').read_text())
manifest['Version'] = TARGET
(ROOT/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

final = p.read_text()
assert 'private CardDefinition? GetActionTargetCard()' in final
assert 'this.ControllerSelectionLocked && this.LockedCard is not null' in final
assert 'CardDefinition? actionTarget = this.GetActionTargetCard();' in final
assert 'CardDefinition? card = this.GetActionTargetCard();' in final
assert 'TryConsumeSyntheticDetailClick(x, y)' in final
assert 'ArmSyntheticDetailClickSuppression(id)' in final
print('0.7.8.9 lock + action-target coexistence patch applied')

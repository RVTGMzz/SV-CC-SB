from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.7.8'
DECOR = 'alpha.27.0.7.7.8'


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


def patch_favorite_controller_and_toast() -> None:
    path = ROOT / 'UI/CardchaBinderMenu.cs'
    text = path.read_text()

    old_fields = '''    private string Status = string.Empty;\n    // alpha.23: hint bar follows the most recently used input family and controller profile.\n'''
    new_fields = '''    private string Status = string.Empty;\n    private string FavoriteToast = string.Empty;\n    private long FavoriteToastExpiresAtMs;\n    private const long FavoriteToastDurationMs = 3000L;\n    // alpha.23: hint bar follows the most recently used input family and controller profile.\n'''
    if new_fields not in text:
        if old_fields not in text:
            raise AssertionError('Could not locate Binder status fields')
        text = text.replace(old_fields, new_fields, 1)

    # A focused action button must win before global semantic shortcuts. On Nintendo/native
    # layouts the printed A/B meaning can differ from XInput, so this guarantees that pressing
    # the user's selection button on FAVORITE activates the visible button itself.
    marker = '''        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n\n        // alpha.23: controller actions are semantic and profile-driven. Individual menus never\n'''
    insert = '''        bool collectionFocused = focusedId >= CardBaseId && focusedId < CardBaseId + this.CardButtons.Count;\n\n        if (focusedId == FavoriteActionId\n            && (this.Controller.IsConfirm(b) || this.Controller.IsFavorite(b)))\n        {\n            this.ActivateFavoriteAction();\n            return;\n        }\n\n        // alpha.23: controller actions are semantic and profile-driven. Individual menus never\n'''
    if insert not in text:
        if marker not in text:
            raise AssertionError('Could not locate controller focus preamble')
        text = text.replace(marker, insert, 1)

    # Global favorite shortcut should use the same action core, but only after restoring the
    # explicitly locked card. This no longer competes with the focused Favorite button above.
    old_global = '''        if (this.Controller.IsFavorite(b))\n        {\n            if (this.ControllerSelectionLocked && this.LockedCard is not null)\n            {\n                this.RestoreLockedSelectionForAction();\n                this.ToggleFavorite();\n            }\n            else\n            {\n                this.Status = ModEntry.T("binder.favorite.select-first");\n                Game1.playSound("cancel");\n            }\n            return;\n        }\n'''
    new_global = '''        if (this.Controller.IsFavorite(b))\n        {\n            if (this.ControllerSelectionLocked && this.LockedCard is not null)\n            {\n                this.RestoreLockedSelectionForAction();\n                this.ActivateFavoriteAction();\n            }\n            else\n            {\n                this.ShowFavoriteToast(ModEntry.T("binder.favorite.select-first"));\n                Game1.playSound("cancel");\n            }\n            return;\n        }\n'''
    if new_global not in text:
        if old_global not in text:
            raise AssertionError('Could not locate controller favorite shortcut')
        text = text.replace(old_global, new_global, 1)

    # Keyboard shortcut follows the same core too.
    old_key = '''        if (key == Keys.F)\n        {\n            if (this.ControllerSelectionLocked && this.LockedCard is not null)\n            {\n                this.RestoreLockedSelectionForAction();\n                this.ToggleFavorite();\n            }\n            else\n            {\n                this.Status = ModEntry.T("binder.favorite.select-first");\n                Game1.playSound("cancel");\n            }\n            return;\n        }\n'''
    new_key = '''        if (key == Keys.F)\n        {\n            if (this.ControllerSelectionLocked && this.LockedCard is not null)\n            {\n                this.RestoreLockedSelectionForAction();\n                this.ActivateFavoriteAction();\n            }\n            else\n            {\n                this.ShowFavoriteToast(ModEntry.T("binder.favorite.select-first"));\n                Game1.playSound("cancel");\n            }\n            return;\n        }\n'''
    if new_key not in text:
        if old_key not in text:
            raise AssertionError('Could not locate keyboard favorite shortcut')
        text = text.replace(old_key, new_key, 1)

    # Explicit controller Confirm path for Favorite. Mouse click below calls the same helper.
    action_marker = '''        if (id == EquipActionId)\n        {\n            this.RestoreLockedSelectionForAction();\n            this.ToggleEquip();\n            return;\n        }\n'''
    action_insert = '''        if (id == FavoriteActionId)\n        {\n            this.ActivateFavoriteAction();\n            return;\n        }\n\n        if (id == EquipActionId)\n        {\n            this.RestoreLockedSelectionForAction();\n            this.ToggleEquip();\n            return;\n        }\n'''
    if action_insert not in text:
        if action_marker not in text:
            raise AssertionError('Could not locate action-button controller block')
        text = text.replace(action_marker, action_insert, 1)

    old_mouse = '''        if (Inflate(this.FavoriteActionButton.bounds, 3).Contains(x, y))\n        {\n            this.RestoreLockedSelectionForAction();\n            this.ToggleFavorite();\n            return;\n        }\n'''
    new_mouse = '''        if (Inflate(this.FavoriteActionButton.bounds, 3).Contains(x, y))\n        {\n            this.ActivateFavoriteAction();\n            return;\n        }\n'''
    if new_mouse not in text:
        if old_mouse not in text:
            raise AssertionError('Could not locate mouse Favorite block')
        text = text.replace(old_mouse, new_mouse, 1)

    old_toggle = '''    private void ToggleFavorite()\n    {\n        if (this.Selected is null || !this.Save.Data.OwnedCards.Contains(this.Selected.Id))\n        {\n            this.Status = ModEntry.T("binder.favorite.locked");\n            Game1.playSound("cancel");\n            return;\n        }\n\n        if (this.Save.Data.FavoriteCardIds.Contains(this.Selected.Id))\n        {\n            this.Save.Data.FavoriteCardIds.Remove(this.Selected.Id);\n            this.Status = ModEntry.T("binder.favorite.removed", new { name = this.Selected.Name });\n        }\n        else\n        {\n            this.Save.Data.FavoriteCardIds.Add(this.Selected.Id);\n            this.Status = ModEntry.T("binder.favorite.added", new { name = this.Selected.Name });\n        }\n\n        this.Save.Save();\n        Game1.playSound("coin");\n\n        if (this.CurrentFilter == BinderFilter.Favorite)\n            this.RebuildCardButtons(resetPage: false);\n    }\n'''
    new_toggle = '''    private void ActivateFavoriteAction()\n    {\n        // The action always targets the card currently rendered on the right page. Do not\n        // rebind Selected here from an older controller lock: the button label and the action\n        // now read the same card state, so ☆ can never report \"removed\" on first activation.\n        CardDefinition? card = this.Selected;\n        if (card is null || !this.Save.Data.OwnedCards.Contains(card.Id))\n        {\n            this.ShowFavoriteToast(ModEntry.T("binder.favorite.locked"));\n            Game1.playSound("cancel");\n            return;\n        }\n\n        bool wasFavorite = this.Save.Data.FavoriteCardIds.Contains(card.Id);\n        if (wasFavorite)\n            this.Save.Data.FavoriteCardIds.Remove(card.Id);\n        else\n            this.Save.Data.FavoriteCardIds.Add(card.Id);\n\n        this.ShowFavoriteToast(\n            wasFavorite\n                ? ModEntry.T("binder.favorite.removed", new { name = card.Name })\n                : ModEntry.T("binder.favorite.added", new { name = card.Name })\n        );\n        this.Save.Save();\n        Game1.playSound("coin");\n\n        if (this.CurrentFilter == BinderFilter.Favorite)\n            this.RebuildCardButtons(resetPage: false);\n    }\n\n    private void ShowFavoriteToast(string text)\n    {\n        this.Status = string.Empty;\n        this.FavoriteToast = text;\n        this.FavoriteToastExpiresAtMs = Environment.TickCount64 + FavoriteToastDurationMs;\n    }\n'''
    if new_toggle not in text:
        if old_toggle not in text:
            raise AssertionError('Could not locate ToggleFavorite implementation')
        text = text.replace(old_toggle, new_toggle, 1)

    old_draw_start = '''    private void DrawStatus(SpriteBatch b)\n    {\n        if (this.IsLoadoutFullStatus())\n            return;\n'''
    new_draw_start = '''    private void DrawStatus(SpriteBatch b)\n    {\n        if (!string.IsNullOrWhiteSpace(this.FavoriteToast))\n        {\n            if (Environment.TickCount64 < this.FavoriteToastExpiresAtMs)\n            {\n                Rectangle toastArea = new(\n                    this.RightPage.X + 64,\n                    this.FavoriteActionButton.bounds.Y - 46,\n                    this.RightPage.Width - 128,\n                    38\n                );\n                DrawRoundedRect(b, toastArea, new Color(58, 77, 81) * 0.96f, 8);\n                DrawRoundedBorder(b, toastArea, new Color(201, 165, 92), 2, 8);\n                CardchaUi.DrawAutoFitWrappedText(\n                    b, Game1.smallFont, this.FavoriteToast, Inflate(toastArea, -6), Color.White,\n                    maxLines: 1, minScale: 0.72f, centerX: true, maxScale: 0.96f, centerY: true\n                );\n                return;\n            }\n\n            this.FavoriteToast = string.Empty;\n            this.FavoriteToastExpiresAtMs = 0;\n        }\n\n        if (this.IsLoadoutFullStatus())\n            return;\n'''
    if new_draw_start not in text:
        if old_draw_start not in text:
            raise AssertionError('Could not locate DrawStatus start')
        text = text.replace(old_draw_start, new_draw_start, 1)

    if 'this.ToggleFavorite();' in text:
        raise AssertionError('Legacy ToggleFavorite call remains')
    path.write_text(text)


def patch_tv_visual_center() -> None:
    path = ROOT / 'Services/MimiAtticVisualService.cs'
    text = path.read_text()
    text = text.replace('private const string DecorVersion = "alpha.27.0.7.7.7";',
                        f'private const string DecorVersion = "{DECOR}";')

    old_tv = 'TryAddFurniture(attic, "(F)1466", 4, 7, offsetX: -0.5f); // TV half-tile left nudge: centered with rug + couch.'
    new_tv = 'TryAddFurniture(attic, "(F)1466", 4, 7, offsetX: -0.25f); // Quarter-tile nudge: visual center matches rug + couch.'
    if new_tv not in text:
        if old_tv not in text:
            raise AssertionError('Could not locate 0.7.7.7 TV placement')
        text = text.replace(old_tv, new_tv, 1)

    path.write_text(text)


def validate() -> None:
    binder = (ROOT / 'UI/CardchaBinderMenu.cs').read_text()
    visual = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()
    assert 'focusedId == FavoriteActionId' in binder
    assert 'this.Controller.IsConfirm(b) || this.Controller.IsFavorite(b)' in binder
    assert 'private void ActivateFavoriteAction()' in binder
    assert 'private void ShowFavoriteToast(string text)' in binder
    assert 'FavoriteToastDurationMs = 3000L' in binder
    assert 'Environment.TickCount64 < this.FavoriteToastExpiresAtMs' in binder
    assert 'this.ToggleFavorite();' not in binder
    assert 'offsetX: -0.25f' in visual
    assert 'offsetX: -0.5f' not in visual
    assert DECOR in visual
    assert json.loads((ROOT / 'manifest.json').read_text())['Version'] == TARGET


def main() -> None:
    patch_favorite_controller_and_toast()
    patch_tv_visual_center()
    set_versions()
    validate()
    print('0.7.7.8 controller favorite + 3s toast + TV center fix applied')


if __name__ == '__main__':
    main()

# NEXT SESSION — Cardcha v0.3.0-alpha.19 Controller Remap

## Current candidate
- Version: `0.3.0-alpha.19`
- Build label: `Cardcha! v0.3.0-alpha.19 CONTROLLER REMAP`
- Baseline: alpha.18 Binder Lock + Typography.

## Controller contract
- **B (bottom):** Select/Confirm the focused component. On a collection card it creates/replaces the locked card. On Equip/Unequip/Upgrade/filter/etc it activates that focused control.
- **A (right):** Favorite shortcut for the explicitly locked card only. If no card is locked, it refuses and asks the player to select one first.
- **Y (left):** Deselect. Releases `LockedCard` and returns to free preview.
- **X (top):** Exit Binder completely to gameplay.

## Exit behavior
- Controller X, keyboard Escape, and the Binder top-left X close the Binder directly to gameplay.
- They do NOT restore the background Inventory, ItemGrab/chest menu, or Cardcha Machine menu behind the Binder.

## Fix for dead action buttons
- Alpha.18 had B mapped to Close while focused action buttons were waiting for A, so controller users could navigate to Equip/Upgrade but couldn't use them naturally.
- Alpha.19 routes B through `ActivateFocusedComponent()`.
- `EquipActionId` dispatches `ToggleEquip()` and `UpgradeActionId` dispatches `TryUpgradeSelected()` after restoring the persistent `LockedCard` action context.

## Inherited behavior
- alpha.18 separate `PreviewCard` / `LockedCard` state machine and persistent lock.
- pixel page arrows and enlarged Binder footer/filter/not-owned typography.
- alpha.17 `Kỹ năng Thần Thoại / Mythic Skill` wording and MiMi/??? minimap marker fixes.
- all earlier MiMi shop/flight, Gacha, Scrap rail, Favorite, and 80-card Binder behavior.

## Test first
1. Free-preview cards without selecting.
2. Press B on card #03: #03 becomes locked.
3. Navigate to Equip/Unequip and press B: action executes on #03.
4. Navigate to Upgrade and press B: action executes on #03, or shows the appropriate copies/max-level feedback.
5. Press A: Favorite toggles for #03 only.
6. Press Y: lock clears and free preview resumes.
7. Open Binder from Inventory/chest/machine, then press X: all Binder/background menu UI disappears and gameplay resumes immediately.

## Artifacts
- `Cardcha_v0.3.0-alpha.19_ControllerRemap_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.19_SOURCE_SNAPSHOT.zip`

Targeted static validation: 16/16 PASS. Real Windows compile with Stardew/SMAPI references is still required.
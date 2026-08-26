# NEXT SESSION — Cardcha v0.3.0-alpha.22 Nintendo Controller Fix

## Root cause
The user's controller is Nintendo-labeled by physical position, while XNA/MonoGame reports the same face-button positions with Xbox enum names. The correct translation is:
- physical Nintendo B (bottom) -> `Buttons.A`
- physical Nintendo A (right) -> `Buttons.B`
- physical Nintendo Y (left) -> `Buttons.X`
- physical Nintendo X (top) -> `Buttons.Y`

## Binder contract
- physical **B bottom** = Select / Confirm (`Buttons.A`)
- physical **A right** = Favorite locked card (`Buttons.B`)
- physical **Y left** = Deselect (`Buttons.X`)
- physical **X top** = Exit Binder + visual parent UI to gameplay (`Buttons.Y`)

Equip/Unequip/Upgrade are confirmed with the same physical B-bottom button.

## Gacha contract
- physical **B bottom** skips the ritual.
- physical A/X/Y do not skip and are consumed during the ritual.
- controller hint says `B: Bỏ qua`, matching the label printed on the user's controller.

## Inherited behavior
- alpha.21 full outer-panel ritual flash and input-family hint switching.
- alpha.20 Binder control hint bar.
- alpha.18 PreviewCard/LockedCard state machine and persistent selection lock.
- alpha.17 Mythic wording and MiMi/??? minimap fixes.
- all earlier MiMi shop/flight, Scrap rail, Gacha, Favorite, loadout and Binder behavior.

## Test first
1. Binder: physical B selects a card.
2. Physical A favorites only the selected card.
3. Physical Y deselects.
4. Physical X exits straight to gameplay.
5. Focus Equip/Unequip/Upgrade and press physical B: action executes on the locked card.
6. Gacha: only physical B skips; physical A/X/Y do nothing.

## Artifacts
- `Cardcha_v0.3.0-alpha.22_NintendoControllerFix_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.22_SOURCE_SNAPSHOT.zip`

Targeted static validation: 13/13 PASS. Real Windows compile with Stardew/SMAPI references is still required.
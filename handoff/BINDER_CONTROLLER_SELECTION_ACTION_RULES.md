# Binder controller selection/action rules

Accepted baseline: `0.3.0-alpha.27.0.7.8.9`
Branch: `cardcha-alpha27-mimi-real-npc`

This file documents the controller-selection rules that must be preserved in future Binder work. These rules were established after repeated regressions around Favorite/Equip and card selection.

## Core state model

Never collapse these concepts into one mutable card state:

- `PreviewCard`: the card currently under controller focus while browsing the Collection.
- `LockedCard`: the card explicitly chosen with Confirm. This is the user's persistent selection.
- Action target: use the locked card when one exists; otherwise fall back to the current preview.

Conceptually:

```text
ActionCard = LockedCard ?? PreviewCard
```

`Selected` may be used for rendering/internal compatibility, but browsing must not overwrite a valid locked selection.

## Required behavior

1. Moving the controller through Collection cards updates preview only.
2. After Confirm selects/locks card A, moving focus to card B/C/etc must NOT forget card A.
3. Favorite, Equip and Upgrade must all act on the same action target.
4. Button labels must read the same action target used by the button action:
   - Favorite vs Remove Favorite
   - Equip vs Unequip
5. Confirming another Collection card intentionally replaces the lock with that new card.
6. Deselect is what clears the persistent lock; after deselect, actions may follow the preview card again.
7. Filtering/page rebuilds must not silently discard a valid lock unless the user explicitly deselects or the locked card is genuinely unavailable.

## Controller double-toggle protection

Preserve the `0.7.8.8` synthetic-click protection.

Stardew/controller runtimes can deliver a Confirm through the gamepad path and then synthesize a mouse click at the snapped cursor. Favorite and Equip are two-way toggles, so executing both paths causes:

```text
Favorite: add -> immediately remove
Equip: equip -> immediately unequip
```

Therefore, after controller activation of Favorite/Equip, suppress exactly the matching synthetic detail click for the short protection window. Do not remove this fix while changing selection logic.

Important distinction:

- Upgrade/Deselect can appear to work even under duplicate activation because they don't symmetrically undo themselves.
- Favorite/Equip expose the duplicate-input bug immediately because a second activation reverses the first.

## Anti-regression rule

Do NOT fix a Favorite/Equip target bug by making Collection browsing overwrite the locked selection. That was the regression that made actions work while breaking persistent selection.

Likewise, do NOT fix persistent selection by making action buttons read a stale locked card while their labels read the preview card. Label and action must always use the same target.

## Minimum controller regression test

Before accepting any future Binder/controller change, test this exact sequence:

1. Focus Collection card A.
2. Confirm card A.
3. Move focus across card B and card C.
4. Verify card A is still visibly selected/locked.
5. Move to Favorite; toggle it once. It must affect card A exactly once.
6. Move to Equip; toggle it once. It must affect card A exactly once.
7. Return to Collection and Confirm card B.
8. Verify the lock moves from A to B.
9. Favorite/Equip must now affect B.
10. Deselect B.
11. Move focus to card C without confirming it; action buttons may now use preview card C.

Also verify several consecutive Favorite/Equip presses do not double-toggle in a single physical press.

## Accepted implementation lesson

The stable design is:

```text
focus navigation -> PreviewCard
Confirm on Collection -> LockedCard
button label/action -> LockedCard if present, else PreviewCard
Deselect -> clear LockedCard
controller Favorite/Equip -> preserve synthetic-click suppression
```

If future UI refactors touch `CardchaBinderMenu`, treat this behavior as a non-regression contract, not an implementation detail.

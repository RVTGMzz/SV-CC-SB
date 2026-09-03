# alpha28.0.4.14.4.5.2 Gate / HUD / Energy / Sprite Fix

## User feedback addressed

- Move the Forest Arcane Gate decisively farther LEFT from the Farm entrance.
- Keep Forest compatibility contract: presentation only, `CollisionEdits=NONE`, no tile/collision mutation.
- Add proximity auto-entry at the Forest gate so a custom fence/tree cannot make the portal interaction unreachable.
- Remove the loud READY/charging instruction line under the ChaCha Energy bar and stop the white-flash READY border.
- Slow ChaCha Boss Energy gain to roughly half the previous pace while preserving source proportions.
- Repair the three visibly squashed sprite sheets: `items.png`, `chacha_skill_materials.png`, `chacha_skill_icons.png`.

## Boss Energy test tuning

- Regular kill: 10 -> 5
- Boss-like kill: 20 -> 10
- Crit-like event: 1 -> 0.5
- Damage contribution: 1 Energy / 100 damage -> 1 / 200 damage
- Damage gain cap per hit: 2 -> 1

Boss Form duration remains 10 seconds and activation inputs are unchanged.

## Sprite contract

Atlas dimensions remain compatible with existing runtime source rectangles:

- `items.png`: 112x16, seven horizontal 16x16 object cells.
- `chacha_skill_materials.png`: 128x32, four horizontal 32x32 material cells.
- `chacha_skill_icons.png`: 128x32, four horizontal 32x32 skill cells.

The first three item cells are restored from the known-good pre-ChaCha-material Cardcha backup. New material/icon cells are normalized without changing stable object IDs or sprite indices.

## Out of scope

- No change to Binder layout/scale in this milestone.
- No change to locked `airship_visual.png`.
- No Region II/Boss content expansion.
- No Forest map replacement or collision edits.

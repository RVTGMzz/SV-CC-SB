# Cardcha alpha28.0.4.14.1 - Airship UX Hotfix

Branch: `cardcha-alpha28-054-airship-ux-hotfix`
Version: `0.3.0-alpha.28.0.4.14.1`
Purpose: hotfix user-reported `.4.14` UX issues without enabling permanent Airship upgrade bonuses.

## User report that triggered this hotfix

After first in-game `.4.14` test, the user reported:
- Scavenger / Nhặt Nhạnh looked like it had no active buff.
- Airship Upgrade Menu text was too small.
- Controller navigation jumped between rows in the wrong order.
- Selected row fill and controller focus border could disagree.
- Forest Arcane Gate could visually sit behind/in front of a bush at the chosen boarding point.
- Cardcha-owned exit lanes should transition automatically when the player walks to the endpoint instead of requiring another Action press.

## Implemented

### Airship Upgrade Menu controller fix
- Controller focus is row-only.
- Up/Down move exactly one row in strict order 1 -> 2 -> 3 -> 4.
- No wrap from row 4 back to row 1 or row 1 to row 4.
- Left/Right are consumed because this is a vertical list.
- Added 140ms navigation debounce to suppress duplicate physical controller events reaching both key/gamepad paths.
- Confirm upgrades the currently selected row.
- Cancel/Deselect closes the menu.
- Selected fill and focus border now share the same row state.

### Airship Upgrade Menu readability
- Maximum menu width increased from 920 to 1080 when viewport permits.
- Rows slightly taller and tighter-spaced.
- System descriptions receive more horizontal width.
- Description minimum scale raised from 0.70 to 0.82.
- Name/level/cost scales increased conservatively.

### Scavenger / Nhặt Nhạnh audit
The card was already implemented in runtime `DropService` and was NOT a dead card.
Actual behavior remains unchanged:
- equipped Scavenger rolls on monster defeat;
- levels 1-5 use 3% / 4% / 5% / 6% / 7%;
- success awards +1 Cardboard Scrap / Mảnh Bìa Cardcha.

The misleading text was corrected in English and Vietnamese to say explicitly:
- it is a passive on monster defeat;
- it awards +1 Cardboard Scrap / Mảnh Bìa Cardcha;
- it has no persistent buff icon because the proc is rolled only when the monster is defeated.

### Forest Arcane Gate foliage avoidance
Forest compatibility contract remains intact:
- no Forest tile replacement;
- no collision edits;
- no NPC path reservation;
- `CollisionEdits=NONE` remains.

Instead of deleting bushes, the dynamic Arcane Gate anchor now rejects a larger 3x3 visual footprint including the row in front of the gate. It also rejects candidates occupied by:
- normal objects;
- terrain features;
- large terrain features / bushes;
- blocked tiles;
- nearby map warps.

This makes the overlay relocate to a cleaner nearby anchor on modded Forest layouts without modifying the map.

### Automatic Cardcha-owned transitions
Walking directly onto the endpoint now transitions automatically for:
- Arcane Dock boarding bay -> Airship Bridge;
- Arcane Dock return exit -> Forest;
- Airship Bridge bottom exit -> Arcane Dock.

The Forest Arcane Gate intentionally remains Action-driven for compatibility and to avoid accidental triggering on heavily overhauled Forest maps.
Existing warp grace prevents immediate bounce-back after arrival.

## Explicitly unchanged
- Airship upgrade TEST costs remain 5 / 10 / 20 Magic Dust.
- No real Airship upgrade gameplay bonus is enabled yet.
- Region I fare remains 100g.
- Region I card requirement remains 20.
- Save schema remains 17.
- `SaveData.SuspiciousDust` remains the internal compatibility field.
- Approved card icon atlas remains byte-locked.
- Approved Airship visual remains byte-locked.
- MiMi Wizard Tower appointment bypass remains.
- English long-card-title auto-fit remains.

## Build QA
GitHub Actions run: `33531275016`
Conclusion: PASS.
Artifact ID: `9809829597`
Package: `Cardcha_v0.3.0-alpha.28.0.4.14.1_AirshipUXHotfix_TEST.zip`
Package SHA-256: `38a3ec6bfcfca8fffa1d9e5137bdbd307ca59fc87222ea660587d33e91546ae4`

Locked asset SHA checks passed:
- `card_icons.png`: `4d659e9a25b188ca7e5e0654aa1124ae562f28ca414236283fef1523df6700ee`
- `airship_visual.png`: `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`

Materialized source commit after CI:
`55ed97f557b3737a413812cd134111d355419255`

## Next user test
Please verify in game:
1. Airship Upgrade Menu controller goes 1 -> 2 -> 3 -> 4 one row at a time and highlight/focus never split.
2. Text is materially easier to read in Vietnamese and English.
3. Scavenger description now accurately explains its passive proc; gameplay remains +1 Cardboard Scrap on the 3-7% roll.
4. Forest Arcane Gate chooses a clean nearby location without a bush blocking its front.
5. Walking onto Arcane Dock boarding/return endpoints and the Airship Bridge bottom exit transitions automatically.
6. Upgrade persistence and Magic Dust persistence from `.4.14` still work.
7. Region I departure/return flow still works.

Do not start permanent Airship upgrade bonuses until this hotfix receives user acceptance or any remaining regression is fixed.

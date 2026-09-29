# CARDCHA D3-L — RUNTIME ROOM COLLISION / LAYER / LIGHTING FEEDBACK

Updated: 2026-09-29

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current Cardcha test version: `0.3.0-alpha.28.0.4.14.4.5.12.76`

## Runtime authority

Ron supplied new in-game screenshots after the previous save-load blocker.

**World entry is now confirmed in the current test setup.**

Do not treat D3-L as overall Runtime PASS yet. The screenshots expose three concrete in-world regressions that must be fixed before collision/layout acceptance can close.

## Confirmed runtime failures

### 1. Room 2 — draw/layer overlap

Observed:
- the player/companion can become visually covered by Room 2 environment;
- the current front/depth arrangement is not respecting the intended player visibility around the authored props.

Classification: **LAYER / DRAW-ORDER FAIL**

Required correction:
- review Room 2 `Back` / `Buildings` / `Front` ownership;
- keep only the intended upper/front lip of tall objects above the Farmer;
- do not let full prop bodies or large decor masks cover the player in ordinary walk lanes;
- preserve the existing interaction labels and authored room composition.

Acceptance:
- Farmer remains visually readable while walking around Room 2 props;
- only physically plausible front portions occlude the Farmer;
- no full-body or large-area accidental overlay in normal lanes.

### 2. Room 2 — UPGRADE stations are walkable

Observed:
- Ron can stand directly on top of an `UPGRADE` pedestal/station.

Classification: **TMX COLLISION FAIL**

This is separate from the removed D3-K runtime Harmony collision hook.

Required correction:
- make every authored UPGRADE station footprint physically solid in TMX `Buildings`;
- interaction must be performed from the front/adjacent interaction lane;
- never require the Farmer to stand on the station itself;
- keep the surrounding runner/walk lanes open.

Known authored upgrade footprints from the D3-J/K contract:
- Engine UPGRADE: x3..5, y8
- Navigation UPGRADE: x18..20, y8
- Hull UPGRADE: x6..8, y11
- Reactor UPGRADE: x15..17, y11

Acceptance:
- Farmer cannot occupy any UPGRADE pedestal body tile;
- all four stations remain interactable from outside their solid footprint;
- no neighboring walk lane becomes blocked accidentally.

### 3. Room 1 — severe darkness

Observed:
- Room 1 is almost completely black in the supplied runtime screenshot;
- props, walk lanes and interaction affordances are barely readable.

Classification: **LIGHTING / AMBIENT FAIL**

Required correction:
- inspect the Room 1 ambient/light property and any runtime tint/lighting override;
- restore a readable indoor baseline;
- retain atmosphere, but do not allow the room to become functionally unreadable;
- verify both daytime and nighttime behavior so one state does not inherit an unintended black tint.

Acceptance:
- Farmer, props, entrances and `BOARD AIRSHIP` affordance are immediately readable;
- room mood can remain dark/warm, but navigation must not depend on guessing silhouettes;
- no near-black full-room overlay in ordinary runtime.

## Priority order

1. **Room 1 lighting**, because the room is currently difficult to use at all.
2. **UPGRADE collision**, because the physical contract is visibly broken.
3. **Room 2 draw/layer ordering**, then recheck collision and interaction lanes together.

## Carry-forward locks

Preserve:
- D3-L load-safe mode;
- no broad `GameLocation.isCollidingPosition` Harmony postfix;
- no forced `Farmer.Position` correction;
- D3-J/K authored Room 1/Room 2 layout intent;
- BOARD AIRSHIP center throat remains open;
- TRAVEL center remains open;
- front interaction lanes remain usable.

Do not reopen D2 and do not redo D3-A/B/C/D/E/F/G/H/I/J/K.

## Next patch

The next Cardcha patch should be a narrow in-world presentation/physical-layout patch based on these screenshots, not another save-load/collision-hook experiment.

Suggested next phase name:

`0696D3-M Room Lighting + TMX Collision + Layer Order Runtime Fix`

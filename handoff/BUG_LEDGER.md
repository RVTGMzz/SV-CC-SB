# Cardcha Acceptance Bug Ledger

This file tracks in-game acceptance separately from CI/build status.

Status meanings:
- `OPEN`: reproduced or reported; no candidate yet.
- `CANDIDATE`: code/build candidate exists, but user has not accepted it in game.
- `PASS/LOCKED`: user accepted in game. Future builds must preserve the contract.

## Current ledger

| ID | Area | Bug | Status | Candidate / Lock |
| --- | --- | --- | --- | --- |
| WIZ-01 | WizardHouse | MiMi attic staircase changes position / “runs” | CANDIDATE | `.5.12.9` / branch `cardcha-alpha28-0648c-wizard-stair-lock` |
| WIZ-02 | WizardHouse | Staircase should sit on the bare floor between the two plants without deleting base-map tiles | CANDIDATE | `.5.12.9` / branch `cardcha-alpha28-0648c-wizard-stair-lock` |
| GATE-01 | Forest Gate | Gate animation/geometry changes awkwardly as player moves | OPEN | none |
| GATE-02 | Forest Gate | Portal interior lost intended purple appearance / can appear black | OPEN | none |
| MIMI-01 | MiMi Home | Home routine does not visibly transition at 17:20 / 17:30 / 20:00 / 22:00 | OPEN | none |
| MIMI-02 | MiMi Portrait | Dialogue portrait can hit disposed-texture crash | OPEN | none |
| AIR-01 | Airship/Sky Dock | Rooms regress to empty shells / missing visual identity | OPEN | none |
| AIR-02 | Airship/Sky Dock | Exit / bottom-edge void access | OPEN | none |
| AIR-03 | Airship/Sky Dock | Invisible collision that does not match visible geometry | OPEN | none |
| AIR-04 | Airship | Upgrade station layout / one-station-one-system interaction needs acceptance | OPEN | none |
| AIR-05 | Airship | Lighting, machine glow, and Stardew-style texture quality need acceptance | OPEN | none |

## WIZ-01 / WIZ-02 candidate contract

Build: `0.3.0-alpha.28.0.4.14.4.5.12.9`

- Stair visual uses one landmark-relative fixed tile only: `x = width - 4`, `y = round(height * 0.58)`.
- `ResolvePreferredWizardStairTile()` must not call `IsTileClear`, `FindClearTileNear`, loops, or NPC/object-dependent placement logic.
- Cardcha must not delete `Buildings` or `Front` tiles in WizardHouse to make room for the staircase.
- This candidate must not change Airship, Forest Gate, MiMi portrait, MiMi routine, card gameplay, save schema, or locked assets.

## Acceptance sequence for WIZ-01 / WIZ-02

1. Fully restart SMAPI and load the save.
2. Enter WizardHouse and verify the staircase is between the two plants in the requested area.
3. Walk left/right/up/down around the room for a few seconds. Stair must remain on the same world tile.
4. Leave WizardHouse and re-enter. Stair must remain on the same tile.
5. Change time once with `world_settime` and verify the stair does not move.
6. If all five checks pass, mark `WIZ-01` and `WIZ-02` as `PASS/LOCKED` before any Gate work begins.

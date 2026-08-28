# Cardcha — Project Working Rules

This file is the persistent working contract for Cardcha development. Read it before changing code, maps, assets, progression, or test builds.

## Core rules

| Rule | Required behavior |
|---|---|
| Report test prerequisites before asking for testing | If a room, event, shop, NPC routine, quest, map, menu, or feature is gated by hearts, time, day, weather, story flag, quest, item, route, save state, or any other gameplay condition, state those conditions explicitly before sending the TEST build. |
| Provide a test bypass when access is inconvenient | When a prerequisite would make testing slow or awkward, add or propose a debug/test-only bypass such as a console command. The bypass must not silently remove or weaken the real gameplay requirement. |
| Every TEST needs a handoff | Before sending a TEST build, include: **Prerequisites → How to enter/trigger → Debug bypass (if any) → What to verify → What is intentionally out of scope**. |
| Functional milestones must compile for real | Do not claim a functional milestone is complete until CI has compiled it and produced a real TEST ZIP. |
| Do not touch `main` automatically | `main` is a rollback baseline. Merge, rebase, or replace it only after explicit user approval. |
| Preserve stable IDs and save-facing contracts | Do not casually rename stable location IDs, NPC IDs, item IDs, save keys, or asset names once established. Prefer migrations or compatibility shims if a change becomes necessary. |
| Do not silently override locked design decisions | When a Design Bible or prior explicit user decision locks behavior, layout, tone, or progression, follow it unless the user explicitly changes direction. |
| Foundation before feature expansion | If a map, room, system, or interaction has not passed acceptance testing, fix and stabilize it before layering major new systems on top unless the user explicitly chooses to skip acceptance. |
| Visual concepts are not final gameplay assets | Concept art can define the target, but playable rooms/maps must use proper in-game map/layer/collision/warp logic. For Stardew interiors, prefer vanilla game tiles/furniture where possible and reserve custom art for Cardcha-specific details. |
| Judge final visuals in game | A preview is not enough to approve a gameplay map. Final visual acceptance should be based on an in-game screenshot or playtest at actual Stardew camera scale. |
| Keep rollback points obvious | Record the active branch, latest accepted baseline, milestone commit, TEST ZIP name, and important checks in the session handoff. |
| Do not hide uncertainty | If CI proves only compile/package validity but not runtime behavior, say so. Do not describe untested runtime behavior as confirmed. |
| Keep scope explicit | State what the milestone does and does not include so a TEST build is not mistaken for a finished feature set. |
| MiMi walk sheet is user-locked | Do not modify `src/Cardcha/assets/mimi_walk.png` unless the user explicitly asks. Social/friend-list mugshots must use the dedicated `mimi_social_mugshot.png` source; runtime stitching may append it outside the 128x192 animation area, but the animation pixels must remain identical. |

## TEST HANDOFF RULE

Before giving the user any TEST build, always provide these five items in plain language:

1. **Prerequisites** — hearts, story flags, time/day/weather, route, required item, save state, or anything else needed to reach the test target.
2. **How to test** — exact in-game route or interaction used to reach/trigger the target.
3. **Debug bypass** — a temporary command or shortcut when prerequisites would slow testing; clearly label it as test-only and preserve the normal progression requirement.
4. **What to verify** — the specific visual, collision, input, dialogue, schedule, save, controller, or compatibility behaviors that need acceptance.
5. **Out of scope** — nearby features intentionally not implemented yet.

### Example — MiMi attic

- **Prerequisites:** MiMi meetup completed + 2 hearts.
- **How to test:** use the attic access point from WizardHouse and enter `Cardcha_MiMiAttic`.
- **Debug bypass:** provide a test-only attic warp/open command if the tester only needs to validate the room.
- **Verify:** map load, visual style, doorway/landing readability, collision, MiMi movement, exit, Desk/TV/ChaCha inspect points.
- **Out of scope:** full 17:30 TV event, full heart event, ChaCha upgrade system, Community Center contribution system.

## Git / branch safety

- Continue active work on the named development branch in the current handoff.
- Do not rebuild newer milestones from old snapshots when the active branch already contains newer source.
- Do not merge to `main` unless the user explicitly accepts a new rollback baseline.
- Prefer small milestone commits with clear messages.
- For generated binary assets, prefer reproducible source/generator + CI generation when practical instead of fragile direct binary uploads.

## Stardew map / visual rules

- For indoor maps, prefer real TMX layers and vanilla `Maps/townInterior`, `TileSheets/furniture`, or other appropriate game assets instead of a room-sized image pretending to be a tile map.
- Maintain correct walkability, collision, layer order, warp/exit behavior, NPC placement, and interaction reachability.
- Custom Cardcha art should be subtle and additive unless the user explicitly approves a stronger custom visual direction.
- If the user rejects a visual technique, document the rejection so later sessions do not accidentally restore it.

## Build / verification rules

- A successful CI compile/package proves source/package validity, not complete in-game behavior.
- Inspect the produced artifact before sending it when possible: manifest version, DLL presence, required assets, expected removed assets, localization keys, and ZIP integrity.
- Always identify whether a result is **CI-verified**, **artifact-verified**, or **in-game verified**.

## Session-start rule

At the start of a new Cardcha development session, read:

1. `docs/PROJECT_WORKING_RULES.md`
2. `NEXT_SESSION_START_HERE.md`
3. the relevant milestone/design bible documents listed by the handoff.

If these documents conflict with an explicit newer instruction from the user, the newer user instruction wins and the docs should then be updated to match.
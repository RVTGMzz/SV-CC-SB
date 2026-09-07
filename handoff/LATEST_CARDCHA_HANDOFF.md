# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0649-region1-huntrun-prototype`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.17`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0649_REGION1_HUNTRUN_PROTOTYPE.md`

## Session status — 2026-09-07
- Region I Hunt Run prototype implemented as 6 authored vanilla-tile rooms; each Airship farming run chooses exactly 4 unique rooms.
- Existing Region I Boss Gate hub and 20-card requirement are preserved at the end of the run.
- 0648J MiMi Gift/Profile scale and WizardHouse stair acceptance remains pending because the user is away from the test machine; do not silently treat those two items as accepted.
- Save schema 19, Boss Form duration 10s, Boss Energy gain 1/3, 76/76 active-card audit, Airship route/visual, Forest gate collision contract, and card canon remain protected.

## Test focus when available
1. Fly Region I repeatedly and confirm the route selects 4 non-repeating rooms from the 6-room pool.
2. Confirm north progression is blocked until the room encounter is cleared.
3. Confirm room 4 exits to the existing Region I Boss Gate hub.
4. Confirm Boss Gate still reports Card Resonance and requires 20 unique cards.
5. Confirm monsters still feed the normal Scrap pipeline.

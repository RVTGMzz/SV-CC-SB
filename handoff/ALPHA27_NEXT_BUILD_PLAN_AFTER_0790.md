# Cardcha alpha.27 — next build plan after 0.7.9.0

Branch: `cardcha-alpha27-mimi-real-npc`
Current accepted checkpoint: `0.3.0-alpha.27.0.7.9.0`

## Frozen / do-not-regress contracts

1. Binder controller selection/action contract
   - `PreviewCard` follows browsing.
   - `LockedCard` survives browsing until explicit Deselect/new selection.
   - Detail actions target `LockedCard ?? PreviewCard`.
   - Favorite / Equip / Upgrade labels and actions must read the same target.
   - Preserve the 0.7.8.8 synthetic-click suppression so controller toggles execute once per press.
   - Keep regression tests from `handoff/BINDER_CONTROLLER_SELECTION_ACTION_RULES.md`.

2. MiMi accepted visuals
   - Do not change `src/Cardcha/assets/mimi_walk.png`.
   - Keep accepted broom and social mugshot assets unchanged unless explicitly requested.
   - MiMi attic room is temporarily accepted; do not move furniture without new feedback.

3. ChaCha mystery phase
   - During pre-Scrap `???` phase, no random idle emotes.
   - Explicit interaction/story emotes remain allowed.
   - Introduced/merchant/follower phase can use normal ChaCha emotes.

4. Cardcha machine placement
   - Stationary Cardcha Machine: placeable indoors.
   - Portable Cardcha Machine: never placeable.

## Planned next builds

### 0.7.9.1 — Regression/stability pass
Scope only:
- Verify Binder controller contract survives filter/page navigation, active-slot navigation, Favorite filter rebuilds, and Deselect.
- Verify stationary vs portable machine placement on old + new saves.
- Verify no mystery-phase ChaCha floating emote artifact.
- No visual redesigns.

### 0.7.9.2 — Story-state/save migration pass
- Audit old saves around `FirstScrapTriggered`, `MimiIntroSeen`, `MimiMeetupPending`, `MimiMeetupCompleted`, `ChaChaLoaned`.
- Ensure no duplicate MiMi/ChaCha actors after save/load/day change.
- Self-heal stale actors/state where safe.

### 0.7.9.3 — Chapter 1 polish pass
- Dialogue/scene cleanup only after stability pass.
- Check MiMi intro, Wizard meetup, forced home visit, broom departure, ChaCha handoff.
- Preserve accepted sprites and room layout.

### 0.7.9.4 — Pre-alpha.28 acceptance build
- Full canonical compile/package.
- Run fixed regression checklist for Binder, machine placement, MiMi/ChaCha actor lifecycle, story handoff, save reload.
- If clean, use as rollback checkpoint before alpha.28 content work.

## Build discipline

- Never touch `main` for alpha.27 iteration.
- Each milestone must compile from canonical source and upload a TEST ZIP artifact before being called complete.
- Prefer one behavioral change per TEST build when debugging regressions.
- If controller behavior regresses again, instrument input/action paths before guessing with another timing/debounce patch.

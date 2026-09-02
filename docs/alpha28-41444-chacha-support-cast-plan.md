# alpha28.0.4.14.4.4 ChaCha Support Cast Runtime Plan

Branch: `cardcha-alpha28-062-chacha-support-cast-runtime`
Base: `.4.14.4.3` ChaCha Skill Materials + Airship Station

## Goal

Implement the first real normal-form ChaCha Support Cast runtime while preserving the one-cast modular architecture documented in `docs/chacha-support-cast-canon.md`.

## Phase A: runtime trigger engine

- Add one centralized `ChaChaSupportCastService` or equivalent runtime component.
- Track shared cooldown state.
- Track pre-hit HP for threshold-crossing detection.
- Implement damage-event Lucky Cast roll using level table: 4/5/6/7/8%.
- Implement guaranteed Emergency Cast when a hit crosses from >30% HP to <=30% HP.
- Ensure Lucky + Emergency on the same hit produces exactly one cast.
- Implement monster-kill cast roll as a cooldown-gated trigger.
- Lock only Lv5 kill chance = 18%; Lv1-Lv4 remain TBD until approved.
- Lock only Lv5 cooldown = 20s; Lv1-Lv4 remain TBD until approved.
- Any successful cast restarts the shared cooldown.

## Phase B: Region I Vital Blessing runtime

- Reuse the existing ChaCha cast presentation as the base animation.
- Hook actual healing only after the heal table is approved.
- Until then, runtime trigger telemetry may fire a visual/test cast without changing HP.
- Do not invent healing percentages.

## Phase C: modular add-on hooks

Prepare hooks without inventing magnitudes:

- `Bunny Aegis`: if learned, attach shield module to each Support Cast; duration locked at 20s, strength TBD.
- `Spirit Aid`: if learned, roll 30% during each Support Cast; magnitude TBD.
- `Lucky Echo`: if learned, roll 50% during each Support Cast; Luck duration locked at 10s, magnitude TBD.

All modules belong to the same cast and shared cooldown.

## Phase D: HUD / feedback

- One Support Cast icon, not four independent cooldown icons.
- Show ready/cooldown state.
- Add compact proc feedback for Lucky Cast and Emergency Cast.
- Keep Boss Energy HUD separate.
- No new controller action is required.

## Test matrix

### Damage trigger tests

1. Lv1 receives damage 100 times with forced RNG seam; verify 4% contract path is testable deterministically.
2. Repeat at Lv2-Lv5 for 5/6/7/8%.
3. With cooldown active and HP high, forced Lucky roll succeeds -> cast must occur.
4. HP 45% before hit -> 25% after hit while cooldown active -> Emergency cast must occur.
5. HP 25% before hit -> 15% after hit -> no Emergency threshold cast.
6. Same hit satisfies Lucky + Emergency -> exactly one cast.
7. Forced cast resets shared cooldown.

### Kill trigger tests

1. Kill while cooldown active -> no Kill Cast.
2. Kill while cooldown ready + failed roll -> no cast.
3. Kill while cooldown ready + successful forced roll -> exactly one cast.
4. Lv5 kill chance contract is 18%.
5. Do not hard-code unapproved Lv1-Lv4 kill rates.

### Module tests

1. Only Vital learned -> one base cast path.
2. Aegis learned -> shield module hook runs on same cast, never starts another cooldown.
3. Spirit learned -> exactly one 30% module roll per cast.
4. Lucky learned -> exactly one 50% module roll per cast.
5. All modules learned -> still one Support Cast transaction and one cooldown reset.

### Regression locks

- `.4.14.4.3` four material item IDs remain unchanged.
- `chacha_skill_icons.png` and `chacha_skill_materials.png` remain unchanged unless art is explicitly revised.
- `card_icons.png` locked SHA-256 remains `c5ff456e9a0a697a10537a391ec5abf2f90966de89299799fd2153356b1e6e41`.
- Airship visual SHA-256 remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Boss Form duration remains 10 seconds.
- Controller semantic Boss Form chord remains intact.
- Card auto audit remains 76/76 PASS.
- Forest collision/map edits remain NONE.
- Save schema should remain 19 unless new persistent data is genuinely required.

## Values still awaiting design approval

Before enabling final gameplay effects, obtain explicit values for:

- Vital Blessing healing per level.
- Shared cooldown Lv1-Lv4.
- Kill Cast chance Lv1-Lv4.
- Bunny Aegis shield strength.
- Spirit Aid stamina amount or buff magnitude.
- Lucky Echo Luck magnitude.

These should be centralized in one balance table/service so later balancing does not require touching trigger logic.

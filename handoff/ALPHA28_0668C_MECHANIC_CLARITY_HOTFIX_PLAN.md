# Alpha28 0668C - Mechanic Clarity Hotfix Plan

Branch: `cardcha-alpha28-0668c-mechanic-clarity-hotfix`
Base: `cardcha-alpha28-0668b-combat-hud-runtime-coverage`
Base build: `0.3.0-alpha.28.0.4.14.4.5.12.36`
Status: implementation planned; no acceptance claim until CI + in-game test.

## Why 0668C exists

0668B passed CI but in-game screenshots exposed concrete usability/readability regressions. Fix those before the larger 0669 art overhaul. Do not hide a broken mechanic under new art.

## Confirmed issues from in-game screenshots

### Verdant Seed Totems
- Four totems exist, but the player cannot immediately read that they are combat objectives.
- Targeting cannot yet be considered accepted.
- Damage/break progression is not obvious enough.
- The effect of living totem count on the Guardian barrier is not obvious enough.
- Final-totem stagger needs unmistakable feedback.

### Lost & Found
- Current implementation is visually only a floating `Kho đồ thất lạc` marker in the tested scene.
- User confirmed it is not behaving as a physical usable chest/object.
- This violates the locked contract: no idle floating label/hint, physical Stardew-style chest/crate, name/content revealed only on interaction.

### Region I / Hunt Run presentation
- Current room geometry reads as repetitive/placeholder-like.
- 0668C may fix only functional/readability defects that obstruct play. Full environment art redesign is deferred to 0669.

## 0668C implementation contract

### A. Totem target / damage / break clarity
Preserve all balance values exactly:
- 4 fixed totems
- 90 HP each
- boss damage reduction: 4=15%, 3=10%, 2=6%, 1=3%, 0=0%
- if at least 2 live, Root/Vine cooldown remains approximately 8% faster
- final totem still causes exactly 1.2 seconds of stagger

Add/strengthen presentation only:
- living totem HUD summary during Boss I: `Totems X/4` + current Barrier percentage;
- clear per-totem HP state while alive;
- strong hit flash / damage response on the actual hit totem;
- destroyed state must remain visibly broken and never remain targetable;
- on each break, barrier-change feedback must be readable;
- on the last break, boss stagger feedback must be visually and audibly unmistakable;
- preserve hidden vanilla proxy presentation.

Acceptance requirement:
- player can identify totems as objectives without guessing;
- player attacks damage the intended totem;
- party/ally attacks must not waste attacks on a dead totem;
- each destroyed totem is removed from live-target logic;
- final stagger visibly lasts the existing 1.2 second mechanic window.

### B. Lost & Found functional object
Replace the idle floating-only presentation with a physical Stardew-style chest/crate interaction.

Locked behavior:
- no permanent floating name;
- no permanent `right click`/button hint;
- a visible physical chest/crate occupies the Lost & Found point;
- mouse/action button and controller action both work from normal adjacent interaction range;
- only after interaction may the UI say `Kho đồ thất lạc` / `Lost & Found` and show current contents/empty state;
- do not change progression, save schema, Airship unlock route or fares.

### C. Preserve 0668B HUD runtime fix
Regression guard:
- Adrenaline still shows its approximately 3-second timed Cardcha HUD icon;
- other 0668B timed/stacked proc coverage remains;
- persistent READY clutter remains hidden;
- separate Verdant Core left-corner READY panel remains hidden;
- Verdant Core gameplay remains active.

## Explicitly out of scope for 0668C

- no Verdant Guardian art overhaul;
- no Guardian Rabbit art overhaul;
- no Airship interior redesign;
- no Sky Dock art redesign;
- no full Region I environment art pass;
- no native-size Briarling / Leaf Wisp redraw;
- no combat balance changes;
- no save-schema change.

Those visual items are queued for 0669 after 0668C mechanics pass in game.

## Required TEST handoff

### Prerequisites
- Load a save where Cardcha is available.
- Boss I normally requires Region I access / the established Boss I route.
- Sky Dock Lost & Found normally requires Airship access.

### Debug bypass
- `cardcha_boss1_test` or the current Boss I debug-enter command should remain available for direct arena testing.
- `cardcha_boss1_totem_status` remains the diagnostic for Totem state.
- `cardcha_hud_runtime_status` remains the 0668B timed-HUD diagnostic.
- Use the existing Airship test access command if normal progression is inconvenient; do not weaken the real gate.

### What to verify
1. Totems read clearly as destructible objectives.
2. Hit the same totem several times: HP/readability updates and feedback follows that totem.
3. Break one: it is visibly broken, no longer live-targetable, and Barrier feedback changes.
4. Break all four: final break visibly staggers the boss for the existing 1.2s window.
5. Lost & Found is a physical chest/crate with no idle floating label; action works by mouse/controller.
6. Adrenaline still shows its approximately 3-second runtime icon.

### Out of scope
All visual-overhaul work listed above belongs to 0669.

## 0669 gate

Do not branch 0669 from 0668B. After 0668C receives in-game mechanic acceptance, fork 0669 from the accepted 0668C source so visual work inherits the fixed interaction/runtime foundation.

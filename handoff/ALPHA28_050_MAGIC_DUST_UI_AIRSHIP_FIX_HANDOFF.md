# Cardcha alpha28.0.4.11 — Magic Dust + UI + Airship Fix Handoff

## Scope locked with Ron

This handoff records the agreed alpha28.0.4.11 scope so the next session does not lose any decisions.

### 1. English 10x Pull UI fix
- Long English card names must never overflow outside their card cell.
- Auto-fit font size by available width and height.
- Smart wrap to a maximum of two lines when needed.
- Center names inside each card with safe left/right padding.
- The shared `CardchaUi.DrawAutoFitWrappedText` path must also split a single overlong word if it cannot fit at the minimum scale.

### 2. Magic Dust rename and progression direction
- Public-facing name changes from Suspicious Dust / Card Dust / Bụi Đáng Ngờ to **Magic Dust / Bụi Ma Thuật**.
- Keep the existing save field / internal identifiers where necessary for backward save compatibility.
- Max-level duplicate cards convert to Magic Dust instead of stockpiling useless copies.
- Magic Dust is intended as a core long-term resource, not only a card currency.
- Future uses: ChaCha upgrades, Airship infrastructure/upgrades, special constructs and later progression systems.
- MiMi's money obsession now has a progression/lore purpose: she hoards money/resources to keep upgrading the Airship, fly farther and farther, and ultimately hopes to reach the universe where her idol exists. Keep this as humorous lore revealed gradually rather than dumping it immediately.

### 3. Airship visual cleanup
- Clean `assets/airship_visual.png` alpha edge so there is no obvious white fringe/halo on dark backgrounds.
- Remove the static propeller blades from the base Airship art.
- Runtime animation is the only visible propeller blade set.
- Runtime propeller pivots are aligned to the actual left/right mounting positions on the ship.
- Do not redraw or redesign the rest of the Airship unless separately approved.

### 4. Magical-girl card icon atlas must be preserved
- Build-ready atlas is 320x1024 RGBA.
- Grid is 5 columns x 16 rows, 64x64 per cell, 80 slots.
- Approved magical-girl/cute bright icon atlas SHA-256: `4d659e9a25b188ca7e5e0654aa1124ae562f28ca414236283fef1523df6700ee`.
- Do not silently fall back to the older `.4.9` icon sheet.

### 5. MiMi appointment must bypass Wizard Tower lock only during the appointment
A real progression deadlock was found in-game: Cardcha requires the MiMi + Wizard meetup inside `WizardHouse`, but vanilla Stardew can still return `It's locked. You can hear someone inside, though.` before the player has normally unlocked Wizard access.

Locked behavior:
- Only active when `Progression.ShouldStartMimiMeetup()` is true.
- Cardcha detects the actual door Action tile whose action string targets `WizardHouse`; it does not hard-code the Forest door coordinate.
- Before 13:00: suppress the vanilla locked-door response and show the existing MiMi appointment-too-early reminder.
- From 13:00 through 17:00 inclusive: temporarily allow that door interaction and warp into `WizardHouse`; the normal Cardcha `OnWarped -> TryStartWizardMeetup()` path then starts the scene.
- After 17:00: Cardcha does not override the door. Base game / map-mod behavior is authoritative again and the meetup remains pending for another valid appointment window.
- After the meetup is completed, Cardcha never owns this door interaction again.
- Arrival coordinates are parsed from the current map's WizardHouse door action where possible; `(3,17)` is only a compatibility fallback for unfamiliar action wrappers.

Implementation status:
- Source finalizer updated in `tools/alpha28_411_finalize.py`.
- `CardchaStoryService.OnButtonPressed` + `ModEntry` input subscription passed source acceptance and **dotnet compile PASS** in GitHub Actions run `33428735914`.
- Compiled source was materialized to branch commit `52393cf163cd8ddca0007ffc81560c0d42ea31e9`.

## Next world-design direction already approved

### Arcane Portal / magical boarding point
Ron chose the most magical option for future boarding:
- A dedicated magical summoning/teleport point rather than a tiny fake Airship sitting in the control room.
- Visual language: arcane circle, crystals, runes, purple/blue/gold fantasy accents.
- Prefer a Cardcha-owned custom map/area for the full portal treatment to reduce conflicts with Forest/Wizard map overhauls.
- The Forest interaction should stay conflict-safe and avoid editing vanilla collision/pathing.

### Airship interior direction
- Remove the small miniature-Airship visual from the interior/control-room presentation.
- Replace it with a believable magical Airship bridge/control room: large sky window, navigation/region map, magical navigation table/core, books/cards, machinery and future upgrade interaction points.
- Future Airship upgrade branches discussed: Energy Core, Engine, Control Room, Arcane Dock, Storage Bay, Exploration Range.

## Unrelated map bug test
Ron A/B tested the Wizard Tower exit map issue with Cardcha removed and confirmed Cardcha is **not** the cause. Do not spend Cardcha development time chasing that specific map-stuck bug unless new evidence appears.

## Build policy
- Fix first, compile/package second, then update GitHub source + this handoff.
- Never call a package final until the compiled artifact has been opened and its actual bundled asset hashes verified.
- alpha28.0.4.11 should contain all four things simultaneously: Magic Dust text/logic, English UI fix, approved magical-girl icon atlas, and cleaned no-static-propeller Airship asset.

## Current alpha28.0.4.11 gate status
- **Source acceptance: PASS.**
- **C# compile: PASS.**
- **MiMi Wizard Tower appointment door fix: materialized to GitHub source.**
- **Airship cleanup generation: runs before compile and is materialized after successful compile.**
- **Final package: intentionally BLOCKED.** The final asset gate currently fails because `src/Cardcha/assets/card_icons.png` on the branch is still not the approved `.4.10` atlas hash `4d659e9a25b188ca7e5e0654aa1124ae562f28ca414236283fef1523df6700ee`.
- Do not weaken or remove this icon hash gate. Materialize the approved atlas first, rerun CI, then package and inspect the ZIP before declaring `.4.11` test-ready.

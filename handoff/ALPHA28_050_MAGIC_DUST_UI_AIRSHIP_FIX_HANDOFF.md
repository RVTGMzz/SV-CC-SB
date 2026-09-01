# Cardcha alpha28.0.4.11 — Magic Dust + UI + Airship Fix Handoff

## Final status

This handoff is the canonical record for alpha28.0.4.11.

- Branch: `cardcha-alpha28-050-magic-dust-ui-airship-fix`
- Current materialized branch head after successful build: `e971fbe0acf52e35ada7ec97fe0610ffdd330e94`
- Main GitHub Actions build run: `33466769570`
- Main build result: **PASS**
- Compile: **PASS**
- Source acceptance: **PASS**
- Final asset acceptance gate: **PASS**
- Package/upload artifact: **PASS**
- Approved icon atlas is now actually materialized at `src/Cardcha/assets/card_icons.png` on the branch. There is no longer a local-only atlas exception.

## Scope locked with Ron

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

### 4. Magical-girl card icon atlas is locked
- Build-ready atlas is 320x1024 RGBA.
- Grid is 5 columns x 16 rows, 64x64 per cell, 80 slots.
- Approved magical-girl/cute bright icon atlas SHA-256: `4d659e9a25b188ca7e5e0654aa1124ae562f28ca414236283fef1523df6700ee`.
- Git blob SHA for the exact approved bytes: `29436bf40054988256467a6da220d076ff427410`.
- Actual branch path: `src/Cardcha/assets/card_icons.png`.
- Never silently fall back to the older `.4.9` icon sheet.

### 5. MiMi appointment bypass for Wizard Tower lock
A real progression deadlock was found in-game: Cardcha requires the MiMi + Wizard meetup inside `WizardHouse`, but vanilla Stardew can still return `It's locked. You can hear someone inside, though.` before the player has normally unlocked Wizard access.

Locked behavior:
- Only active when `Progression.ShouldStartMimiMeetup()` is true.
- Cardcha detects the actual door Action tile whose action string targets `WizardHouse`; it does not hard-code the Forest door coordinate.
- Before 13:00: suppress the vanilla locked-door response and show the MiMi appointment-too-early reminder.
- From 13:00 through 17:00 inclusive: temporarily allow the door interaction and warp into `WizardHouse`; the normal Cardcha `OnWarped -> TryStartWizardMeetup()` path then starts the scene.
- After 17:00: Cardcha does not override the door. Base game / map-mod behavior is authoritative again and the meetup remains pending for another valid appointment window.
- After the meetup is completed, Cardcha never owns this door interaction again.
- Arrival coordinates are parsed from the current map's WizardHouse door action where possible; `(3,17)` is only a compatibility fallback for unfamiliar action wrappers.

Implementation:
- Source finalizer lives in `tools/alpha28_411_finalize.py`.
- `CardchaStoryService.OnButtonPressed` + `ModEntry` input subscription compile successfully.
- Compiled/source fixes were materialized back to the branch by GitHub Actions.

## Next world-design direction already approved

### Arcane Portal / magical boarding point
- Use a magical summoning/teleport point rather than a tiny fake Airship sitting in the control room.
- Visual language: arcane circle, crystals, runes, purple/blue/gold fantasy accents.
- Prefer a Cardcha-owned custom map/area for the full portal treatment to reduce conflicts with Forest/Wizard map overhauls.
- The Forest interaction should stay conflict-safe and avoid editing vanilla collision/pathing.

### Airship interior direction
- Remove the small miniature-Airship visual from the interior/control-room presentation.
- Replace it with a believable magical Airship bridge/control room: large sky window, navigation/region map, magical navigation table/core, books/cards, machinery and future upgrade interaction points.
- Future Airship upgrade branches discussed: Energy Core, Engine, Control Room, Arcane Dock, Storage Bay, Exploration Range.

## Unrelated Wizard exterior map issue
Ron A/B tested the Wizard Tower exit map issue with Cardcha removed and confirmed Cardcha is **not** the cause. Do not spend Cardcha development time chasing that specific map-stuck bug unless new evidence appears.

## Final GitHub-built test package
GitHub Actions run `33466769570` produced the package directly from the repository after the exact `.4.10` atlas was materialized. No local atlas swap is required anymore.

Package:
`Cardcha_v0.3.0-alpha.28.0.4.11_MagicDust_UI_Airship_FIX_TEST.zip`

Final package QA:
- manifest version = `0.3.0-alpha.28.0.4.11`
- card atlas = 320x1024, 770371 bytes, exact approved SHA-256
- `Magic Dust` / `Bụi Ma Thuật` logic/text included
- English card-name auto-fit/wrap fix included
- MiMi Wizard Tower appointment bypass compiled into the build
- airship visual = cleaned alpha / no-static-propeller asset used by the package

Hashes from the GitHub-built artifact:
- package ZIP SHA-256: `161968a190d1a1848a92c63ae8be591bb8a204bcdd604b5a6dae8ed1519f0ca8`
- `card_icons.png`: `4d659e9a25b188ca7e5e0654aa1124ae562f28ca414236283fef1523df6700ee`
- `airship_visual.png`: `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`
- GitHub Actions outer artifact digest: `5eacc132d06bd5bc7f191971eb3bf593f0b0ba9e4f0cecd7198fb8fe362cedf7`

## Build policy going forward
- Fix first, compile/package second, then update GitHub source + handoff.
- Never call a package final until the compiled artifact has been opened and its actual bundled asset hashes verified.
- If a connector limitation blocks a simple binary upload and Ron can solve it manually in under a minute, ask Ron for the direct GitHub upload early instead of spending excessive time on connector workarounds.
- For binary files uploaded through GitHub web, verify the exact repository path before committing. For the card atlas the required path is always `src/Cardcha/assets/card_icons.png`.

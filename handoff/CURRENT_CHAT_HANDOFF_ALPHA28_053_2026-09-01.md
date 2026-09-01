# Cardcha / Shardbound — MASTER CHAT TRANSFER HANDOFF

Transfer date: 2026-09-01
Purpose: continue the current ChatGPT development session in a new chat without losing implementation state, test status, binary locks, story decisions, or build lessons.

## 0. READ THIS FIRST

This is the master handoff for the development work from alpha28.0.4.11 through alpha28.0.4.14.

Current source-of-truth development branch:
`cardcha-alpha28-053-airship-upgrade-foundation`

Code baseline commit immediately before these transfer docs:
`ad07a8e49c12977e51ae633fcd90acf093a4f137`

Commit message:
`docs: finalize alpha28.0.4.14 Airship upgrade handoff [skip ci]`

Any commits after that which only update handoff files are documentation-only and must not be treated as gameplay changes.

Current target build:
`0.3.0-alpha.28.0.4.14`

Current package:
`Cardcha_v0.3.0-alpha.28.0.4.14_AirshipUpgradeFoundation_TEST.zip`

Package SHA-256:
`5cb1c41b3dc6a805de8b661598e417368785abf7d1b013f94502598a67e37f12`

Final successful GitHub Actions run for .4.14:
`33498632897`

Artifact ID:
`9796770354`

## 1. IMPORTANT TEST STATUS, DO NOT CONFUSE CI PASS WITH USER TEST

### alpha28.0.4.11
USER REPORTED TEST OK in game before moving on.

This is the last build explicitly confirmed by the user as tested OK in this chat.

### alpha28.0.4.12
CI/build PASS. The user asked to continue building afterward, but there was no separate explicit full in-game acceptance message for this version.

### alpha28.0.4.13
CI/build PASS. The user asked to continue to the upgrade system afterward, but there was no separate explicit full in-game acceptance message for this version.

### alpha28.0.4.14
CI/build/package PASS. NOT YET USER-TESTED because the user is moving to a new chat immediately after receiving the build.

Therefore the first job in the next chat should be to receive and act on the user's .4.14 in-game test results. Do not assume .4.14 gameplay acceptance yet.

## 2. VERSION CHRONOLOGY FROM THIS CHAT

### alpha28.0.4.11 — Magic Dust + UI + Airship + MiMi appointment fix
Branch:
`cardcha-alpha28-050-magic-dust-ui-airship-fix`

Known final PASS run:
`33466769570`

Known GitHub-built package SHA-256:
`161968a190d1a1848a92c63ae8be591bb8a204bcdd604b5a6dae8ed1519f0ca8`

Implemented/fixed:
- Player-facing resource renamed to `Magic Dust` / `Bụi Ma Thuật`.
- INTERNAL save field remains `SuspiciousDust`. DO NOT rename this field because save compatibility depends on it.
- Max-level duplicate cards award the existing dust resource.
- English 10x Pull title fitting fixed so long single-word titles do not overflow card cells.
- Airship PNG alpha/white fringe cleanup.
- Static propeller blades removed from the base visual; runtime animated propellers remain.
- Runtime rotor alignment/polish retained.
- MiMi/Wizard Tower meetup deadlock fixed.

MiMi meetup door behavior:
- Story appointment window is 13:00–17:00.
- If the MiMi meetup is pending and the player interacts with the Wizard Tower door during the valid window, Cardcha temporarily bypasses the vanilla locked-door behavior and enters `WizardHouse`.
- Before 13:00, Cardcha can show an appointment reminder.
- After 17:00, Cardcha does not unlock the door.
- Once the meetup is complete, the exception disables itself.
- The implementation should detect the actual door `Action` leading to `WizardHouse`, not depend on fixed Forest tile coordinates.
- Do not edit Forest map tiles or collision for this feature.

User explicitly reported this stage/test as OK before development continued.

### alpha28.0.4.12 — Arcane Dock + Airship Bridge gameplay skeleton
Branch:
`cardcha-alpha28-051-arcane-dock-airship-bridge`

Successful run:
`33468046526`

Package SHA-256:
`61414d2661962967ebbe787a632da152c9b9a5330afca3ae34a3d97fb78de4b1`

Implemented gameplay flow:
`Forest Arcane Gate -> Arcane Dock -> Boarding Gate -> Airship Bridge -> Helm -> Region I`

Region I return flow:
`Region I -> Airship Bridge -> Arcane Dock -> Forest`

Important compatibility choice:
- Forest remains authoritative.
- Cardcha does not replace Forest map tiles, collision, or NPC pathing.
- Arcane Gate is a Cardcha overlay / interaction anchor.

Arcane Dock roles:
- Arrival / summoning seal.
- Route Console is informational.
- Violet boarding gate enters the Airship Bridge.
- Exit returns to Forest.

Airship Bridge roles:
- Real helm/navigation space.
- Region I fare/confirmation remains the existing flow.
- No miniature Airship model inside the room.

### alpha28.0.4.13 — Arcane Dock + Airship Bridge visual polish
Branch:
`cardcha-alpha28-052-arcane-dock-bridge-visual-polish`

Primary successful run:
`33494112364`

Package SHA-256:
`a03ed99359cf358c8a5cfed5bdea29d948bdab009eb7ee13611480e59c0c2d8d`

Presentation-only polish, no intended gameplay balance changes:
- Forest Arcane Gate gained layered portal depth, crystal pylons, rune crown and sparkles.
- Arcane Dock gained animated mana lanes, larger summoning seal, route console altar, deeper boarding portal and quieter return rune.
- Airship Bridge gained panoramic day/night sky, moving clouds or stars, window framing, navigation dais, mana lane, side consoles and four visible dormant upgrade sockets.
- No new bespoke binary art was added in this pass. Runtime pixel drawing was used deliberately for fast testing and rollback safety.
- Region I flow/fare/unlock remained unchanged.

### alpha28.0.4.14 — Airship Upgrade Foundation
Branch:
`cardcha-alpha28-053-airship-upgrade-foundation`

Final successful run:
`33498632897`

Package SHA-256:
`5cb1c41b3dc6a805de8b661598e417368785abf7d1b013f94502598a67e37f12`

Implemented:
- Dedicated `AirshipUpgradeMenu`.
- Four interactive upgrade sockets on the Airship Bridge:
  1. Aether Engine
  2. Navigation Core
  3. Hull & Shield
  4. Arcane Reactor
- Each subsystem has persistent levels 0–3.
- Save schema increased from 16 to 17.
- New save fields:
  - `AirshipEngineLevel`
  - `AirshipNavigationLevel`
  - `AirshipHullLevel`
  - `AirshipReactorLevel`
- All four levels are normalized to 0–3 and included in save persistence fingerprinting.
- Upgrades consume the existing Magic Dust wallet using `Save.Data.SuspiciousDust` internally.
- Current provisional TEST cost curve:
  - Level 0 -> 1: 5 Magic Dust
  - Level 1 -> 2: 10 Magic Dust
  - Level 2 -> 3: 20 Magic Dust
- UI explicitly labels the costs as TEST/provisional.
- Bridge socket visual reacts immediately to level:
  - stronger subsystem color
  - taller/brighter crystal
  - level pips
  - extra rune from level 2
  - sparkles at level 3
- TEST helper command:
  `cardcha_give_dust [amount]`
  Default amount is 50.
- `cardcha_airship_status` reports the four infrastructure levels.

INTENTIONALLY NOT enabled yet:
- no travel speed bonus
- no fare discount
- no new Region unlock from upgrades
- no combat stat bonus
- no boss gate based on upgrade levels

This is deliberate. The user has not approved permanent costs or gameplay effects yet.

## 3. CURRENT .4.14 TEST CHECKLIST FOR THE NEXT CHAT

Ask the user to test / react to these, or process the screenshots/log they provide:

1. Enter Airship Bridge.
2. Press action near all four upgrade sockets.
3. Confirm each opens the upgrade UI focused on the corresponding subsystem.
4. If currency is needed, use `cardcha_give_dust 100`.
5. Upgrade at least one subsystem 0 -> 1 -> 2 -> 3.
6. Confirm Magic Dust decreases by 5, then 10, then 20.
7. Confirm the socket visual changes after each level.
8. Save the game.
9. Exit/reload.
10. Confirm the subsystem level persists.
11. Confirm remaining Magic Dust persists.
12. Confirm helm -> Region I departure still works.
13. Confirm Region I -> Bridge -> Dock -> Forest return flow still works.
14. Watch for controller focus/navigation issues in `AirshipUpgradeMenu`.
15. Watch for UI text clipping in Vietnamese and English.

Do not proceed to permanent upgrade bonuses until basic persistence/UI interaction is confirmed or any reported bug is fixed.

## 4. BINARY ASSET LOCKS — CRITICAL

### Approved magical-girl card icon atlas
Path:
`src/Cardcha/assets/card_icons.png`

Dimensions:
`320 x 1024`

Approved SHA-256:
`4d659e9a25b188ca7e5e0654aa1124ae562f28ca414236283fef1523df6700ee`

This exact binary is the approved .4.10 magical-girl atlas and must be preserved byte-for-byte.

Do NOT:
- regenerate it
- resave it through Pillow/Photoshop/Canva
- replace it with the older atlas
- weaken/remove the hash assertion just to make CI green

Historical binary-sync lesson from this chat:
- The ChatGPT GitHub connector had difficulty transmitting the large PNG byte-for-byte.
- The user manually uploaded the exact approved PNG through GitHub web.
- The first manual upload landed at `src/Cardcha/card_icons.png` instead of `src/Cardcha/assets/card_icons.png`.
- Once the exact binary existed in GitHub, it was moved/referenced into the correct asset path without altering bytes.
- CI then confirmed the exact approved hash.

User workflow preference established in this chat:
If a future connector limitation blocks a simple binary/file operation and the user can complete it manually on GitHub in seconds, ask the user for that manual step EARLY instead of spending a long time fighting the connector. Give precise branch/path/button instructions, then continue automatically after the user confirms.

### Airship visual
Path:
`src/Cardcha/assets/airship_visual.png`

Locked SHA-256:
`1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`

Keep:
- clean alpha / no white matte fringe
- no unwanted static propeller blades in base art
- runtime animated propellers

Do not alter this binary casually in upgrade-system work.

## 5. MAGIC DUST DESIGN / SAVE COMPATIBILITY

Player-facing English:
`Magic Dust`

Player-facing Vietnamese:
`Bụi Ma Thuật`

Internal compatibility field:
`SaveData.SuspiciousDust`

DO NOT rename the internal field unless a deliberate migration strategy is designed and tested.

Lore direction already accepted in this chat:
- Magic Dust is condensed arcane residue from duplicate cards that have already reached maximum level.
- ChaCha can use it now.
- MiMi has plans for using it on the Airship later.
- MiMi's greed/resource obsession can partly support the longer-term story that she wants to upgrade the Airship enough to travel farther and eventually reach a universe connected to her idol.

Do not invent permanent Airship upgrade costs or effects without user approval.

## 6. ARCANE DOCK / AIRSHIP VISUAL DIRECTION

Long-term art direction accepted:

Arcane Dock exterior/intermediate space:
- magical portal / summoning-station feeling
- magic circle
- crystals
- runic pillars
- purple/cyan/gold language
- not a conventional airport terminal

Airship Bridge/interior:
- magical control bridge
- central arcane navigation table/dais
- astral map / compass feeling
- crystal core
- spell/card shelves possible later
- large sky windows
- purple/blue/gold palette

Future possibilities, NOT implemented yet:
- region selection
- route list
- travel log
- real upgrade effects
- boss gates
- Region II+

Current .4.13/.4.14 runtime visual layer is a gameplay/presentation foundation, not final bespoke pixel art.

## 7. FOREST / MAP COMPATIBILITY CONTRACT

The user uses a heavily modded Stardew setup and may use overhauled Forest maps.

Hard compatibility rule:
- Do not replace Forest tiles for Cardcha's Airship system.
- Do not modify Forest collision.
- Do not reserve or block NPC paths.
- Prefer dynamic anchors/actions/warps over hard-coded vanilla coordinates.

Current Airship diagnostics/regression lock includes:
`CollisionEdits=NONE`

Keep this lock unless the user explicitly approves a different architecture.

## 8. REGION I LOCKS

Current Region I gate card requirement:
`20 cards`

Current Region I fare:
`100g`

Keep these unchanged during .4.14 upgrade-foundation testing.

Do not let provisional Airship upgrades silently alter these values.

## 9. BUILD ARCHITECTURE / CI LESSONS

Local ChatGPT runtime used during this session does not have a reliable local Stardew/.NET mod build environment, so authoritative compile verification is GitHub Actions with SMAPI reference assemblies.

Current .4.14 workflow:
`.github/workflows/cardcha-alpha28-053-airship-upgrade-foundation.yml`

Current .4.14 finalizer:
`tools/alpha28_414_airship_upgrades.py`

Current build hook:
`src/Cardcha/Directory.Build.targets`

CRITICAL LESSON:
The finalizer can be executed once by the workflow and again by `Directory.Build.targets` during `dotnet build`.
Therefore finalizers MUST be idempotent.

Historical .4.14 failed run:
`33498528711`

Failure:
`AirshipFoundationService` contained duplicate `Controller` field insertion because the finalizer ran twice.

Fix:
The finalizer was changed so the Controller field is inserted only if it is not already present.

Successful rerun/new run after fix:
`33498632897`

Do not reintroduce non-idempotent text insertion in future finalizers.

Related earlier build-hook lesson from .4.12/.4.13:
`Directory.Build.targets` can hard-code an older version/finalizer and silently pull the build backward. Whenever bumping versions, update/verify:
- manifest version
- Cardcha.csproj version
- Directory.Build.targets version/finalizer target
- ModEntry version log/command where relevant
- workflow package version assertions

## 10. REGRESSION LOCKS THAT MUST SURVIVE FUTURE BUILDS

- Approved `card_icons.png` exact SHA remains locked.
- Clean `airship_visual.png` exact SHA remains locked.
- Magic Dust / Bụi Ma Thuật player-facing naming remains.
- Internal `SuspiciousDust` save field remains for compatibility.
- English long-card-title auto-fit remains.
- MiMi Wizard Tower appointment bypass remains.
- Arcane Gate / Arcane Dock / Airship Bridge / Region I flow remains.
- Forest collision edits remain NONE.
- Region I fare stays 100g unless intentionally changed with user approval.
- Region I card requirement stays 20 unless intentionally changed with user approval.
- `.4.14` save schema is 17.
- Four Airship infrastructure levels are included in persistence fingerprinting.

## 11. RELEVANT SOURCE FILES FOR THE NEXT CHAT

Primary .4.14 files:
- `src/Cardcha/UI/AirshipUpgradeMenu.cs`
- `src/Cardcha/Services/AirshipFoundationService.cs`
- `src/Cardcha/Models/SaveData.cs`
- `src/Cardcha/Services/SaveService.cs`
- `src/Cardcha/ModEntry.cs`
- `src/Cardcha/i18n/default.json`
- `src/Cardcha/i18n/vi.json`
- `src/Cardcha/assets/airship_deck.tmx`
- `src/Cardcha/assets/sky_dock_interior.tmx`
- `src/Cardcha/Directory.Build.targets`
- `tools/alpha28_414_airship_upgrades.py`
- `.github/workflows/cardcha-alpha28-053-airship-upgrade-foundation.yml`

Existing detailed .4.14 handoff:
`handoff/ALPHA28_053_AIRSHIP_UPGRADE_FOUNDATION.md`

This master file supersedes scattered chat context but does not replace version-specific handoffs.

## 12. RECOMMENDED NEXT DEVELOPMENT DECISION AFTER .4.14 TEST

If .4.14 interaction + save/load persistence PASS in game:

First discuss with the user before coding:
1. Permanent Magic Dust cost curve.
2. Real effect for Aether Engine.
3. Real effect for Navigation Core.
4. Real effect for Hull & Shield.
5. Real effect for Arcane Reactor.
6. Whether upgrades gate Region II, reduce fare, affect travel presentation, affect combat survivability, or mainly unlock story/routes.

A reasonable next version name would be a new branch after .4.14, not edits back into the accepted .4.13 branch.

Potential next branch theme:
`alpha28.0.4.15 Airship Upgrade Effects / Balance`

But DO NOT create this branch until either:
- user confirms .4.14 test is satisfactory, or
- any .4.14 bugs reported by the user are fixed first.

## 13. USER COLLABORATION STYLE FOR THIS PROJECT

The user expects actual implementation/build work, not long speculative planning when a concrete next step is already agreed.

Useful pattern:
- short progress update
- implement
- CI/build
- inspect artifact
- provide test ZIP

If blocked by a tool limitation that the user can solve quickly manually, say exactly what is blocked and give the shortest precise manual GitHub step. Then resume automatically after confirmation.

Do not say something is built or PASS until CI/artifact verification actually confirms it.

## 14. STARTING MESSAGE FOR A NEW CHAT

Recommended user prompt:
`Đọc handoff/CURRENT_CHAT_HANDOFF_ALPHA28_053_2026-09-01.md trên branch cardcha-alpha28-053-airship-upgrade-foundation rồi tiếp tục từ .4.14.`

If the user immediately provides screenshots/logs instead, first read this handoff plus `handoff/ALPHA28_053_AIRSHIP_UPGRADE_FOUNDATION.md`, then diagnose the screenshots/logs against .4.14.

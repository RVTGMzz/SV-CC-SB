# v0.1.17-alpha.11.36 — MiMi Placement + Loot Toast + Shiny Economy + Home Machine

- Fixed a stale StoryService ownership path which could leave MiMi stranded at the player's farm after her story beat.
- Farm intro now hides MiMi immediately after the rendezvous dialogue finishes.
- Wizard meetup exit now self-recovers if the player warps away before the short exit animation completes.
- Binder-wallet Scrap drops now use Stardew's native `HUDMessage.ForItemGained`, restoring the item pickup toast after Scrap stops spawning as physical debris.
- MiMi economy: normal Scrap = player buys 1,000g / sells 100g; Shiny Scrap = player buys 10,000g / sells 1,000g.
- Stationary Cardcha Machine is now a main-farmhouse-only appliance: outdoor placement is disabled in BigCraftable data and non-main-house placements are recovered back to inventory. Existing misplaced machines are recovered on save load.
- MiMi shop wording pushed further toward hurried, cheeky, money-loving personality.
- Portable Cardcha Machine progression is intentionally documented only, not activated yet: 50,000g early purchase; free at 50 unique cards if still unowned; 80-card Binder-direct Cardcha feature reserved for a later third requirement.
- Official visual assets unchanged.

# v0.1.17-alpha.11.35 — Smooth Fairy + Controller + Physical Scrap + Weekday MiMi

- Removed ChaCha's player-proximity teleport branch; follower side offsets now ease and obstacle recovery stays smooth/local.
- Binder controller graph now includes both Scrap counters and the detail scrollbar; card focus auto-inspects details.
- Scrap is physical before Binder unlock, then migrates from backpack into the Binder wallet at the Wizard handoff.
- MiMi merchant begins the day after handoff, Monday-Friday 11:00-17:00; Town in normal weather, WizardHouse in harsh weather.
- Added MiMi handoff dialogue explaining Binder Scrap storage and merchant hours.
- Official assets remain byte-for-byte unchanged.

# v0.1.17-alpha.11.34 — Stable Talk + Shadow + Late Departure

- Removed talk-time `EnsureConversationSpacing` teleport.
- Removed obsolete synthetic personal-space escape from MiMi wander now that MiMi is a native world actor.
- Freeze MiMi world position during dialogue/menu interaction.
- Freeze ChaCha base position during MiMi dialogue while keeping fairy hover animation.
- Added explicit Stardew `CharacterShadowData` for MiMi and ChaCha at 0.55 shadow scale.
- Added a visible departure grace window: 15:00–16:00. If the player misses exactly 15:00, entering Town during the grace window still triggers MiMi's broom departure instead of an instant disappearance.
- Preserved native world actor rendering and official assets unchanged.

# v0.1.17-alpha.11.34 — Native World Actors

- Architectural render fix: MiMi and ChaCha bodies no longer render in `RenderedWorld`.
- MiMi normal world actor now uses official 32x48 `mimi_walk.png` directly at native Character scale 0.575 (effective 2.3x draw scale).
- MiMi broom flight swaps the same native NPC to `mimi_broom.png` and is depth-sorted by Stardew.
- ChaCha follower/story companion is a runtime NPC-style actor at Character scale 0.45 (effective 1.8x draw scale).
- Native Stardew shadows now come from the actors' actual ground anchors.
- Story scenes and WizardHouse exit moved to native MiMi/ChaCha actors.
- ChaCha runtime actor is removed before save serialization and recreated automatically.
- `RenderedWorld` remains only for the cosmetic sparkle trail.
- Official user-master assets unchanged.
- Vanilla `SpawnIfMissing` is disabled for MiMi; Cardcha owns actor creation to prevent duplicate native MiMis.
- ChaCha machine-scene native frame indexing uses the real 6-column x 3-row machine sheet layout.
- ChaCha fairy flutter uses native `drawOffset` while `shouldShadowBeOffset=false`, so visual flight no longer drags the ground shadow/depth anchor.
- Wizard story dialogue no longer receives MiMi's portrait override.
- Runtime actor lookup deduplicates leftover MiMi/ChaCha actors from older experimental saves.

# v0.1.17-alpha.11.31 — World Integration + Fairy Hover

- ChaCha no longer disappears just because a dialogue/speech bubble is visible.
- ChaCha follower now uses a drifting fairy-style target, damped glide, tiny flutter, obstacle sliding, and collision-aware safe slots around the player.
- ChaCha checks a 9-point visual footprint before moving so it avoids trees, bushes, props, and blocked tiles instead of floating through them.
- MiMi's hidden native NPC is now kept as a real collision body (farmerPassesThrough=false, collidesWithOtherCharacters=true, one-tile-wide body).
- MiMi wander checks the full custom-sprite footprint, not only one tile under her feet.
- MiMi gains a gentle personal-space escape when another mod/map lets the player overlap the invisible collision actor.
- MiMi/ChaCha ground shadows remain anchored to ground positions and are not included in hover motion.
- Official user-master assets remain locked and unchanged.

# v0.1.17-alpha.11.31 — Compile fix + clean ChaCha back sprite

- Replaced removed `isTileLocationTotallyClearAndPlaceable` calls with Stardew 1.6 `IsTileBlockedBy` checks.
- Removed the now-unused mystery villager reaction counter warning.
- Cleaned ChaCha's rear-facing row: removed the leftover Cardcha machine/orb overlay and rebuilt it from the two clean rear frames.
- Keeps closer-follow, sparkle movement effect, shadows, safer positioning, and Binder double-click / Y quick equip + unequip from alpha.11.19.

# v0.1.17-alpha.11.19 — ChaCha back view + sparkle + Binder quick equip

- Replaced the follower UP/back row that accidentally used Cardcha-machine capture animation with a real back-facing ChaCha row.
- ChaCha follower distance reduced to roughly half the previous gap, with safe-tile fallback so he does not sit inside scenery.
- Added lightweight moving sparkle twinkles around ChaCha while flying/following.
- Binder: double-click a card in the collection list to equip it into the next free unlocked slot.
- Binder: press controller Y on a collection card to quick-equip it.
- Binder: double-click an equipped active slot to remove that card.
- Binder: press controller Y (X remains supported) on an equipped active slot to remove it.

# v0.1.17-alpha.11.8 — MiMi visual pass + 6 portraits + test hours

- Temporary mystery Town test window: 10:00–15:00.
- Removed floating `???` over MiMi; mystery name now belongs in portrait dialogue only.
- Expanded MiMi portraits to six standard Stardew slots: neutral, happy, worried/sad, surprised/unique, love, determined/angry.
- Story and mystery dialogue now attach portrait commands (`$0`..`$5`) per situation.
- MiMi walk/broom/Wizard-exit story render increased from 2.0x to 2.3x (~15%).
- Native MiMi sheet enlarged inside its 16x32 frame for normal Town/merchant presence.
- ChaCha beside MiMi is 2x and moved farther away to avoid overlap; follower offsets also widened.

# v0.1.17-alpha.11.6 — MiMi Merchant + Scrap Wallet

- Wizard meetup MiMi scaled to player-sized 2x render.
- MiMi exit walk after Wizard meetup.
- ChaCha follower scaled to 2x with safer front-facing separation.
- Post-meetup MiMi merchant: 11:00–17:00, Farm on clear days, WizardHouse on rain days.
- MiMi buys Scrap for 100g and sells for 1,000g.
- Two Scrap counts shown in Cardcha Binder; Scrap currency stored in save data instead of inventory.
- Existing physical Scrap items migrate into the wallet on load.
- Vietnamese MiMi dialogue changed from gendered `anh/em` to neutral `bạn/mình`.

# Cardcha! Build History — condensed development log

This file is intentionally kept inside every future builder. Update it whenever a new build is made.

## Early core
- v0.1.10–0.1.14: machine, Binder, normal gameplay onboarding, pull presentation, loot compatibility, controller work.
- v0.1.15 series: Binder levels/upgrades, Book tab navigation, cursor/controller fixes, safe installer, loot balance.
- Key controller solution: current `GameMenu` page graph + low-level movement-key Harmony intercept.

## v0.1.16
- alpha.1: star-upgrade celebration overlay; exact BEFORE / NEW EFFECT.
- Duplicate pull feedback was planned but temporarily deferred when MiMi story became priority.

## v0.1.17 story / mascot branch
- alpha.1: MiMi Chapter 1 story scaffold. First natural Scrap arms story; meetup window 15:00–17:00; Wizard handoff.
- alpha.2: MiMi visual scaffold + ChaCha mascot + ChaCha-themed machine direction.
- alpha.3: MiMi hair-star direction fix + transparent ChaCha orb direction.
- alpha.4 / alpha.4.1: ChaCha machine ritual animation; custom MiMi render + portrait dialogue for ambiguous XNA `Color(...)` overload.
- alpha.5: MiMi/ChaCha story polish + first-pull quest. ChaCha officially loaned to player; Wizard supplies missing Scrap only.
- alpha.6: animation asset organization pass.
- alpha.7 / 7.1 / 7.1.1: runtime animation cleanup, distinct machine/ChaCha sheets, compile guard.
- alpha.8: MiMi walk/broom animation rework.
- alpha.9: pre-Scrap mystery MiMi appears as `???` around Town 15:00–17:00 with vague dialogue.
- alpha.10: MiMi broom front/down pose fix.
- alpha.10.1: source pose integration while preserving character design.
- alpha.10.2: front broom hand-grip fix; hands closer together gripping shaft more naturally.
- alpha.11: native Stardew NPC foundation for mystery `???` + persistent handoff/history files. Initial user compile exposed `CS0266` from assuming SMAPI dictionary data was a concrete `Dictionary`.
- **alpha.11.1 CURRENT:** custom MiMi render + portrait dialogue: use `IDictionary<string, CharacterData>` for `Data/Characters` asset edit; preserve native-NPC foundation and handoff/history files.

## Locked design decisions
- First story trigger is the **first natural Cardboard Scrap**, not a calendar day.
- Before that trigger, MiMi's identity stays `???` and she does not explain Cardcha.
- MiMi is story lead; Wizard is mentor/lore source.
- ChaCha is MiMi's fairy bunny familiar and machine activation key.
- Cardcha orb is transparent with one light core; avoid Poké Ball-like red/white split.
- MiMi default town presence concept: 15:00–17:00.
- Regular normal-enemy Shiny chance: 3%.
- Card Seeker affects normal Scrap only.
- Do not rapidly expand card count until story/core/UI are stable.

## Build behavior expected from future ChatGPT sessions
When user says “build”, do the build immediately and return a clickable ZIP link. Do not repeatedly restate the plan.

## v0.1.17-alpha.11.2 — MiMi Timed Broom Arrival + Buff Lock
- Disabled native schedule-driven Town placement and moved exact mystery-phase timing into C# runtime.
- MiMi is hidden off-map before 15:00 and after 17:00.
- 15:00 while player is in Town: broom arrival animation (Down/front row) -> native ??? actor lands in plaza.
- 17:00 while player is in Town: native actor removed -> broom departure animation (Up/back row).
- Added vanilla-safe native `mimi_npc.png` (16x32 cells) and `mimi_npc_portraits.png` to fix half-face cropping.
- Added native dialogue fallback asset; manual localized mystery dialogue interception remains.
- Added `LoadoutService.CardEffectsActive`: equipped-card effects/HUD are locked until Machine + Binder are actually delivered.
- Preserves old equipped loadout data instead of deleting it.

## v0.1.17-alpha.11.5 — MiMi 13–17 Mystery / Next-Day Farm Visit
- Town mystery window widened to 13:00–17:00.
- ChaCha now stays visibly beside MiMi before being lent.
- Nearby villagers can react with speech bubbles to the unknown girl.
- First Scrap no longer causes same-day MiMi visit; farm broom arrival is next day.
- Farm dialogue waits until the visible broom landing finishes.
- Wizard meetup moved to WizardHouse, 13:00–17:00.
- Hard combat/HUD lock before the Wizard hands over Machine + Binder.
- Explicit MiMi MugShotSourceRect for better minimap icon crop compatibility.


## v0.1.17-alpha.11.5 — Farm Arrival Scale Fix
- Fixed next-day Farm MiMi broom scene being drawn at 1x and appearing tiny.
- MiMi broom story event now uses 2x scale, consistent with Town broom arrival/departure.
- Adjusted ChaCha story-event offset/scale to remain beside MiMi.


## alpha.11.9 hotfix
- Switched MiMi / Wizard dialogue to use NPC dialogue stacks so portraits actually render.
- Mystery Town departure now always starts a broom-flight state instead of instant hide.
- Arrival is also allowed to start as broom flight when the player enters Town during the active window.
- MiMi world sprites were given a small clarity/contrast pass to reduce the washed-out look.


## alpha.11.10 compile hotfix
- Fixed `Dialogue` constructor argument order for Stardew 1.6 API: `new Dialogue(speaker, text)`.
- Keeps MiMi as the actual NPC speaker even when her displayed name is `???`, so the dialogue UI can use MiMi's portrait asset while preserving the mystery name.
- Retains alpha.11.9 broom arrival/departure and clarity pass.


## v0.1.17-alpha.11.11
- Reduced ChaCha size to 90% of the previous scale.
- Regenerated `mimi_npc.png` from `mimi_walk.png` for a closer style match in native NPC runtime.
- Regenerated `mimi_npc_portraits.png` from the prettier `mimi_portraits.png` strip so portrait expressions stay consistent.
- Dialogue constructor fix from alpha.11.10 preserved.


## v0.1.17-alpha.11.12 — installer pending-state regression fix
- Build output from alpha.11.11 was already successful; install failed only because SMAPI still had Cardcha.dll loaded.
- Restored exit-code 51 handling: DLL lock is now shown as BUILD SUCCESS / INSTALL PENDING, not INSTALL FAILED.
- Added retry-after-closing-game flow without rebuilding.
- Restored INSTALL_CARDCHA_ONLY.bat so the already-built ZIP can be installed later.
- No gameplay/art changes from alpha.11.11.


## v0.1.17-alpha.11.19 — mystery no greetings + portrait force
- Fixed dark/dirty-looking artifacts around MiMi's mouth.
- Replaced the six portrait slots with a clean consistent set: neutral, happy, worried, surprised, wink/cute, determined.
- Regenerated `mimi_npc_portraits.png` from the cleaned master strip so both portrait files stay visually identical in style.
- Kept alpha.11.12 installer pending logic unchanged.

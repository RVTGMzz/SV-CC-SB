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
- alpha.4 / alpha.4.1: ChaCha machine ritual animation; compile fix for ambiguous XNA `Color(...)` overload.
- alpha.5: MiMi/ChaCha story polish + first-pull quest. ChaCha officially loaned to player; Wizard supplies missing Scrap only.
- alpha.6: animation asset organization pass.
- alpha.7 / 7.1 / 7.1.1: runtime animation cleanup, distinct machine/ChaCha sheets, compile guard.
- alpha.8: MiMi walk/broom animation rework.
- alpha.9: pre-Scrap mystery MiMi appears as `???` around Town 15:00–17:00 with vague dialogue.
- alpha.10: MiMi broom front/down pose fix.
- alpha.10.1: source pose integration while preserving character design.
- alpha.10.2: front broom hand-grip fix; hands closer together gripping shaft more naturally.
- alpha.11: native Stardew NPC foundation for mystery `???` + persistent handoff/history files. Initial user compile exposed `CS0266` from assuming SMAPI dictionary data was a concrete `Dictionary`.
- **alpha.11.1 CURRENT:** compile fix: use `IDictionary<string, CharacterData>` for `Data/Characters` asset edit; preserve native-NPC foundation and handoff/history files.

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

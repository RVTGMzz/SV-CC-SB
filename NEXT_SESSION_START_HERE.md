# NEXT SESSION — Cardcha v0.1.17-alpha.11.45

## Verify current build first

- Binder visually-rightmost card -> RIGHT -> detail panel.
- Detail up/down scrolls and left/right exits correctly.
- MiMi works same weekday after handoff once story exit ends.
- First post-handoff merchant interaction gives one-time surprise-reward tease.
- Circular buff HUD sits higher.

## New design state preserved on 2026-08-25

Read these before implementing the next progression pass:

- `design/CARDCHA_DESIGN_CURRENT.md`
- `CARDCHA_PROJECT_STATE.json`

Key approved/planned direction:

- Base Set remains 80 cards; latest rarity distribution is 27 Common / 23 Rare / 16 Epic / 10 Legendary / 4 Mythic.
- Player now starts from 1 normal active card slot and progresses toward 5; exact normal-slot unlock milestones remain open.
- 20/40/60/80 unique-card milestones are the current plan for four Boss encounters.
- First Boss milestone unlocks one circular dedicated Boss Slot.
- Boss Slot uses manually activated Boss Energy rather than a long automatic cooldown.
- Activating the equipped Boss Card transforms ChaCha into that boss for a limited Boss Form duration.
- First-clear milestone Boss Cards are auto-granted special progression rewards outside the normal Common–Mythic pool.
- Max-star duplicates convert to Suspicious Dust; Dust is planned as the long-term Boss Slot leveling resource.
- Ticket Sense is replaced by Victory Charge (Ultimate/Boss Sync).
- Essence Finder is now Rare and can add +1 to either normal Cardboard Scrap or Shiny Cardboard Scrap after that Scrap type has already dropped.

Local detailed workbook snapshot: `Cardcha_BaseSet80_Design_Tracker_v0.1.5_EssenceFinderRare.xlsx`.

**Important:** these are design decisions only unless explicitly implemented in source after 11.45. Do not report Boss Slot/transformation as active in the current build yet.

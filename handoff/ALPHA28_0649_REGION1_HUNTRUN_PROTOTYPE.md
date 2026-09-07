# Alpha.28 0649 — Region I Hunt Run prototype

Status: implementation candidate; in-game acceptance pending.

## Locked purpose
Region I now uses a Rune Factory / roguelite-inspired authored-room run instead of one static farming field. Exactly **4 unique rooms are selected from a pool of 6** per paid/free Airship trip.

## Runtime flow
`Airship -> random 4-of-6 Region I rooms -> existing Region I Boss Gate hub -> Boss Gate 20 -> return / future Boss I`

The six prototype rooms are Cardcha-owned TMX maps made only from vanilla Stardew outdoor tilesheet references:
1. Verdant Clearing
2. Moss Creek
3. Old Ruins
4. Briar Thicket
5. Hollow Grove
6. Card Shrine

A run route never repeats a room. The seed includes save ID, in-game day, and Airship flight count, so later farming trips can roll a different route.

## Combat rules
- Each room rolls a controlled 5–8 monster encounter from Green Slime / Bat / Bug pools.
- Existing Cardcha monster-death -> Scrap economy remains authoritative. No direct normal-card drops were added.
- The north route only advances after all Cardcha-marked monsters in that room are defeated.
- The south route aborts/extracts back toward the Airship.
- After room 4, the player reaches the existing Region I Boss Gate hub.
- Existing 20 unique-card Boss Gate requirement is unchanged.

## Non-regression
No SaveData schema change. No progression milestone change. No Boss Card/Boss Form tuning change. No MiMi/stair changes. No changes to the Forest Arcane Gate, Airship visual, Airship deck, Sky Dock interior, or existing Region I Boss Gate TMX.

## Pending acceptance
Visual/layout quality and controller feel need in-game testing. This is the first functional 4-of-6 Hunt Run vertical slice, not final Region I art.

# Cardcha! — Current Design State

**Design snapshot:** 2026-08-25  
**Implementation baseline:** v0.1.17-alpha.11.45  
**Status:** Design decisions below are approved/planned unless marked otherwise. They are not necessarily implemented in the current build.

## 1. Base Collection

- Base collection remains **80 cards**.
- Current rarity distribution after the latest rebalance:
  - **Common:** 27
  - **Rare:** 23
  - **Epic:** 16
  - **Legendary:** 10
  - **Mythic:** 4
- Card upgrade caps are intentionally mixed between **3★ and 5★** depending on effect strength and balance risk.
- The detailed spreadsheet remains the balance/source tracker for the 80-card set.

### Art/design numbering currently completed

1. Iron Edge
2. Thick Hide
3. Keen Eye
4. Swift Feet
5. Blood Fang
6. Executioner
7. Card Seeker
8. Chain Hunter
9. Last Stand
10. Phoenix Heart

The art-design index is **1–10** (not 0–9).

## 2. Card Drops / Scrap Economy

- Finished normal cards **do not drop directly from monsters**.
- Monsters drop Cardcha resources; cards are obtained through the Cardcha machine / collection systems.
- Economy remains centered around:
  - **Cardboard Scrap**
  - **Shiny Cardboard Scrap**
  - **Suspicious Dust** (working name)

### Essence Finder — latest rule

- **Rarity:** Rare.
- Essence Finder does **not** increase the chance that a monster produces a Scrap drop.
- When a Scrap drop has already occurred, it gives a level-scaled chance to add **+1 of the same Scrap type**.
- It applies to **both Cardboard Scrap and Shiny Cardboard Scrap**.
- Current spreadsheet draft uses an **8–16%** bonus chance across its star progression.

Example:
- 3 Cardboard Scrap can become 4.
- 1 Shiny Cardboard Scrap can become 2.

## 3. Ticket Sense Replacement

**Ticket Sense is removed.** There is no direct Card Ticket/card drop mechanic to support it.

Replacement card:

### Victory Charge

- **Rarity:** Common.
- **Build:** Ultimate / Boss Sync.
- Kills increase the amount of **Boss Energy** gained from kill-based energy generation.
- Current spreadsheet draft: **+10% / +15% / +20% / +25% / +30%** from 1★ to 5★.
- The effect only becomes useful after the Boss Slot system is unlocked.

## 4. Normal Card Slot Progression

- New design direction: the player starts with **1 normal active card slot**, rather than receiving several active slots immediately.
- Progression gradually expands the normal loadout toward the existing long-term maximum of **5 normal slots**.
- Exact unlock milestones for normal slots 2–5 are still open for balance testing.

## 5. Boss Milestone System

Boss progression is tied to Base Collection milestones.

Current intended cadence:

- **20 / 80 unique Base cards** → Boss encounter 1
- **40 / 80** → Boss encounter 2
- **60 / 80** → Boss encounter 3
- **80 / 80** → Final milestone Boss encounter

First-clear of each milestone boss grants its corresponding **special Boss Card automatically**.

This is a deliberate exception to the normal rule that monsters/bosses do not directly drop finished cards. Normal Base cards still do not drop directly. Boss Cards are progression trophies/rewards and live outside the Common–Mythic Base rarity pool.

## 6. Boss Slot

- At the first Boss milestone (**currently planned at 20 unique Base cards**), the player unlocks **one dedicated Boss Slot**.
- Boss Slot is visually distinct: **circular**, while normal card slots remain square/rectangular.
- There is only **one Boss Slot**.
- It is separate from the normal 1–5 card-slot limit.
- A Boss Card is equipped into this circular slot.

### Activation direction

Boss Card is an **active Ultimate**, not a passive auto-proc.

- Combat fills a **Boss Energy meter**.
- When the meter is full, the circular Boss Slot shows a clear `READY` state.
- The player manually activates it, preferably by tapping/selecting the Boss Slot itself so mobile does not need another permanent HUD button.
- A very short internal lockout may exist for technical safety, but the core recharge system is **Energy**, not waiting for a long cooldown.

## 7. ChaCha Boss Transformation

Activating a Boss Card does **not** summon a separate permanent companion.

Instead:

1. The equipped Boss Card reaches full Boss Energy.
2. The player manually activates the circular Boss Slot.
3. **ChaCha transforms into that Boss Form** for a limited duration.
4. The Boss Form uses behavior/mechanics tied to that specific boss.
5. ChaCha returns to normal when the transformation ends.

Boss Forms should preserve recognizable ChaCha identity where practical (visual marker, expression, aura, accessory, etc.) so the transformation reads as **ChaCha becoming the boss**, not a random boss spawning nearby.

The preferred implementation style is controlled/scripted targeting and attacks rather than building a fully independent pathfinding companion framework.

## 8. Boss Energy / Boss Sync Build Direction

A new card-build family should support the transformation system. Working labels:

- **Ultimate**
- **Boss Sync**

Useful effect families include:

- faster Boss Energy generation;
- extra Boss Energy from kills/crit/combat actions;
- longer Boss Form duration;
- retaining a small amount of Energy after transformation;
- overcharge that converts excess Energy into extra transformation duration;
- limited kill-based extension while transformed, with hard caps.

This family is a good replacement target for Base cards whose old effects are difficult to detect, difficult to implement reliably, or no longer fit the current economy.

## 9. Duplicate / Dust / Boss Slot Progression

Duplicate progression should remain useful even late-game.

Current direction:

1. A duplicate of a card that is **not yet at its maximum star level** contributes to that card's normal upgrade progression.
2. Once that card is already **Max ★**, further duplicates convert automatically into **Suspicious Dust**.
3. Suspicious Dust becomes a long-term resource used to **level the Boss Slot / Boss system**.

Boss Slot levels should primarily improve system qualities such as:

- Boss Energy gain efficiency;
- Boss Form duration;
- other tightly capped Ultimate utility.

Avoid making Boss Slot levels a simple large direct-damage multiplier, because normal card synergies already provide substantial combat scaling.

## 10. Design Guardrails

- Boss Cards are special progression rewards, not a sixth ordinary gacha rarity.
- Boss Slot remains one dedicated slot.
- Boss transformation should feel like a signature Cardcha/ChaCha mechanic.
- Avoid turning Boss Forms into permanent pets or a separate heavy companion/pathfinding framework.
- Avoid creating a full elemental resistance/weakness subsystem solely for Boss Cards unless that becomes a future intentional expansion.
- Ultimate-support cards should enable distinct build choices (fast charge vs long duration vs transformation-focused), not all collapse into generic damage increases.

## 11. Detailed Tracker

Local working artifact at this snapshot:

`Cardcha_BaseSet80_Design_Tracker_v0.1.5_EssenceFinderRare.xlsx`

The workbook contains the current 80-card database, rarity/progress tracking, star-upgrade drafts, Boss Slot notes, economy synchronization, and the latest Essence Finder / Victory Charge changes. Binary workbook upload is tracked separately from this readable GitHub design snapshot.

# Cardcha: Shardbound — Story & Gameplay Bible

Status: **Design documentation / implementation roadmap**

This file records decisions that have been clearly agreed for MiMi, ChaCha, the 20/40/60/80 boss arc, Community Center integration, and the future airship system. Items marked **LOCKED** should be treated as current canon/design requirements. Items marked **TBD** are intentionally not finalized yet.

---

## 1. MiMi as a real Stardew NPC

### LOCKED
- MiMi should eventually behave as a full NPC rather than only a merchant/event actor.
- The player can give MiMi gifts and raise friendship hearts with her.
- MiMi starts as a wandering Scrap merchant, but later moves into the Community Center and operates a permanent stall there.
- MiMi should have friendship/story progression, contextual behavior, and mail interactions.

### MiMi's private hobby / 17:30 secret

**LOCKED:** MiMi has a favorite TV series at **17:30 (5:30 PM)**.

Her gradually revealed secret is that she is a BL-couple/shipping fan ("hủ nữ" / fujoshi-style fandom). This should be uncovered progressively through story and friendship rather than stated immediately.

Relationship-aware behavior is also **LOCKED**:
- If the player dates a male NPC, MiMi's dialogue/behavior changes and she becomes noticeably curious and excited about the couple.
- If the player marries a male NPC, MiMi gives the player a very large celebratory gift.
- After such a marriage, MiMi may occasionally send additional gifts through the mailbox.

Exact dialogue, heart-event thresholds, birthday, gift tastes, and daily schedule are **TBD**.

---

## 2. MiMi and the Community Center

### LOCKED design direction
- MiMi participates in the Community Center restoration instead of only using it as a shop location.
- Once per season, MiMi contributes **one missing seasonal Community Center item/requirement** that the player still needs.
- The intention is to help the player gradually, not complete the Community Center for them.
- Later in progression, MiMi moves her merchant stall into the Community Center.

### TBD implementation details
The exact Stardew implementation still needs research/testing because Community Center state can vary by save. Before coding this system, confirm behavior for:
- normal Bundles;
- Remixed Bundles;
- Vault/money requirements;
- Joja-route saves;
- what counts as an eligible "seasonal" missing item;
- when the seasonal contribution is applied if no valid item is missing.

Do not hard-code a fixed vanilla bundle list until these cases are verified.

---

## 3. Boss progression: 20 / 40 / 60 / 80 cards

### LOCKED
Card collection progression has four major boss milestones:
- **20 discovered cards** → Boss milestone I
- **40 discovered cards** → Boss milestone II
- **60 discovered cards** → Boss milestone III
- **80 discovered cards** → Final boss milestone

The specific identities/designs of the 20/40/60 bosses are **TBD**.

A mythology/Olympus-inspired direction is a preferred concept candidate for some of these bosses, but the exact roster is not locked.

### Final boss
**LOCKED:** MiMi is the intended **80-card final boss** of the first major Cardcha story arc.

The preferred story direction is that this is not a simple "MiMi was evil all along" reveal. MiMi has a deeper connection to Cardcha and the final fight should function as a major story payoff/test/confrontation after the player has spent a long time knowing her as a real NPC.

Exact lore explaining why MiMi is the final boss is **TBD** and should be written before implementation.

### Art-direction guardrail
Use original Cardcha artwork/sprites for mythological bosses. Mythology itself can inspire the designs, but do not ship edited/reused character sprites from the game *Hades* or other copyrighted games.

---

## 4. Airship / sky boss hub

### LOCKED
Cardcha will use a **Rune Factory-inspired airship / flying vessel concept** to solve access to boss content.

Instead of spawning major bosses directly in Pelican Town:
- the player uses the airship to travel upward/outward;
- boss encounters take place on dedicated Cardcha mini-maps/arenas;
- the 20/40/60/80 milestones can unlock new destinations or routes.

This gives Cardcha a scalable boss system without crowding or destabilizing normal Stardew maps.

### TBD
- Airship name.
- Exact unlock quest.
- Where the boarding point exists in Stardew Valley.
- Exact layout of the airship.
- Whether the ship visibly upgrades at 20/40/60/80.
- Exact boss destination maps.

The airship should be designed as an extensible hub so future bosses can be added as new destinations instead of requiring major changes to Pelican Town.

---

## 5. ChaCha identity and expressions

### LOCKED
- ChaCha does **not** speak dialogue normally.
- ChaCha communicates through contextual expressions/visual reactions beside the player.
- These reactions should respond to gameplay/story situations and help ChaCha feel like a real companion despite being non-verbal.
- ChaCha can transform/use forms tied to Boss/Mythic cards as part of the boss progression system.

The complete expression set, animation list, and exact Boss/Mythic transformation rules are **TBD**.

---

## 6. ChaCha passive — healing/support system

### Core behavior — LOCKED
ChaCha's support passive is available from the time ChaCha is received.

There are two ways it can trigger:
1. **When the player successfully hits a monster** — normal proc chance.
2. **When the player takes damage** — half of the normal proc chance.

When the passive triggers:
- ChaCha restores a percentage of the player's **HP** based on the currently activated tier.
- After the HP heal triggers, there is a separate **30% chance** to also restore the same tier percentage of the player's **Energy/Stamina**.

Use Stardew-facing terminology such as **Energy/Stamina**, not MP.

### Proc chance by major collection milestone — LOCKED

| Discovered cards | On successful monster hit | When player takes damage |
|---:|---:|---:|
| 0–19 | 2% | 1% |
| 20–39 | 4% | 2% |
| 40–59 | 6% | 3% |
| 60–79 | 8% | 4% |
| 80 | 10% | 5% |

The damage-received chance is intentionally exactly half of the attack-hit chance.

### Healing/energy strength by 10-card tier — LOCKED

| Activated card tier | HP restored on proc | Energy/Stamina restored if 30% secondary proc succeeds |
|---:|---:|---:|
| 0 cards | 10% | 10% |
| 10 cards | 11% | 11% |
| 20 cards | 12% | 12% |
| 30 cards | 13% | 13% |
| 40 cards | 14% | 14% |
| 50 cards | 15% | 15% |
| 60 cards | 16% | 16% |
| 70 cards | 17% | 17% |
| 80 cards | 18% | 18% |

### Tier activation quest — LOCKED
Reaching the collection count alone does **not** automatically activate the next support-strength tier.

For each 10-card milestone, the player must:
- prepare/collect **9 foods that ChaCha loves**;
- complete the associated quest;
- return/turn in the quest to **MiMi**.

Only after the milestone quest is completed does that passive tier become active.

At 20/40/60/80, the corresponding proc-rate milestone is part of that progression and should not bypass the required activation quest.

### Example — LOCKED behavior
If the player has activated the **40-card tier**:
- successful hit on a monster → 6% chance to trigger ChaCha support;
- taking damage → 3% chance to trigger ChaCha support;
- successful trigger → restore 14% HP;
- then 30% chance to additionally restore 14% Energy/Stamina.

### TBD balance/technical details
- Internal cooldown, if any.
- How multi-hit attacks are counted.
- Whether damage-over-time can trigger it.
- Multiplayer ownership/synchronization.
- Exact visual/audio feedback for HP-only vs HP+Energy procs.

These should be balance-tested rather than silently assumed.

---

## 7. Relationship between collection milestones

Current intended structure:
- **Every 10 cards:** opens a new ChaCha support-strength tier, activated through MiMi's 9-food quest.
- **Every 20 cards:** also increases ChaCha's passive proc chance and advances the major boss/story progression.
- **20/40/60/80:** boss milestones and major story beats.
- **80:** MiMi final boss for the first major arc.

This lets collection progress feed both everyday companion power and large story/boss milestones.

---

## 8. Do not treat these as finalized yet

The following are intentionally still open:
- identities/mechanics of Boss 20, 40, and 60;
- exact lore behind MiMi's final-boss role;
- exact friendship-heart event script;
- MiMi's full gift taste table and birthday;
- precise Community Center implementation edge cases;
- airship name/map/layout and boarding location;
- exact ChaCha expression sprites;
- passive internal cooldown/multi-hit rules;
- exact Mythic/Boss transformation mechanics.

When these are decided, update this document instead of relying on chat history.

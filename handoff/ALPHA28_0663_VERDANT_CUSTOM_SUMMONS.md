# Alpha28 0663 - Verdant custom summon mobs

Build: `0.3.0-alpha.28.0.4.14.4.5.12.30`
Branch: `cardcha-alpha28-0663-verdant-custom-summons`
Status: implementation candidate, in-game acceptance pending. 0660-0662 acceptance also remains pending.

## Custom summons
- Verdant Guardian no longer presents vanilla Green Slime/Bug art for Summon Adds.
- Two Cardcha-owned summon identities now exist: `briarling` and `leaf_wisp`.
- Briarling: compact bark/thorn bud, slower and tougher melee proxy.
- Leaf Wisp: floating seed spirit, faster and lighter Bug proxy.
- Both use dedicated 4-direction x 4-frame Cardcha sprite sheets. Vanilla proxy art is hidden through `isInvisible`; AI/collision/damage/death routing stay native and stable.
- Summon cast now pre-plans exact spawn tiles and renders custom Verdant portals at those tiles during the 600ms telegraph.

## Phase composition
- Phase 1: Briarling + Briarling.
- Phase 2: Briarling + Leaf Wisp + Briarling.
- Phase 3: Leaf Wisp + Briarling + Leaf Wisp.
- Existing hard cap of 4 living Boss I adds remains unchanged.
- Existing SummonAdds cooldowns remain unchanged.

## Provisional add stats
- Briarling HP 55/75/95 and Speed 2/3/3 by phase.
- Leaf Wisp HP 38/52/68 and Speed 4/5/6 by phase.
- These are test values for later balance acceptance, not a global balance pass.

## Debug
- `cardcha_boss1_summons` clears current Boss I adds and spawns one deterministic custom wave for the current phase.
- `cardcha_boss1_visual_status` now includes custom summon renderer state.

## Locked systems preserved
Save schema 19, 20/40/60/80 milestones, 76 active normal-card audit / 80 stored base IDs, Boss Form 10 sec, Boss Energy x1/3, Guardian Rabbit 0662 runtime, Verdant Colossus 0660, Verdant Core Boss Card 0661, 0659 MiMi stair behavior, MiMi native profile + CC continuity, Region I Hunt Run 4-of-6, Airship route/upgrades, controller mapping and Forest gate are unchanged.

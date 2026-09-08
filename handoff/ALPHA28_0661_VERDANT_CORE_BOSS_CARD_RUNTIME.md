# Alpha28 0661 - Verdant Core Boss Card Runtime

Build: `0.3.0-alpha.28.0.4.14.4.5.12.28`
Branch: `cardcha-alpha28-0661-verdant-core-boss-card-runtime`
Status: implementation candidate, in-game acceptance pending. 0660 visual acceptance is still pending because the user continued before testing it.

## Boss Card architecture
- Boss Cards are a separate system from the normal 76-card pool.
- Save schema remains 19 and reuses `BossCardsUnlocked` + `EquippedBossCardId`.
- Boss I first clear already unlocks `verdant_core` and auto-equips it if the dedicated Boss Card slot is empty.
- 0661 adds the first real runtime effect, HUD state, world feedback, debug equip/unlock/trigger commands, and an authored Verdant Core icon.

## Verdant Core effect
- Trigger: an incoming hit would leave the local player at or below 50% Max HP.
- The triggering hit is protected too.
- Verdant Guard duration: 6 seconds.
- Incoming damage reduction while active: 35%.
- Recovery: 2 HP each second while active.
- Cooldown: 24 seconds from activation.
- Runtime state is transient; unlock/equip persistence remains in existing save fields.

## Debug
- `cardcha_boss_card_status`
- `cardcha_boss_card_unlock`
- `cardcha_boss_card_equip verdant_core|none`
- `cardcha_boss_card_trigger`

## Locked systems preserved
Save schema 19, 20/40/60/80 milestones, 76/76 normal card audit, Boss Form 10 sec, Boss Energy x1/3, 0659 MiMi stair resolver, MiMi profile/CC continuity, Region I Hunt Run 4-of-6, Verdant Guardian 0660 Colossus visuals/combat/reward timing, Airship route/upgrades, controller mapping and Forest gate are unchanged.

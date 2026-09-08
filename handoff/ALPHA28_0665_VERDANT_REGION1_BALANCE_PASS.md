# Alpha28 0665 - Verdant Region I Balance Pass

Build: `0.3.0-alpha.28.0.4.14.4.5.12.32`
Branch: `cardcha-alpha28-0665-verdant-balance-pass`
Status: balance candidate; in-game acceptance for 0660-0665 remains pending.

## Verdant Guardian
- HP: 1300 -> 1600 (+23%, deliberately not doubled).
- Phase damage: Swipe 10/12/14; Root 8/10/12; Charge 14/16/19; Vine 4/5/7; Slam 16/18/22.
- Cooldowns/decision gaps are slightly more readable; telegraph and animation timings are unchanged.

## Heavy body
- 8% final knockback, 12 trajectory cap.
- 18 px recoil envelope, then recenter to HeavyAnchor.
- Charge and phase recenter remain the only ways HeavyAnchor itself moves, preventing team wall-pinning.

## Summons
- Briarling HP 50/68/84, speed 2/3/3.
- Leaf Wisp HP 34/46/58, speed 4/5/5.
- Max active adds remains 4; 0663 species/composition is unchanged.

## Guardian Rabbit
- Duration 10s, pulse every 2s, radius 176 px unchanged.
- Root Pulse damage 18 -> 14.
- Boss Energy cost 100 and gain x1/3 unchanged.

## Verdant Core
- Trigger 50% projected HP, duration 6s, regen 2 HP/s unchanged.
- Damage reduction 35% -> 30%.
- Cooldown 24s -> 28s.

## Debug
- `cardcha_boss1_balance_status`

## Locked systems preserved
Save schema 19, 20/40/60/80 milestones, 76 active normal cards / 80 stored IDs, 0659 MiMi stair resolver, MiMi profile/CC continuity, Region I Hunt Run 4-of-6, 0660 visuals, 0663 custom summon art, 0664 arena/camera/sound polish, Airship route/upgrades, controller mapping and Forest gate are unchanged.

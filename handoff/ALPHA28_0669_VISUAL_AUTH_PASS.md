# Alpha28 0669 - Visual / Auth Pass

Build: `0.3.0-alpha.28.0.4.14.4.5.12.38`
Branch: `cardcha-alpha28-0669-visual-auth-pass`
Status: CI/package pending; in-game visual acceptance required.

## Scope
### 1. Combat actor auth
- Totem and summon gameplay proxies are no longer `isInvisible`.
- Harmony suppresses GreenSlime proxy DRAW only for Boss, Totem and Boss Add markers.
- Both Briarling and Leaf Wisp use stable targetable GreenSlime actor proxies; custom art remains authoritative.
- Summon custom art is reduced toward native Stardew scale and gets a compact HP confirmation bar.
- Totem art follows the actual proxy position.
- Totem monster-style HP bars are removed; damage states are authored into the 4-frame seed-effigy sprite.
- Totem balance remains frozen: 4 x 90 HP, barrier 15/10/6/3/0%, final stagger 1.2s.

### 2. Airship gate visual fix
- Procedural oversized portal tower is replaced by a compact authored boarding-gate sprite.
- Forest gate anchor, interaction radius and collision contract remain unchanged.
- Gate still uses the existing farmer-depth patch.

### 3. Sky Dock + map polish foundation
- Airship Deck and Sky Dock props are grouped into purposeful clusters rather than scattered test props.
- Boarding marker is reduced to a small ground confirmation.
- Region I Hunt Run uses an 8-cell authored environment atlas and room-specific asymmetric edge clusters.
- This is a foundation pass, not the final Region I map redraw.

## Preserved
- 0668C physical Hunt Run Lost Cache.
- 0668B timed combat HUD / Adrenaline runtime coverage.
- Boss I 1600 HP and 0665 damage/cooldown profile.
- Save schema 19, 76 active cards / 80 source entries, controller semantics, MiMi/ChaCha locked contracts.

## Acceptance
1. `cardcha_test_boss1`, then `cardcha_boss1_summons`: Briarling/Leaf Wisp must move under native actor AI, take damage and die.
2. Totem sprite, hit feedback and damage target must occupy the same place. No monster-style HP bar under decorative pillars.
3. Break all four Totems and confirm Barrier reduction + final 1.2s stagger still works.
4. `cardcha_test_gate`: Forest boarding gate must render as one compact authored object with correct player depth.
5. `cardcha_test_airship`: inspect Sky Dock and Deck for reduced scatter/placeholder feel.
6. Run several Hunt Run rooms and judge only the visible 0669 foundation: less repetition, more organic edge dressing.
7. Lost Cache remains a physical interactable chest.
8. Adrenaline timed HUD still appears for ~3 seconds after kill.

## Next
Do not claim the full boss/ChaCha concept art overhaul is finished in 0669. If this auth/foundation pass is accepted, the next visual build can focus on native-size Verdant Guardian + Guardian Rabbit authored animation sets.

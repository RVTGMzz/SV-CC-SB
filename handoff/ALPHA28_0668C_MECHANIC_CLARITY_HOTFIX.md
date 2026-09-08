# Alpha28 0668C - Mechanic Clarity Hotfix

Build: `0.3.0-alpha.28.0.4.14.4.5.12.37`
Branch: `cardcha-alpha28-0668c-mechanic-clarity-hotfix`
Status: CI/package pending until workflow completes; in-game acceptance pending.

## Screenshot-corrected issue identity
The screenshot labeled `KHO ĐỒ THẤT LẠC` was a Hunt Run `LostCache` rare encounter, not the Sky Dock Lost & Found point. 0668C fixes the actual Hunt Run room behavior.

## Implemented
### Verdant Seed Totems
- Balance frozen: 4 x 90 HP, barrier 15/10/6/3/0%, >=2 totems keeps the existing Root/Vine ~8% cooldown acceleration, final stagger remains exactly 1.2s.
- Vanilla GreenSlime totem proxy is hidden.
- Boss HUD now shows living Totems and current Barrier percentage.
- Stronger per-totem hit flash and floating damage feedback.
- Dead totem proxies are pruned from the arena actor list so they cannot remain live targets.
- Each break reports the new barrier percentage.
- Final break adds a strong camera/sound/world burst while preserving the existing 1.2s state-machine stagger.

### Hunt Run Lost Cache
- LostCache no longer auto-clears merely because the room has zero monsters.
- A physical Stardew Chest is spawned at the rare-room interaction point.
- No floating `KHO ĐỒ THẤT LẠC` name or button hint is shown before interaction.
- Adjacent action/controller input and direct mouse right-click can claim the cache.
- Only after interaction are +4 Scrap and +1 Shiny Scrap granted to the run's unbanked reward pool and the node becomes cleared.
- Route/boon progression stays hidden until the cache is actually opened.

## Preserved from 0668B
- Adrenaline and the other timed Cardcha HUD runtime states remain unchanged.
- Persistent READY clutter remains hidden.
- Verdant Core separate READY panel remains hidden; gameplay remains active.

## Explicitly out of scope
- Verdant Guardian native-size art overhaul.
- Guardian Rabbit / ChaCha boss-form art overhaul.
- Airship/Sky Dock redesign.
- Full Region I environment redesign.
- Briarling/Leaf Wisp native-size redraw.
These remain 0669 work after 0668C in-game mechanic acceptance.

## TEST handoff
### Prerequisites
- Load a save with Cardcha available.
- Normal Boss I access still follows established Region I/Boss I progression.
- LostCache is a Hunt Run rare encounter and normally appears from later run nodes according to the existing rare-room roll.

### Debug bypass
- Boss I direct test: `cardcha_test_boss1`.
- Totem diagnostic: `cardcha_boss1_totem_status`.
- Timed HUD diagnostic: `cardcha_hud_runtime_status`.
- Hunt Run diagnostic: `cardcha_huntrun_status`.
- `cardcha_huntrun_clear` remains a test-only combat/node bypass and intentionally bypasses the physical-cache acceptance path.

### Verify
1. Boss I has four custom Verdant totems with no visible vanilla slime proxy.
2. Damage one totem repeatedly: HP bar, hit flash and damage number follow the correct totem.
3. Break one: broken state remains visible, live target disappears, HUD Barrier percentage drops.
4. Break all four: the final break produces an unmistakable 1.2s Guardian stagger.
5. In a Hunt Run LostCache room, the center is a physical chest, with no idle floating `KHO ĐỒ THẤT LẠC` label.
6. Before opening the chest, route choices must not become available.
7. Interact by controller/action or right-click: chest resolves, reward message appears, then route/boon progression becomes available.
8. Equip Adrenaline, kill a monster and confirm its approximately 3.0s timed HUD icon still appears.

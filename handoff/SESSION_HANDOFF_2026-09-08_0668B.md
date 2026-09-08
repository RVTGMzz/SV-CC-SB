# Cardcha session handoff — 2026-09-08 — 0668B

## Resume point

- Repository: `ronvotri/Cardcha-Shardbound`
- Branch: `cardcha-alpha28-0668b-combat-hud-runtime-coverage`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.36`
- Materialized gameplay/source head: `8f3c1ef5e644a47d4c5b2eaa8b27c36080578dff`
- CI run: `34239146350` — PASS
- Artifact ID: `10061185722`
- Package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.36_CombatHudRuntimeCoverage_HOTFIX_TEST.zip`
- Package SHA-256: `1268fe8fa76ae0b61e931a963de591a4b13a866be9f80c418fe5fc013477da08`
- In-game acceptance: PENDING

Do not resume from `main` or any stale alpha26/alpha27 branch. Continue from the branch above.

## Latest user-reported issues and fixes

### 0668B Combat HUD runtime coverage

User reported that equipping card #34 `Adrenaline` and killing monsters gave no visible Cardcha buff feedback even though the runtime effect existed.

0668B adds compact HUD coverage for timed/stacked Cardcha proc effects, including:

- Guard Step
- Backstep
- Explorer
- Momentum
- Adrenaline
- Fleet Hunter
- Battle Trance
- Overclock
- Void Walker
- Time Breaker
- Apex Predator
- Predator stacks
- War Drum stacks

`Adrenaline` remains a 3-second proc and should now display its own Cardcha icon/timer when active.

Persistent READY indicators are temporarily hidden to reduce UI clutter. The separate large Verdant Core left-corner READY panel is also temporarily hidden. Verdant Core gameplay remains active: trigger, damage reduction, healing, cooldown, world feedback and diagnostics are unchanged.

Debug command:

`cardcha_hud_runtime_status`

Expected Adrenaline test: equip Adrenaline, kill a monster, Cardcha HUD should show the Adrenaline icon and roughly 3.0 seconds of duration, then disappear.

## 0668 Verdant Totem + Airship/Hub Cleanup

User identified the four green objects around the Verdant Guardian arena as looking like summoned minions, while allies attacked them without useful feedback. 0668 converted them into destructible Verdant Seed Totems.

Totem current contract:

- 4 fixed arena totems
- 90 HP each
- stationary, no knockback
- targetable/damageable
- boss damage reduction by living count: 4=15%, 3=10%, 2=6%, 1=3%, 0=0%
- if at least 2 live, Root/Vine cooldown is approximately 8% faster
- last totem breaking causes a 1.2s boss stagger

Debug command:

`cardcha_boss1_totem_status`

Still requires in-game acceptance for team targeting, HP feedback, destruction, proxy hiding and final stagger.

## Airship / Lost & Found / environment feedback

User's visual feedback before 0668:

1. Two Airship rooms looked empty and placeholder-like.
2. Lost & Found interaction was unclear/unusable.
3. Boarding/deck segment looked artificial.
4. Region I maps should feel more detailed and organic, closer to Stardew Valley forest maps.
5. Monster visuals looked enlarged by render scaling rather than authored at larger native sprite size, causing a blown-up/pixel-broken appearance.

User explicitly requested for Lost & Found:

- no floating name
- no floating `right click` hint
- use a normal Stardew-style chest/crate/object
- only reveal `Kho đồ thất lạc` when the player actually interacts/opens it or receives the contents

For Airship rooms, the only hard visual requirement is that they feel naturally Stardew Valley in style. Do not force futuristic Command/Support room labeling or sci-fi showroom presentation.

0668 added an initial hub/decor/interaction cleanup, but all of this is still in-game acceptance pending. Do not claim the Airship or forest map presentation is finished until screenshots/tests confirm it.

## Hunt Run 2.0 current design

0666/0667 expanded Region I farming into a daily roguelike-style Hunt Run.

Current route contract:

- 7–10 nodes per run
- branching Moss / Briar / Ancient paths
- checkpoint at nodes 3 and 6
- Boss Gate branch from node 7 onward
- optional Extract rather than mandatory boss finish
- temporary Run Boons only, never normal Binder cards
- normal monsters still feed the Scrap -> Gacha -> Unique Cards progression

Encounter foundation:

- Combat
- Ambush
- Elite Hunt
- Root Nest
- Ancient Shrine

Advanced layer:

- Elite Affixes
- Daily Mutation
- Rare Rooms such as Lost Cache, Moonwell and Ancient Echo

Debug commands:

- `cardcha_huntrun_status`
- `cardcha_huntrun_daily`
- `cardcha_huntrun_clear`

Daily-farming fun/replayability is still acceptance pending.

## Boss I stack currently included

0660–0665 remain included under the current branch:

- Verdant Guardian custom visual layer / large Colossus presentation
- hidden Green Slime boss proxy
- heavy-body anti-wall-pinning behavior
- custom attack animations and FX
- defeat sequence before reward
- Verdant Core Boss Card
- Guardian Rabbit ChaCha Boss Form
- custom Briarling / Leaf Wisp summon layer
- arena intro/camera/sound polish
- 0665 balance pass

Boss I balance currently includes 1600 HP and phase-scaled damage. Guardian Rabbit remains 10 seconds, Boss Energy 1/3 gain rate, Root Pulse 14 damage every 2 seconds.

In-game acceptance for the full 0660–0668 stack is still pending.

## Frozen / regression guard

Preserve unless new real evidence specifically implicates them:

- save schema 19
- 76 active normal-card audit / 80 source entries with 4 legacy mythic exclusions
- Boss Form duration 10 seconds
- Boss Energy gain scale 1/3
- Forest Arcane Gate interaction distance/collision
- Airship locked visual identity/hash and route
- MiMi Gift/Profile vanilla 4x profile scaling fix
- MiMi Community Center restored dialogue continuity
- WizardHouse stair resolver from 0659, which user previously marked temporarily OK
- controller semantic mapping
- MiMi birthday Spring 17
- MiMi remains final boss at 80
- ChaCha remains rabbit-like, never cat-like
- strict TMX CSV validation

## Immediate test order for next chat

1. Install only the latest 0668B package, not stacked older test zips.
2. Equip Adrenaline and kill a monster. Verify Cardcha timed icon/timer appears for roughly 3 seconds.
3. Verify the previous left-corner READY overlap is gone.
4. Enter Boss I and test all four Totems: team targeting, HP loss, break, no vanilla proxy art, final stagger.
5. Test Lost & Found interaction. No floating label/hint should be present.
6. Screenshot both Airship rooms and boarding/deck after 0668 decor changes. Judge purely by what is visible, do not infer missing objects from code.
7. Run several Hunt Run rooms for route, checkpoint, rare room and environment readability.
8. Inspect Briarling / Leaf Wisp visual quality. If still visibly blown-up, proceed to native-size art instead of further render scaling.
9. Continue Boss I acceptance: custom boss scale, animations, summon behavior, camera reset, death sequence, Verdant Core trigger and Guardian Rabbit.

## Likely next build after acceptance feedback

`0669` should focus on native-size enemy art and a stronger Region I environment art pass if the user's in-game screenshots confirm the current monsters/maps still look enlarged or placeholder-like.

Do not automatically start 0669 if the user first reports a concrete 0668B regression. Fix the observed regression on top of this branch first.

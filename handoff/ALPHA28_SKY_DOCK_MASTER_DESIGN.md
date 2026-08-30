# Alpha.28 — Sky Dock master design

Status: approved design direction after `0.3.0-alpha.28.0.2.0`.

## Role
Sky Dock is Cardcha's permanent travel hub. It must be convenient enough for repeated monster-farming trips while remaining low-conflict with vanilla Stardew Valley maps/NPCs.

## Exterior
- Gameplay entrance remains in `Forest`, immediately below the Farm and visibly left of the existing Forest -> Farm warp.
- Resolve position from the live Farm warp; do not hard-code vanilla-only coordinates.
- Exterior is cosmetic + interaction only.
- NEVER replace Forest tiles, collision, terrain features, objects, warps, or NPC pathing for Sky Dock.
- If a map overhaul changes the area, prefer moving the cosmetic dock marker to a nearby safe tile rather than claiming map space.

## Interior
Canonical internal location name: `Cardcha_SkyDockInterior`.

Visual direction:
- Stardew-scale wooden transit hall / sheltered dock.
- Warm wood, rope, lantern-like accents, restrained MiMi cyan magic.
- Central route board/console.
- Right-side airship docking bay / open-sky visual.
- Bottom entrance/exit back to Forest.
- Leave one utility corner open for future MiMi/ChaCha dialogue, route board, shop, quest board, or progression UI.
- Use Cardcha-owned layout + vanilla tiles for the foundation. Stardew Druid remains reference only; do not copy its source, sprites, maps, sheets, or paths.

## Travel loop
Normal gameplay loop:
`Forest Sky Dock exterior -> Cardcha_SkyDockInterior -> select route -> departure cutscene -> destination -> return cutscene -> Cardcha_SkyDockInterior -> Forest`.

For the alpha.28.0.3 foundation, Region I's real hunting map is not built yet, so a confirmed Region I departure may land on `Cardcha_AirshipDeck` as the staging destination. When Region I exists, change the destination without changing the fare/cutscene contract.

## Flight cutscenes
- Every normal outbound route selection gets a short departure cinematic.
- Every normal return trip gets a short arrival cinematic.
- Keep each cinematic short enough for farming loops (target ~3 seconds).
- Cutscene art is Cardcha-owned/procedural/vanilla-compatible; no Druid assets.
- Returning must remain safe even if the intended interior location fails to load; fall back outward rather than strand the player.

## MiMi fare contract
MiMi operates the route, so normal outbound farming trips have a modest fare.

Planned fare ladder:
- Region I: 100g
- Region II: 250g
- Region III: 500g
- Region IV: 1000g

Non-regression rules:
1. The player's first-ever outbound Airship trip is free.
2. Return travel is always free. Never strand a player because they spent all their gold while farming.
3. Fare is charged only after a deliberate route confirmation, not on entering Sky Dock or viewing route information.
4. Check the player's money again immediately before charging.
5. Persist flights taken and total fare paid for save-safe balancing/telemetry.
6. If departure cannot be created, do not consume fare.
7. Future friendship/trust discounts may modify the price, but must not break rules 1-6.

MiMi tone: practical merchant humor. The fee should read as fuel/docking/maintenance money, not punishment.

## Region progression contract
- Region I farming supports collection progress 0-20; Boss Gate unlock target 20 unique cards.
- Region II supports 21-40; gate target 40.
- Region III supports 41-60; gate target 60.
- Region IV supports 61-80; gate target 80.
- Old regions stay accessible after higher regions unlock.

## Frozen compatibility contracts
Do not regress:
- Binder PreviewCard/LockedCard action targeting.
- Controller synthetic-click suppression.
- stationary vs portable machine placement behavior.
- accepted MiMi walk/broom/mugshot assets.
- unidentified `???` ChaCha spontaneous-emote suppression.
- Sky Dock exterior must remain non-blocking to base-game NPC/gameplay.

# Cardcha Alpha 28 - 0683 Region II Room Interactions

Branch: `cardcha-alpha28-0683-region2-room-interactions`  
Build: `0.3.0-alpha.28.0.4.14.4.5.12.51`

## Purpose

0682 made Region II physically multi-room, but non-combat nodes still resolved immediately on entry. 0683 converts the archive into a tactile roguelike space: the player must walk to and interact with a physical room focus before Mirror Choice, Archive Event, Cache, Restoration, Cursed Archive, or Final Cache resolves.

## Physical interaction contract

- Mirror Shrine, Archive Lectern, Restoration Font and Cursed Tome are authored 32x32 native-pixel station art stamped into TMX `Buildings` layers through `region2_interaction_stations.png`.
- Cache and Final Cache use a real Stardew `Chest` object with Cardcha modData.
- No physical station is drawn from `RenderedWorld`.
- No floating action label is used. The entry message names the target; the room itself communicates the object.
- Controller and keyboard action-tile interaction are supported; direct right-click also works.

## Node behavior

- Mirror Choice: interact with the Archive Mirror, then the existing Mirror reward/record logic resolves.
- Archive Event: interact with the Archive Lectern before its existing reward/heal behavior resolves.
- Restoration: interact with the Restoration Font before the existing heal/reward resolves.
- Cache: a real chest must be opened; it disappears after Cardcha resolves the reward.
- Cursed Archive: enemies do not spawn until the player activates the Cursed Tome.
- Final Cache: the run does not become complete until the deep cache is opened.
- Boss Gate remains physical in Warden Vault and unchanged.

## Frozen contracts

- Region II remains 6-9 nodes, four room identities and 250g fare.
- Checkpoints remain node 3 and 6.
- Curator Records You remains intact.
- Hollow Curator remains 2200 HP, 40-card milestone, Mirror Archive reward.
- Region III/IV, Boss III/IV, Airship and MiMi assets are unchanged.
- Save schema remains 19; 80 source / 76 normal cards.
- Repository rendering-depth contract remains mandatory.

## Acceptance

In game, verify each manual node can be found and activated without props covering Farmer/NPCs. Cache chest must be physical and removable. Cursed Archive must stay dormant until the tome is activated. Internal room warps must retain node/record/cargo state.

# Alpha28 0666 - Region I Hunt Run 2.0 Foundation

Build: `0.3.0-alpha.28.0.4.14.4.5.12.33`
Branch: `cardcha-alpha28-0666-region1-huntrun2-foundation`
Status: implementation candidate; in-game acceptance pending.

## Run length
- Each Region I flight now rolls 7-10 nodes.
- Six handcrafted room maps remain the visual pool; rooms may recur later in a run, but the next node never immediately repeats the current room and the two visible branch choices point to different rooms.

## Branching routes
After a node is cleared, two world-space route markers appear:
- Moss Path: safer weighting, mostly Combat/Ambush.
- Briar Path: high-pressure weighting, Elite/Root Nest/Ambush, +1 unbanked Scrap on clear.
- Ancient Path: Shrine/Root/Elite mix, +1 unbanked Scrap on clear.
Two of the three are offered each node.

## Encounter foundation
- Combat: 5-7 controlled monsters.
- Ambush: 8-10 monsters.
- Elite Hunt: one high-HP elite proxy plus three adds.
- Root Nest: three stationary root-node proxies plus guards; root nodes receive a Cardcha world marker.
- Ancient Shrine: no combat; it immediately feeds the boon-choice flow.
All monster deaths still use the existing Scrap drop pipeline. No finished cards drop from rooms.

## Run Boons
At nodes 2, 5 and 8, plus Ancient Shrine encounters, the run offers 3 temporary boons as three in-world totems. Choose one by interacting with it. Current pool: Verdant Recovery, Scrap Compass, Deep Roots, Fortune Bud, Hunter's Edge, Moss Ward. Boons reset when the run ends.

## Checkpoints / extract risk
- Checkpoints at nodes 3 and 6 bank route bonuses into the existing virtual Scrap wallets.
- South exit remains a safe voluntary extract and banks current unbanked bonuses.
- An unexpected exit/death discards only the unbanked route bonus; previously checkpointed rewards remain safe.

## Boss branch
- From node 7 onward, a center Boss Gate branch appears.
- If the player has 20 unique cards, it banks current run rewards and routes to the existing Region I Boss Gate hub.
- If below 20, the marker shows progress and the player can keep hunting or extract.
- Boss remains optional for repeat farming.

## Debug
- `cardcha_huntrun_status`
- `cardcha_huntrun_clear`

## Preserved locks
Save schema 19, 76 active normal cards / 80 base IDs, Monster -> Scrap -> Gacha canon, Region I Boss package 0660-0665, Verdant Core, Guardian Rabbit 10 sec, Boss Energy x1/3, Airship visual/upgrade progression, Forest gate, MiMi profile/CC/stair fixes and TMX strict CSV safety remain unchanged.

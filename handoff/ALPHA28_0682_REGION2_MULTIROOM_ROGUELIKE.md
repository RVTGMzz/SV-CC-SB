# Cardcha Alpha 28 - 0682 Region II Multi-Room Roguelike

Branch: `cardcha-alpha28-0682-region2-multiroom-roguelike`  
Build: `0.3.0-alpha.28.0.4.14.4.5.12.50`

## Purpose
0680 made Region II a 6-9 node branching run. 0681 connected the run record to Hollow Curator. 0682 removes the remaining one-floor repetition: nodes now move through four physical Forgotten Archive room identities instead of replaying every encounter on one map.

## Room set
1. **Archive Vestibule** - broad early-run floor and ordinary combat/event space. Uses the accepted 0679 base map.
2. **Inkbound Stacks** - broken shelf islands and narrower combat pockets. Favours Ambush/Cursed Archive and some caches.
3. **Mirror Gallery** - wider symmetric reflection floor. Favours Mirror Choice, later events and some recovery/cache nodes.
4. **Warden Vault** - compact late-run chamber containing the assembled Archive Seal. Elite, Final Cache and Boss Gate resolve here.

A 6-9 node run may revisit a room identity, but standard combat rotates by depth and encounter kinds strongly bias different rooms. Node count remains the roguelike progression unit; a room is presentation/space, not a fixed checklist node.

## Runtime transitions
Internal Region II warps are explicitly distinguished from entering/leaving the region. Moving between Archive rooms never resets the run, never loses unbanked cargo and never restarts node 1. The selected node begins only after the destination room's Warped event resolves. Each room has its own spawn candidate set.

## Depth contract
All physical shelves, seal pieces and room motifs live in TMX Back/CardchaGround/Buildings/Front. No room furniture or scenery is drawn from RenderedWorld.

## Frozen contracts
- Region II remains 6-9 nodes.
- Fare remains 250g.
- Checkpoints remain nodes 3 and 6.
- Curator Records You remains active.
- Boss II remains 2200 HP / 40-card milestone / Mirror Archive reward.
- Region III/IV, Boss III/IV, Airship and MiMi art are unchanged.
- Save schema remains 19; 80 source / 76 normal cards.

## Acceptance
CI proves static/compile/package only. In-game verify at least one run crosses multiple room identities, internal warps preserve cargo/records/node count, enemy spawns are reachable, the Warden Vault seal is aligned, and no TMX physical prop covers Farmer incorrectly.

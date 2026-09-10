# Alpha.28 0684 Region II Room-Specific Mechanics

Branch: `cardcha-alpha28-0684-region2-room-specific-mechanics`
Build: `0.3.0-alpha.28.0.4.14.4.5.12.52`
Base: 0683 Region II Room Interactions

## Purpose

0684 makes the four Forgotten Archive room identities change how combat is played instead of changing only geometry/art. The 6–9 node route, physical room interactions, Curator Records You, progression and rewards remain intact.

## Room mechanics

- **Archive Vestibule:** intentionally no extra repeating room hazard. It remains the lower-pressure entry/breathing space.
- **Mirror Gallery / Reflected Trace:** periodically records the Farmer tile and its horizontal mirror position, telegraphs both 3x3 zones, then resolves damage through native `Farmer.takeDamage`.
- **Inkbound Stacks / Ink Sweep:** periodically telegraphs a horizontal row through the current player Y position; stepping off the row avoids it. This applies to Ambush/Cursed combat after the cursed tome is actually activated.
- **Warden Vault / Warden Seal:** Elite nodes pulse a telegraphed radius around the living Archive Warden. Killing/repositioning around the elite changes the pressure.

## Rendering-depth contract

`Region2Rogue.OnRenderedWorld` is newly wired **only for transient thin hazard outlines**. It draws no Chest, furniture, tree, rock, gate, station, boss body or other physical object. `render_depth_audit.json` marks the subscriber as `physicalAllowed=false`. Physical 0683 stations remain TMX/native objects.

## Frozen contracts

- Region II run target: 6–9 nodes.
- Checkpoints: 3 and 6.
- Region II fare: 250g.
- Boss II: Hollow Curator, 2200 HP, 40-card milestone.
- Curator Records You remains active.
- Save schema stays 19.
- Card audit stays 80 source / 76 active normal.
- Region III/IV, Boss III/IV, Airship accepted assets and `mimi_walk.png` are untouched.

## Debug

- `cardcha_test_region2`
- `cardcha_expedition_clear`
- `cardcha_region2_rogue_status`
- `cardcha_region2_mechanic_status`
- `cardcha_test_region2_bossgate`

## Acceptance

CI proves static/compile/package contracts only. In-game acceptance is pending. Test especially whether telegraphs are readable without becoming visual clutter, whether Ink Sweep can be dodged comfortably, and whether Warden Seal feels like elite pressure rather than unavoidable chip damage.

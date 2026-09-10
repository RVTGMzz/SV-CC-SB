# Alpha.28 0686 Hollow Curator Archive Rule Adaptation

Branch: `cardcha-alpha28-0686-hollow-curator-archive-rule-adaptation`
Build: `0.3.0-alpha.28.0.4.14.4.5.12.54`
Base: 0685 Region II Encounter Composition + Run Modifiers

## Purpose

0686 closes the run-to-boss loop: Hollow Curator now receives the current Region II Archive Rule in addition to the existing `Curator Records You` tendency record. The run modifier no longer disappears at the Archive Seal.

## Boss adaptation

- Phase 1 remains normal Observation with no Archive Rule gameplay effect.
- **Loose Folios:** phases 2/3 bias toward quick direct/paired attacks and shorten the decision gap by 100ms.
- **Iron Bindings:** phases 2/3 add weight to the heavy compression attack and lengthen the decision gap by 120ms.
- **Mirror Draft:** phases 2/3 add a mirrored Curator attack to the pool; every second eligible two-zone attack mirrors its secondary target across the arena.
- **Redacted Ledger:** phases 2/3 add extra weight to remembered-position echo attacks.
- The dominant run tendency remains the primary recorded adaptation; Archive Rule is a secondary layer and never disables the player's build.

## Transfer/lifecycle

Region II sends the Archive Rule through a transient parallel sink immediately before Boss II entry. It is consumed when Hollow Curator starts and cleared on runtime reset. `CuratorRunRecord` and save schema remain unchanged. Direct Boss II record-debug entry defaults to no Archive Rule; Region II boss-gate debug carries the run's selected rule.

## Presentation

At phase 2, one localized message reveals both the recorded tendency and inherited Archive Rule. Boss HUD shows the rule in phases 2/3. No new `RenderedWorld` subscriber or physical object is added; existing actor-depth boss rendering and telegraph VFX remain authoritative.

## Frozen contracts

- Region II run target 6–9 nodes; checkpoints 3 and 6.
- Region II fare 250g.
- 0683 physical interactions/Final Cache remain intact.
- 0684 room-specific mechanics remain intact.
- 0685 four Archive Rules and encounter composition remain intact.
- Hollow Curator remains 2200 HP at the 40-card milestone.
- Save schema remains 19.
- Card audit remains 80 source / 76 active normal.
- Region III/IV, Boss III/IV, accepted maps/art/Airship and `mimi_walk.png` are untouched.

## Debug

- `cardcha_test_region2`
- `cardcha_region2_rogue_status`
- `cardcha_test_region2_bossgate`
- `cardcha_test_boss2_record <risk|precision|pressure|recovery|mirror|neutral>`
- `cardcha_boss_milestone_status`

## Acceptance

CI proves static/compile/package contracts only. In-game acceptance remains pending. Compare several Region II runs through Boss II and confirm the Archive Rule remains noticeable but secondary to the tendency record, telegraphs stay readable, and phase 1 pacing remains unchanged.

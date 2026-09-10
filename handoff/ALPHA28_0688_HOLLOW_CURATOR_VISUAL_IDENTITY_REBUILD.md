# Alpha 28 0688: Hollow Curator Visual Identity Rebuild

Branch: `cardcha-alpha28-0688-hollow-curator-visual-identity-rebuild`  
Build: `0.3.0-alpha.28.0.4.14.4.5.12.56`

## Why this pass exists
Asset review found Boss II, III and IV shared the same 94-tile Buildings shell, while Hollow Curator had one 864x64 strip made of nine two-frame families. Boss I already used behavior-specific animation sheets, so Boss II was below the project visual bar.

## Boss II separation
Boss II now owns a dedicated 32-tile Forgotten Archive architecture sheet. The Buildings layer keeps the exact 0687 non-zero coordinates so collision/combat space stay frozen, but the generic shell is replaced by shelves, carved archive edges, mirrors, catalog drawers and seal props. Back receives non-collision record, paper, mirror-shard and central archive-seal motifs. Boss III/IV maps and visual assets are byte-frozen by CI.

## Hollow Curator animation library
Runtime no longer references the old two-frame-family strip. Ten dedicated 48x64-frame clips are used: idle 8, drift 8, observe 10, cast 10, page volley 10, mirror 10, adapt 10, hurt 6, phase transition 12, defeat 12. Damage creates a 360ms visual hurt window. Animation selection reads the existing state and attack IDs only.

## Frozen contracts
Hollow Curator stays 2200 HP. Phase 1 stays `new[] { 0, 0, 1 }`. 0686 Archive Rule adaptation, Region II 6-9 nodes/checkpoints 3/6/fare 250g, 40-card gate, save schema 19, 0683 interactions/Final Cache, 0684 room mechanics, 0685 modifiers and 0687 runtime-safe TMX remain unchanged.

## Rendering
Arena identity remains TMX/native world art. Hollow Curator remains on its Monster actor draw slot. RenderedWorld remains transient VFX only.

## Acceptance
CI validates clip sizes/frame counts, Boss II separation, unchanged collision footprint, runtime-safe TMX, compile/package and Boss III/IV byte freeze. In-game visual acceptance is still required.

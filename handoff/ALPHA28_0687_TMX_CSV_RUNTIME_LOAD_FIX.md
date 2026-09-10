# Alpha 28 0687: TMX CSV Runtime Load Fix

Branch: `cardcha-alpha28-0687-tmx-csv-runtime-load-fix`  
Build: `0.3.0-alpha.28.0.4.14.4.5.12.55`

## Purpose
Repair a runtime TMX CSV serialization defect discovered by live SMAPI testing. TMXTile splits CSV data on commas and passes every token to `UInt32.Parse`; an empty token therefore prevents the entire map from loading.

## Fix
- Canonicalizes every authored `<data encoding="csv">` block to exactly one comma between real GIDs and no trailing delimiter.
- Preserves every non-empty tile GID in the exact same order.
- Does not alter map dimensions, tilesets, properties, layers, artwork, gameplay anchors, or render ownership.
- Applies repository-wide to Cardcha `.tmx` assets so boss arenas and Region II rooms share the same runtime-safe format.
- Adds a validator that rejects empty CSV tokens, non-UInt32 GIDs, and layer tile-count mismatches.

## Live failure fixed
The reported stack ended in `TMXTile.TMXData.decode -> UInt32.Parse` for Hollow Curator, Tricolor Resonance, Mimi Resonance, Forgotten Archive, Inkbound Stacks, Mirror Gallery, and Warden Vault. Their subsequent `ContentLoadException: content file was not found` messages were downstream failures after the loader rejected the TMX.

## Frozen contracts
0686 Archive Rule transfer/adaptation remains unchanged. Region II fare remains 250g, route length 6-9 nodes, checkpoints 3/6, Hollow Curator 2200 HP, 40-card milestone, save schema 19, 0683 interactions/Final Cache, 0684 room mechanics, 0685 modifiers, and the rendering-depth contract remain frozen.

## Acceptance
CI must compile and validate every CSV layer. Final acceptance still requires a live SMAPI launch confirming the affected maps load without `TMXData.decode` / `UInt32.Parse` errors.

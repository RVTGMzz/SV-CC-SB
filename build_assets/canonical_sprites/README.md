# Canonical visual guard

`manifest.json` is the source of truth for approved decoded RGBA hashes and dimensions.

The guard is **fail-closed and non-destructive**. It never rewrites artwork. This is intentional, especially for `mimi_walk.png`, which is user-locked and may only change after an explicit user request.

The `data/` directory contains legacy/diagnostic payload fragments from the bootstrap attempt and is not used by the current guard. The current guard verifies the actual tracked source PNGs against `manifest.json`.

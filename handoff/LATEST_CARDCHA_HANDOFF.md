# Latest Cardcha Handoff

Current branch: `cardcha-alpha28-0687-tmx-csv-runtime-load-fix`
Current build: `0.3.0-alpha.28.0.4.14.4.5.12.55`
Continue from: `handoff/ALPHA28_0687_TMX_CSV_RUNTIME_LOAD_FIX.md`
Design direction: `handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`

0687 is a runtime TMX compatibility hotfix over 0686. It canonicalizes CSV blocks so TMXTile receives only valid GID tokens while preserving the exact non-empty tile GID sequence and all gameplay/render contracts. In-game acceptance is pending.

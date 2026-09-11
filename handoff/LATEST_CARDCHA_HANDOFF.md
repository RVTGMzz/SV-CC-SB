# Latest Cardcha Handoff

Current development branch: `cardcha-alpha28-0694-region1-environment-prop-concept`

Current handoff: `handoff/ALPHA28_0694_REGION1_ENVIRONMENT_PROP_CONCEPT.md`

Current concept contract: `handoff/REGION1_ENVIRONMENT_PROP_CONCEPT_0694.json`

Status: **CONCEPT ONLY - awaiting Ron approval before production integration.**

Production / TEST baseline remains:
- branch: `cardcha-alpha28-0693-airship-interior-density-rebuild`
- baseline head: `c438d8664538e0b64212d2566f47188294effe93`
- current build: `0.3.0-alpha.28.0.4.14.4.5.12.60`
- materialized source head: `e235e33826dddbf158837d3f5cdbc6af505136b6`
- successful CI run: `34631829934`
- artifact ID: `10275959178`
- verified inner TEST ZIP SHA256: `7c7e572bec7ba682a91af519482922e6ec9cb80677ae1d731002fd83d2d0c649`

Airship 0693 in-game visual acceptance is still **PENDING**. Do not claim the Airship visual gap is accepted until Ron tests the actual `.60` package.

0694 does not change runtime code, gameplay, TMX production maps, collision, encounters, rewards, Airship art, or production Region I assets. It audits the legacy Region I physical `RenderedWorld` decor debt and defines the Stardew-faithful map-native replacement direction for the six Hunt Run rooms.

Next step after Ron approves 0694: create the production integration pass that builds the real Region I prop tilesheet, authors six room-specific TMX compositions, freezes gameplay anchors, and removes/suppresses `Region1StardewDecorRenderer` physical post-world decor after TMX coverage is complete.

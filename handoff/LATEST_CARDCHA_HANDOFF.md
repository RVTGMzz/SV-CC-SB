# Latest Cardcha Handoff

Current source-of-truth branch: `cardcha-alpha28-0695-region1-prop-integration`

Current build: `0.3.0-alpha.28.0.4.14.4.5.12.61`

Current materialized source head: `39e13a370281b29f77d94be497603a3243edda41`

Current handoff: `handoff/ALPHA28_0695_REGION1_ENVIRONMENT_PROP_PRODUCTION_INTEGRATION.md`

Parent concept: `cardcha-alpha28-0694-region1-environment-prop-concept` @ `5f8fdafa4dfd7db964728cbe6378da1c82b102ea`

Authoritative successful CI run: `34655852302`

Artifact ID: `10285408808`

Artifact digest: `sha256:065ed6936c5d06479eb2927a7c2b717d359a598447f3b9f6e5c35bc57221bbac`

Verified inner TEST ZIP SHA256: `fac7aaa1c9014aedfd0eba887a1b2bd46531fbb9f676ebd7896b15e321fce726`

Status: **CI / repository validation / compile / package PASS.** 0695 migrates the six Region I Hunt Run room environment props from the legacy physical `RenderedWorld` renderer into map-native TMX `BackDecor` / `Buildings` / selective `Front` layers while preserving collision topology and all locked gameplay anchors.

Region I 0695 in-game visual acceptance remains **PENDING** until Ron tests the actual `.61` package.

Airship 0693 in-game visual acceptance also remains **PENDING** unless Ron separately reports acceptance.

Continuation rule: if the six-room composition reads well in-game, lock 0695 and move forward. If a room has a specific density/depth/readability problem, use a targeted 0696 acceptance/polish pass; never restore permanent physical environment art through `Display.RenderedWorld`.

# Cardcha-Shardbound — Alpha.28 Airship implementation checkpoint

This file marks the start of implementation after the accepted `0.3.0-alpha.27.0.7.9.0` baseline.

Planned first vertical slice:

1. one-time mysterious airship flyby over the Farm before the first Cardboard Scrap / before MiMi is introduced;
2. persistent save flags for flyby + Airship unlock state;
3. Airship unlock at the Chapter 1 MiMi/Wizard handoff so vanilla-only players gain a Cardcha-owned monster-farming route early;
4. a real custom `Cardcha_AirshipDeck` GameLocation loaded from a Cardcha-owned TMX asset;
5. safe TEST access while the physical boarding point and Region I are still being built;
6. no Stardew Druid source or art copied into Cardcha. Stardew Druid is architecture/mood reference only.

Frozen regressions from alpha.27 remain mandatory: Binder controller selection/action contract, synthetic-click suppression, accepted MiMi art hashes, stationary-vs-portable machine placement, and no random ChaCha emotes during the `???` phase.

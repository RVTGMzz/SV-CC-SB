# Cardcha: Shardbound v0.1.17-alpha.11.32 — Native World Actors

This build replaces the old post-world body rendering for MiMi and ChaCha with native Stardew world actors. Their bodies now live inside `GameLocation.characters`, so Stardew's own front-to-back world renderer decides whether they appear in front of or behind the player, NPCs, trees, bushes, and world props.

## Key changes
- MiMi now renders directly from the official `mimi_walk.png` 32x48 master through her native NPC actor. No derived world sprite is used for normal walking/merchant/mystery presentation.
- MiMi's broom arrival/departure swaps the same native actor to `mimi_broom.png`, so the flight also participates in Stardew's world depth sorting.
- ChaCha is now a runtime NPC-style world actor using the official `chacha_follow.png`; follower motion still uses the fairy-glide spring from alpha.11.31.
- Story MiMi/ChaCha scenes also use native world actors instead of `RenderedWorld` body overlays.
- Stardew's native `Character.DrawShadow` now supplies both MiMi and ChaCha shadows from the same ground anchor used for sorting.
- `RenderedWorld` is retained only for ChaCha's tiny cosmetic sparkle trail; no character body is drawn there.
- ChaCha is removed before save serialization and recreated automatically at runtime, so the follower doesn't pollute save files.

## Official asset rule
The user-provided `src/Cardcha/assets/` remains the source of truth. This build does not regenerate or overwrite those files.

- MiMi auto-spawn is disabled in `Data/Characters`; the world-actor service owns creation so old saves/mod load order cannot produce duplicate MiMis.

- ChaCha's fairy flutter is now a native `drawOffset`; his ground position controls depth/collision while the shadow stays on that ground anchor.
- Wizard story lines keep the Wizard portrait; MiMi's runtime portrait override is applied only to MiMi.

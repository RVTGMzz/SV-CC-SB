# Alpha.28 0678 — Boss II-IV Visual Completion + Actor Depth

Branch: `cardcha-alpha28-0678-boss234-visual-completion`
Build: `0.3.0-alpha.28.0.4.14.4.5.12.46`

## Scope
- Boss II/III/IV physical bodies now render from the declared `Monster.draw(SpriteBatch)` slot through `MilestoneBossActorDrawPatch`.
- `MilestoneBossService.OnRenderedWorld` owns VFX only: aura, telegraphs, retreat cue.
- Fixed 0.99/0.985 physical post-world depths removed from milestone boss rendering.
- Hollow Curator expanded to 4 states; Ignis/Vita/Aether to 2 frames each; Unified to 4 states; MiMi Resonance Master to 4 states.
- Boss scale reduced to 1.80-1.95x to avoid blown-up pixel art.
- Three Cardcha-owned transparent 16px ground tile sheets are embedded into each arena TMX as `CardchaArenaGround`, under actors.
- `mimi_walk.png` is untouched.
- Gameplay values, HP, attack timings, rewards, 40/60/80 route gates, Boss Form pacing and save schema remain unchanged.

## In-game acceptance
Run `cardcha_test_boss2`, `cardcha_test_boss3`, `cardcha_test_boss4`. Screenshot each arena with Farmer standing both above and below the boss. Physical boss art must sort naturally and never swallow the Farmer. Boss III should show three distinct guardians and then Unified; Boss IV phase changes should visibly progress.

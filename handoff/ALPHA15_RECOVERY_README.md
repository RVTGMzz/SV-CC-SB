# Cardcha v0.3.0-alpha.15 recovery handoff

Prepared from the alpha.14/alpha.13 playable-candidate line after user testing exposed six remaining issues.

## Candidate identity
- Version: `0.3.0-alpha.15`
- Build label: `Cardcha! v0.3.0-alpha.15 GACHA + CONTROLLER + MINIMAP`
- Full Windows Builder SHA-256: `926000a3928ba8ea8f7896c5d019944e209e6db29d9237678ee8ad44170a851d`
- Source Snapshot SHA-256: `6aedd66070a0bce09f61df4584124f5500004ec69750a59cda1d6c6e33860ecb`
- MiMi minimap face design SHA-256: `8a63163941a6ef35d2a83b2e9bb7802927b6d5f21b4d1ab9134e196fdc153b4b`

## User-approved fixes
- Fresh runtime entropy is mixed into each Gacha pull, so reloading the same pre-pull save is not forced to reproduce the identical result.
- Controller selection persists after A across unlimited cursor movement. Focus movement never changes the selected card; A on another card does.
- Explicit action-button neighbor graph keeps Favorite/Equip/Upgrade navigation stable.
- Footer page buttons use ASCII `<` and `>` because Unicode triangles fell back to star glyphs in Stardew's font.
- Normal/Shiny Scrap count text is approximately doubled in visual size.
- Scheduled MiMi arrival keeps the ground actor hidden until the broom actor is already at its off-screen start point, removing the one-frame pre-flight flash.
- NPC Map Locations 3.5.x compatibility: patch `Mods/Bouhm.NPCMapLocations/NPCs` with MiMi `MarkerCropOffset=1`; correct `MugShotSourceRect` for Vanilla marker mode; preserve `assets/mimi_minimap_icon.png` as the approved front-face/red-bow/purple-hair marker design reference.

## Important inherited state
- Alpha.14 larger MiMi/???/ChaCha shadows and Binder X button.
- Alpha.13 official broom art, +10% broom runtime compensation, MiMi revealed identity, +/- shop quantity chooser, full off-screen flights, portable purchase feedback.
- Alpha.13 compile hotfix in CardchaMachineMenu must remain.
- 20-card future progression remains: ChaCha info -> quest -> Boss -> Portable reward. 40-card future progression remains machine fusion into ChaCha/Binder.

## Validation
Static validation passed for JSON/version consistency, fresh Gacha entropy marker, persistent controller lock, action neighbors, ASCII arrows, larger Scrap counts, pre-flight hold logic, NPC Map Locations customization, corrected MugShotSourceRect, and minimap design asset. Windows compile/game test is still required.
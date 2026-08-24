# Cardcha! v0.1.17-alpha.11.6 — Animation Asset Roles

This build cleans up the animation source layout so the runtime-facing files are clearer:

- `assets/mimi_walk.png` — MiMi walk + idle sheet for NPC/town use.
- `assets/mimi_broom.png` — MiMi broom/flying sheet for cutscenes.
- `assets/chacha_follow.png` — ChaCha follow/hover sheet.
- `assets/chacha_machine.png` — ChaCha machine-interaction sheet used by pull animation.
- `assets/machine_anim.png` — machine ritual/pull animation strip.
- `assets/machine_ui.png` — machine menu strip.

Legacy duplicate source files `mimi_sheet.png` and `chacha_sheet.png` were removed from the builder package to reduce confusion.

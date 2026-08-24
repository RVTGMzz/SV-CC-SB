# Cardcha! v0.1.17-alpha.11.6 — Actual Runtime Animation + Compile Guard

This build focuses on the first full animation pass for **MiMi**, **ChaCha**, and the **Cardcha Machine**.

## Highlights
- Added organized animation asset sheets:
  - `assets/mimi_walk.png`
  - `assets/mimi_broom.png`
  - `assets/chacha_follow.png`
  - `assets/chacha_machine.png`
  - `assets/machine_anim.png`
- MiMi story scenes now use separate broom / meetup animation sheets.
- Loaned ChaCha follower now uses a directional animation sheet and simple facing logic.
- Pull animation now uses the dedicated ChaCha + machine animation sheets.
- Cleaned the builder root by removing extra handoff/test text files.

## Notes
- This is an animation-focused milestone.
- Story progression from alpha.5 is preserved.
- The builder still contains `BUILD_TEST.md`, `LOCAL_BUILD.md`, and the normal build/install scripts.


## Alpha.11.11 art cleanup
- `mimi_walk.png` is now treated as the visual master for MiMi runtime style; `mimi_npc.png` is regenerated from it to keep the native NPC look closer to the prettier walk sheet.
- `mimi_portraits.png` is the master portrait strip. `mimi_npc_portraits.png` is now a derived 64x64 runtime strip so dialogue portraits keep the same art style.
- ChaCha beside MiMi and follower visuals reduced to 90% of the previous size.


## Alpha.11.13 mystery no greetings + portrait force
- Rebuilt the six MiMi expressions from a clean master set: neutral, happy, worried, surprised, wink/cute, determined.
- Cleaned the dark mouth artifacts and inconsistent lip shading.
- `mimi_portraits.png` remains the art master.
- `mimi_npc_portraits.png` is regenerated from the same six expressions for native Stardew dialogue compatibility.
- No gameplay timing or installer behavior changed from alpha.11.12.


## Alpha.11.14
- Mystery-phase Town chatter temporarily disabled.
- ChaCha hides during visible speech bubbles/dialogue.
- Portrait display path now forcibly assigns MiMi's portrait texture before opening dialogue.


## Alpha.11.16
- MiMi world body uses `mimi_walk.png` directly for mystery/merchant presentation; the native NPC body is hidden.
- Portrait dialogue opens through a real `DialogueBox` with MiMi as the speaker.


## Alpha.11.18
- Fixed the source `mimi_walk.png` body/leg seam.
- Collision-aware mystery wandering: no walking through trees/bushes and more distance from other NPCs.
- ChaCha picks a clear companion position instead of hovering inside scenery.
- Added shadows under MiMi and ChaCha.


## Alpha.11.21
- Minor ChaCha back-view sprite cleanup to remove the odd protruding front-looking artifact.


## Alpha.11.22
- Rear-view ChaCha is now orb-free: no gold ring/halo and no stray side fragments around the ears.


## Alpha.11.23
- Corrected ChaCha rear view: back of cape visible between wings, no orb/halo, clean ear/cheek silhouette, tiny gold sparkles retained near the feet.


## Alpha.11.24
- Rear-facing ChaCha now follows the intended anatomy/layer order: body -> wings behind -> cape in front.


## Alpha.11.25
- ChaCha back view now shows full folded wings behind the cloak/cape.
- MiMi side-walk frames received a small leg cleanup pass on the marked problematic frames.


## Alpha.11.26
- ChaCha back view updated so the wings feel attached to ChaCha's upper back instead of floating awkwardly beside the cloak.


## Alpha.11.28
- Fixes CharacterData field assignment, mystery NPC greetings, MiMi/player overlap, and keeps the literal portrait dialogue path.
- The official assets supplied by the project owner remain the source of truth and are not regenerated.


## Alpha.11.29
- MiMi portrait dialogue reads from `assets/mimi_portraits.png` directly as the master source (runtime conversion is memory-only).
- MiMi and ChaCha custom-render shadows now use Stardew's native shadow opacity/ground placement so they are clearly visible.


## Alpha.11.30 compile hotfix
`mimi_npc_portraits.png` remains only an engine-compatible fallback asset. Dialogue portraits still come from the official `mimi_portraits.png` master and are resized in memory at runtime. This hotfix restores the missing fallback path constant that caused CS0103 in alpha.11.29.


## Alpha.11.31 — World Integration + Fairy Hover
- World-integration pass for MiMi and ChaCha: stronger obstacle/actor spacing, ground-anchored shadows, and collision-aware movement.
- ChaCha stays visible during dialogue and now glides with a fairy-like drifting flight path instead of bobbing in one fixed spot.
- No official asset file is regenerated or overwritten by this pass.

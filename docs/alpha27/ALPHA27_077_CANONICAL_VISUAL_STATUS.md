# Alpha.27.0.7.7 canonical visual status

Current accepted gameplay candidate: `0.3.0-alpha.27.0.7.7` on branch `cardcha-alpha27-mimi-real-npc`.

The approved visual hashes used by the acceptance package are recorded in `build_assets/canonical_sprites/manifest.json`.

Important policy:
- `mimi_walk.png` is user-locked. Do not modify or auto-rewrite it unless the user explicitly requests an asset change.
- `mimi_social_mugshot.png` is a dedicated Social/Friend-list asset and is also fail-closed.
- `chacha_follow.png`, `chacha_machine.png`, `card_icons.png`, and `chacha_portrait.png` are approved visual assets. Unexpected pixel changes must fail CI rather than silently ship.
- The canonical guard is intentionally fail-closed and non-destructive. It verifies dimensions + decoded RGBA SHA256 and does not rewrite artwork.

Latest acceptance package fixes include WizardHouse stair relocation, sofa/TV spacing, large rug under the bed, removal of the skull/pirate poster, cleaner attic shell, isolated MiMi social mugshot, static ChaCha menu portrait, strict TMX validation, reveal close localization, and removal of redundant Binder status text.

Normal attic access remains MiMi meetup + 2 hearts. `cardcha_test_attic` remains the runtime-only test bypass without altering progression.

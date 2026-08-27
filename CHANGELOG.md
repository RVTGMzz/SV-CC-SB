# Cardcha! — Changelog / Handoff Lineage

This file is a concise migration-oriented changelog. It focuses on changes that matter when inheriting the project.

## v0.3.0-alpha.23 — Multi-Controller + Gacha Polish
- Introduced centralized `ControllerProfileService`.
- Semantic physical controls: South=Confirm, East=Favorite, West=Deselect, North=Exit.
- Added controller layout/mapping overrides for Xbox/Nintendo/PlayStation/Generic and Steam Input ambiguity.
- Binder double-click/double-confirm quick toggle restored for equip/unequip.
- Gacha result cards rounded and simplified to localized Name + large Icon + NEW/DUPLICATE.
- Added reveal sparkles.
- Removed the small inner ritual aura; resonance targets the full large gold-bordered panel.
- Audited EN/VI card names/descriptions and localized star-rule rows; clarified damage-variance terminology.
- Static validation: 53/53 PASS; Windows compile/in-game verification still pending at handoff time.

## v0.3.0-alpha.22 — Nintendo Controller Fix
- Identified Nintendo-printed labels vs XNA/XInput enum-position mismatch.
- Temporary Nintendo-position remap used as a bridge before alpha.23 generalized the architecture.

## v0.3.0-alpha.21 — Gacha Controller + Full Flash
- Gacha face-button skip logic narrowed so one intended control skips instead of all face buttons.
- Full outer-panel ritual pulse expanded.
- Input-family hint switching improved.

## v0.3.0-alpha.20 — Control Hints
- Added Binder hint bar below the book.
- Added keyboard shortcuts mirroring controller actions.
- Hint bar tracks recent input family.

## v0.3.0-alpha.19 — Controller Remap
- Reworked Binder controller action dispatch.
- Confirm routes to focused Equip/Unequip/Upgrade actions.
- Exit intended to close Binder + parent UI back to gameplay.

## v0.3.0-alpha.18 — Binder Lock + Typography
- Replaced fragile selection flag logic with separate free-preview and locked-card action context.
- Only Deselect releases locked action context.
- Added visible locked-card border.
- Replaced unreliable font page arrows with pixel-drawn arrows.
- Enlarged discovery/filter/not-owned text.

## v0.3.0-alpha.17 — Mythic + Minimap + Browse
- Cleaned Binder heading.
- Player-facing Boss slot wording changed to Mythic Skill / Kỹ năng Thần Thoại.
- Fixed MiMi/??? minimap marker crop strategy for larger sprite frames.
- Hardened locked-card action targeting.

## v0.3.0-alpha.16 — Binder Deselect
- Added explicit Deselect behavior.
- Free browse previews focused cards until a card is explicitly locked.

## v0.3.0-alpha.15 — Gacha/Controller/Minimap fixes
- Addressed deterministic reload-repeat gacha behavior with runtime entropy while preserving progression counters.
- Reverted unsupported Unicode arrows.
- Improved MiMi broom visibility transition.
- Researched NPC Map Locations integration.

## v0.3.0-alpha.14
- Enlarged MiMi/ChaCha shadows.
- Enlarged Scrap resource presentation.
- Added Binder top-left X.
- Attempted controller/minimap improvements later superseded.

## v0.3.0-alpha.13
- MiMi identity remains MiMi after reveal/handoff.
- Portable purchase remains interactive with insufficient-money feedback.
- Added quantity selector for Scrap trading.
- Broom arrivals/departures originate/finish beyond viewport.
- Adopted user-supplied official `mimi_broom.png`.
- Added builder cleanup/version guard.
- Fixed constructor compile regression caused by missing `ResourceService` argument.

## v0.3.0-alpha.12
- Single confirm selects card; double activation quick-toggles equip.
- Added normal/shiny Scrap resource rail.
- Refined top-slot grouping and book icon handling.

## v0.3.0-alpha.11
- Binder action/input expansion.
- Full-cell/full-panel gacha flash groundwork.
- Boss/ChaCha slot visual separation.
- Portable milestone compatibility bridge standardized around 20 unique cards pending story quest implementation.

## v0.3.0-alpha.10 — Important GitHub baseline
- Full-source baseline previously committed to `binder-v0.3-alpha1`.
- 80-card Binder/base collection present.
- Favorite persistence, rarity filtering, locked grayscale atlas, equipped overlay, Boss/Secret placeholders, Portable Machine.

## Earlier v0.1.17-alpha.11.xx lineage
Older MiMi story/follower/shop/HUD work exists in repository history and `CARDCHA_PROJECT_STATE.json`.
Treat old numeric values marked HISTORICAL/SUPERSEDED as history, not current design.

## Design milestones agreed after alpha.23
Not yet fully implemented:
- 20/40/60/80 boss arc;
- MiMi as intended 80-card final boss;
- airship boss-travel hub;
- MiMi full friendship NPC + Community Center role + relationship-aware dialogue;
- ChaCha expressive non-verbal companion and support passive progression.

See `docs/STORY_GAMEPLAY_BIBLE.md` for LOCKED vs TBD status.

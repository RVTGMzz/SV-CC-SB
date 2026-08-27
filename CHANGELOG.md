# Cardcha! — Changelog / Handoff Lineage

This file is a concise migration-oriented changelog. It focuses on changes that matter when inheriting the project.

## v0.3.0-alpha.25 — Gacha Interior Flash
- Current canonical working baseline.
- Ritual resonance now flashes as a rarity/white filter across the panel interior instead of pulsing the frame itself.
- Filter is inset from the panel border so the outer gold frame remains visually stable.
- Applies to both Stationary and Portable ritual paths through shared `DrawFlash()` logic.
- Retains the alpha.24 GMCM/Cinderbox compatibility fix and all alpha.23 controller/Binder/localization work.
- Source tree synchronized and verified byte-for-byte against the alpha.25 source snapshot.
- User accepted alpha.25 as the current in-game working baseline; this is not a claim of exhaustive release QA.

## v0.3.0-alpha.24 — Cinderbox GMCM Fix
- Changed `IGenericModConfigMenuApi` from internal/non-public to `public`.
- Fixes SMAPI/Cinderbox API mapping error: `must be a public interface`.
- No intentional controller/button, Binder, gameplay, balance, story, or asset changes.

## v0.3.0-alpha.23 — Multi-Controller + Gacha Polish
- Introduced centralized `ControllerProfileService`.
- Semantic physical controls: South=Confirm, East=Favorite, West=Deselect, North=Exit.
- Added controller layout/mapping overrides for Xbox/Nintendo/PlayStation/Generic and Steam Input ambiguity.
- Binder double-click/double-confirm quick toggle restored for equip/unequip.
- Gacha result cards rounded and simplified to localized Name + large Icon + NEW/DUPLICATE.
- Added reveal sparkles.
- Removed the small inner ritual aura and expanded full-panel resonance behavior, later refined in alpha.25 so the border remains stable.
- Audited EN/VI card names/descriptions and localized star-rule rows; clarified damage-variance terminology.
- Alpha.23 source was the first fully synchronized 69-file v0.3 source baseline on the active branch.

## v0.3.0-alpha.22 — Nintendo Controller Fix
- Identified Nintendo-printed labels vs XNA/XInput enum-position mismatch.
- Temporary Nintendo-position remap used as a bridge before alpha.23 generalized the architecture.

## v0.3.0-alpha.21 — Gacha Controller + Full Flash
- Narrowed Gacha face-button skip behavior so only the intended semantic control skips.
- Expanded ritual pulse groundwork.

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
- Earlier full-source baseline on `binder-v0.3-alpha1`.
- 80-card Binder/base collection present.

## Earlier v0.1.17-alpha.11.xx lineage
Older MiMi story/follower/shop/HUD work exists in repository history and `CARDCHA_PROJECT_STATE.json`.
Treat old numeric values marked HISTORICAL/SUPERSEDED as history, not current design.

## Design milestones not yet fully implemented
- 20/40/60/80 boss arc;
- MiMi as intended 80-card final boss;
- airship boss-travel hub;
- MiMi full friendship NPC + Community Center role + relationship-aware dialogue;
- ChaCha expressive non-verbal companion and support passive progression.

See `docs/STORY_GAMEPLAY_BIBLE.md` for LOCKED vs TBD status.

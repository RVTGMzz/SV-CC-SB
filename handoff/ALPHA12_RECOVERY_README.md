# Cardcha v0.3.0-alpha.12 recovery handoff

Prepared 2026-08-26 from the confirmed alpha.11 candidate source.

## Candidate

- Version: `0.3.0-alpha.12`
- Build label: `Cardcha! v0.3.0-alpha.12 BINDER SELECT + RESOURCE RAIL`
- Local candidate commit: `32e82a6221d058554adb54889a1f668ce58c2cce`
- Previous local alpha.11 commit: `928e6d44b5ae8b46a2f618c985fb2c95d3ce21fe`
- Confirmed alpha.10 source baseline: `b58f5e929c1433c5a4cbf4726d2bfd64e6548251`

## Alpha.12 scope

- Single click / single controller confirm selects the collection card only.
- Explicit selection is locked; RIGHT enters the detail action group for that same selected card.
- Double mouse/controller confirm on the same card still quick-equips/unequips, with a 100–650ms valid interval so one physical controller press is not interpreted twice.
- Restores Normal + Shiny Cardboard Scrap counters on the left rail below rarity bookmarks and above Favorites.
- Hover/controller focus on either resource counter shows localized name, count, and description.
- Top row is grouped as five normal slots + Boss, then a larger gap, then the pink ChaCha slot. All circles remain equal size.
- Boss uses Mythic border; ChaCha uses pink border; no BOSS/SECRET text inside the circles.
- Footer keeps `Trang x/y` in the same position; compact discovery count remains to its left.
- Binder GameMenu icon prefers `assets/binder_tab_icon.png` with `binder_tab_icon.jpg` fallback, preserving the book artwork.
- Retains alpha.11 full-panel/full-card gacha flash and 20-card portable milestone text sync.

## Progression design preserved (not fully implemented here)

- 20 unique cards -> ChaCha info begins unlocking -> quest -> Boss encounter -> Portable Machine reward.
- 40 unique cards -> quest/encounter -> ChaCha absorbs/fuses stationary + portable machines -> direct Cardcha access from Binder.

## Validation

Static validation passed for JSON/i18n, 80-card registry, version consistency, selection-lock/resource-rail/icon markers, and C# lexical structure. A real Windows compile with Stardew Valley + SMAPI references is still required.

Conversation artifacts:
- `Cardcha_v0.3.0-alpha.12_BinderSelectionResources_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.12_SOURCE_SNAPSHOT.zip`

The full source snapshot is the authoritative alpha.12 candidate if remote tracked source has not yet been promoted atomically.

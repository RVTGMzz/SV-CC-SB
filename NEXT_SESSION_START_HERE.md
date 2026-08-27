# NEXT SESSION — Cardcha v0.3.0-alpha.23 Multi-Controller + Gacha Polish

## Current candidate
- Version: `0.3.0-alpha.23`
- Build label: `Cardcha! v0.3.0-alpha.23 MULTI-CONTROLLER + GACHA POLISH`
- Baseline: alpha.22 Nintendo-specific controller fix.

## Controller architecture
- Cardcha menus now use `ControllerProfileService`; raw A/B/X/Y checks are not duplicated through Binder/Machine/Pull/Reveal/MiMi Shop.
- Semantic physical actions are South=Confirm, East=Favorite, West=Deselect, North=Exit.
- Controller Layout options: Auto, Xbox, Nintendo, PlayStation, Generic.
- Runtime Mapping options: Auto, Standard (XInput positions), NintendoNative (printed Nintendo labels).
- Auto falls back to Xbox/Standard when Steam Input or the runtime hides controller identity.
- Optional GMCM options expose both settings; config.json can also be edited manually.
- `cardcha_controller_status` prints the resolved profile and labels.

## Binder fixes
- Quick double activation window is 650ms with no artificial minimum delay.
- Double click / double Confirm on an owned card toggles equip; if already equipped it unequips.
- Locked-card selection semantics remain intact.

## Gacha UI
- Reveal/result cards use rounded corners.
- Result cards no longer print rarity text. They show localized Name + a much larger Icon + NEW/DUPLICATE only.
- Reveal phase and result aura add sparkle bursts.
- Ritual-local rectangular glow/aura was removed; the broad resonance flash uses the full rounded large panel and repaints the outer gold frame.

## EN / VI localization
- All 80 card names and descriptions are present in both `default.json` and `vi.json`.
- All 304 per-star rule rows are localized in both languages and are preferred by the Binder over legacy `cards.json` StarRules.
- `steady_grip` now explains variance clearly: random damage fluctuation / độ dao động ngẫu nhiên của sát thương.
- Mixed English fragments in the audited Vietnamese card rules (e.g. Boss Energy, Cardboard/Shiny Scrap) were normalized to Vietnamese player-facing terminology.

## Story / gameplay design bible — READ THIS BEFORE NEW STORY WORK
The newly added `docs/STORY_GAMEPLAY_BIBLE.md` is the source of truth for the design decisions agreed after alpha.23.

It records:
- MiMi becoming a full giftable/friendship NPC;
- MiMi's 17:30 favorite-TV/BL-shipping secret and relationship-aware reactions to male dating/marriage;
- MiMi's later Community Center stall and one-missing-seasonal-requirement contribution per season;
- 20/40/60/80 boss milestone structure and MiMi as the intended 80-card final boss;
- Rune Factory-inspired airship travel to dedicated boss mini-maps;
- ChaCha as a non-verbal expressive companion with Boss/Mythic transformations;
- ChaCha support passive proc rates, heal/energy scaling, and the 9-favorite-food MiMi quest required to activate each 10-card tier;
- an explicit TBD section so unresolved ideas are not accidentally treated as canon.

For story/progression implementation, update `docs/STORY_GAMEPLAY_BIBLE.md` when a TBD becomes locked instead of relying on chat history.

## Test first
1. Xbox/Standard: South(A)=Confirm, East(B)=Favorite, West(X)=Deselect, North(Y)=Exit.
2. Nintendo Native override: South(B)=Confirm, East(A)=Favorite, West(Y)=Deselect, North(X)=Exit.
3. Double-click an equipped card with mouse: it must unequip. Repeat using double Confirm.
4. Pull 1 and pull 10: result cards are rounded; icon is large; no rarity line; only Name + MỚI/TRÙNG.
5. Watch a reveal: sparkles appear around the card.
6. During ritual resonance, there is no small inner rectangular aura; the whole large gold-bordered panel pulses.
7. Check Vietnamese/English card details, especially Tay Vững / Steady Grip.

## Artifacts
- `Cardcha_v0.3.0-alpha.23_MultiControllerGachaPolish_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.23_SOURCE_SNAPSHOT.zip`

Targeted static validation: **53/53 PASS**. The container has no `dotnet` executable and no Stardew/SMAPI assemblies, so real Windows compile is still required through `BUILD_ALPHA23_TEST.bat`.
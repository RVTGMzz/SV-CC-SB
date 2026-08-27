# NEXT SESSION — Cardcha v0.3.0-alpha.23 Multi-Controller + Gacha Polish

## READ FIRST
Before editing code, read:
1. `PROJECT_HANDOFF.md`
2. `KNOWN_ISSUES.md`
3. `BUILD.md`
4. `docs/STORY_GAMEPLAY_BIBLE.md`

### Critical source-sync warning
The branch documentation is at alpha.23, but the checked-in GitHub `src/Cardcha/manifest.json` still reports alpha.10. Until source synchronization is completed, the packaged `Cardcha_v0.3.0-alpha.23_SOURCE_SNAPSHOT.zip` is the latest source candidate. Do not treat the older GitHub `src/` tree as alpha.23 by assumption.

## Current candidate
- Version: `0.3.0-alpha.23`
- Build label: `Cardcha! v0.3.0-alpha.23 MULTI-CONTROLLER + GACHA POLISH`
- Baseline: alpha.22 Nintendo-specific controller fix, generalized in alpha.23.

## Controller architecture
- Cardcha menus use `ControllerProfileService`; raw A/B/X/Y behavior should not be duplicated through Binder/Machine/Pull/Reveal/MiMi Shop.
- Semantic physical actions are South=Confirm, East=Favorite, West=Deselect, North=Exit.
- Controller Layout options: Auto, Xbox, Nintendo, PlayStation, Generic.
- Runtime Mapping options: Auto, Standard (XInput positions), NintendoNative (printed Nintendo labels).
- Auto falls back to Xbox/Standard when Steam Input or the runtime hides controller identity.
- Optional GMCM/config overrides exist.
- `cardcha_controller_status` reports the resolved profile/labels.

## Binder fixes
- Quick double activation window is 650ms with no artificial minimum delay.
- Double click / double Confirm on an owned card toggles equip; if already equipped it unequips.
- Locked-card selection semantics remain intact.

## Gacha UI
- Reveal/result cards use rounded corners.
- Result cards no longer print rarity text.
- Result cards show localized Name + a much larger Icon + NEW/DUPLICATE only.
- Reveal phase and result aura add sparkle bursts.
- Ritual-local rectangular glow/aura was removed; resonance flash uses the full rounded large panel and repaints the outer gold frame.

## EN / VI localization
- All 80 card names and descriptions are present in both `default.json` and `vi.json` in the alpha.23 source snapshot.
- All 304 per-star rule rows are localized in both languages and preferred by the Binder over legacy `cards.json` StarRules.
- damage variance wording is clarified as random damage fluctuation / `độ dao động ngẫu nhiên của sát thương`.
- mixed English fragments in audited Vietnamese card rules were normalized.

## Story / gameplay design bible
`docs/STORY_GAMEPLAY_BIBLE.md` is the source of truth for agreed future story/progression.
It records MiMi full-NPC direction, 17:30 TV/BL-shipping secret, relationship-aware reactions, Community Center role, 20/40/60/80 boss arc, MiMi as intended final boss, airship travel, ChaCha expressions/forms/passive progression, and a separate TBD section.

## Test first
1. Run `BUILD_ALPHA23_TEST.bat` on Windows and confirm version guard passes.
2. Xbox/Standard: South(A)=Confirm, East(B)=Favorite, West(X)=Deselect, North(Y)=Exit.
3. Nintendo override: verify physical South/East/West/North actions match Confirm/Favorite/Deselect/Exit without a second exit button.
4. Double-click an equipped card with mouse: it must unequip. Repeat using double Confirm.
5. Pull 1 and pull 10: result cards are rounded; icon is large; no rarity line; only Name + MỚI/TRÙNG.
6. Watch a reveal: sparkles appear around the card.
7. During ritual resonance, there is no small inner rectangular aura; the whole large gold-bordered panel pulses.
8. Check Vietnamese/English card details, especially Tay Vững / Steady Grip.

## Artifacts
- `Cardcha_v0.3.0-alpha.23_MultiControllerGachaPolish_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.23_SOURCE_SNAPSHOT.zip`

## Validation status
Targeted static validation: **53/53 PASS**.
Real Windows compile with Stardew/SMAPI references is still required.

## Next repository hygiene task
After alpha.23 is compile/test-confirmed, synchronize the alpha.23 source snapshot into GitHub and record the exact last-known-good commit in `PROJECT_HANDOFF.md`.

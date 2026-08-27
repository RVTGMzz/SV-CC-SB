# NEXT SESSION — Cardcha v0.3.0-alpha.25 Gacha Interior Flash

## READ FIRST
Before editing code, read:
1. `PROJECT_HANDOFF.md`
2. `KNOWN_ISSUES.md`
3. `BUILD.md`
4. `docs/STORY_GAMEPLAY_BIBLE.md`

## Source status
The alpha.25 source is synchronized and verified on GitHub.

Canonical repository baseline:
- default branch: `main`
- alpha.25 source anchor commit: `a083e0a0cb1eb94852964a6f732a73fd7f506b04`
- promotion merge to `main`: `ef7b34bbd9aebdd53c2aae3c6ead60606a1c8d33`
- exact `src/Cardcha` tree: `89cff25d67700762ed94399a5905bdf1a52e736f`

The tree above matches all 69 files in `Cardcha_v0.3.0-alpha.25_SOURCE_SNAPSHOT.zip` byte-for-byte. Use checked-in GitHub `src/Cardcha` on `main` as the baseline source of truth. The `binder-v0.3-alpha1` branch is the v0.3 development branch and is kept reconciled with this baseline before new work begins.

## Current candidate
- Version: `0.3.0-alpha.25`
- Build label: `Cardcha! v0.3.0-alpha.25 GACHA INTERIOR FLASH`
- User status: accepted as the current working baseline after in-game testing; not declared a final public stable release.

## alpha.24 compatibility fix retained
alpha.23 exposed `IGenericModConfigMenuApi` as non-public, which caused SMAPI/Cinderbox to reject API mapping. The interface is now `public` and this fix is retained in alpha.25.

Do not fold unrelated button/remapping work from other conversations into this fix unless a new regression is explicitly reported.

## Controller architecture
- Cardcha menus use `ControllerProfileService`; raw A/B/X/Y behavior should not be duplicated through Binder/Machine/Pull/Reveal/MiMi Shop.
- Semantic physical actions are South=Confirm, East=Favorite, West=Deselect, North=Exit.
- Controller Layout options: Auto, Xbox, Nintendo, PlayStation, Generic.
- Runtime Mapping options: Auto, Standard, NintendoNative.
- Auto may fall back to Xbox/Standard when Steam Input or a virtual runtime hides controller identity.
- Optional GMCM/config overrides exist.
- `cardcha_controller_status` reports the resolved profile/labels.

## Binder protected behavior
- quick double activation window is 650ms with no artificial minimum delay;
- double click / double Confirm on an owned card toggles equip and can unequip an already equipped card;
- free focus movement previews cards without replacing the locked-card action context;
- only explicit Deselect releases the locked card.

## Gacha UI — alpha.25 contract
- Reveal/result cards use rounded corners.
- Result cards show localized Name + large Icon + NEW/DUPLICATE only; no rarity line.
- Reveal/result aura includes sparkle bursts.
- No old small rectangular aura around the machine.
- During ritual resonance, the rarity/white flash is a near-full-panel **interior filter**.
- The filter is inset 8px so it does not overdraw the frame.
- The outer gold frame/border must remain visually stable instead of pulsing with the filter.
- Stationary and Portable rituals share this `DrawFlash()` behavior.

## EN / VI localization
- All 80 card names and descriptions are present in `default.json` and `vi.json`.
- All 304 per-star rule rows are localized in both languages and preferred by the Binder over legacy `cards.json` StarRules.
- damage variance wording is clarified as random damage fluctuation / `độ dao động ngẫu nhiên của sát thương`.
- avoid mixed-language fragments in Vietnamese UI unless they are proper names.

## Story / gameplay design bible
`docs/STORY_GAMEPLAY_BIBLE.md` is the source of truth for agreed future story/progression. It records MiMi full-NPC direction, relationship-aware behavior, Community Center role, the 20/40/60/80 boss arc, MiMi as intended final boss, airship travel, and ChaCha expression/form/passive progression, while keeping undecided items in TBD sections.

## Regression checks for the next change
1. Verify `manifest.json`, `Cardcha.csproj`, startup log, and `cardcha_version` all stay on the intended version.
2. Start with GMCM installed: there must be no Cardcha `non-public interface` API-mapping error.
3. Verify controller semantics have not changed accidentally.
4. Verify Binder free-preview / locked-card / double-unequip behavior.
5. Pull 1 and pull 10: rounded result cards, large icon, Name + MỚI/TRÙNG only.
6. During ritual resonance, the interior flashes while the outer gold border stays visually stable.
7. Check both Stationary and Portable rituals.
8. Spot-check EN/VI card details and MiMi/ChaCha story/shop/world actors.

## Artifacts
- `Cardcha_v0.3.0-alpha.25_GachaInteriorFlash_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.25_SOURCE_SNAPSHOT.zip`
- expected built test package: `_READY_TO_TEST/Cardcha_v0.3.0-alpha.25_GachaInteriorFlash_TEST.zip`

## Validation status
- GitHub source sync: **VERIFIED**
- exact source tree comparison against alpha.25 snapshot: **VERIFIED**
- alpha.25 static validation prepared before handoff: **41/41 PASS**
- user in-game visual acceptance: **CURRENT WORKING BASELINE**
- do not infer exhaustive platform/regression coverage from that acceptance.

## Next development rule
Start future work from `main` or from a fresh development branch created from the current `main`. If continuing `binder-v0.3-alpha1`, first make sure it is at least at the current `main` baseline. Do not resurrect the older alpha.23 branch state.

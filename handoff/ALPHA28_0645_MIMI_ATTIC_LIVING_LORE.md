# Alpha28.0.4.14.4.5.10 MiMi Attic Living Lore

Canonical branch:
`cardcha-alpha28-0645-mimi-attic-living-lore`

Verified materialization commit before handoff docs:
`25e7c1f38abc936b93fc916964c21e84a54f72d0`

Workflow run:
`33860738098` — SUCCESS

TEST package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.10_MiMiAtticLivingLore_TEST.zip`

TEST package SHA-256:
`117ba6168d2d0149e2257ed419604c16dd46031b43728c3855fc1cfdd174b8e3`

GitHub artifact:
- artifact id: `9932015649`
- artifact wrapper digest: `sha256:e525a687568f1ee73d7b9eef8c86d7c18dda3081bfdcff2104f0b18f1369709f`

## Scope completed

0645 turns MiMi Attic from a visually complete room into a room that reveals character and lore through interaction.

### Research desk
- first inspection gives general research/lived-in detail;
- repeat inspection changes text;
- 4+ hearts reveals a more personal layer;
- 8+ hearts reveals a deeper Farmer-related note;
- no quest/gameplay state is changed by inspecting.

### TV secret nook
- first/repeat inspections differ;
- 6+ hearts reveals the hidden 17:30 clue;
- at/after 17:30 the environmental line changes to imply recent private TV activity;
- the real 17:30 routine is still NOT enabled in this milestone.

### ChaCha corner
- base/repeat lines differ;
- when ChaCha is loaned to the Farmer the empty-cushion line reflects that state;
- at higher friendship a future Magic Dust prototype sketch can be discovered;
- no ChaCha upgrade menu/function was enabled here.

### Personal corner
- bed/bedside/dresser gained a lightweight environmental inspect anchor;
- late-night inspection changes tone;
- this is character atmosphere only.

### Interaction memory
- inspect repetition is remembered only for the current in-game day;
- memory resets on a new day;
- no new persistent SaveData fields were added;
- save schema remains 19.

### Localization
New layered inspect dialogue exists in both:
- `src/Cardcha/i18n/default.json`
- `src/Cardcha/i18n/vi.json`

## Visual state preserved from 0643
- stable location ID remains `Cardcha_MiMiAttic`;
- true Stardew `townInterior` TMX + vanilla furniture remain the visual owners;
- `mimi_attic_room_frame.png` remains removed;
- five core zones remain readable: landing, research, personal, TV secret, ChaCha/upgrade;
- furniture DecorVersion intentionally stays on the accepted `.5.9` visual layout so this interaction-only milestone does not restack/reseed room furniture.

## Progression/canon preserved
- attic access remains 2 hearts;
- secret TV eligibility hook remains 6 hearts and 17:30;
- actual secret-TV routine remains deferred;
- MiMi Attic is her private home, not a second shop;
- no new shop/menu/buff/economy behavior was added.

## Locked regression guards preserved
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate action distance 160px with `CollisionEdits=NONE`.
- locked Airship exterior `airship_visual.png` SHA-256 remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route, upgrade menu/costs and deferred gameplay bonuses remain unchanged.

## In-game acceptance checklist
1. Enter MiMi Attic with current test access/progression.
2. Inspect the research desk multiple times on the same day.
3. Test desk again at 4+ hearts and 8+ hearts if convenient.
4. Inspect TV before 17:30, then at/after 17:30 with 6+ hearts.
5. Inspect ChaCha corner while ChaCha is loaned to the Farmer.
6. Inspect the bed/personal corner, including after 22:00 if convenient.
7. Confirm dialogue does not double-trigger or swallow unrelated furniture actions.
8. Confirm room visuals remain identical to the accepted `.5.9` layout except for dialogue behavior.

## Recommended next milestone
After 0645 interaction acceptance, either:
- patch any concrete inspect hitbox/dialogue issues in a small follow-up, or
- move to the actual MiMi 17:30 / 6-heart private TV routine as a separate milestone.

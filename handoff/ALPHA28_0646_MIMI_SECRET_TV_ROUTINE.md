# ALPHA28_0646 MiMi Secret TV Routine

Canonical branch:
`cardcha-alpha28-0646-mimi-secret-tv-routine`

Build:
`0.3.0-alpha.28.0.4.14.4.5.11`

Materialization commit:
`a1b022c3f0cf1dce0fe1a87d155837fcba849732`

Workflow:
`.github/workflows/cardcha-alpha28-0646-mimi-secret-tv-routine.yml`

Verified CI run:
`33861687099` SUCCESS

GitHub Actions artifact:
- ID: `9932363536`
- name: `cardcha-alpha28-0646-mimi-secret-tv-routine`
- outer artifact digest: `sha256:0f1cff7f2a6d929bced631af6dacca169c4ad52bd642df4aa851d4ab6bcd72f5`

TEST package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.11_MiMiSecretTvRoutine_TEST.zip`

TEST SHA-256:
`aca4128a84df63d09259158c0307b53076ecb22fdaaac225b131948d884f8b11`

## 0646 behavior

- The previous 6-heart / 17:30 eligibility hook is now a real MiMi home routine.
- Requirement remains 6 hearts with MiMi.
- Active TV window is 17:30 through 21:50; at 22:00 the TV routine ends.
- During the routine, MiMi is physically repositioned into the TV nook and kept facing the television.
- The TV placement resolves against actual attic collision near preferred tile `(6,10)` so furniture changes do not strand her.
- At 22:00+, high-friendship MiMi winds down near the personal/bed corner.
- Below 6 hearts, pre-0646 generic home behavior is preserved.
- Routine-specific talk lines exist for early evening, late evening, and when ChaCha is currently loaned to the farmer.
- TV inspect text now distinguishes active routine, post-routine, and pre-unlock clues.
- Fixed the same-location placement bug: HomeService can now move MiMi between positions inside the attic instead of returning early just because she is already in the same location.

## MiMi Attic state retained

- Stable location: `Cardcha_MiMiAttic`.
- 2-heart attic access unchanged.
- True Stardew `townInterior` TMX + vanilla furniture retained.
- No room-sized `mimi_attic_room_frame.png` overlay.
- Five room zones retained: landing, research, personal/bed, TV secret, ChaCha/upgrade.
- 0645 layered inspect system remains active.
- No new SaveData fields and no schema bump for this routine.

## Regression locks

- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate uses 160px action distance and `CollisionEdits=NONE`.
- Locked Airship exterior `airship_visual.png` unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses unchanged.

## In-game test checklist

1. Ensure MiMi friendship is at least 6 hearts.
2. Enter `Cardcha_MiMiAttic` before 17:30 and confirm normal home placement.
3. Advance to 17:30 and confirm MiMi moves to the TV nook and faces north toward the TV.
4. Talk to MiMi near the TV between 17:30 and 22:00 and verify routine-specific dialogue.
5. Test once while ChaCha is loaned to the farmer and confirm the ChaCha-specific line.
6. Inspect the TV while the routine is active and verify the active-routine environmental text.
7. Advance to 22:00 and confirm MiMi leaves the TV nook for the personal corner; inspect the TV again for post-routine text.
8. Test below 6 hearts and confirm the routine does not activate.
9. Re-test attic exit/stairs to ensure the schedule placement never blocks the landing.

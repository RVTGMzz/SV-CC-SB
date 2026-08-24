# BUILD TEST — Cardcha v0.1.17-alpha.11.32

## 1. Build identity
1. Fully close Stardew Valley and SMAPI.
2. Run `BUILD_CARDCHA.bat`.
3. Build should finish with `0 Error(s)`. The known analyzer/compiler mismatch may remain a warning.
4. In SMAPI run `cardcha_version`.
5. Expected: `Cardcha! v0.1.17-alpha.11.32 NATIVE WORLD ACTORS ACTIVE`.

## 2. Native depth sorting — highest priority
Stand immediately above, below, and beside MiMi, then cross in front of/behind her. Repeat near a tree/bush and another NPC. Expected: MiMi is sorted by her feet exactly like a normal Stardew NPC; she must not always draw over the player.

With ChaCha loaned, walk around NPCs, trees, bushes, buildings, and the player. Expected: ChaCha's body is sorted by Stardew's world renderer instead of being pasted over everything.

## 3. Shadows
MiMi and ChaCha should both have Stardew-style ground shadows. The shadow should remain anchored to the world actor and follow the same ground position used for depth sorting.

## 4. Fairy follower
Run in several directions and circle obstacles. Expected: ChaCha softly glides toward its drifting target, slides around blocked areas, stays visible during dialogue, and keeps the light sparkle trail while moving.

## 5. MiMi phases
- Mystery test window: 10:00–15:00 Town.
- Arrival/departure: broom actor should fly in/out without becoming a post-world overlay.
- Merchant: 11:00–17:00, Farm normally / WizardHouse on rain.
- MiMi should not exchange vanilla greeting bubbles while mysterious.

## 6. Dialogue portrait
Talking to mystery MiMi should show display name `???` while using the runtime 64x64 portrait sheet generated in memory from official `mimi_portraits.png`.

## 7. Save safety
Save the game with ChaCha loaned, then reload. Expected: ChaCha is recreated at runtime and there is no duplicate ChaCha actor.

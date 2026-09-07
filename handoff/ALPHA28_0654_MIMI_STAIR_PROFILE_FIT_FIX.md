# Alpha28 0654 - MiMi stair + Gift Log profile fit fix

Branch: `cardcha-alpha28-0654-mimi-stair-profile-fit-fix`

Build target: `0.3.0-alpha.28.0.4.14.4.5.12.21`

## In-game evidence driving this patch
- WizardHouse ladder was almost correctly placed but needed one tile right, snug against the right wall without entering the wall.
- Returning from MiMi's attic must still land at the same stair route; no separate invisible exit relocation is introduced.
- MiMi remained oversized/clipped in ProfileMenu Gift Log while a vanilla NPC such as Martin fit normally inside the portrait background.

## Fix
- WizardHouse preferred stair anchor: `(15,15)` -> `(16,15)` only. Y, ladder height, route, attic landing logic, and solid Buildings-layer behavior stay unchanged.
- ProfileMenu now sets a caller-context flag when the currently selected character is MiMi. The AnimatedSprite draw correction therefore no longer relies on texture-name matching alone.
- MiMi's profile frame is fitted into a 64x112 maximum envelope with max scale 2x. Canonical 32x48 MiMi frames render 64x96 and are recentered against ProfileMenu's vanilla 4x positioning calculation.
- Added `cardcha_mimi_profile_status` diagnostics so real in-game tests can prove whether ProfileMenu guard and scaled draw hooks fire.

## Regression guard
- 0653 strict TMX runtime compatibility fix is retained.
- No attic layout/furniture, HOME/TV/LATE routine, friendship/story progression, Save schema 19, Cardcha progression, Airship, Boss I, cards, controller profile, or MiMi portrait-dialogue lifecycle is changed.

## Acceptance pending
- Stair must visually sit just left of the right wall, not overlap the wall and not float over the stove/log nook.
- Going up and returning down must use the same stair location.
- MiMi Gift Log sprite must fit comfortably inside the same portrait frame envelope as normal NPCs, with no clipping.

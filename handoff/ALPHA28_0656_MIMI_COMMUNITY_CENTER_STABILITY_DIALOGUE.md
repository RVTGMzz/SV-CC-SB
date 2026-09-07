# Alpha28 0656 - MiMi Community Center stability + dialogue

Branch: `cardcha-alpha28-0656-mimi-community-center-stability-dialogue`

Build target: `0.3.0-alpha.28.0.4.14.4.5.12.23`

## In-game evidence
- In the restored Community Center work route, MiMi visibly flickered between two vertically offset positions, reading as a laggy clone/afterimage.
- Her first Stardew social dialogue could still say that the farmer and MiMi were “officially acquainted now,” which contradicts the story because the Wizard meetup happened long before this route.

## Root cause / fix
### Community Center ghost flicker
`MimiHomeService` was resolving `FindClearTileNear(center, ...)` every update tick. Once MiMi occupied the chosen tile, occupancy checks could reject her own current tile on the next pass and select a neighbor, then select the original again after she moved. That creates a high-frequency two-position ping-pong.

0656 resolves and caches one Community Center work tile per save/day session, then reuses it for the full work routine. `cardcha_mimi_home_status` now exposes `CCWork=x,y` for in-game verification.

### Dialogue continuity
- Generic `mimi.social.introduction` no longer says the farmer and MiMi just met.
- On the restored Community Center route, Stardew's `Introduction` entry instead uses `mimi.social.community-center`.
- VI approved direction: “Cuối cùng gian hàng của mình cũng có chỗ trú mưa rồi. Từ nay mấy lá bài khỏi phải học bơi nữa!”
- Social dialogue cache now refreshes if the restored Community Center route changes mid-save, not only when MiMi friendship unlocks.

## Regression guard
- 0655 native 16x32 Gift Log profile pipeline remains unchanged.
- 0655 WizardHouse stair anchor/art nudge remains unchanged.
- 0653 strict TMX runtime compatibility fix remains unchanged.
- No Save schema, progression, Airship, Hunt Run, Boss I, card balance, MiMi attic furniture/layout, HOME/TV/LATE routine, controller profile, or story milestone changes.

## Acceptance pending
- MiMi should remain in one stable Community Center work position with no clone/ghost flicker.
- Her Community Center first social line should fit established continuity and mention the newly sheltered stall rather than “officially meeting.”

# CARDCHA — NEXT SESSION START HERE

Upload the latest builder ZIP and tell ChatGPT to continue Cardcha from this file.

## Latest
**v0.1.17-alpha.11.6** — MiMi 13–17 mystery + 11–17 merchant + Scrap wallet + 2x ChaCha follower.

## Locked story flow
1. Before first natural Scrap: MiMi is `???`, appears in Town 13:00–17:00.
2. At 13:00 she can visibly fly in by broom; at 17:00 fly out.
3. ChaCha is always beside MiMi before he is lent.
4. Villagers may react to the mysterious girl.
5. First natural Scrap sets `FirstScrapDay`; MiMi ambient Town phase stops immediately.
6. MiMi visits the Farm **next day**, not same day. Show broom arrival first, then dialogue.
7. MiMi says she is busy and asks player to meet at WizardHouse 13:00–17:00.
8. During Wizard meetup ChaCha is still beside MiMi.
9. Wizard gives Machine + Binder; only then MiMi lends ChaCha / ChaCha follows player.
10. Card combat effects and Combat HUD are locked until the Wizard handoff is complete.
11. First real pull completes Chapter 1.

## Visual rules
- MiMi original lavender/silver-haired witch design, burgundy bow, purple/navy outfit.
- Hair star direction rule preserved from previous builds.
- ChaCha = white fairy rabbit mascot.
- Cardcha orb = fully transparent glass-like sphere with one light core; never red/white split.

## Current source assets
- `mimi_walk.png`
- `mimi_broom.png`
- `mimi_npc.png`
- `mimi_npc_portraits.png`
- `chacha_follow.png`
- `chacha_machine.png`
- `machine_anim.png`
- `machine_ui.png`

## Testing / known tooling
- User builds locally with .NET SDK 6.0.428.
- Exact game path: `E:\SteamLibrary\steamapps\common\Stardew Valley`.
- CS9057 compiler/analyzer warning is non-fatal.
- Always provide the finished builder as a clickable sandbox link.
- Every future builder MUST update this file, `BUILD_HISTORY.md`, and `CARDCHA_PROJECT_STATE.json`.

## Alpha.11.4 additions
- Pre-Scrap Town MiMi target anchor: `Town (45,62)`, intended central red-brick plaza.
- MiMi takes short walks around the anchor every few seconds instead of standing frozen.
- ChaCha visually stays beside her while she moves.
- Villager mystery bubbles are human-only. Pokémon/custom creatures must never generate them.
- If user says the plaza tile is still slightly off, adjust only `TownAnchor` in `MimiMysteryTownService.cs`; do not reset story architecture.


### Latest alpha.11.5 fix
Next-day Farm MiMi broom arrival scale corrected: event MiMi now 2x instead of 1x; ChaCha offset updated.


## Alpha.11.6 additions
- Wizard meetup MiMi is rendered at 2x with a foot-anchored origin so she matches the player instead of appearing tiny.
- After the meetup dialogue MiMi walks toward the nearest WizardHouse exit and fades out; ChaCha immediately becomes the player's follower.
- ChaCha follower base scale is 2x; front-view offset is moved farther from the farmer to prevent overlap.
- From the handoff onward MiMi is a daily merchant 11:00–17:00: Farmhouse area on normal days, WizardHouse on rainy days. On the handoff day, her merchant placement begins after the player leaves WizardHouse so the walk-out animation can finish cleanly.
- MiMi buys either Scrap for 100g and sells either Scrap for 1,000g, with intentionally shameless merchant banter.
- Cardboard Scrap + Shiny Scrap now live in two Binder wallet slots with visible counts and no longer occupy backpack slots.
- Old physical Scrap stacks are migrated from the backpack into the Binder wallet on save load.

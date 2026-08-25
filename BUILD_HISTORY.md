# BUILD HISTORY

## v0.1.17-alpha.11.41 — Circular HUD

- Replaced wide top-center text rows with up to three circular buff slots in one horizontal row.
- Timed effects show a large integer countdown (5 → 4 → 3 → 2 → 1) plus a depleting circular progress-dot ring.
- Hovering/touching a circle shows a compact tooltip with card name, state, effect description, remaining/cooldown duration, and stacks when relevant.
- BUFF uses the normal gold ring, READY uses green + check marker, ACTIVATED uses purple + pulse + exclamation marker.
- Keeps soft fade/slide and the existing priority order ACTIVATED > READY > BUFF.
- No official art assets changed. The circular masks are generated at runtime.

## v0.1.17-alpha.11.40 — HUD Polish
- Moved Cardcha combat HUD from lower-left to top-center.
- Reduced panel background opacity to ~66%.
- Capped visible Cardcha combat rows at 3.
- Added priority: ACTIVATED > READY > BUFF.
- Added soft fade/slide entrance and exit animation.
- Added distinct BUFF / READY / ACTIVATED badges.
- Activation toast now carries its card icon.
- Removed duplicate Phoenix Heart vanilla left-side HUD message.
- Added alpha-aware card icon rendering for smooth HUD fades.

## v0.1.17-alpha.11.39 — Portable UI + ChaCha Fetch
- Added dedicated portable-machine artwork without changing existing official assets.
- Portable machine menu now uses its own blue/gold handheld presentation and ChaCha idle.
- Added portable-only pull ritual where ChaCha dives into the device and physically fetches/presents the card.
- Added rarity sparkles and multi-pull card-back stack.
- Stationary machine ritual remains separate and unchanged.
- Added `cardcha_open_portable_machine` debug command.

## v0.1.17-alpha.11.38 — Portable Cardcha Machine
- Added persistent portable-machine purchase/gift entitlement (save schema v11).
- MiMi price: 50,000g.
- Free at 50 unique cards only if the player has not already acquired one.
- Toolbar Use Tool opens the existing Cardcha Machine menu.
- Portable machine cannot be placed indoors or outdoors.
- Reuses official `machine.png`; no official asset bytes modified.
- Expanded MiMi shop with a third portable-machine row and gamepad A/B actions.
- Added debug commands: `cardcha_give_portable_machine`, `cardcha_portable_status`.
- Preserves 11.37 centered first-Scrap notice, meetup quest, pending-MiMi hiding, and third-morning MiMi+Wizard forced handoff.

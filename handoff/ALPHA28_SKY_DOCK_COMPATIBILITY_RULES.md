# Alpha.28 Sky Dock compatibility rules

Accepted direction for the Cardcha Airship entrance after `0.3.0-alpha.28.0.2.0`.

## Placement intent

- Player leaves the Farm through the south exit into `Forest` / Cindersap.
- Sky Dock should be immediately visible to the **left** of the Farm-facing entrance area.
- Do not put the primary dock near WizardHouse; it is too far away for a repeat monster-farming loop.
- The permanent player-facing name is **Sky Dock**.

## Non-regression priority: base-game compatibility first

Sky Dock must not break vanilla NPC schedules, pathfinding, warps, forage, map collision, or other normal Forest gameplay.

The alpha.28 foundation therefore uses these rules:

1. Resolve the existing `Forest -> Farm` warp at runtime instead of assuming a fixed vanilla coordinate.
2. Search for a clear dock candidate several tiles to the **left** of that warp.
3. Keep a safety margin around every existing warp.
4. Never add/remove Forest objects or terrain features for the dock foundation.
5. Never edit Forest map layers, tile properties, or collision for the dock foundation.
6. The current visible dock is a non-blocking Cardcha overlay only.
7. Base-game NPC movement remains authoritative; Cardcha does not reserve or block an NPC route.
8. If a custom map overhaul makes the cosmetic placement imperfect, prefer a harmless visual mismatch over breaking movement/gameplay.

## Current flow

`Forest Sky Dock -> Cardcha_AirshipDeck -> route console / future Region I`

Leaving `Cardcha_AirshipDeck` returns the player to Sky Dock, not to the Farm boarding marker used in the first Airship foundation prototype.

The Farm remains the location for the pre-MiMi one-time Airship flyby only.

## Frozen systems that Sky Dock work must not regress

- Binder PreviewCard / LockedCard action-target contract.
- Controller synthetic-click suppression.
- Stationary vs Portable Cardcha Machine placement rules.
- Mystery-phase ChaCha random emotes remain disabled while MiMi is still `???`.
- Locked MiMi walk/broom/social mugshot assets remain untouched.

## Next visual pass

The current Sky Dock art is deliberately lightweight. Final art may become richer, but it should preserve the no-collision/no-NPC-blocking contract unless there is a separately tested map-specific compatibility layer.

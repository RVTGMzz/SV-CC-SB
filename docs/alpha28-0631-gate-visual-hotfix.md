# alpha28.0.4.14.4.5.1 Gate Visual Hotfix

Scope is intentionally narrow after in-game screenshot feedback.

- Cardcha Binder/UI sizing is not changed by this hotfix.
- Forest Arcane Gate remains presentation-only with `CollisionEdits=NONE`.
- Portal/cloud rectangles are clipped to their intended aperture so no translucent bars leak across the world.
- Forest gate anchor validation also rejects static `Buildings`/`Front` map-layer obstacles used by map overhauls.
- Forest gate activation is action-button only and can be triggered from a wider reachable radius, so a fence/tree between the player and the decorative overlay cannot trap access.
- Existing Airship exterior art remains locked and unchanged.
- PNG chunk CRCs are repaired deterministically before compile/package and then validated, preventing SMAPI texture failures from malformed CRC fields.

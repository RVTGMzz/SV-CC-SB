# Alpha28 0659 - Wizard stair interior-edge resolver

Build: `0.3.0-alpha.28.0.4.14.4.5.12.26`
Branch: `cardcha-alpha28-0659-wizard-stair-interior-edge-resolver`
Status: implementation candidate, in-game acceptance pending.

## In-game evidence
0658 successfully installed and rendered the stair, but the screenshot showed it entirely in the black exterior to the right of the WizardHouse room. This proves `Buildings width - 1` is a legal layer coordinate but not the visible interior boundary.

## Fix
`ResolvePreferredWizardStairTile` now scans the active `Back` + `Buildings` layers at the stair landing row. It chooses the rightmost tile that:
- has a real `Back` floor tile,
- has no blocking `Buildings` tile at the landing, and
- is immediately beside either void or a wall/building tile on its right.

A second pass chooses the rightmost real floor tile if the boundary condition is unavailable. Only if a replacement lacks standard layers does the fallback stay one tile inside the raw layer edge.

The resolved coordinate remains the single source of truth for stair visual placement, collision, interaction, ascent and return landing.

No save schema, progression, card canon, MiMi profile, Community Center stability/dialogue, attic layout, Airship, Hunt Run, Boss Gate, Boss Form, or controller behavior is changed.

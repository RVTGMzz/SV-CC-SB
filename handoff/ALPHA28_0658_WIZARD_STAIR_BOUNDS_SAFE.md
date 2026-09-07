# Alpha28 0658 - Wizard stair bounds-safe placement

Build: `0.3.0-alpha.28.0.4.14.4.5.12.25`
Branch: `cardcha-alpha28-0658-wizard-stair-bounds-safe`
Status: implementation candidate, in-game acceptance pending.

## Root cause confirmed from in-game log
The active WizardHouse replacement exposes a `Buildings` layer of `15x35`, so valid X coordinates are `0..14`. 0657 requested stair target `(15,15)`, which is outside that layer. The visual service therefore refused installation and retried every render, producing repeated warnings.

## Fix
`MimiHomeService.ResolvePreferredWizardStairTile` now resolves the preferred right-wall stair position against the active WizardHouse Buildings-layer dimensions. Preferred X remains 15 on maps wide enough for it, but clamps to `width - 1` when required. On the reported `15x35` map the resolved target is `(14,15)`.

The same resolved coordinate remains authoritative for visual placement, collision, player interaction, ascent and return landing.

No save schema, card canon, progression, MiMi profile, attic layout, Airship, Hunt Run, Boss Gate, Boss Form, or controller behavior is changed.

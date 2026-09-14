# AIRSHIP 0696D3-A CHECKPOINT

Status: IMPLEMENTED + CI PASS

Materialized commit:
`fa23a9ba178d36da5d1cf55080d3594ea20a16ff`

Successful workflow run:
`34895005876`

Validation:
`handoff/AIRSHIP_0696D3A_GAMEPLAY_ROOM_INTEGRATION_VALIDATION.json`

## Completed in D3-A

- Map travel is no longer hidden on the central helm/radar interaction.
- A dedicated travel gate is resolved at deck tile `(4,5)` and uses the existing Cardcha `boarding_gate_arch.png` art.
- The dedicated gate owns Region I departure interaction.
- All four upgrade systems remain present: Engine, Navigation, Hull, Reactor.
- Upgrade stations received grounded plinth treatment instead of floating-only presentation.
- Physical collision footprints were added for all four upgrade stations.
- D2.1 Observation Window production assets and the accepted D1S independent airship stayed frozen.
- Navigation Console image assets stayed frozen.
- Legacy Window overlay guard PASS.
- Render-depth contract PASS.
- Release compile PASS.

## Upgrade collision footprints

- Engine: `(4,8)`, `(5,8)`
- Navigation: `(18,8)`, `(19,8)`
- Hull: `(7,11)`, `(8,11)`
- Reactor: `(15,11)`, `(16,11)`

## Next batch

Proceed to **0696D3-B Prop Integration and Visual Believability**:

1. Reposition/scale props so the room reads naturally rather than pasted together.
2. Correct oversized machine footprints/presentation.
3. Rework the radar/navigation machine from Ron's supplied reference. Preserve the characteristic yellow/gold background. Do not improvise a different machine.
4. Remove unintended background/cutout artifacts while preserving the approved reference look.

Room 1 border, entrance arch x2 and Observation Window size remain deferred to D3-C.

No D3 test package is required at this checkpoint; package after the planned regression batch unless a targeted visual build becomes necessary.

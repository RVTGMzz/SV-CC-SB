# Alpha 28 / 0696C — Airship Deck Visual Recovery

## Build
`0.3.0-alpha.28.0.4.14.4.5.12.64`

## Ron in-game rejection carried forward
`.63` is **VISUAL REJECTED** for the Airship Deck screenshot pass. Technical foundation success did not equal visual acceptance.

Observed blockers from Ron:
- opaque black window wipe frames;
- four upgrade stations missing;
- room shell/border visually absent;
- lower doorway allowed the farmer to remain in black void;
- environment selection did not match the promised time/weather list.

## 0696C corrections
- Observation Window now resolves an explicit **season × time × weather** scene matrix.
- Matrix contains 5 season keys (`default`, spring, summer, fall, winter) × 4 time buckets × 4 weather states = **80 authored/generated scene entries**.
- Time buckets: morning, noon, evening, night.
- Weather: clear, rain, storm, snow.
- Moving cloud/rain/snow FX remain separate animation layers; lightning remains an event overlay.
- Old window overlay frames 2–4 are forbidden as fallback because they contain opaque black wipe pixels. If new ambient assets fail, the clean TMX base remains instead.
- Navigation Console receives an 8-frame radar sweep plus ping/glow layers.
- Engine / Navigation / Hull / Reactor upgrade stations are restored through the existing `DrawUpgradeStations` production method.
- Airship Deck receives a visible Cardcha wood/brass shell on top, sides and lower boundary while base `Buildings` still owns collision.
- Bottom doorway remains exactly two tiles wide at x=11..12 and crossing it immediately returns to the Arcane Dock. Any illegal side/bottom escape is recovered back inside the room.

## Acceptance
Technical validation may PASS in CI, but visual status remains **PENDING-RON-IN-GAME** until Ron tests `.64`.

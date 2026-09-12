# Alpha 28 / 0696C — Airship Deck Visual Recovery

## Build
`0.3.0-alpha.28.0.4.14.4.5.12.64`

## Verified checkpoint
- Materialized source head: `58e3d80147e6e5490d32b83527587ca4156ff0cc`
- Authoritative successful workflow run: `34698643517`
- Artifact ID: `10298949682`
- Artifact digest: `sha256:ceca18eee2378302e714ff14462be639897459051b5d0981e315b2c9bbc2130c`
- TEST ZIP SHA256: `d8128de076f0d22d60ae8c9a8dc8b51a4040e67d047121ce833ca440e7bf7cce`
- Technical validation: **PASS**
- Visual acceptance: **PENDING-RON-IN-GAME**

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
- Matrix contains 5 season keys (`default`, spring, summer, fall, winter) × 4 time buckets × 4 weather states = **80 scene entries**.
- Time buckets: morning, noon, evening, night.
- Weather: clear, rain, storm, snow.
- All 80 scene backdrops are package-gated as fully opaque so black void cannot bleed through the glass.
- Moving cloud/rain/snow FX remain separate animation layers; lightning remains an event overlay.
- Old window overlay frames 2–4 are forbidden as fallback because they contain opaque black wipe pixels. If new ambient assets fail, the clean TMX base remains instead.
- Navigation Console receives an 8-frame radar sweep plus ping/glow layers.
- Engine / Navigation / Hull / Reactor upgrade stations are restored through the existing `DrawUpgradeStations` production method.
- Airship Deck receives a visible Cardcha wood/brass shell on top, sides and lower boundary while base `Buildings` still owns collision.
- Bottom doorway remains exactly two tiles wide at x=11..12 and crossing it immediately returns to the Arcane Dock. Any illegal side/bottom escape is recovered back inside the room.
- Sky Dock and unrelated Region maps were frozen during this pass.

## Evidence gate
The first 0696C visual evidence pass exposed an additional snow-scene alpha bug before release. That artifact was rejected internally and not shipped. Run `34698643517` is the corrected authoritative build; its package audit opens all 80 environment PNGs and requires alpha `(255,255)` for every one.

## Acceptance
Technical validation is PASS, but visual status remains **PENDING-RON-IN-GAME** until Ron tests `.64`.

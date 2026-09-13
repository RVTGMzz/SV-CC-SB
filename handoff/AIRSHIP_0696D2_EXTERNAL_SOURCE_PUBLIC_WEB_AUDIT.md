# AIRSHIP 0696D2 External Source Recovery: Public Web Audit

Date: 2026-09-14
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Scope: exact D2.1 source recovery only. No source recreation, no image substitution, and no GitHub Actions re-audit.

## Exact fingerprint search

The public web was searched for each authoritative D2.1 SHA256 value:

- `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0`
- `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff`
- `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638`
- `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990`

Result: **0 indexed matches**.

## Production filename search

The public web was searched for the exact required production filenames:

- `window_scene_default_morning_clear.png`
- `window_scene_default_noon_clear.png`
- `window_scene_default_evening_clear.png`
- `window_scene_default_night_clear.png`

Result: **0 indexed matches**.

## Source-pack / project-alias search

Additional searches combined the known archive aliases and project terms:

- `concept(1).rar` + Cardcha
- `sprite(1).rar` + Cardcha
- `concept(1).rar` + airship
- `sprite(1).rar` + airship
- `Cardcha` + `Observation Window` + `0696`
- `Cardcha: Shardbound` + airship

The returned results were either empty or unrelated generic web content. No Cardcha D2.1 archive, image, mirror, attachment, or downloadable source candidate was found.

## Result

**0 authoritative D2.1 source candidates found on the indexed public web surface.**

No public result provided a byte stream that could be validated against the exact source gate.

## Recovery implication

Do not repeat public-web SHA/filename/archive-alias searches unless new provenance information appears, such as a specific host, URL, mirror, uploader, or alternate source filename.

The next valid recovery route remains an authoritative original/local copy whose four PNG byte streams independently match the recorded SHA256 values.

`.69` remains intentionally unmaterialized.

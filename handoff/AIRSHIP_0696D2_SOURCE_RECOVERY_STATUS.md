# AIRSHIP 0696D2 Source Recovery Status

Date: 2026-09-13
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Pre-evidence HEAD: `d461e06af63760e881e33a1d386b3eb8ae8d5f8c`
Target release when materialized: `0.3.0-alpha.28.0.4.14.4.5.12.69`

## Status

**BLOCKED ON EXACT APPROVED SOURCE BYTES.**

Do not materialize `.69`, bump the production manifest/version, or publish a `.69` TEST package until all four approved PNGs exist at the exact required paths and pass the existing source gate.

Required files, all PNG / 160x80 / RGBA:

| Time | Required SHA256 |
|---|---|
| morning | `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0` |
| noon | `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff` |
| evening | `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638` |
| night | `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990` |

Required paths:

- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_morning_clear.png`
- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_noon_clear.png`
- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_evening_clear.png`
- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_night_clear.png`

## D1S `.68` artifact inspection

Workflow run: `34706205130` (`Cardcha 0696D1S Real Airship Motion Repair`)
Artifact ID: `10301895768`
Artifact name: `cardcha-alpha28-0696D1S-real-airship-motion`
Artifact digest: `sha256:d410892812d68e3c6749336437bc84ec62cd7fe86f12f224004157f34400311a`

Inner package inspected:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.68_0696D1S_RealAirshipMotion_TEST.zip`

The four `default_*_clear` files in `.68` are **legacy 128x42 RGBA** and are not approved D2 source:

| File | Size | SHA256 |
|---|---:|---|
| `window_scene_default_morning_clear.png` | 128x42 | `40c8ffac23c69ded8d4048bb8583bd1c72d77c816582a1ec031eadd6c56846af` |
| `window_scene_default_noon_clear.png` | 128x42 | `5d6b4e7f15c4f55998ef395b1212bc692d0fd7aebc625892c95a9c9012c7c8ad` |
| `window_scene_default_evening_clear.png` | 128x42 | `5c727c9a52fb0d0f31a21e6ff730211835f4856656784dd017825c3b57eebd9b` |
| `window_scene_default_night_clear.png` | 128x42 | `9af844db633b1f41f22e30d7477d8f6394a56afa4d6a9a4de6b1f9223e2963a7` |

The accepted independent D1S ship inside the same artifact is correct and remains frozen:

- `observation_window_airship.png`
- 15x9 RGBA
- SHA256 `58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce`

## Full `.68` 160x80 sweep

The entire `.68` TEST package contains 10 PNGs at 160x80. None match any of the four approved D2 SHA256 values.

Relevant candidates and SHA256:

- `airship_0692_observation_window.png` -> `34bb4ca85fd3b2690794d4b4686ef4fc46508d3c21beb99a4ab22f28c016d9ba`
- `observation_window_base.png` -> `2859298bda3049c7c1479fff416e3f7a0a853cf81cd625a8951c2bd95b8e2ef7`
- `observation_window_overlay_1.png` -> `439c3bdbdbbbed4228b7145015f80dd147cb3b1f7ee0668eca8d167f2a3680c4`
- `observation_window_overlay_2.png` -> `ed918738062177010ebdb13689d25920f4e49143176d300ec6ced5cbd0ada9ae`
- `observation_window_overlay_3.png` -> `2460ace9fe95e4c8ea8b3a6cc7de8d7539093e31bb97cd6efb7342b188d3db31`
- `observation_window_overlay_4.png` -> `0f10e9a0c4fdca4bc11b841ce906b6c71dc684c963b58526ad6823d76e8a9aa3`
- `window_runtime/observation_window_frame.png` -> `2859298bda3049c7c1479fff416e3f7a0a853cf81cd625a8951c2bd95b8e2ef7`
- `window_runtime/observation_window_view_mask.png` -> `c16711e353257e79057f92ad9295642c40729d36754e292c1d6c9680433c4f71`
- `window_runtime/window_fx_lightning_flash_01.png` -> `f9704c9cbcf85f54f266204b1255f677569e4e6248ef8220aaff829070220912`
- `window_runtime/window_fx_lightning_flash_02.png` -> `3554361daa2b6003c80ce081f1555e3a700d1feb7f29470f5783af242c76bf8b`

Therefore `.68` contains no renamed 160x80 copy of the approved D2 clear environment images.

## Recovery searches already completed

- Current D2 branch tree/history.
- 0696 concept branch.
- `cardcha-alpha28-0696d1-observation-window-source-cleanup`.
- `cardcha-alpha28-0696d1s-airship-motion-repair`.
- D1 TEST package `.65`: known legacy `default_*_clear` assets are 128x42 and rejected.
- D1S TEST package `.68`: exact evidence above.
- GitHub Actions artifacts relevant to the 0696 lineage.
- Accessible File Library search for the exact approved filenames/hashes.
- Accessible File Library search for source archives named `concept(1).rar` and `sprite(1).rar`; no relevant archive was returned.

D1 source documentation records those two source archives as external/missing source material. Do not fabricate replacements for missing approved bytes.

## Safe implementation state

Prepared but intentionally not materialized:

- exact 4-file source gate: PNG + 160x80 + RGBA + exact SHA256
- D2 clear-time resolver for morning/noon/evening/night
- no legacy observation overlay reuse guard
- D1S independent ship SHA guard
- CI/package audit for `.69`

Existing CI evidence: workflow reaches the exact-source gate and fails there when approved bytes are absent. This is the expected safe behavior.

## Next allowed action

1. Recover the exact approved source bytes from an external/original source archive, prior local export, chat attachment, or other authoritative source.
2. Place them at the four required paths without re-encoding or editing.
3. Run `--check-source`.
4. Only after all four hashes pass: `--apply` -> validate -> compile -> package audit -> `.69` TEST.
5. Ron performs visual acceptance before `.69` is considered complete.

## Explicit prohibitions

- No upscale from 128x42.
- No redraw/recolor/re-encode.
- No substitution from `observation_window_overlay_2/3/4.png`.
- No Navigation Console changes.
- No `.69` package while source gate is red.

# SOURCE NAME MAP — 0696D2 Observation Window

Updated: 2026-09-14
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Purpose: provide a permanent mapping between the recovered original concept/master images, intended canonical names, known derived sprites, and the lost historical D2.1 production-byte gate.

## 1. Recovered concept/master source mapping

These four images were confirmed to still exist in the original chat/session sandbox. They are the surviving high-resolution concept/master artworks for the approved Morning / Noon / Evening / Night Observation Window set.

| Time state | Original sandbox filename | Intended repo/canonical master name | Size / mode | SHA256 |
|---|---|---|---|---|
| Morning | `khung_cửa_sổ_phi_thuyền_bình_minh.png` | `observation_window_master_morning.png` | `1774x887 RGBA` | `e42ce1e1199f30ac8d30ab592ecbec01b9176388ed2a6572b68005b812e2bc85` |
| Noon | `cửa_sổ_khinh_khí_cầu_giữa_trời_xanh.png` | `observation_window_master_noon.png` | `1774x887 RGBA` | `c6f99df25a7dee04d0aeab8f1d9ac928a7e6dcb1af43db092187e1ad7831ae9e` |
| Evening | `cửa_sổ_phi_thuyền_hoàng_hôn_rực_rỡ.png` | `observation_window_master_evening.png` | `1774x887 RGBA` | `650adec1a8d08631d02b31a59c45bc3dda96a49706a68feea3508996ee2a4fbe` |
| Night | `cửa_sổ_phi_thuyền_dưới_trăng_rằm.png` | `observation_window_master_night.png` | `1774x887 RGBA` | `7788da7428b7a808794c2ba14716c1ed0c25b59a3f2990f1d6c8437a92b55ee8` |

These hashes identify the surviving master artwork bytes. They are **not** the old 160x80 D2.1 production hashes.

## 2. Historical D2.1 production target names

The old implementation expected these runtime source filenames:

- `window_scene_default_morning_clear.png`
- `window_scene_default_noon_clear.png`
- `window_scene_default_evening_clear.png`
- `window_scene_default_night_clear.png`

Historical exact SHA256 gate:

| Time state | Historical production SHA256 | Recovery state |
|---|---|---|
| Morning | `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0` | exact 160x80 byte stream not recovered |
| Noon | `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff` | exact 160x80 byte stream not recovered |
| Evening | `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638` | exact 160x80 byte stream not recovered |
| Night | `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990` | exact 160x80 byte stream not recovered |

Do not confuse the master SHA values in section 1 with these historical production SHA values.

## 3. Known derived / test sprite

A surviving derivative was also found:

- original path: `d2_q24/window_time_evening.png`
- size/mode: `160x80 RGBA`
- SHA256: `6f572a16e435bdbefee3000798cb012afbcd439659673122412988f214659a2d`

This file does **not** match the historical approved Evening SHA and must not be silently treated as the old canonical D2.1 production source.

It may only be used later as a comparison/reference artifact if explicitly documented.

## 4. Naming rule going forward

When the four surviving master files are committed to a recovery branch, preserve their bytes exactly and use these repo names:

```text
recovery/0696d2-concept-masters/
  observation_window_master_morning.png
  observation_window_master_noon.png
  observation_window_master_evening.png
  observation_window_master_night.png
```

Do not crop, resize, re-encode, recolor, or otherwise modify the master files during recovery.

Any future 160x80 production sprites derived from these masters must have **new hashes recorded explicitly** and must not reuse the lost historical SHA identities unless the exact old bytes are genuinely recovered.

## 5. Interpretation rule for future sessions

If a future session sees the four 1774x887 master files above, it should treat them as the surviving approved visual source set.

If it sees the old 160x80 SHA table, it should treat those as historical production-byte identities that are currently lost.

Never claim the two sets are byte-equivalent.

See `README_FOR_NEXT_SESSION.md` and `handoff/AIRSHIP_0696D2_ACCESSIBLE_SURFACES_EXHAUSTED.md` before continuing D2 work.

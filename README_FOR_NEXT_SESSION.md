# README FOR NEXT SESSION — Cardcha 0696D2

Updated: 2026-09-14
Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Start here

Do not restart image recovery from zero.

Read first:

- `SOURCE_NAME_MAP.md`
- `handoff/HANDOFF_CURRENT.md`
- `handoff/AIRSHIP_0696D2_ACCESSIBLE_SURFACES_EXHAUSTED.md`

Safe base:
`0.3.0-alpha.28.0.4.14.4.5.12.68`

Next candidate, still blocked:
`0.3.0-alpha.28.0.4.14.4.5.12.69`

## Surviving approved master artwork

The original session still contains four 1774x887 RGBA master images:

- Morning: `khung_cửa_sổ_phi_thuyền_bình_minh.png`
  SHA256 `e42ce1e1199f30ac8d30ab592ecbec01b9176388ed2a6572b68005b812e2bc85`
- Noon: `cửa_sổ_khinh_khí_cầu_giữa_trời_xanh.png`
  SHA256 `c6f99df25a7dee04d0aeab8f1d9ac928a7e6dcb1af43db092187e1ad7831ae9e`
- Evening: `cửa_sổ_phi_thuyền_hoàng_hôn_rực_rỡ.png`
  SHA256 `650adec1a8d08631d02b31a59c45bc3dda96a49706a68feea3508996ee2a4fbe`
- Night: `cửa_sổ_phi_thuyền_dưới_trăng_rằm.png`
  SHA256 `7788da7428b7a808794c2ba14716c1ed0c25b59a3f2990f1d6c8437a92b55ee8`

These are surviving visual masters, not the old lost 160x80 production byte streams.

## Immediate next action

Preserve the four master files first on a dedicated recovery branch, copying bytes without transformation.

Recommended branch:
`recovery/0696d2-concept-masters`

Recommended paths:

```text
recovery/0696d2-concept-masters/
  observation_window_master_morning.png
  observation_window_master_noon.png
  observation_window_master_evening.png
  observation_window_master_night.png
```

During recovery:

- no resize
- no crop
- no re-encode
- no recolor
- no regeneration
- no `.69` build

After commit, record branch, commit SHA, dimensions, mode and SHA256 of all four files.

## Old historical production gate

The old 160x80 SHA set is still unrecovered:

- Morning `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0`
- Noon `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff`
- Evening `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638`
- Night `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990`

Do not silently replace these with newly generated hashes.

Once the four masters are safely preserved, Ron must explicitly choose one of two paths:

1. keep exact historical recovery active, or
2. intentionally re-baseline D2.1 from the preserved masters and record a new canonical 160x80 SHA set.

## Known derivative

`d2_q24/window_time_evening.png`

- 160x80 RGBA
- SHA256 `6f572a16e435bdbefee3000798cb012afbcd439659673122412988f214659a2d`

This does not match the old approved Evening production SHA and must not be treated as canonical without new provenance evidence.

## Rule going forward

Any visual master Ron approves must be preserved to Git or a dedicated source archive before runtime sprite work begins.

# OFFICIAL USER-MASTER ASSETS

Status: LOCKED as of v0.1.17-alpha.11.32.

The entire `src/Cardcha/assets/` directory in this builder was copied byte-for-byte from the user-provided `assets.zip`.
These files are the official art/data master for Cardcha: Shardbound.

Rules for future work:
- Do NOT regenerate, redraw, resize, derive, recolor, or overwrite these assets unless the user explicitly asks for an asset edit.
- Code changes must adapt to these assets, not the other way around.
- If a future user-provided master asset pack is supplied, replace the official master only with that pack.
- Runtime/native helper art should not be regenerated automatically from another image unless explicitly requested.

Source pack SHA-256:
`2226b7611cd82bd8d94222df1b8869dba99bfe443f6bd5e3f94d80cc03197a36`

## File checksums
- `CARD_ICON_ATLAS_SPEC.txt` — 1204 bytes — `516c91d919295bad808418db7f37f1ab5cac9b2850451c178831dbfae91d94c5`
- `card_icons.png` — 74929 bytes — `09e441343375f755bf4eb5520688d00e7d8979ee5f12a1f2faa7f506fd677bf1`
- `cards.json` — 2658 bytes — `36ccee1066938698ec924d9dab912c59a8e61727124baf9064928bd89881d340`
- `chacha_follow.png` — 22343 bytes — `57ec844b991e0ab59e7bd9ef53690cbd4d0e290d51aae0a4342c265b3e96e4e2`
- `chacha_machine.png` — 24418 bytes — `070a50bf926b568401e0582df57b00b1677f18b94f737932719932dc47057e75`
- `items.png` — 612 bytes — `fc135f468e5e23d793ae7829fef18750e9eaff59e98b275aad2680617f60d14a`
- `machine.png` — 1906 bytes — `ca3e9e00f99c0ff2d8e8d76177f363eb6816d1bdb936cea2cd16f4b9aa6e89be`
- `machine_anim.png` — 89258 bytes — `bce83d20f1ee124aea63b5783fd401e2c37753bf3e4d4f9aa7fb48f85ca8804b`
- `machine_ui.png` — 79882 bytes — `44cd8abc534d12ad369e83b8f0ca2f38acf138fc85876c9953690bec578958f8`
- `mimi_broom.png` — 30532 bytes — `7a794ed4fbec6c48ee67fbc82331a8eb0bd1cbfdfb866fdc8992d1f191d6ab5e`
- `mimi_dialogue.json` — 599 bytes — `c4b87387e6bfb5d12b1f375bbc731b54cc69858fa61f1448f843833166b1d22f`
- `mimi_npc.png` — 8207 bytes — `494a62ab03ea975a201ef559446f36063b215df6fe8d97ac44959a885b8fc40f`
- `mimi_npc_portraits.png` — 56318 bytes — `23e344f80930b73b1e0dd4bf2c0011e9311fcd7f82c0fa1db5cec427cfc5b1db`
- `mimi_portraits.png` — 61769 bytes — `f5d32e9d7e94713facfecd1b2b3bb14d253a9e2805fa0439ca6d62bcc76be27f`
- `mimi_schedule.json` — 3 bytes — `ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356`
- `mimi_walk.png` — 19458 bytes — `79a2ddd16e423c5052231a00a3b609585286eefc21551f5f1136c72a7efa0c5a`


## Runtime portrait rule
`mimi_portraits.png` is the official MiMi portrait source. Cardcha may create a temporary 64x64-per-expression texture in memory for vanilla Stardew dialogue rendering, but must never write that derived texture back over the user-master assets.

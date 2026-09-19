# NEXT CHAT PROMPT — CARDCHA 0696D3-K

Updated: 2026-09-19

Copy/paste the block below into the next ChatGPT session.

---

Tiếp tục Cardcha từ **0696D3-K Collision Hook Runtime Fix** trên repo `RVTGMzz/SV-CC-SB`, branch `cardcha-alpha28-0696d2-window-environment-matrix`.

Đọc theo thứ tự:
1. `handoff/NEXT_CHAT_PROMPT_2026-09-19_CARDCHA_0696D3K.md`
2. `handoff/AIRSHIP_0696D3K_COLLISION_HOOK_RUNTIME_FIX.md`
3. `handoff/SESSION_HANDOFF_2026-09-19_CARDCHA_0696D3K.md`
4. `handoff/LATEST_CARDCHA_HANDOFF.md`
5. `handoff/AIRSHIP_0696D3J_COLLISION_LANES_CHECKPOINT.md`

Authority hiện tại:
- Repo canonical: `RVTGMzz/SV-CC-SB`
- Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
- Phase: `0696D3-K`
- Version: `0.3.0-alpha.28.0.4.14.4.5.12.75`
- CI / compile / package audit / prerelease: **PASS**
- Runtime: **RETEST REQUIRED**
- Không gọi Runtime PASS nếu Ron chưa test exact package và xác nhận.

Canonical D3-K TEST package:
`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3k-test-4431c51f/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.75_0696D3K_CollisionHookRuntimeFix_TEST.zip`

SHA256:
`be00e20fc67b5f08d784c55d5ebeba86abd3e2449d6d1832e31174ffad79f163`

D3-K được tạo trực tiếp từ runtime log của Ron vì D3-J báo:
`0696D3-J couldn't resolve GameLocation.isCollidingPosition`

D3-K đã:
- bỏ hard-coded exact 9-parameter `GameLocation.isCollidingPosition`;
- quét mọi overload tương thích và patch động;
- dùng generic postfix với `MethodBase __originalMethod` + `object[] __args`;
- giữ toàn bộ D3-J TMX collision footprints;
- không dùng `Farmer.Position` để ép vị trí;
- sửa startup banner hardcode `.69 / 0686`;
- banner hiện lấy version thật từ `ModManifest.Version`.

Khi Ron test exact package `.75`, ưu tiên kiểm ngay log startup.

Phải thấy:
`0696D3-K installed collision hooks on <N> GameLocation.isCollidingPosition overload(s).`
trong đó **N > 0**.

Và:
`Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.75 0696D3-K COLLISION HOOK RUNTIME FIX TEST`

Không được còn:
`couldn't resolve GameLocation.isCollidingPosition`

Nếu các dòng log trên đúng, mới test collision thực tế bằng cách cố tình đi vào:
- Room 1: notice board, Lost & Found, waiting bench, luggage, cargo, hai bên BOARD AIRSHIP, lamp;
- Room 2: navigation console, hai bên TRAVEL, cả 4 UPGRADE, lamp, 2x ChaCha Resonance machine.

Collision authority:
- TMX `Buildings` footprints + runtime collision query phải cùng contract;
- chỉ chừa front interaction lanes;
- runner/thảm phải không bị block;
- center throat BOARD AIRSHIP/TRAVEL phải mở;
- tuyệt đối không reintroduce forced-position / ghost-body blocker.

Không restart D2 và không redo D3-A/B/C/D/E/F/G/H/I/J.
Chỉ patch incrementally từ D3-K nếu Ron có runtime feedback mới.

GitHub account routing cho repo này dùng account RVTGMzz / `lengochung28191@gmail.com`.

---

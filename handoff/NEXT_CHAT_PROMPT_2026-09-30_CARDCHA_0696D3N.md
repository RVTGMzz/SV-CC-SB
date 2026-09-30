# NEXT CHAT PROMPT — CARDCHA 0696D3-N

Updated: 2026-09-30

Copy/paste this into the next ChatGPT session:

---

Tiếp tục Cardcha từ **0696D3-N Cabin Light Sources Night Fix** trên repo `RVTGMzz/SV-CC-SB`, branch `cardcha-alpha28-0696d2-window-environment-matrix`.

Dùng đúng GitHub account `lengochung28191@gmail.com`.

Đọc theo thứ tự:
1. `handoff/NEXT_CHAT_PROMPT_2026-09-30_CARDCHA_0696D3N.md`
2. `handoff/LATEST_CARDCHA_HANDOFF.md`
3. `handoff/AIRSHIP_0696D3N_CABIN_LIGHT_SOURCES_NIGHT_FIX.md`
4. `handoff/SESSION_HANDOFF_2026-09-30_CARDCHA_0696D3N.md`
5. `handoff/AIRSHIP_0696D3M_ROOM_LIGHTING_COLLISION_LAYER_FIX.md`

Authority hiện tại:
- Phase: `0696D3-N`
- Version: `0.3.0-alpha.28.0.4.14.4.5.12.78`
- CI / compile / static validation / package audit / prerelease: **PASS**
- Runtime: **RETEST REQUIRED**
- Không gọi Runtime PASS trước khi Ron test exact .78 package.

Canonical source/package commit:
`1a66357931b35bffff7a0894320e7d868880ab2c`

Current branch HEAD có thêm docs-only commits:
`18b50fdf042c9339a24def74371a408e9a82e8c3`

Canonical TEST package:
`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3n-test-1a663579/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.78_0696D3N_CabinLightSourcesNightFix_TEST.zip`

SHA256:
`133f6decaae31ce61578dc56075c7f2059be19189fb8f4243ac97112ef7354c7`

Latest runtime authority:
Ron test D3-M .77 lúc khoảng 20:00 và Room 1 vẫn gần như tối đen. Vì vậy ambient-only fix của D3-M đã Runtime FAIL cho ban đêm.

D3-N .78 đã:
- giữ ambient fallback;
- thêm 8 Stardew `LightSource` thật vào Room 1;
- phủ route board, Lost & Found, waiting bench, luggage, boarding left/right/center và exit;
- scope đèn chỉ cho `Cardcha_SkyDockInterior`;
- tự re-add nếu Stardew clear light dictionary;
- remove đèn khi rời Room 1 / reset runtime;
- giữ nguyên toàn bộ D3-M Room 2 collision/depth fixes.

Ưu tiên đầu tiên phiên mới:
1. Ron test exact .78 ở 20:00+.
2. Xác nhận Room 1 có light pools và đọc được map.
3. Ra khỏi phòng xem đèn có leak sang map khác không.
4. Vào lại xem đèn có trở lại không.
5. Quick regression Room 2: 4 UPGRADE, Window sill, Window/console depth, TRAVEL/BOARD/Resonance.

Nếu vẫn tối:
- lấy SMAPI runtime log;
- kiểm startup banner D3-N;
- kiểm light IDs/EnsureD3NRoom1Lights;
- không quay lại cách chỉ tăng `Game1.ambientLight`.

Nếu pass:
- promote D3-N night lighting Runtime PASS;
- chỉ patch tiếp từ runtime feedback mới.

Không restart D2. Không redo D3-A/B/C/D/E/F/G/H/I/J/K/L/M.

---

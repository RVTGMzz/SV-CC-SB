Stardew Squad - Dialogue Recruit Button alpha3
=============================================

Mục tiêu
- Giữ nguyên The Stardew Squad 0.12.1 và toàn bộ follower/combat/task logic của mod gốc.
- Không xoá hay thay đổi các hotkey E/F/Alt+... hiện tại; chúng vẫn hoạt động cho người đã quen chơi.
- Bổ sung đường điều khiển bằng UI/hộp thoại để mobile và controller chơi thuận tiện hơn.
- Hỗ trợ UI: English, Tiếng Việt, 日本語, 한국어, ไทย, 简体中文, Français, Español.

Flow mới
1. NPC CHƯA vào đội
   - Nếu NPC còn thoại trong ngày: nói chuyện như Stardew bình thường; trên hộp thoại hiện "R — Mời vào đội".
   - Bấm shoulder R trên controller, hoặc chạm trực tiếp vào gợi ý trên mobile, để mở xác nhận mời bằng hộp thoại Stardew gốc.
   - Ngoài lúc hộp thoại recruit đang mở, R không bị addon chiếm nên vẫn dùng đổi toolbar như bình thường.

2. NPC ĐÃ HẾT thoại trong ngày nhưng CHƯA vào đội
   - Addon KHÔNG reset dialogue, KHÔNG cho nói vô hạn và KHÔNG cộng thêm friendship.
   - Tương tác lại với NPC sẽ mở một hộp thoại ngữ cảnh trung tính "...".
   - Trên hộp thoại này vẫn hiện "R — Mời vào đội", nên người chơi không bị mất cơ hội recruit chỉ vì đã nói chuyện với NPC trước đó trong ngày.

3. NPC ĐÃ vào đội
   - Chỉ cần tương tác/chạm vào NPC.
   - Không cần bấm R lần nữa và không phụ thuộc NPC còn thoại hay đã hết thoại trong ngày.
   - Một hộp thoại lựa chọn hiện ra với:
     + Ra lệnh
     + Quản lý đội
     + Công việc tự động BẬT/TẮT
     + Trò chuyện
     + Huỷ

4. Ra lệnh
   - Chọn "Ra lệnh" rồi chọn mục tiêu.
   - Mobile/mouse: chạm mục tiêu.
   - Controller: quay về phía mục tiêu rồi bấm nút tương tác.
   - Addon gọi lại chính manual-command routing của Stardew Squad, bao gồm đường multiplayer farmhand -> host khi có.

5. Quản lý đội
   - Mở menu quản lý gốc của Stardew Squad bằng giao diện question dialogue vanilla để controller/mobile dễ dùng.
   - Các lựa chọn gốc như Kho đồ / Chờ ở đây / Cho về / Cho cả đội về vẫn do Stardew Squad xử lý.

6. Trò chuyện
   - Gọi lại interaction vanilla của NPC.
   - Nếu NPC còn thoại thì nói chuyện bình thường.
   - Nếu đã hết thoại, Stardew giữ nguyên hành vi gốc; addon không tạo thêm lời thoại để tránh farm friendship hoặc làm NPC lặp thoại vô hạn.

Ngôn ngữ
- default.json: English
- vi.json: Tiếng Việt
- ja.json: 日本語
- ko.json: 한국어
- th.json: ไทย (custom locale code th)
- zh.json: 简体中文
- fr.json: Français
- es.json: Español

Lưu ý
- Điều kiện tình bạn, giới hạn thành viên, từ chối recruit, save state, combat, task, multiplayer... vẫn do Stardew Squad sở hữu.
- Addon chỉ thêm lớp điều khiển UI và gọi lại các manager/action sẵn có của mod gốc.
- Trong festival/cutscene, addon tránh can thiệp để không phá state sự kiện.

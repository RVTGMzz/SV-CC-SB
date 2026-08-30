Stardew Squad - Dialogue Recruit Button alpha2
=============================================

Mục tiêu
- Giữ nguyên The Stardew Squad 0.12.1 và toàn bộ follower/combat/task logic của mod gốc.
- Không xoá hay thay đổi các hotkey E/F/Alt+... hiện tại; chúng vẫn hoạt động cho người đã quen chơi.
- Bổ sung một đường điều khiển bằng UI/hộp thoại để mobile và controller chơi thuận tiện hơn.

Flow mới
1. NPC CHƯA vào đội
   - Nói chuyện với NPC như Stardew bình thường.
   - Trên hộp thoại hiện gợi ý: "R — Mời vào đội".
   - Bấm shoulder R/L trên controller, hoặc chạm trực tiếp vào gợi ý trên mobile, để mở xác nhận mời bằng hộp thoại Stardew gốc.
   - Ngoài lúc hộp thoại này đang mở, R/L không bị addon chiếm nên vẫn dùng đổi toolbar như bình thường.

2. NPC ĐÃ vào đội
   - Chỉ cần tương tác/chạm vào NPC.
   - Không cần bấm R lần nữa.
   - Một hộp thoại lựa chọn hiện ra với:
     + Ra lệnh
     + Quản lý đội
     + Công việc tự động BẬT/TẮT
     + Trò chuyện
     + Huỷ

3. Ra lệnh
   - Chọn "Ra lệnh" rồi chọn mục tiêu.
   - Mobile/mouse: chạm mục tiêu.
   - Controller: quay về phía mục tiêu rồi bấm nút tương tác.
   - Addon gọi lại chính manual-command routing của Stardew Squad, bao gồm đường multiplayer farmhand -> host khi có.

4. Quản lý đội
   - Mở menu quản lý gốc của Stardew Squad bằng giao diện question dialogue vanilla để controller/mobile dễ dùng.
   - Các lựa chọn gốc như Kho đồ / Chờ ở đây / Cho về / Cho cả đội về vẫn do Stardew Squad xử lý.

5. Trò chuyện
   - Cho phép nói chuyện bình thường với NPC đã vào đội, tránh việc menu squad làm mất tương tác xã hội vanilla.

Lưu ý
- Điều kiện tình bạn, giới hạn thành viên, từ chối recruit, save state, combat, task, multiplayer... vẫn do Stardew Squad sở hữu.
- Addon chỉ thêm lớp điều khiển UI và gọi lại các manager/action sẵn có của mod gốc.
- Trong festival/cutscene, addon tránh can thiệp để không phá state sự kiện.

from pathlib import Path
import json
import re

ROOT = Path("src/Cardcha")
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.9"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.10"


def replace_version(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if NEW_VERSION in text:
        return
    if OLD_VERSION not in text:
        raise RuntimeError(f"Expected {OLD_VERSION} in {path}")
    path.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")


def patch_service() -> None:
    path = ROOT / "Services" / "MimiAtticVisualService.cs"
    text = path.read_text(encoding="utf-8")

    text = text.replace(
        "/// Alpha28 .5.9 true-Stardew MiMi Attic rebuild with test access.",
        "/// Alpha28 .5.10 MiMi Attic living-lore interaction pass with test access.",
    )
    text = text.replace(
        "/// Furniture instances for the five locked zones with no room-sized visual overlay, keeps inspect points, and preserves the",
        "/// Furniture instances for the five locked zones with no room-sized visual overlay. Inspect points now reveal",
    )
    text = text.replace(
        "/// future 17:30 / 6-heart TV eligibility hook.",
        "/// layered character/environmental lore by friendship, time, and repeat inspection while preserving the future 17:30 / 6-heart TV eligibility hook.",
    )

    field_anchor = "    private GameLocation? DecorAppliedLocation;\n"
    if "InspectCountsToday" not in text:
        if field_anchor not in text:
            raise RuntimeError("Could not find inspect-state field anchor")
        text = text.replace(
            field_anchor,
            field_anchor
            + "    private readonly Dictionary<string, int> InspectCountsToday = new(StringComparer.OrdinalIgnoreCase);\n"
            + "    private int InspectMemoryDay = -1;\n",
            1,
        )

    old_block = '''        AtticLayout layout = GetLayout(Game1.currentLocation);
        Point actionTile = GetActionTile();

        string? key = null;
        if (Touches(actionTile, layout.DeskLeft) || Touches(actionTile, layout.DeskRight) || Touches(actionTile, layout.Notes))
            key = "mimi.attic.inspect.desk";
        else if (Touches(actionTile, layout.Television) || Touches(actionTile, layout.TvChair))
            key = "mimi.attic.inspect.tv";
        else if (Touches(actionTile, layout.ChaChaCushion) || Touches(actionTile, layout.Prototype))
            key = "mimi.attic.inspect.chacha";

        if (key is null)
            return;

        this.Helper.Input.Suppress(e.Button);
        Game1.drawObjectDialogue(this.Helper.Translation.Get(key).ToString());
'''

    new_block = '''        AtticLayout layout = GetLayout(Game1.currentLocation);
        Point actionTile = GetActionTile();

        string? target = null;
        if (Touches(actionTile, layout.DeskLeft) || Touches(actionTile, layout.DeskRight) || Touches(actionTile, layout.Notes))
            target = "desk";
        else if (Touches(actionTile, layout.Television) || Touches(actionTile, layout.TvChair))
            target = "tv";
        else if (Touches(actionTile, layout.ChaChaCushion) || Touches(actionTile, layout.Prototype))
            target = "chacha";
        else if (Touches(actionTile, layout.Bed) || Touches(actionTile, layout.Bedside) || Touches(actionTile, layout.Dresser))
            target = "personal";

        if (target is null)
            return;

        string key = this.ResolveInspectKey(target);
        this.Helper.Input.Suppress(e.Button);
        Game1.drawObjectDialogue(this.Helper.Translation.Get(key).ToString());
'''

    if old_block in text:
        text = text.replace(old_block, new_block, 1)
    elif "ResolveInspectKey(target)" not in text:
        raise RuntimeError("Could not find the old inspect interaction block")

    method_anchor = "    /// <summary>\n    /// Still only an eligibility hook"
    if "private string ResolveInspectKey" not in text:
        methods = '''    private string ResolveInspectKey(string target)
    {
        this.ResetInspectMemoryIfNeeded();

        int hearts = GetMimiHeartLevel();
        int seen = this.InspectCountsToday.TryGetValue(target, out int count) ? count : 0;
        this.InspectCountsToday[target] = seen + 1;

        return target switch
        {
            "desk" when hearts >= 8 && seen >= 1 => "mimi.attic.inspect.desk.deep",
            "desk" when hearts >= 4 && seen >= 1 => "mimi.attic.inspect.desk.personal",
            "desk" when seen == 0 => "mimi.attic.inspect.desk.first",
            "desk" => "mimi.attic.inspect.desk.repeat",

            "tv" when hearts >= SecretTvHeartRequirement && Game1.timeOfDay >= SecretTvTime => "mimi.attic.inspect.tv.evening",
            "tv" when hearts >= SecretTvHeartRequirement && seen >= 1 => "mimi.attic.inspect.tv.secret",
            "tv" when seen == 0 => "mimi.attic.inspect.tv.first",
            "tv" => "mimi.attic.inspect.tv.repeat",

            "chacha" when hearts >= 8 && seen >= 1 => "mimi.attic.inspect.chacha.prototype",
            "chacha" when this.Save.Data.ChaChaLoaned => "mimi.attic.inspect.chacha.away",
            "chacha" when seen == 0 => "mimi.attic.inspect.chacha.first",
            "chacha" => "mimi.attic.inspect.chacha.repeat",

            "personal" when Game1.timeOfDay >= 2200 => "mimi.attic.inspect.personal.late",
            "personal" when seen == 0 => "mimi.attic.inspect.personal.first",
            "personal" => "mimi.attic.inspect.personal.repeat",

            _ => "mimi.attic.inspect.desk.repeat",
        };
    }

    private void ResetInspectMemoryIfNeeded()
    {
        int day = (int)Game1.stats.DaysPlayed;
        if (this.InspectMemoryDay == day)
            return;

        this.InspectMemoryDay = day;
        this.InspectCountsToday.Clear();
    }

    private static int GetMimiHeartLevel()
    {
        if (!Game1.player.friendshipData.TryGetValue(MimiMysteryTownService.NpcId, out Friendship? friendship) || friendship is null)
            return 0;

        return Math.Clamp(friendship.Points / 250, 0, 10);
    }

'''
        if method_anchor not in text:
            raise RuntimeError("Could not find TV eligibility method anchor")
        text = text.replace(method_anchor, methods + method_anchor, 1)

    layout_old = '''            // ChaCha / future upgrade corner on the lower-right.
            ChaChaCushion: P(17, 10),
            Prototype: P(16, 9)
        );
'''
    layout_new = '''            // ChaCha / future upgrade corner on the lower-right.
            ChaChaCushion: P(17, 10),
            Prototype: P(16, 9),

            // Personal corner. These are environmental-storytelling inspect anchors only.
            Bed: P(15, 4),
            Bedside: P(14, 5),
            Dresser: P(19, 4)
        );
'''
    if layout_old in text:
        text = text.replace(layout_old, layout_new, 1)
    elif "Bedside: P(14, 5)" not in text:
        raise RuntimeError("Could not extend attic layout points")

    record_old = '''        Point TvChair,
        Point ChaChaCushion,
        Point Prototype
    );
'''
    record_new = '''        Point TvChair,
        Point ChaChaCushion,
        Point Prototype,
        Point Bed,
        Point Bedside,
        Point Dresser
    );
'''
    if record_old in text:
        text = text.replace(record_old, record_new, 1)
    elif "Point Dresser" not in text:
        raise RuntimeError("Could not extend AtticLayout record")

    required = [
        "ResolveInspectKey(target)",
        "InspectCountsToday",
        "GetMimiHeartLevel()",
        "mimi.attic.inspect.tv.evening",
        "mimi.attic.inspect.chacha.prototype",
        "mimi.attic.inspect.personal.late",
        "IsSecretTvRoutineEligible()",
    ]
    for token in required:
        if token not in text:
            raise RuntimeError(f"Missing service token after patch: {token}")

    if "mimi_attic_room_frame.png" in text or "DrawRoomFrame" in text:
        raise RuntimeError("The removed room overlay must not return in .5.10")

    path.write_text(text, encoding="utf-8")


def patch_i18n() -> None:
    en = {
        "mimi.attic.inspect.desk.first": "Three notebooks are open across MiMi's desk: scrap resonance, ChaCha calibration, and a grocery list that somehow has more corrections than the research notes.",
        "mimi.attic.inspect.desk.repeat": "A loose Cardboard Scrap is being used as a bookmark. In the margin: 'If it hums, measure it. If it bites, ask ChaCha why.'",
        "mimi.attic.inspect.desk.personal": "Between the diagrams is a tiny list: tea, batteries, ChaCha treats, remember to sleep. The last item has been crossed out twice.",
        "mimi.attic.inspect.desk.deep": "One page is labeled 'Farmer'. It tracks scrap resonance, combat habits, and several worried notes. The last line reads: 'Still reckless. Still alive. Good.'",
        "mimi.attic.inspect.tv.first": "The TV nook is suspiciously comfortable. A blanket, two snack bowls, and a romance-drama schedule are arranged with the precision of laboratory equipment.",
        "mimi.attic.inspect.tv.repeat": "A folded page lists character pairings with arrows, question marks, and one furious 'NO, ABSOLUTELY NOT' written across the bottom.",
        "mimi.attic.inspect.tv.secret": "One time slot is circled over and over: 17:30. Beside it, MiMi wrote 'private research'... then added 'technically emotions are research.'",
        "mimi.attic.inspect.tv.evening": "The remote is warm and a drama is paused mid-confession. Someone left in a hurry, but carefully covered the snack bowl first.",
        "mimi.attic.inspect.chacha.first": "ChaCha's cushion has tiny brackets, a dust jar, and three adjustment knobs. Apparently maximum comfort requires engineering.",
        "mimi.attic.inspect.chacha.repeat": "A tiny maintenance card reads: 'Cushion tension: perfect. Snack access: unacceptable. MiMi refuses to revise this.'",
        "mimi.attic.inspect.chacha.away": "The cushion is empty while ChaCha travels with you. A note is tucked underneath: 'Bring him back in one piece. Preferably with fewer new bad habits.'",
        "mimi.attic.inspect.chacha.prototype": "Under the cushion is a prototype sketch linking ChaCha's perch to Magic Dust. The final box is heavily underlined: 'NOT READY. Do not let him press anything.'",
        "mimi.attic.inspect.personal.first": "The bed is a little messy, the dresser is overfull, and a mug sits where a bedside lamp would have been safer. MiMi actually lives here, not just researches here.",
        "mimi.attic.inspect.personal.repeat": "A spare blanket is folded badly but carefully. One corner has several tiny stitch repairs, all in slightly different thread colors.",
        "mimi.attic.inspect.personal.late": "At this hour the room feels quieter. The research corner is dark, but the bedside mug still smells faintly of tea.",
    }

    vi = {
        "mimi.attic.inspect.desk.first": "Trên bàn MiMi đang mở cùng lúc ba quyển sổ: cộng hưởng Mảnh Bìa, hiệu chỉnh ChaCha, và một danh sách đi chợ bị sửa còn nhiều hơn cả ghi chú nghiên cứu.",
        "mimi.attic.inspect.desk.repeat": "Một mảnh Cardboard Scrap đang bị dùng làm dấu trang. Ngoài lề có ghi: 'Nếu nó rung thì đo. Nếu nó cắn thì hỏi ChaCha tại sao.'",
        "mimi.attic.inspect.desk.personal": "Kẹp giữa đống sơ đồ là một danh sách nhỏ: trà, pin, đồ ăn cho ChaCha, nhớ đi ngủ. Dòng cuối đã bị gạch đi hai lần.",
        "mimi.attic.inspect.desk.deep": "Một trang được đề tên 'Farmer'. Bên dưới là số liệu cộng hưởng, thói quen chiến đấu và khá nhiều ghi chú đầy lo lắng. Dòng cuối: 'Vẫn liều. Vẫn sống. Tốt.'",
        "mimi.attic.inspect.tv.first": "Góc TV thoải mái một cách đáng ngờ. Chăn, hai bát đồ ăn vặt và lịch phim tình cảm được xếp ngay ngắn chẳng khác gì dụng cụ thí nghiệm.",
        "mimi.attic.inspect.tv.repeat": "Một tờ giấy gấp ghi kín các cặp nhân vật, mũi tên và dấu hỏi. Cuối trang có một dòng viết thật to: 'KHÔNG. TUYỆT ĐỐI KHÔNG.'",
        "mimi.attic.inspect.tv.secret": "Một khung giờ bị khoanh đi khoanh lại: 17:30. Bên cạnh MiMi ghi 'nghiên cứu riêng'... rồi chèn thêm: 'xét cho cùng cảm xúc cũng là nghiên cứu.'",
        "mimi.attic.inspect.tv.evening": "Remote vẫn còn ấm và bộ phim đang dừng đúng giữa một cảnh tỏ tình. Ai đó rời đi rất vội, nhưng vẫn nhớ đậy bát đồ ăn vặt trước.",
        "mimi.attic.inspect.chacha.first": "Đệm của ChaCha có giá đỡ tí hon, một lọ Bụi Ma Thuật và ba núm chỉnh. Xem ra độ thoải mái tối đa cũng cần kỹ thuật.",
        "mimi.attic.inspect.chacha.repeat": "Một tấm thẻ bảo trì tí hon ghi: 'Độ căng đệm: hoàn hảo. Khả năng tiếp cận đồ ăn: không thể chấp nhận. MiMi từ chối sửa.'",
        "mimi.attic.inspect.chacha.away": "Chiếc đệm đang trống khi ChaCha đi cùng bạn. Bên dưới có mẩu giấy: 'Mang cậu ta về nguyên vẹn. Tốt nhất là đừng kèm thêm thói hư mới.'",
        "mimi.attic.inspect.chacha.prototype": "Dưới đệm là bản phác thảo nguyên mẫu nối chỗ nằm của ChaCha với Bụi Ma Thuật. Ô cuối bị gạch chân rất đậm: 'CHƯA SẴN SÀNG. Đừng để cậu ta bấm bất cứ thứ gì.'",
        "mimi.attic.inspect.personal.first": "Giường hơi bừa, tủ đồ chật cứng và một chiếc cốc được đặt ở vị trí mà đáng lẽ đèn ngủ sẽ an toàn hơn. MiMi thật sự sống ở đây, chứ không chỉ nghiên cứu ở đây.",
        "mimi.attic.inspect.personal.repeat": "Một chiếc chăn dự phòng được gấp hơi vụng nhưng khá cẩn thận. Một góc có vài đường vá nhỏ, mỗi đường lại dùng một màu chỉ khác nhau.",
        "mimi.attic.inspect.personal.late": "Giờ này căn phòng yên hẳn. Góc nghiên cứu đã tối, nhưng chiếc cốc cạnh giường vẫn còn phảng phất mùi trà.",
    }

    for filename, additions in [("default.json", en), ("vi.json", vi)]:
        path = ROOT / "i18n" / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        data.update(additions)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for p in [ROOT / "manifest.json", ROOT / "Cardcha.csproj", ROOT / "Directory.Build.targets"]:
        replace_version(p)

    patch_service()
    patch_i18n()
    print(f"alpha28 0645 MiMi Attic living lore prepared: {NEW_VERSION}")


if __name__ == "__main__":
    main()

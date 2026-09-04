from pathlib import Path
import json

ROOT = Path("src/Cardcha")
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.10"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.11"


def replace_version(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if NEW_VERSION in text:
        return
    if OLD_VERSION not in text:
        raise RuntimeError(f"Expected {OLD_VERSION} in {path}")
    path.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")


def patch_home_service() -> None:
    path = ROOT / "Services" / "MimiHomeService.cs"
    text = path.read_text(encoding="utf-8")

    text = text.replace(
        "/// Alpha.27 home/schedule layer for MiMi.",
        "/// Alpha28 .5.11 home/schedule layer for MiMi, including her unlocked 17:30 secret-TV routine.",
        1,
    )

    constants_anchor = "    private const int WorkEnd = 1700;\n"
    constants = (
        constants_anchor
        + "    private const int SecretTvHeartRequirement = 6;\n"
        + "    private const int SecretTvStart = 1730;\n"
        + "    private const int SecretTvEnd = 2200;\n"
        + "    private static readonly Point SecretTvWatchTile = new(6, 10);\n"
        + "    private static readonly Point SecretLateHomeTile = new(13, 7);\n"
    )
    if "SecretTvWatchTile" not in text:
        if constants_anchor not in text:
            raise RuntimeError("Could not find HomeService constants anchor")
        text = text.replace(constants_anchor, constants, 1)

    old_attic_button = '''        if (location.NameOrUniqueName.Equals(AtticLocationName, StringComparison.OrdinalIgnoreCase))
        {
            Point stair = this.ResolveAtticStairTile(location);
            if (!PlayerIsNear(stair))
                return;

            this.Helper.Input.Suppress(e.Button);
            GameLocation? wizard = Game1.getLocationFromName("WizardHouse");
            Point target = wizard is null ? new Point(4, 6) : this.ResolveWizardStairTile(wizard);
            Point landing = wizard is null ? new Point(target.X, target.Y + 1) : ResolveWizardLandingTile(wizard, target);
            Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);
        }
'''
    new_attic_button = '''        if (location.NameOrUniqueName.Equals(AtticLocationName, StringComparison.OrdinalIgnoreCase))
        {
            // At 6+ hearts MiMi really spends 17:30-22:00 in the TV nook. Talking to her there
            // gets routine-specific dialogue instead of falling through to the old mystery lines.
            if (this.IsSecretTvRoutineNow())
            {
                NPC? mimi = this.WorldActors.FindMimiActor();
                if (mimi is not null
                    && mimi.currentLocation == location
                    && PlayerIsNearNpc(mimi, 118f))
                {
                    this.Helper.Input.Suppress(e.Button);
                    Game1.drawObjectDialogue(this.T(this.ResolveSecretTvTalkKey()));
                    return;
                }
            }

            Point stair = this.ResolveAtticStairTile(location);
            if (!PlayerIsNear(stair))
                return;

            this.Helper.Input.Suppress(e.Button);
            GameLocation? wizard = Game1.getLocationFromName("WizardHouse");
            Point target = wizard is null ? new Point(4, 6) : this.ResolveWizardStairTile(wizard);
            Point landing = wizard is null ? new Point(target.X, target.Y + 1) : ResolveWizardLandingTile(wizard, target);
            Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);
        }
'''
    if old_attic_button in text:
        text = text.replace(old_attic_button, new_attic_button, 1)
    elif "ResolveSecretTvTalkKey()" not in text:
        raise RuntimeError("Could not patch attic routine interaction")

    old_describe = '        return $"MiMiHome=Attic({attic is not null}) | AtticAccess={this.GetMimiHearts()}/{AtticAccessHearts} hearts | WizardStair={wizardStair.X},{wizardStair.Y} | WorkRoute={route} | WorkHours=11:00-17:00";\n'
    new_describe = '        string secretTv = this.IsSecretTvRoutineNow() ? "ACTIVE" : this.IsSecretTvRoutineUnlocked() ? "unlocked" : "locked";\n        return $"MiMiHome=Attic({attic is not null}) | AtticAccess={this.GetMimiHearts()}/{AtticAccessHearts} hearts | WizardStair={wizardStair.X},{wizardStair.Y} | WorkRoute={route} | WorkHours=11:00-17:00 | SecretTV={secretTv} 17:30-22:00";\n'
    if old_describe in text:
        text = text.replace(old_describe, new_describe, 1)
    elif "SecretTV={secretTv}" not in text:
        raise RuntimeError("Could not patch HomeService Describe")

    old_home = '''            Point home = FindClearTileNear(attic, preferUpperHalf: true);
            PlaceMimi(mimi, attic, home, 2);
            return;
'''
    new_home = '''            // The secret TV routine is friendship-gated and only owns the evening window.
            // We resolve against the real furniture collision so a future decor nudge can't strand MiMi.
            if (this.IsSecretTvRoutineNow())
            {
                Point tv = FindClearTileNear(attic, SecretTvWatchTile);
                PlaceMimi(mimi, attic, tv, 0); // face north toward the TV
                return;
            }

            // After the show window, high-friendship MiMi winds down by her personal corner.
            // Lower friendship preserves the pre-0646 generic home placement exactly.
            if (this.IsSecretTvRoutineUnlocked() && Game1.timeOfDay >= SecretTvEnd)
            {
                Point lateHome = FindClearTileNear(attic, SecretLateHomeTile);
                PlaceMimi(mimi, attic, lateHome, 1);
                return;
            }

            Point home = FindClearTileNear(attic, preferUpperHalf: true);
            PlaceMimi(mimi, attic, home, 2);
            return;
'''
    if old_home in text:
        text = text.replace(old_home, new_home, 1)
    elif "Point tv = FindClearTileNear(attic, SecretTvWatchTile);" not in text:
        raise RuntimeError("Could not patch off-hours home routine")

    old_place = '''        if (mimi.currentLocation == target && !mimi.isInvisible.Value)
        {
            this.WorldActors.ConfigureMimiActor(mimi, broom: false, visible: true);
            mimi.displayName = "MiMi";
            mimi.hideShadow.Value = false;
            return;
        }

        this.WorldActors.MoveMimiActor(mimi, target, world, facing, broom: false, visible: true);
'''
    new_place = '''        if (mimi.currentLocation == target && !mimi.isInvisible.Value)
        {
            int currentX = (int)(mimi.Position.X / 64f);
            int currentY = (int)(mimi.Position.Y / 64f);
            if (currentX == tile.X && currentY == tile.Y)
            {
                this.WorldActors.ConfigureMimiActor(mimi, broom: false, visible: true);
                mimi.faceDirection(facing);
                mimi.displayName = "MiMi";
                mimi.hideShadow.Value = false;
                return;
            }
        }

        // A same-location move is intentional here. Before .5.11 PlaceMimi returned early whenever
        // MiMi was already in the attic, which meant a timed home routine could never reposition her.
        this.WorldActors.MoveMimiActor(mimi, target, world, facing, broom: false, visible: true);
'''
    if old_place in text:
        text = text.replace(old_place, new_place, 1)
    elif "A same-location move is intentional here" not in text:
        raise RuntimeError("Could not patch same-location MiMi repositioning")

    helper_anchor = "    private int GetMimiHearts()\n"
    helpers = '''    private bool IsSecretTvRoutineUnlocked()
        => this.GetMimiHearts() >= SecretTvHeartRequirement;

    private bool IsSecretTvRoutineNow()
        => Context.IsWorldReady
           && this.IsSecretTvRoutineUnlocked()
           && Game1.timeOfDay >= SecretTvStart
           && Game1.timeOfDay < SecretTvEnd;

    private string ResolveSecretTvTalkKey()
    {
        if (this.Save.Data.ChaChaLoaned)
            return "mimi.attic.routine.tv.talk.chacha-away";
        if (Game1.timeOfDay >= 2000)
            return "mimi.attic.routine.tv.talk.late";
        return "mimi.attic.routine.tv.talk.early";
    }

    private static bool PlayerIsNearNpc(NPC npc, float distance)
    {
        Vector2 npcCenter = npc.Position + new Vector2(32f, 32f);
        Vector2 playerCenter = Game1.player.Position + new Vector2(32f, 32f);
        return Vector2.DistanceSquared(npcCenter, playerCenter) <= distance * distance;
    }

'''
    if "private bool IsSecretTvRoutineUnlocked()" not in text:
        if helper_anchor not in text:
            raise RuntimeError("Could not find GetMimiHearts helper anchor")
        text = text.replace(helper_anchor, helpers + helper_anchor, 1)

    required = [
        "SecretTvHeartRequirement = 6",
        "SecretTvStart = 1730",
        "SecretTvEnd = 2200",
        "SecretTvWatchTile = new(6, 10)",
        "IsSecretTvRoutineNow()",
        "ResolveSecretTvTalkKey()",
        "PlayerIsNearNpc(mimi, 118f)",
        "Point tv = FindClearTileNear(attic, SecretTvWatchTile)",
        "mimi.faceDirection(facing)",
        "A same-location move is intentional here",
    ]
    for token in required:
        if token not in text:
            raise RuntimeError(f"Missing HomeService token after patch: {token}")

    path.write_text(text, encoding="utf-8")


def patch_attic_visual_service() -> None:
    path = ROOT / "Services" / "MimiAtticVisualService.cs"
    text = path.read_text(encoding="utf-8")

    text = text.replace(
        "/// Alpha28 .5.10 MiMi Attic living-lore interaction pass with test access.",
        "/// Alpha28 .5.11 MiMi Attic living-lore + real 17:30 secret-TV routine support.",
        1,
    )
    text = text.replace(
        "/// layered character/environmental lore by friendship, time, and repeat inspection while preserving the future 17:30 / 6-heart TV eligibility hook.",
        "/// layered character/environmental lore by friendship, time, and repeat inspection; the 17:30 / 6-heart TV hook is now a real home routine.",
        1,
    )

    if "SecretTvEndTime" not in text:
        text = text.replace(
            "    private const int SecretTvTime = 1730;\n",
            "    private const int SecretTvTime = 1730;\n    private const int SecretTvEndTime = 2200;\n",
            1,
        )

    old_tv_switch = '''            "tv" when hearts >= SecretTvHeartRequirement && Game1.timeOfDay >= SecretTvTime => "mimi.attic.inspect.tv.evening",
            "tv" when hearts >= SecretTvHeartRequirement && seen >= 1 => "mimi.attic.inspect.tv.secret",
'''
    new_tv_switch = '''            "tv" when this.IsSecretTvRoutineEligible() => "mimi.attic.inspect.tv.routine",
            "tv" when hearts >= SecretTvHeartRequirement && Game1.timeOfDay >= SecretTvEndTime => "mimi.attic.inspect.tv.after",
            "tv" when hearts >= SecretTvHeartRequirement && seen >= 1 => "mimi.attic.inspect.tv.secret",
'''
    if old_tv_switch in text:
        text = text.replace(old_tv_switch, new_tv_switch, 1)
    elif "mimi.attic.inspect.tv.routine" not in text:
        raise RuntimeError("Could not patch routine-aware TV inspect switch")

    old_comment = '''    /// <summary>
    /// Still only an eligibility hook in alpha.27.0.7.1. The actual private TV routine remains
    /// intentionally out of scope until the true Stardew attic passes in-game layout acceptance.
    /// </summary>
'''
    new_comment = '''    /// <summary>
    /// Shared eligibility rule for the real .5.11 private-TV routine window.
    /// MimiHomeService owns physical placement; this service mirrors the gate for inspect text.
    /// </summary>
'''
    if old_comment in text:
        text = text.replace(old_comment, new_comment, 1)

    old_elig = '''        if (!Context.IsWorldReady || Game1.timeOfDay < SecretTvTime)
            return false;
'''
    new_elig = '''        if (!Context.IsWorldReady
            || Game1.timeOfDay < SecretTvTime
            || Game1.timeOfDay >= SecretTvEndTime)
        {
            return false;
        }
'''
    if old_elig in text:
        text = text.replace(old_elig, new_elig, 1)
    elif "Game1.timeOfDay >= SecretTvEndTime" not in text:
        raise RuntimeError("Could not bound TV eligibility to 22:00")

    required = [
        "SecretTvEndTime = 2200",
        "this.IsSecretTvRoutineEligible() => \"mimi.attic.inspect.tv.routine\"",
        "mimi.attic.inspect.tv.after",
        "Game1.timeOfDay >= SecretTvEndTime",
    ]
    for token in required:
        if token not in text:
            raise RuntimeError(f"Missing attic visual token after patch: {token}")

    path.write_text(text, encoding="utf-8")


def patch_i18n() -> None:
    en = {
        "mimi.attic.inspect.tv.routine": "MiMi has claimed the TV nook with a blanket and both snack bowls. The drama is running, and she is watching with the concentration usually reserved for unstable magic.",
        "mimi.attic.inspect.tv.after": "The TV is dark now. The blanket has been folded back onto the couch, but one snack bowl is mysteriously empty.",
        "mimi.attic.routine.tv.talk.early": "MiMi: Shh. This is private research. My current hypothesis is that those two should have confessed three episodes ago.",
        "mimi.attic.routine.tv.talk.late": "MiMi: One more episode. That's not procrastinating if I call it a controlled variable.",
        "mimi.attic.routine.tv.talk.chacha-away": "MiMi: Don't tell ChaCha I watched this without him. He gets weirdly invested in the villains.",
    }
    vi = {
        "mimi.attic.inspect.tv.routine": "MiMi đã chiếm trọn góc TV với chăn và cả hai bát đồ ăn vặt. Phim đang chạy, còn cô ấy thì tập trung chẳng kém lúc xử lý một nguồn ma lực bất ổn.",
        "mimi.attic.inspect.tv.after": "TV đã tắt. Chiếc chăn được gấp lại trên ghế, nhưng một trong hai bát đồ ăn vặt đã trống một cách đầy bí ẩn.",
        "mimi.attic.routine.tv.talk.early": "MiMi: Suỵt. Đây là nghiên cứu riêng. Giả thuyết hiện tại của tui là hai người đó đáng lẽ phải tỏ tình từ ba tập trước rồi.",
        "mimi.attic.routine.tv.talk.late": "MiMi: Thêm một tập nữa thôi. Nếu tui gọi nó là biến số kiểm soát thì không tính là trì hoãn đâu.",
        "mimi.attic.routine.tv.talk.chacha-away": "MiMi: Đừng kể ChaCha là tui xem tập này mà không có cậu ta nha. Cậu ta nhập tâm với phe phản diện một cách kỳ lạ lắm.",
    }

    for filename, additions in [("default.json", en), ("vi.json", vi)]:
        path = ROOT / "i18n" / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        data.update(additions)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for p in [ROOT / "manifest.json", ROOT / "Cardcha.csproj", ROOT / "Directory.Build.targets"]:
        replace_version(p)
    patch_home_service()
    patch_attic_visual_service()
    patch_i18n()
    print(f"alpha28 0646 MiMi secret TV routine prepared: {NEW_VERSION}")


if __name__ == "__main__":
    main()

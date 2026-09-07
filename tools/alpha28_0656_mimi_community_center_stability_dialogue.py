from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.22"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.23"
BRANCH = "cardcha-alpha28-0656-mimi-community-center-stability-dialogue"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"0656 {label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def set_version() -> None:
    manifest = CARDCHA / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("Version") != OLD_VERSION:
        raise RuntimeError(f"0656 expected manifest {OLD_VERSION}, got {data.get('Version')}")
    data["Version"] = NEW_VERSION
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for rel in ["Cardcha.csproj", "Directory.Build.targets"]:
        path = CARDCHA / rel
        text = path.read_text(encoding="utf-8")
        if OLD_VERSION not in text:
            raise RuntimeError(f"0656 version anchor missing in {rel}")
        path.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")

    mod_entry = CARDCHA / "ModEntry.cs"
    text = mod_entry.read_text(encoding="utf-8")
    old_log = f"Cardcha! {OLD_VERSION} MIMI NATIVE PROFILE + STAIR ANCHOR TEST"
    if old_log in text:
        text = text.replace(old_log, f"Cardcha! {NEW_VERSION} MIMI COMMUNITY CENTER STABILITY TEST", 1)
    mod_entry.write_text(text, encoding="utf-8")


def stabilize_community_center_work_tile() -> None:
    path = CARDCHA / "Services" / "MimiHomeService.cs"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "    private Point? CachedWizardStairTile;\n    private Point? CachedAtticStairTile;",
        "    private Point? CachedWizardStairTile;\n    private Point? CachedAtticStairTile;\n    private Point? CachedCommunityCenterWorkTile;",
        "Community Center cached field",
    )

    # Save/day/title resets. Resolve once per day/save session, never once per tick.
    save_anchor = "    public void OnSaveLoaded()\n    {\n        this.CachedWizardStairTile = null;\n        this.CachedAtticStairTile = null;"
    save_new = save_anchor + "\n        this.CachedCommunityCenterWorkTile = null;"
    text = replace_once(text, save_anchor, save_new, "save reset")

    day_anchor = "    public void OnDayStarted()\n    {\n        this.CachedWizardStairTile = null;\n        this.CachedAtticStairTile = null;"
    day_new = day_anchor + "\n        this.CachedCommunityCenterWorkTile = null;"
    text = replace_once(text, day_anchor, day_new, "day reset")

    title_anchor = "    public void OnReturnedToTitle()\n    {\n        this.CachedWizardStairTile = null;\n        this.CachedAtticStairTile = null;"
    title_new = title_anchor + "\n        this.CachedCommunityCenterWorkTile = null;"
    text = replace_once(text, title_anchor, title_new, "title reset")

    old_work = '''        Point work = FindClearTileNear(center, preferUpperHalf: false);\n        PlaceMimi(mimi, center, work, 2);'''
    new_work = '''        // 0656: resolve this once, then keep one stable work anchor. Re-running the clear-tile\n        // search every tick can see MiMi herself as an occupied tile, choose the neighboring tile,\n        // then choose the original tile on the next tick. That creates the visible two-position\n        // "ghost/clone" flicker reported in the restored Community Center.\n        Point work = this.CachedCommunityCenterWorkTile\n            ??= FindClearTileNear(center, preferUpperHalf: false);\n        PlaceMimi(mimi, center, work, 2);'''
    text = replace_once(text, old_work, new_work, "stable Community Center work anchor")

    # Surface the cached work tile in the existing status string for real-game verification.
    old_diag = '        string actorTile = actor is null ? "<missing>" : $"{(int)(actor.Position.X / 64f)},{(int)(actor.Position.Y / 64f)}@{actor.currentLocation?.NameOrUniqueName}";\n        Point wanderTile = new((int)(this.HomeWanderTarget.X / 64f), (int)(this.HomeWanderTarget.Y / 64f));\n        return $"MiMiHome=Attic({attic is not null}) | AtticAccess={this.GetMimiHearts()}/{AtticAccessHearts} hearts | WizardStair={wizardStair.X},{wizardStair.Y} | WorkRoute={route}'
    new_diag = '        string actorTile = actor is null ? "<missing>" : $"{(int)(actor.Position.X / 64f)},{(int)(actor.Position.Y / 64f)}@{actor.currentLocation?.NameOrUniqueName}";\n        string ccWork = this.CachedCommunityCenterWorkTile is Point cc ? $"{cc.X},{cc.Y}" : "<unset>";\n        Point wanderTile = new((int)(this.HomeWanderTarget.X / 64f), (int)(this.HomeWanderTarget.Y / 64f));\n        return $"MiMiHome=Attic({attic is not null}) | AtticAccess={this.GetMimiHearts()}/{AtticAccessHearts} hearts | WizardStair={wizardStair.X},{wizardStair.Y} | CCWork={ccWork} | WorkRoute={route}'
    text = replace_once(text, old_diag, new_diag, "Community Center status diagnostic")

    path.write_text(text, encoding="utf-8")


def fix_social_dialogue_logic() -> None:
    path = CARDCHA / "Services" / "MimiSocialService.cs"
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "    private bool LastUnlocked;\n    private bool CacheInitialized;",
        "    private bool LastUnlocked;\n    private bool CacheInitialized;\n    private bool LastCommunityCenterRoute;\n    private bool RouteCacheInitialized;",
        "social route cache fields",
    )

    text = replace_once(
        text,
        '                data["Introduction"] = this.T("mimi.social.introduction");',
        '                data["Introduction"] = this.IsRestoredCommunityCenterRoute()\n                    ? this.T("mimi.social.community-center")\n                    : this.T("mimi.social.introduction");',
        "route-aware Introduction",
    )

    text = replace_once(
        text,
        "    public void OnSaveLoaded()\n    {\n        this.LastUnlocked = false;\n        this.CacheInitialized = false;",
        "    public void OnSaveLoaded()\n    {\n        this.LastUnlocked = false;\n        this.CacheInitialized = false;\n        this.LastCommunityCenterRoute = false;\n        this.RouteCacheInitialized = false;",
        "social save reset",
    )

    text = replace_once(
        text,
        "    public void OnReturnedToTitle()\n    {\n        this.LastUnlocked = false;\n        this.CacheInitialized = false;\n    }",
        "    public void OnReturnedToTitle()\n    {\n        this.LastUnlocked = false;\n        this.CacheInitialized = false;\n        this.LastCommunityCenterRoute = false;\n        this.RouteCacheInitialized = false;\n    }",
        "social title reset",
    )

    old_refresh = '''        bool unlocked = this.Save.Data.MimiMeetupCompleted;\n        bool changed = !this.CacheInitialized || unlocked != this.LastUnlocked;\n        this.CacheInitialized = true;\n        this.LastUnlocked = unlocked;\n\n        if (unlocked)\n            this.EnsureFriendshipEntry();\n\n        if (!forceRefresh && !changed)\n            return;'''
    new_refresh = '''        bool unlocked = this.Save.Data.MimiMeetupCompleted;\n        bool changed = !this.CacheInitialized || unlocked != this.LastUnlocked;\n        this.CacheInitialized = true;\n        this.LastUnlocked = unlocked;\n\n        bool communityCenterRoute = this.IsRestoredCommunityCenterRoute();\n        bool routeChanged = !this.RouteCacheInitialized || communityCenterRoute != this.LastCommunityCenterRoute;\n        this.RouteCacheInitialized = true;\n        this.LastCommunityCenterRoute = communityCenterRoute;\n\n        if (unlocked)\n            this.EnsureFriendshipEntry();\n\n        if (!forceRefresh && !changed && !routeChanged)\n            return;'''
    text = replace_once(text, old_refresh, new_refresh, "route cache refresh")

    helper_anchor = '''    private string BuildGiftTasteRow()\n    {'''
    helper = '''    private bool IsRestoredCommunityCenterRoute()\n    {\n        if (!Context.IsWorldReady || Game1.MasterPlayer.mailReceived.Contains("JojaMember"))\n            return false;\n        try\n        {\n            return Game1.MasterPlayer.hasCompletedCommunityCenter()\n                || Game1.MasterPlayer.mailReceived.Contains("ccIsComplete");\n        }\n        catch\n        {\n            return Game1.MasterPlayer.mailReceived.Contains("ccIsComplete");\n        }\n    }\n\n    private string BuildGiftTasteRow()\n    {'''
    text = replace_once(text, helper_anchor, helper, "Community Center route helper")

    path.write_text(text, encoding="utf-8")


def update_dialogue_text() -> None:
    default_path = CARDCHA / "i18n" / "default.json"
    default = default_path.read_text(encoding="utf-8")
    old_en = '  "mimi.social.introduction": "So we\'re officially acquainted now. Try not to make it sound too respectable.",'
    new_en = '  "mimi.social.introduction": "There you are again. Ever since that business at the Wizard’s place, weird things seem to keep finding us.",\n  "mimi.social.community-center": "Finally, my stall has a roof over it. At least the cards won’t have to learn how to swim anymore!",'
    default = replace_once(default, old_en, new_en, "English social dialogue")
    default_path.write_text(default, encoding="utf-8")

    vi_path = CARDCHA / "i18n" / "vi.json"
    vi = vi_path.read_text(encoding="utf-8")
    old_vi = '  "mimi.social.introduction": "Vậy là giờ tụi mình chính thức quen nhau rồi. Đừng làm chuyện này nghe đứng đắn quá nha.",'
    new_vi = '  "mimi.social.introduction": "Lại gặp bạn rồi. Từ sau vụ ở nhà Phù thủy, hình như mấy chuyện kỳ quặc cứ tự tìm tới tụi mình ấy nhỉ.",\n  "mimi.social.community-center": "Cuối cùng gian hàng của mình cũng có chỗ trú mưa rồi. Từ nay mấy lá bài khỏi phải học bơi nữa!",'
    vi = replace_once(vi, old_vi, new_vi, "Vietnamese social dialogue")
    vi_path.write_text(vi, encoding="utf-8")


def write_handoff() -> None:
    handoff = ROOT / "handoff" / "ALPHA28_0656_MIMI_COMMUNITY_CENTER_STABILITY_DIALOGUE.md"
    handoff.write_text(f'''# Alpha28 0656 - MiMi Community Center stability + dialogue\n\nBranch: `{BRANCH}`\n\nBuild target: `{NEW_VERSION}`\n\n## In-game evidence\n- In the restored Community Center work route, MiMi visibly flickered between two vertically offset positions, reading as a laggy clone/afterimage.\n- Her first Stardew social dialogue could still say that the farmer and MiMi were “officially acquainted now,” which contradicts the story because the Wizard meetup happened long before this route.\n\n## Root cause / fix\n### Community Center ghost flicker\n`MimiHomeService` was resolving `FindClearTileNear(center, ...)` every update tick. Once MiMi occupied the chosen tile, occupancy checks could reject her own current tile on the next pass and select a neighbor, then select the original again after she moved. That creates a high-frequency two-position ping-pong.\n\n0656 resolves and caches one Community Center work tile per save/day session, then reuses it for the full work routine. `cardcha_mimi_home_status` now exposes `CCWork=x,y` for in-game verification.\n\n### Dialogue continuity\n- Generic `mimi.social.introduction` no longer says the farmer and MiMi just met.\n- On the restored Community Center route, Stardew's `Introduction` entry instead uses `mimi.social.community-center`.\n- VI approved direction: “Cuối cùng gian hàng của mình cũng có chỗ trú mưa rồi. Từ nay mấy lá bài khỏi phải học bơi nữa!”\n- Social dialogue cache now refreshes if the restored Community Center route changes mid-save, not only when MiMi friendship unlocks.\n\n## Regression guard\n- 0655 native 16x32 Gift Log profile pipeline remains unchanged.\n- 0655 WizardHouse stair anchor/art nudge remains unchanged.\n- 0653 strict TMX runtime compatibility fix remains unchanged.\n- No Save schema, progression, Airship, Hunt Run, Boss I, card balance, MiMi attic furniture/layout, HOME/TV/LATE routine, controller profile, or story milestone changes.\n\n## Acceptance pending\n- MiMi should remain in one stable Community Center work position with no clone/ghost flicker.\n- Her Community Center first social line should fit established continuity and mention the newly sheltered stall rather than “officially meeting.”\n''', encoding="utf-8")

    latest = ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md"
    latest.write_text(f'''# Latest Cardcha handoff\n\nCurrent development branch:\n`{BRANCH}`\n\nCurrent build target:\n`{NEW_VERSION}`\n\nRead first:\n- `handoff/ALPHA28_0656_MIMI_COMMUNITY_CENTER_STABILITY_DIALOGUE.md`\n- `handoff/ALPHA28_0655_MIMI_NATIVE_PROFILE_STAIR_ANCHOR_FIX.md`\n- `handoff/ALPHA28_0653_TMX_RUNTIME_COMPAT_FIX.md`\n- `handoff/ALPHA28_0652_VERDANT_VISUAL_PROTOTYPE.md`\n- `handoff/BOSS_CONCEPT_CANON.md`\n\n## Current acceptance state\n- 0656 fixes the Community Center work-anchor ping-pong and route-inappropriate MiMi introduction dialogue; in-game acceptance pending.\n- 0655 native Gift Log profile + sub-tile Wizard stair approach remain included; acceptance depends on current user test.\n- 0653 TMX runtime compatibility repair remains included.\n- Verdant Guardian gameplay + first custom visual overlay remain implemented; visual acceptance pending.\n\n## Locked regression guard\nSave schema 19; Boss Form 10 sec; Boss Energy 1/3; 76/76 active cards; Forest Arcane Gate/collision; Airship route/visual; MiMi HOME/TV/LATE and attic furniture/layout; card canon.\n''', encoding="utf-8")


set_version()
stabilize_community_center_work_tile()
fix_social_dialogue_logic()
update_dialogue_text()
write_handoff()
print("0656 MiMi Community Center stability/dialogue generator complete", NEW_VERSION)

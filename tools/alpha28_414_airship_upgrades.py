from __future__ import annotations

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "src" / "Cardcha"
VERSION = "0.3.0-alpha.28.0.4.14"


def replace_required(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Required marker not found in {path}: {old[:180]!r}")
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def insert_before(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if block.strip() in text:
        return
    if marker not in text:
        raise RuntimeError(f"Insertion marker not found in {path}: {marker!r}")
    path.write_text(text.replace(marker, block + marker, 1), encoding="utf-8")


def patch_version() -> None:
    manifest = MOD / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["Version"] = VERSION
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csproj = MOD / "Cardcha.csproj"
    text = csproj.read_text(encoding="utf-8")
    text = re.sub(r"<Version>[^<]+</Version>", f"<Version>{VERSION}</Version>", text, count=1)
    csproj.write_text(text, encoding="utf-8")

    entry = MOD / "ModEntry.cs"
    text = entry.read_text(encoding="utf-8")
    text = re.sub(
        r"Cardcha! v0\.3\.0-alpha\.28\.0\.4\.\d+ [A-Z0-9 +_-]+ TEST with",
        f"Cardcha! v{VERSION} AIRSHIP UPGRADE FOUNDATION TEST with",
        text,
        count=1,
    )
    text = re.sub(
        r'"Cardcha! v0\.3\.0-alpha\.28\.0\.4\.\d+ [A-Z0-9 +_-]+ TEST"',
        f'"Cardcha! v{VERSION} AIRSHIP UPGRADE FOUNDATION TEST"',
        text,
        count=1,
    )
    entry.write_text(text, encoding="utf-8")


def patch_save_model() -> None:
    path = MOD / "Models" / "SaveData.cs"
    text = path.read_text(encoding="utf-8")
    text = text.replace("public int SchemaVersion { get; set; } = 16;", "public int SchemaVersion { get; set; } = 17;")
    marker = "    public int AirshipTotalFarePaid { get; set; }\n\n"
    block = """    public int AirshipTotalFarePaid { get; set; }

    // alpha.28.0.4.14: persistent Airship infrastructure levels. Gameplay bonuses are not
    // attached yet; this foundation validates Magic Dust economy, UI and persistence first.
    public int AirshipEngineLevel { get; set; }
    public int AirshipNavigationLevel { get; set; }
    public int AirshipHullLevel { get; set; }
    public int AirshipReactorLevel { get; set; }

"""
    if "public int AirshipEngineLevel" not in text:
        if marker not in text:
            raise RuntimeError("SaveData Airship fare marker missing")
        text = text.replace(marker, block, 1)
    path.write_text(text, encoding="utf-8")


def patch_save_service() -> None:
    path = MOD / "Services" / "SaveService.cs"
    text = path.read_text(encoding="utf-8")
    text = text.replace("private const int CurrentSchemaVersion = 16;", "private const int CurrentSchemaVersion = 17;")

    migration_marker = "        if (loadedSchema < CurrentSchemaVersion)\n"
    migration = """        // v17: Airship infrastructure foundation. Existing saves begin with all four
        // subsystems dormant at level 0 and retain their Magic Dust untouched.
        if (loadedSchema < 17)
        {
            this.Data.AirshipEngineLevel = Math.Clamp(this.Data.AirshipEngineLevel, 0, 3);
            this.Data.AirshipNavigationLevel = Math.Clamp(this.Data.AirshipNavigationLevel, 0, 3);
            this.Data.AirshipHullLevel = Math.Clamp(this.Data.AirshipHullLevel, 0, 3);
            this.Data.AirshipReactorLevel = Math.Clamp(this.Data.AirshipReactorLevel, 0, 3);
        }

"""
    if migration.strip() not in text:
        if migration_marker not in text:
            raise RuntimeError("SaveService migration marker missing")
        text = text.replace(migration_marker, migration + migration_marker, 1)

    normalize_marker = "        this.Data.ActiveCardSlotCount = Math.Clamp(this.Data.ActiveCardSlotCount <= 0 ? 2 : this.Data.ActiveCardSlotCount, 2, 5);\n"
    normalize = """        this.Data.AirshipEngineLevel = Math.Clamp(this.Data.AirshipEngineLevel, 0, 3);
        this.Data.AirshipNavigationLevel = Math.Clamp(this.Data.AirshipNavigationLevel, 0, 3);
        this.Data.AirshipHullLevel = Math.Clamp(this.Data.AirshipHullLevel, 0, 3);
        this.Data.AirshipReactorLevel = Math.Clamp(this.Data.AirshipReactorLevel, 0, 3);

"""
    if normalize.strip() not in text:
        if normalize_marker not in text:
            raise RuntimeError("SaveService Normalize marker missing")
        text = text.replace(normalize_marker, normalize + normalize_marker, 1)

    fp_old = """            data.AirshipFlightsTaken,
            data.AirshipTotalFarePaid
        );"""
    fp_new = """            data.AirshipFlightsTaken,
            data.AirshipTotalFarePaid,
            data.AirshipEngineLevel,
            data.AirshipNavigationLevel,
            data.AirshipHullLevel,
            data.AirshipReactorLevel
        );"""
    if fp_new not in text:
        if fp_old not in text:
            raise RuntimeError("SaveService fingerprint Airship marker missing")
        text = text.replace(fp_old, fp_new, 1)

    path.write_text(text, encoding="utf-8")


def patch_mod_entry() -> None:
    path = MOD / "ModEntry.cs"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save);",
        "this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save, this.Controller);",
    )

    registration = '        helper.ConsoleCommands.Add("cardcha_give_scrap", "Give prototype Scrap: cardcha_give_scrap [normal|shiny] [amount]", this.CommandGiveScrap);\n'
    give_dust_registration = '        helper.ConsoleCommands.Add("cardcha_give_dust", "TEST ONLY: give Magic Dust for Airship upgrade testing: cardcha_give_dust [amount]", this.CommandGiveDust);\n'
    if give_dust_registration not in text:
        if registration not in text:
            raise RuntimeError("ModEntry give scrap command registration missing")
        text = text.replace(registration, registration + give_dust_registration, 1)

    marker = "    private void CommandGiveMachine(string command, string[] args)\n"
    method = """    private void CommandGiveDust(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;

        int amount = args.Length >= 1 && int.TryParse(args[0], out int parsed)
            ? Math.Clamp(parsed, 1, 9999)
            : 50;
        this.Save.Data.SuspiciousDust += amount;
        this.Save.Save();
        this.Monitor.Log($"Added {amount} Magic Dust for Airship upgrade TEST. Total={this.Save.Data.SuspiciousDust}.", LogLevel.Info);
    }

"""
    if method.strip() not in text:
        if marker not in text:
            raise RuntimeError("ModEntry CommandGiveMachine marker missing")
        text = text.replace(marker, method + marker, 1)

    path.write_text(text, encoding="utf-8")


def patch_airship_service() -> None:
    path = MOD / "Services" / "AirshipFoundationService.cs"
    text = path.read_text(encoding="utf-8")

    if not text.startswith("using Cardcha.UI;"):
        text = "using Cardcha.UI;\n" + text

    text = text.replace(
        "    private readonly SaveService Save;\n",
        "    private readonly SaveService Save;\n    private readonly ControllerProfileService Controller;\n",
        1,
    )
    text = text.replace(
        "    public AirshipFoundationService(IModHelper helper, IMonitor monitor, SaveService save)\n    {\n        this.Helper = helper;\n        this.Monitor = monitor;\n        this.Save = save;\n    }",
        "    public AirshipFoundationService(IModHelper helper, IMonitor monitor, SaveService save, ControllerProfileService controller)\n    {\n        this.Helper = helper;\n        this.Monitor = monitor;\n        this.Save = save;\n        this.Controller = controller;\n    }",
        1,
    )

    helm_block = """        if (Touches(action, helm) || PlayerIsNear(helm))
        {
            this.Helper.Input.Suppress(e.Button);
            this.HandleRegion1DepartureRequest();
            return;
        }

"""
    upgrade_block = """        if (Touches(action, helm) || PlayerIsNear(helm))
        {
            this.Helper.Input.Suppress(e.Button);
            this.HandleRegion1DepartureRequest();
            return;
        }

        foreach ((AirshipUpgradeSystem system, Point tile) in ResolveDeckUpgradeSockets())
        {
            if (!Touches(action, tile) && !PlayerIsNear(tile))
                continue;

            this.Helper.Input.Suppress(e.Button);
            Game1.playSound("smallSelect");
            Game1.activeClickableMenu = new AirshipUpgradeMenu(this.Save, this.Controller, system);
            return;
        }

"""
    if upgrade_block not in text:
        if helm_block not in text:
            raise RuntimeError("Airship deck helm interaction marker missing")
        text = text.replace(helm_block, upgrade_block, 1)

    resolve_marker = "    private static Point ResolveDeckArrivalTile(GameLocation deck)\n"
    resolve_helpers = """    private static (AirshipUpgradeSystem System, Point Tile)[] ResolveDeckUpgradeSockets()
        => new[]
        {
            (AirshipUpgradeSystem.Engine, new Point(5, 9)),
            (AirshipUpgradeSystem.Navigation, new Point(18, 9)),
            (AirshipUpgradeSystem.Hull, new Point(8, 10)),
            (AirshipUpgradeSystem.Reactor, new Point(15, 10)),
        };

    private int GetAirshipUpgradeLevel(AirshipUpgradeSystem system)
        => system switch
        {
            AirshipUpgradeSystem.Engine => this.Save.Data.AirshipEngineLevel,
            AirshipUpgradeSystem.Navigation => this.Save.Data.AirshipNavigationLevel,
            AirshipUpgradeSystem.Hull => this.Save.Data.AirshipHullLevel,
            AirshipUpgradeSystem.Reactor => this.Save.Data.AirshipReactorLevel,
            _ => 0,
        };

"""
    if resolve_helpers.strip() not in text:
        if resolve_marker not in text:
            raise RuntimeError("Airship ResolveDeckArrivalTile marker missing")
        text = text.replace(resolve_marker, resolve_helpers + resolve_marker, 1)

    old_sockets = """        // Dormant upgrade sockets now look like actual ship infrastructure rather than debug marks.
        Point[] sockets = { new(5, 9), new(18, 9), new(8, 10), new(15, 10) };
        foreach (Point socket in sockets)
        {
            Vector2 s = Game1.GlobalToLocal(Game1.viewport, new Vector2(socket.X * 64f + 32f, socket.Y * 64f + 38f));
            DrawArcaneSigil(batch, s, 28f, new Color(116, 101, 148) * 0.46f, phase * 0.24f);
            DrawCrystalPylon(batch, new Vector2(s.X, s.Y + 18f), 24f, new Color(110, 98, 145) * 0.62f, gold * 0.38f);
        }
"""
    new_sockets = """        // Four real infrastructure sockets. Their persistent level now changes the Bridge visual immediately.
        foreach ((AirshipUpgradeSystem system, Point socket) in ResolveDeckUpgradeSockets())
        {
            Vector2 s = Game1.GlobalToLocal(Game1.viewport, new Vector2(socket.X * 64f + 32f, socket.Y * 64f + 38f));
            DrawUpgradeSocket(batch, s, system, this.GetAirshipUpgradeLevel(system), phase, gold);
        }
"""
    if new_sockets not in text:
        if old_sockets not in text:
            raise RuntimeError("Airship visual socket block missing")
        text = text.replace(old_sockets, new_sockets, 1)

    draw_marker = "    private static void DrawArcaneSigil(SpriteBatch batch, Vector2 center, float radius, Color color, float phase)\n"
    draw_helper = """    private static void DrawUpgradeSocket(
        SpriteBatch batch,
        Vector2 center,
        AirshipUpgradeSystem system,
        int level,
        float phase,
        Color gold)
    {
        level = Math.Clamp(level, 0, AirshipUpgradeMenu.MaxLevel);
        Color systemColor = system switch
        {
            AirshipUpgradeSystem.Engine => new Color(247, 179, 82),
            AirshipUpgradeSystem.Navigation => new Color(92, 207, 232),
            AirshipUpgradeSystem.Hull => new Color(127, 151, 220),
            AirshipUpgradeSystem.Reactor => new Color(205, 113, 232),
            _ => new Color(180, 160, 200),
        };
        float active = level <= 0 ? 0.28f : 0.48f + level * 0.13f;
        DrawArcaneSigil(batch, center, 28f + level * 3f, systemColor * active, phase * (0.22f + level * 0.09f));
        DrawCrystalPylon(
            batch,
            new Vector2(center.X, center.Y + 18f),
            24f + level * 5f,
            systemColor * (0.54f + level * 0.12f),
            gold * (0.34f + level * 0.14f)
        );
        for (int pip = 0; pip < AirshipUpgradeMenu.MaxLevel; pip++)
        {
            int x = (int)center.X - 18 + pip * 18;
            Color pipColor = pip < level ? systemColor * 0.92f : new Color(93, 82, 112) * 0.52f;
            DrawRect(batch, new Rectangle(x, (int)center.Y + 26, 9, 5), pipColor);
        }
        if (level >= 2)
            DrawDiamondRune(batch, new Vector2(center.X, center.Y - 28f - level * 3f), 8f + level * 2f, systemColor * 0.68f);
        if (level >= 3)
            DrawArcaneSparkles(batch, center, 44f, 6, phase * 1.4f, Color.White * 0.48f);
    }

"""
    if draw_helper.strip() not in text:
        if draw_marker not in text:
            raise RuntimeError("Airship DrawArcaneSigil marker missing")
        text = text.replace(draw_marker, draw_helper + draw_marker, 1)

    describe_old = '| CollisionEdits=NONE";'
    describe_new = '| Upgrades=Engine:{this.Save.Data.AirshipEngineLevel}/3,Navigation:{this.Save.Data.AirshipNavigationLevel}/3,Hull:{this.Save.Data.AirshipHullLevel}/3,Reactor:{this.Save.Data.AirshipReactorLevel}/3 | CollisionEdits=NONE";'
    if describe_new not in text:
        if describe_old not in text:
            raise RuntimeError("Airship Describe CollisionEdits marker missing")
        text = text.replace(describe_old, describe_new, 1)

    path.write_text(text, encoding="utf-8")


def patch_localization() -> None:
    en_path = MOD / "i18n" / "default.json"
    vi_path = MOD / "i18n" / "vi.json"
    en = json.loads(en_path.read_text(encoding="utf-8"))
    vi = json.loads(vi_path.read_text(encoding="utf-8"))

    en.update({
        "airship.upgrade.title": "Airship Infrastructure",
        "airship.upgrade.dust": "Magic Dust: {{amount}}",
        "airship.upgrade.test_notice": "TEST COSTS: 5 / 10 / 20. Gameplay bonuses are not enabled yet.",
        "airship.upgrade.level": "Level {{level}} / {{max}}",
        "airship.upgrade.cost": "TEST\n{{cost}} Dust",
        "airship.upgrade.cost.max": "MAX",
        "airship.upgrade.button.upgrade": "Upgrade",
        "airship.upgrade.button.max": "Max Level",
        "airship.upgrade.button.close": "Close",
        "airship.upgrade.status.ready": "Select an Airship system. This build tests spending, persistence, and Bridge visuals.",
        "airship.upgrade.status.max": "That system is already at the current TEST maximum.",
        "airship.upgrade.status.not_enough": "Not enough Magic Dust. Need {{cost}}; you have {{dust}}.",
        "airship.upgrade.status.success": "{{system}} reached Level {{level}} for {{cost}} Magic Dust.",
        "airship.upgrade.system.engine.name": "Aether Engine",
        "airship.upgrade.system.engine.desc": "The propulsion lattice that will eventually govern travel performance and distant routes.",
        "airship.upgrade.system.navigation.name": "Navigation Core",
        "airship.upgrade.system.navigation.desc": "MiMi's arcane route computer. Future upgrades will support safer, farther synchronization.",
        "airship.upgrade.system.hull.name": "Hull & Shield",
        "airship.upgrade.system.hull.desc": "Reinforces the vessel and its warding field. Combat benefits are intentionally not active yet.",
        "airship.upgrade.system.reactor.name": "Arcane Reactor",
        "airship.upgrade.system.reactor.desc": "Feeds Magic Dust resonance into the ship's infrastructure and future high-tier systems.",
    })
    vi.update({
        "airship.upgrade.title": "Hạ Tầng Tàu Bay",
        "airship.upgrade.dust": "Bụi Ma Thuật: {{amount}}",
        "airship.upgrade.test_notice": "GIÁ TEST: 5 / 10 / 20. Chưa kích hoạt chỉ số gameplay.",
        "airship.upgrade.level": "Cấp {{level}} / {{max}}",
        "airship.upgrade.cost": "TEST\n{{cost}} Bụi",
        "airship.upgrade.cost.max": "TỐI ĐA",
        "airship.upgrade.button.upgrade": "Nâng cấp",
        "airship.upgrade.button.max": "Đã tối đa",
        "airship.upgrade.button.close": "Đóng",
        "airship.upgrade.status.ready": "Chọn một hệ thống của Tàu Bay. Bản này test tiêu Bụi, lưu cấp và hiệu ứng trên Bridge.",
        "airship.upgrade.status.max": "Hệ thống này đã đạt cấp TEST tối đa hiện tại.",
        "airship.upgrade.status.not_enough": "Không đủ Bụi Ma Thuật. Cần {{cost}}; bạn đang có {{dust}}.",
        "airship.upgrade.status.success": "{{system}} đã lên Cấp {{level}}, tốn {{cost}} Bụi Ma Thuật.",
        "airship.upgrade.system.engine.name": "Động Cơ Aether",
        "airship.upgrade.system.engine.desc": "Mạng lực đẩy của tàu. Về sau sẽ chi phối hiệu suất hành trình và các tuyến xa hơn.",
        "airship.upgrade.system.navigation.name": "Lõi Dẫn Đường",
        "airship.upgrade.system.navigation.desc": "Máy điều tuyến ma pháp của MiMi. Về sau hỗ trợ đồng bộ những hành trình xa và ổn định hơn.",
        "airship.upgrade.system.hull.name": "Thân Tàu & Khiên",
        "airship.upgrade.system.hull.desc": "Gia cố thân tàu và kết giới bảo vệ. Bản này chưa kích hoạt lợi ích chiến đấu.",
        "airship.upgrade.system.reactor.name": "Lò Phản Ứng Ma Pháp",
        "airship.upgrade.system.reactor.desc": "Dẫn cộng hưởng Bụi Ma Thuật vào hạ tầng tàu và các hệ thống cao cấp trong tương lai.",
    })

    en_path.write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    vi_path.write_text(json.dumps(vi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_map_metadata() -> None:
    dock = MOD / "assets" / "sky_dock_interior.tmx"
    text = dock.read_text(encoding="utf-8")
    text = re.sub(r'CardchaSkyDockVersion" value="[^"]+"', 'CardchaSkyDockVersion" value="alpha.28.0.4.14"', text, count=1)
    dock.write_text(text, encoding="utf-8")

    bridge = MOD / "assets" / "airship_deck.tmx"
    text = bridge.read_text(encoding="utf-8")
    text = re.sub(r'CardchaAirshipVersion" value="[^"]+"', 'CardchaAirshipVersion" value="alpha.28.0.4.14"', text, count=1)
    text = re.sub(
        r'CardchaAirshipRole" value="[^"]+"',
        'CardchaAirshipRole" value="airship-bridge|navigation-core|interactive-upgrade-sockets|magic-dust-infrastructure|arcane-dock-return"',
        text,
        count=1,
    )
    bridge.write_text(text, encoding="utf-8")


def main() -> None:
    patch_version()
    patch_save_model()
    patch_save_service()
    patch_mod_entry()
    patch_airship_service()
    patch_localization()
    patch_map_metadata()
    print(f"Cardcha {VERSION} Airship Upgrade Foundation applied")


if __name__ == "__main__":
    main()

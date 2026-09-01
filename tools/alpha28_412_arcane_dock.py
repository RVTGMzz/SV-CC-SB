from __future__ import annotations

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "src" / "Cardcha"
VERSION = "0.3.0-alpha.28.0.4.12"


def replace_between(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    if replacement in text:
        return
    i = text.find(start)
    if i < 0:
        raise RuntimeError(f"Start marker not found in {path}: {start!r}")
    j = text.find(end, i + len(start))
    if j < 0:
        raise RuntimeError(f"End marker not found in {path}: {end!r}")
    text = text[:i] + replacement + text[j:]
    path.write_text(text, encoding="utf-8")


def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Required marker not found in {path}: {old[:160]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


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
        r"v0\.3\.0-alpha\.28\.0\.4\.\d+ [A-Z0-9 +_-]+ TEST",
        f"v{VERSION} ARCANE DOCK + AIRSHIP BRIDGE TEST",
        text,
        count=1,
    )
    entry.write_text(text, encoding="utf-8")


def patch_localization() -> None:
    en_path = MOD / "i18n" / "default.json"
    vi_path = MOD / "i18n" / "vi.json"
    en = json.loads(en_path.read_text(encoding="utf-8"))
    vi = json.loads(vi_path.read_text(encoding="utf-8"))

    en.update({
        "airship.arcane.route_console": "The Arcane Route Console hums softly. Region I is synchronized. Board the Airship through the violet gate to depart. Cards attuned: {{cards}}.",
        "airship.arcane.bridge.unavailable": "The boarding gate flickers, but the Airship Bridge cannot stabilize right now.",
        "airship.arcane.bridge.entered": "The violet gate folds around you. The Airship Bridge comes into focus.",
        "airship.arcane.dock.returned": "The Bridge gate returns you to MiMi's Arcane Dock.",
        "airship.arcane.bridge.helm": "The navigation core is ready. Use it again to confirm the Region I departure.",
    })
    vi.update({
        "airship.arcane.route_console": "Bàn Điều Tuyến Ma Pháp khẽ ngân lên. Vùng I đã được đồng bộ. Hãy bước qua cổng tím để lên Tàu Bay rồi khởi hành. Số lá bài cộng hưởng: {{cards}}.",
        "airship.arcane.bridge.unavailable": "Cổng lên tàu chập chờn, nhưng Cầu Điều Khiển Tàu Bay chưa thể ổn định lúc này.",
        "airship.arcane.bridge.entered": "Ánh tím khép lại quanh bạn. Cầu Điều Khiển Tàu Bay dần hiện ra.",
        "airship.arcane.dock.returned": "Cổng trên tàu đưa bạn trở lại Bến Ma Pháp của MiMi.",
        "airship.arcane.bridge.helm": "Lõi dẫn đường đã sẵn sàng. Hãy dùng nó lần nữa để xác nhận chuyến bay tới Vùng I.",
    })

    en_path.write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    vi_path.write_text(json.dumps(vi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_map_metadata() -> None:
    dock = MOD / "assets" / "sky_dock_interior.tmx"
    text = dock.read_text(encoding="utf-8")
    text = re.sub(r'CardchaSkyDockVersion" value="[^"]+"', 'CardchaSkyDockVersion" value="alpha.28.0.4.12"', text, count=1)
    text = re.sub(r'CardchaSkyDockRole" value="[^"]+"', 'CardchaSkyDockRole" value="arcane-dock|route-console|boarding-gate|forest-return"', text, count=1)
    text = re.sub(r'CardchaLayout" value="[^"]+"', 'CardchaLayout" value="bottom-entry|left-route-console|right-violet-boarding-gate|central-summoning-sigil"', text, count=1)
    dock.write_text(text, encoding="utf-8")

    bridge = MOD / "assets" / "airship_deck.tmx"
    text = bridge.read_text(encoding="utf-8")
    text = re.sub(r'CardchaAirshipVersion" value="[^"]+"', 'CardchaAirshipVersion" value="alpha.28.0.4.12"', text, count=1)
    text = re.sub(r'CardchaAirshipRole" value="[^"]+"', 'CardchaAirshipRole" value="airship-bridge|navigation-core|arcane-dock-return|future-upgrade-sockets"', text, count=1)
    bridge.write_text(text, encoding="utf-8")


def patch_flow() -> None:
    path = MOD / "Services" / "AirshipFoundationService.cs"

    interior_start = '        if (location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))\n'
    interior_end = '        if (location.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase))\n'
    interior_replacement = '''        if (location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))
        {
            Point interiorAction = GetActionTile();
            Point route = ResolveSkyDockInteriorRouteTile(location);
            Point bay = ResolveSkyDockInteriorBayTile(location);
            Point interiorExit = ResolveSkyDockInteriorExitTile(location);

            if (Touches(interiorAction, route) || PlayerIsNear(route))
            {
                this.Helper.Input.Suppress(e.Button);
                int owned = this.Save.Data.OwnedCards?.Count ?? 0;
                Game1.drawObjectDialogue(ModEntry.T("airship.arcane.route_console", new { cards = owned }));
                return;
            }

            if (Touches(interiorAction, bay) || PlayerIsNear(bay))
            {
                this.Helper.Input.Suppress(e.Button);
                if (this.WarpToAirshipBridge())
                    Game1.showGlobalMessage(ModEntry.T("airship.arcane.bridge.entered"));
                else
                    Game1.drawObjectDialogue(ModEntry.T("airship.arcane.bridge.unavailable"));
                return;
            }

            if (Touches(interiorAction, interiorExit) || PlayerIsNear(interiorExit))
            {
                this.Helper.Input.Suppress(e.Button);
                this.ReturnToSkyDockExterior();
            }
            return;
        }

'''
    replace_between(path, interior_start, interior_end, interior_replacement)

    deck_start = '        if (!location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))\n'
    deck_end = '    public void OnWarped(object? sender, WarpedEventArgs e)\n'
    deck_replacement = '''        if (!location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
            return;

        Point action = GetActionTile();
        Point helm = ResolveDeckHelmTile(location);
        Point exit = ResolveDeckExitTile(location);

        if (Touches(action, helm) || PlayerIsNear(helm))
        {
            this.Helper.Input.Suppress(e.Button);
            this.HandleRegion1DepartureRequest();
            return;
        }

        if (!Touches(action, exit) && !PlayerIsNear(exit))
            return;

        this.Helper.Input.Suppress(e.Button);
        if (this.WarpToSkyDockInterior())
            Game1.showGlobalMessage(ModEntry.T("airship.arcane.dock.returned"));
    }

'''
    replace_between(path, deck_start, deck_end, deck_replacement)

    old_return = '''            if (this.FlightCutsceneReturning)
            {
                if (!this.WarpToSkyDockInterior())
                    this.ReturnToSkyDockExterior();
            }
'''
    new_return = '''            if (this.FlightCutsceneReturning)
            {
                if (!this.WarpToAirshipBridge() && !this.WarpToSkyDockInterior())
                    this.ReturnToSkyDockExterior();
            }
'''
    replace_required(path, old_return, new_return)

    marker = '    private bool WarpToSkyDockInterior()\n'
    helper = '''    private bool WarpToAirshipBridge()
    {
        GameLocation? deck = this.EnsureDeckLocation();
        if (deck is null)
            return false;

        Point arrival = ResolveDeckArrivalTile(deck);
        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
        Game1.playSound("wand");
        Game1.warpFarmer(DeckLocationName, arrival.X, arrival.Y, 0);
        return true;
    }

'''
    text = path.read_text(encoding="utf-8")
    if 'private bool WarpToAirshipBridge()' not in text:
        if marker not in text:
            raise RuntimeError("WarpToSkyDockInterior insertion marker missing")
        text = text.replace(marker, helper + marker, 1)
        path.write_text(text, encoding="utf-8")

    text = path.read_text(encoding="utf-8")
    text = text.replace('Sky Dock is the normal gameplay entrance.', 'The Arcane Gate is the normal gameplay entrance.')
    text = text.replace('returned to Sky Dock interior.', 'returned to the Arcane Dock.')
    text = text.replace('Run cardcha_test_airship again to return to Sky Dock interior.', 'Run cardcha_test_airship again to return to the Arcane Dock.')
    text = text.replace('Created Cardcha_SkyDockInterior from Cardcha-owned vanilla-tile layout.', 'Created Cardcha_SkyDockInterior as Cardcha-owned Arcane Dock layout.')
    path.write_text(text, encoding="utf-8")


def patch_visuals() -> None:
    path = MOD / "Services" / "AirshipFoundationService.cs"

    sky_dock_start = '    private void DrawSkyDock(SpriteBatch batch, Point tile)\n'
    sky_dock_end = '    private void DrawSkyDockInteriorDetails(SpriteBatch batch, GameLocation interior)\n'
    sky_dock = '''    private void DrawSkyDock(SpriteBatch batch, Point tile)
    {
        Vector2 center = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(tile.X * 64f + 32f, tile.Y * 64f + 28f)
        );

        float phase = (float)(Environment.TickCount64 / 900.0);
        float pulse = 0.58f + 0.18f * (float)Math.Sin(Environment.TickCount64 / 250.0);
        Color violet = new Color(176, 118, 255) * pulse;
        Color cyan = new Color(104, 224, 244) * (pulse * 0.88f);
        Color gold = new Color(255, 216, 118) * 0.82f;
        Color stone = new Color(68, 58, 82) * 0.90f;

        // Conflict-safe Arcane Gate: pure overlay, no Forest tile/collision edits.
        DrawArcaneSigil(batch, new Vector2(center.X, center.Y + 34f), 58f, violet, phase);
        DrawArcaneSigil(batch, new Vector2(center.X, center.Y + 34f), 36f, cyan, -phase * 0.72f);

        DrawCrystalPylon(batch, new Vector2(center.X - 72f, center.Y + 42f), 44f, violet, gold);
        DrawCrystalPylon(batch, new Vector2(center.X + 72f, center.Y + 42f), 44f, cyan, gold);

        // Upright portal plane and runic crown.
        DrawRect(batch, new Rectangle((int)center.X - 43, (int)center.Y - 54, 86, 96), stone * 0.72f);
        DrawRect(batch, new Rectangle((int)center.X - 35, (int)center.Y - 46, 70, 84), new Color(87, 46, 134) * (0.36f + pulse * 0.28f));
        DrawRect(batch, new Rectangle((int)center.X - 4, (int)center.Y - 64, 8, 106), gold * 0.46f);
        DrawRect(batch, new Rectangle((int)center.X - 36, (int)center.Y - 12, 72, 7), cyan * 0.56f);

        for (int i = -2; i <= 2; i++)
        {
            int x = (int)center.X + i * 17;
            int y = (int)center.Y - 66 + Math.Abs(i) * 5;
            DrawRect(batch, new Rectangle(x - 3, y, 7, 7), i % 2 == 0 ? gold : violet);
        }
    }

'''
    replace_between(path, sky_dock_start, sky_dock_end, sky_dock)

    interior_start = '    private void DrawSkyDockInteriorDetails(SpriteBatch batch, GameLocation interior)\n'
    interior_end = '    private void DrawRegion1Details(SpriteBatch batch, GameLocation region)\n'
    interior = '''    private void DrawSkyDockInteriorDetails(SpriteBatch batch, GameLocation interior)
    {
        Point route = ResolveSkyDockInteriorRouteTile(interior);
        Point exit = ResolveSkyDockInteriorExitTile(interior);
        Point bay = ResolveSkyDockInteriorBayTile(interior);
        Point arrival = ResolveSkyDockInteriorArrivalTile(interior);

        float phase = (float)(Environment.TickCount64 / 950.0);
        float pulse = 0.56f + 0.17f * (float)Math.Sin(Environment.TickCount64 / 260.0);
        Color violet = new Color(181, 116, 255) * pulse;
        Color cyan = new Color(100, 225, 245) * (pulse * 0.92f);
        Color gold = new Color(255, 216, 118) * 0.86f;
        Color dark = new Color(48, 38, 68) * 0.92f;

        // Central summoning seal around the arrival point.
        Vector2 arrivalCenter = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(arrival.X * 64f + 32f, arrival.Y * 64f + 40f)
        );
        DrawArcaneSigil(batch, arrivalCenter, 72f, violet, phase);
        DrawArcaneSigil(batch, arrivalCenter, 48f, cyan, -phase * 0.65f);

        // Left route console: magical navigation slab, no longer a wooden notice board.
        Vector2 board = Game1.GlobalToLocal(Game1.viewport, new Vector2((route.X - 1) * 64f, (route.Y - 2) * 64f));
        DrawRect(batch, new Rectangle((int)board.X, (int)board.Y, 156, 88), dark);
        DrawRect(batch, new Rectangle((int)board.X + 8, (int)board.Y + 8, 140, 72), new Color(68, 54, 92) * 0.96f);
        DrawRect(batch, new Rectangle((int)board.X + 20, (int)board.Y + 22, 116, 7), gold * 0.62f);
        DrawRect(batch, new Rectangle((int)board.X + 28, (int)board.Y + 43, 100, 6), cyan * 0.64f);
        DrawRect(batch, new Rectangle((int)board.X + 42, (int)board.Y + 61, 72, 6), violet * 0.68f);
        DrawCrystalPylon(batch, new Vector2(board.X - 18f, board.Y + 76f), 36f, violet, gold);

        // Right violet boarding gate. No miniature Airship is drawn inside this room anymore.
        Vector2 gate = Game1.GlobalToLocal(Game1.viewport, new Vector2((bay.X - 2) * 64f, (bay.Y - 4) * 64f));
        DrawRect(batch, new Rectangle((int)gate.X, (int)gate.Y, 250, 174), new Color(32, 31, 58) * 0.94f);
        DrawRect(batch, new Rectangle((int)gate.X + 12, (int)gate.Y + 10, 226, 154), new Color(66, 44, 102) * 0.74f);
        Vector2 gateCenter = new(gate.X + 125f, gate.Y + 92f);
        DrawArcaneSigil(batch, gateCenter, 70f, violet, phase * 1.18f);
        DrawArcaneSigil(batch, gateCenter, 48f, cyan, -phase * 0.92f);
        DrawRect(batch, new Rectangle((int)gateCenter.X - 34, (int)gateCenter.Y - 58, 68, 116), new Color(103, 64, 176) * (0.30f + pulse * 0.32f));
        DrawCrystalPylon(batch, new Vector2(gate.X + 22f, gate.Y + 154f), 48f, cyan, gold);
        DrawCrystalPylon(batch, new Vector2(gate.X + 228f, gate.Y + 154f), 48f, violet, gold);

        DrawWorldMarker(batch, route, gold * 0.68f);
        DrawWorldMarker(batch, bay, violet * 0.78f);
        DrawWorldMarker(batch, exit, cyan * 0.62f);
    }

'''
    replace_between(path, interior_start, interior_end, interior)

    deck_start = '    private void DrawDeckMarkers(SpriteBatch batch, GameLocation deck)\n'
    deck_end = '    private static void DrawWorldMarker(SpriteBatch batch, Point tile, Color color)\n'
    deck = '''    private void DrawDeckMarkers(SpriteBatch batch, GameLocation deck)
    {
        Point helm = ResolveDeckHelmTile(deck);
        Point exit = ResolveDeckExitTile(deck);
        float phase = (float)(Environment.TickCount64 / 1050.0);
        float pulse = 0.54f + 0.16f * (float)Math.Sin(Environment.TickCount64 / 270.0);
        Color violet = new Color(177, 116, 255) * pulse;
        Color cyan = new Color(102, 224, 244) * (pulse * 0.94f);
        Color gold = new Color(255, 216, 118) * 0.84f;
        Color frame = new Color(55, 42, 63) * 0.96f;

        // Wide sky-facing bridge window. This replaces the old tiny-Airship-in-a-room illusion.
        Vector2 window = Game1.GlobalToLocal(Game1.viewport, new Vector2(3f * 64f, 1f * 64f));
        DrawRect(batch, new Rectangle((int)window.X, (int)window.Y, 18 * 64, 4 * 64), new Color(66, 125, 176) * 0.92f);
        DrawRect(batch, new Rectangle((int)window.X + 22, (int)window.Y + 42, 180, 17), new Color(228, 239, 246) * 0.74f);
        DrawRect(batch, new Rectangle((int)window.X + 370, (int)window.Y + 88, 220, 15), new Color(228, 239, 246) * 0.62f);
        DrawRect(batch, new Rectangle((int)window.X + 730, (int)window.Y + 54, 165, 16), new Color(228, 239, 246) * 0.68f);
        DrawRect(batch, new Rectangle((int)window.X - 10, (int)window.Y - 10, 18 * 64 + 20, 12), frame);
        DrawRect(batch, new Rectangle((int)window.X - 10, (int)window.Y + 4 * 64, 18 * 64 + 20, 12), frame);
        for (int i = 0; i <= 6; i++)
            DrawRect(batch, new Rectangle((int)window.X + i * 192 - 5, (int)window.Y, 10, 4 * 64), frame * 0.92f);

        // Central arcane navigation table/core at the helm.
        Vector2 helmCenter = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(helm.X * 64f + 32f, helm.Y * 64f + 40f)
        );
        DrawRect(batch, new Rectangle((int)helmCenter.X - 94, (int)helmCenter.Y - 22, 188, 86), new Color(68, 50, 74) * 0.96f);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 80, (int)helmCenter.Y - 10, 160, 58), new Color(91, 70, 103) * 0.94f);
        DrawArcaneSigil(batch, new Vector2(helmCenter.X, helmCenter.Y + 16f), 50f, violet, phase);
        DrawArcaneSigil(batch, new Vector2(helmCenter.X, helmCenter.Y + 16f), 30f, cyan, -phase * 0.82f);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 5, (int)helmCenter.Y - 42, 10, 54), gold * 0.66f);

        // Dormant infrastructure sockets foreshadow Magic Dust Airship upgrades.
        Point[] sockets = { new(5, 8), new(18, 8), new(8, 10), new(15, 10) };
        foreach (Point socket in sockets)
        {
            Vector2 s = Game1.GlobalToLocal(Game1.viewport, new Vector2(socket.X * 64f + 32f, socket.Y * 64f + 38f));
            DrawArcaneSigil(batch, s, 26f, new Color(111, 96, 142) * 0.46f, phase * 0.25f);
            DrawRect(batch, new Rectangle((int)s.X - 4, (int)s.Y - 18, 8, 36), gold * 0.28f);
        }

        DrawWorldMarker(batch, helm, gold * 0.72f);
        DrawWorldMarker(batch, exit, cyan * 0.62f);
    }

    private static void DrawArcaneSigil(SpriteBatch batch, Vector2 center, float radius, Color color, float phase)
    {
        const int segments = 16;
        for (int i = 0; i < segments; i++)
        {
            float angle = phase + i * MathHelper.TwoPi / segments;
            float x = center.X + MathF.Cos(angle) * radius;
            float y = center.Y + MathF.Sin(angle) * radius * 0.52f;
            int size = i % 2 == 0 ? 7 : 5;
            DrawRect(batch, new Rectangle((int)x - size / 2, (int)y - size / 2, size, size), color);
        }

        for (int i = 0; i < 4; i++)
        {
            float angle = phase * 0.35f + i * MathHelper.PiOver2;
            DrawRotorStroke(batch, center, angle, radius * 0.78f, 3f, color * 0.62f);
        }
    }

    private static void DrawCrystalPylon(SpriteBatch batch, Vector2 baseCenter, float height, Color crystal, Color trim)
    {
        int h = Math.Max(20, (int)height);
        int x = (int)baseCenter.X;
        int y = (int)baseCenter.Y;
        DrawRect(batch, new Rectangle(x - 10, y - h, 20, h), crystal * 0.76f);
        DrawRect(batch, new Rectangle(x - 6, y - h - 12, 12, 16), crystal);
        DrawRect(batch, new Rectangle(x - 13, y - 5, 26, 7), trim * 0.74f);
        DrawRect(batch, new Rectangle(x - 3, y - h + 5, 6, Math.Max(8, h - 12)), Color.White * 0.22f);
    }

'''
    replace_between(path, deck_start, deck_end, deck)


def main() -> None:
    patch_version()
    patch_localization()
    patch_map_metadata()
    patch_flow()
    patch_visuals()
    print(f"Cardcha {VERSION} Arcane Dock + Airship Bridge patch applied")


if __name__ == "__main__":
    main()

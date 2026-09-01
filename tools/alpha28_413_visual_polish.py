from __future__ import annotations

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "src" / "Cardcha"
VERSION = "0.3.0-alpha.28.0.4.13"


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
    path.write_text(text[:i] + replacement + text[j:], encoding="utf-8")


def patch_version_and_metadata() -> None:
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
        f"v{VERSION} ARCANE DOCK + BRIDGE VISUAL POLISH TEST",
        text,
        count=1,
    )
    entry.write_text(text, encoding="utf-8")

    dock = MOD / "assets" / "sky_dock_interior.tmx"
    text = dock.read_text(encoding="utf-8")
    text = re.sub(r'CardchaSkyDockVersion" value="[^"]+"', 'CardchaSkyDockVersion" value="alpha.28.0.4.13"', text, count=1)
    text = re.sub(
        r'CardchaLayout" value="[^"]+"',
        'CardchaLayout" value="layered-sigil|route-orbit-console|deep-violet-boarding-gate|mana-lanes|ambient-motes"',
        text,
        count=1,
    )
    if 'CardchaVisualProfile' not in text:
        text = text.replace(
            '  <property name="CardchaAssetPolicy" value="cardcha-owned-map|vanilla-tiles-only|no-druid-assets" />\n',
            '  <property name="CardchaAssetPolicy" value="cardcha-owned-map|vanilla-tiles-only|no-druid-assets" />\n'
            '  <property name="CardchaVisualProfile" value="arcane-sanctum|violet-cyan-gold|runtime-pixel-polish" />\n',
            1,
        )
    dock.write_text(text, encoding="utf-8")

    bridge = MOD / "assets" / "airship_deck.tmx"
    text = bridge.read_text(encoding="utf-8")
    text = re.sub(r'CardchaAirshipVersion" value="[^"]+"', 'CardchaAirshipVersion" value="alpha.28.0.4.13"', text, count=1)
    if 'CardchaBridgeVisualProfile' not in text:
        text = text.replace(
            '  <property name="CardchaAssetPolicy" value="cardcha-owned-map|vanilla-tiles-only|no-druid-assets" />\n',
            '  <property name="CardchaAssetPolicy" value="cardcha-owned-map|vanilla-tiles-only|no-druid-assets" />\n'
            '  <property name="CardchaBridgeVisualProfile" value="panoramic-sky|arcane-navigation-dais|mana-lanes|upgrade-sockets" />\n',
            1,
        )
    bridge.write_text(text, encoding="utf-8")

    targets = MOD / "Directory.Build.targets"
    targets.write_text(
        f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <Target Name="CardchaAlpha280413Finalize" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 &quot;$(MSBuildProjectDirectory)/../../tools/alpha28_413_visual_polish.py&quot;" />\n  </Target>\n\n  <Target Name="CardchaAlpha280413Manifest" BeforeTargets="BeforeBuild" DependsOnTargets="CardchaAlpha280413Finalize">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n''',
        encoding="utf-8",
    )


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

        float phase = (float)(Environment.TickCount64 / 820.0);
        float pulse = 0.58f + 0.18f * (float)Math.Sin(Environment.TickCount64 / 240.0);
        Color violet = new Color(186, 126, 255) * pulse;
        Color cyan = new Color(104, 229, 247) * (pulse * 0.92f);
        Color gold = new Color(255, 220, 126) * 0.88f;
        Color stone = new Color(63, 52, 79) * 0.94f;
        Color shadow = new Color(29, 25, 43) * 0.76f;

        // Conflict-safe Arcane Gate: presentation only, never Forest collision/pathing.
        DrawRect(batch, new Rectangle((int)center.X - 55, (int)center.Y + 31, 110, 15), shadow);
        DrawArcaneSigil(batch, new Vector2(center.X, center.Y + 36f), 62f, violet, phase);
        DrawArcaneSigil(batch, new Vector2(center.X, center.Y + 36f), 40f, cyan, -phase * 0.74f);

        // Layered portal frame gives the entrance depth without claiming any map tiles.
        DrawRect(batch, new Rectangle((int)center.X - 52, (int)center.Y - 61, 14, 104), stone);
        DrawRect(batch, new Rectangle((int)center.X + 38, (int)center.Y - 61, 14, 104), stone);
        DrawRect(batch, new Rectangle((int)center.X - 52, (int)center.Y - 64, 104, 14), stone);
        DrawRect(batch, new Rectangle((int)center.X - 43, (int)center.Y - 51, 86, 88), new Color(60, 38, 94) * 0.74f);
        DrawRect(batch, new Rectangle((int)center.X - 35, (int)center.Y - 45, 70, 77), new Color(111, 66, 177) * (0.24f + pulse * 0.34f));
        DrawRect(batch, new Rectangle((int)center.X - 27, (int)center.Y - 39, 54, 65), new Color(93, 206, 235) * (0.12f + pulse * 0.22f));
        DrawRect(batch, new Rectangle((int)center.X - 4, (int)center.Y - 56, 8, 90), gold * 0.48f);

        DrawCrystalPylon(batch, new Vector2(center.X - 75f, center.Y + 43f), 48f, violet, gold);
        DrawCrystalPylon(batch, new Vector2(center.X + 75f, center.Y + 43f), 48f, cyan, gold);
        DrawDiamondRune(batch, new Vector2(center.X, center.Y - 71f), 16f, gold);
        DrawArcaneSparkles(batch, new Vector2(center.X, center.Y - 4f), 82f, 11, phase, Color.White * 0.62f);
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

        float phase = (float)(Environment.TickCount64 / 900.0);
        float pulse = 0.56f + 0.18f * (float)Math.Sin(Environment.TickCount64 / 250.0);
        Color violet = new Color(188, 125, 255) * pulse;
        Color cyan = new Color(103, 229, 247) * (pulse * 0.94f);
        Color gold = new Color(255, 220, 126) * 0.88f;
        Color dark = new Color(42, 34, 61) * 0.94f;
        Color panel = new Color(72, 56, 96) * 0.94f;

        Vector2 arrivalCenter = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(arrival.X * 64f + 32f, arrival.Y * 64f + 40f)
        );
        Vector2 routeCenter = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(route.X * 64f + 32f, route.Y * 64f + 36f)
        );
        Vector2 bayCenter = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(bay.X * 64f + 32f, bay.Y * 64f + 36f)
        );

        // Mana lanes visually explain the room: arrival seal branches toward information and boarding.
        DrawManaLane(batch, arrivalCenter, routeCenter, violet * 0.44f, phase);
        DrawManaLane(batch, arrivalCenter, bayCenter, cyan * 0.48f, -phase * 0.82f);
        DrawArcaneSigil(batch, arrivalCenter, 78f, violet, phase);
        DrawArcaneSigil(batch, arrivalCenter, 51f, cyan, -phase * 0.67f);
        DrawDiamondRune(batch, arrivalCenter, 19f, gold * 0.78f);
        DrawArcaneSparkles(batch, arrivalCenter, 94f, 12, phase, Color.White * 0.54f);

        // Left route console becomes a small floating navigation altar rather than a flat board.
        Vector2 board = Game1.GlobalToLocal(Game1.viewport, new Vector2((route.X - 1) * 64f, (route.Y - 2) * 64f));
        DrawRect(batch, new Rectangle((int)board.X - 8, (int)board.Y + 8, 172, 96), new Color(25, 22, 38) * 0.66f);
        DrawRect(batch, new Rectangle((int)board.X, (int)board.Y, 156, 88), dark);
        DrawRect(batch, new Rectangle((int)board.X + 8, (int)board.Y + 8, 140, 72), panel);
        DrawRect(batch, new Rectangle((int)board.X + 16, (int)board.Y + 14, 124, 5), gold * 0.72f);
        DrawRect(batch, new Rectangle((int)board.X + 22, (int)board.Y + 55, 112, 5), cyan * 0.56f);
        DrawArcaneSigil(batch, new Vector2(board.X + 78f, board.Y + 39f), 28f, violet * 0.78f, -phase * 1.2f);
        DrawDiamondRune(batch, new Vector2(board.X + 78f, board.Y + 39f), 11f, cyan * 0.82f);
        DrawCrystalPylon(batch, new Vector2(board.X - 18f, board.Y + 83f), 39f, violet, gold);
        DrawArcaneSparkles(batch, new Vector2(board.X + 78f, board.Y + 39f), 48f, 7, -phase, gold * 0.58f);

        // Right boarding gate reads as a deep portal chamber. No miniature Airship appears here.
        Vector2 gate = Game1.GlobalToLocal(Game1.viewport, new Vector2((bay.X - 2) * 64f, (bay.Y - 4) * 64f));
        DrawRect(batch, new Rectangle((int)gate.X - 10, (int)gate.Y + 10, 270, 174), new Color(23, 21, 38) * 0.72f);
        DrawRect(batch, new Rectangle((int)gate.X, (int)gate.Y, 250, 174), dark);
        DrawRect(batch, new Rectangle((int)gate.X + 12, (int)gate.Y + 10, 226, 154), new Color(66, 44, 102) * 0.78f);
        DrawRect(batch, new Rectangle((int)gate.X + 24, (int)gate.Y + 20, 202, 134), new Color(94, 60, 145) * (0.28f + pulse * 0.18f));
        DrawRect(batch, new Rectangle((int)gate.X + 38, (int)gate.Y + 30, 174, 114), new Color(73, 168, 211) * (0.12f + pulse * 0.15f));
        Vector2 gateCenter = new(gate.X + 125f, gate.Y + 91f);
        DrawArcaneSigil(batch, gateCenter, 72f, violet, phase * 1.18f);
        DrawArcaneSigil(batch, gateCenter, 49f, cyan, -phase * 0.92f);
        DrawDiamondRune(batch, gateCenter, 18f, gold * 0.82f);
        DrawArcaneSparkles(batch, gateCenter, 92f, 14, phase * 1.3f, Color.White * 0.62f);
        DrawCrystalPylon(batch, new Vector2(gate.X + 20f, gate.Y + 163f), 52f, cyan, gold);
        DrawCrystalPylon(batch, new Vector2(gate.X + 230f, gate.Y + 163f), 52f, violet, gold);

        // A quiet return rune anchors the bottom exit without turning it into another giant portal.
        Vector2 exitCenter = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(exit.X * 64f + 32f, exit.Y * 64f + 38f)
        );
        DrawArcaneSigil(batch, exitCenter, 28f, cyan * 0.52f, -phase * 0.4f);

        DrawWorldMarker(batch, route, gold * 0.72f);
        DrawWorldMarker(batch, bay, violet * 0.82f);
        DrawWorldMarker(batch, exit, cyan * 0.66f);
    }

'''
    replace_between(path, interior_start, interior_end, interior)

    deck_start = '    private void DrawDeckMarkers(SpriteBatch batch, GameLocation deck)\n'
    deck_end = '    private static void DrawArcaneSigil(SpriteBatch batch, Vector2 center, float radius, Color color, float phase)\n'
    deck = '''    private void DrawDeckMarkers(SpriteBatch batch, GameLocation deck)
    {
        Point helm = ResolveDeckHelmTile(deck);
        Point exit = ResolveDeckExitTile(deck);
        float phase = (float)(Environment.TickCount64 / 980.0);
        float pulse = 0.55f + 0.17f * (float)Math.Sin(Environment.TickCount64 / 260.0);
        Color violet = new Color(187, 124, 255) * pulse;
        Color cyan = new Color(103, 229, 247) * (pulse * 0.95f);
        Color gold = new Color(255, 220, 126) * 0.88f;
        Color frame = new Color(49, 40, 62) * 0.98f;
        bool night = Game1.timeOfDay >= 1800 || Game1.timeOfDay < 600;

        // Panoramic bridge window with subtle moving sky. This is the ship's viewpoint, not a model room.
        Vector2 window = Game1.GlobalToLocal(Game1.viewport, new Vector2(3f * 64f, 1f * 64f));
        Rectangle windowRect = new((int)window.X, (int)window.Y, 18 * 64, 4 * 64);
        Color skyTop = night ? new Color(30, 43, 83) : new Color(76, 145, 201);
        Color skyMid = night ? new Color(47, 55, 101) : new Color(101, 173, 219);
        Color skyLow = night ? new Color(69, 63, 114) : new Color(151, 202, 232);
        DrawRect(batch, new Rectangle(windowRect.X, windowRect.Y, windowRect.Width, windowRect.Height / 3), skyTop * 0.96f);
        DrawRect(batch, new Rectangle(windowRect.X, windowRect.Y + windowRect.Height / 3, windowRect.Width, windowRect.Height / 3), skyMid * 0.96f);
        DrawRect(batch, new Rectangle(windowRect.X, windowRect.Y + windowRect.Height * 2 / 3, windowRect.Width, windowRect.Height / 3 + 2), skyLow * 0.96f);

        if (night)
            DrawStarfield(batch, windowRect, 34, phase, new Color(239, 235, 204) * 0.78f);
        else
        {
            DrawCloudBand(batch, windowRect, 34, phase * 18f, Color.White * 0.62f);
            DrawCloudBand(batch, windowRect, 108, -phase * 12f, Color.White * 0.48f);
        }

        DrawRect(batch, new Rectangle(windowRect.X - 10, windowRect.Y - 10, windowRect.Width + 20, 12), frame);
        DrawRect(batch, new Rectangle(windowRect.X - 10, windowRect.Bottom, windowRect.Width + 20, 12), frame);
        for (int i = 0; i <= 6; i++)
            DrawRect(batch, new Rectangle(windowRect.X + i * 192 - 5, windowRect.Y, 10, windowRect.Height), frame * 0.94f);

        Vector2 helmCenter = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(helm.X * 64f + 32f, helm.Y * 64f + 40f)
        );
        Vector2 exitCenter = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(exit.X * 64f + 32f, exit.Y * 64f + 36f)
        );

        // Energy lane makes the path from boarding gate to helm immediately legible.
        DrawManaLane(batch, exitCenter, helmCenter, cyan * 0.42f, phase);

        // Navigation dais: layered base, rotating route rings, floating core.
        DrawRect(batch, new Rectangle((int)helmCenter.X - 112, (int)helmCenter.Y + 33, 224, 22), new Color(31, 27, 43) * 0.72f);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 98, (int)helmCenter.Y - 25, 196, 88), frame);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 84, (int)helmCenter.Y - 12, 168, 62), new Color(86, 67, 103) * 0.96f);
        DrawArcaneSigil(batch, new Vector2(helmCenter.X, helmCenter.Y + 16f), 55f, violet, phase);
        DrawArcaneSigil(batch, new Vector2(helmCenter.X, helmCenter.Y + 16f), 34f, cyan, -phase * 0.88f);
        DrawDiamondRune(batch, new Vector2(helmCenter.X, helmCenter.Y + 5f), 18f, gold);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 5, (int)helmCenter.Y - 55, 10, 50), gold * 0.62f);
        DrawArcaneSparkles(batch, new Vector2(helmCenter.X, helmCenter.Y + 4f), 70f, 10, phase * 1.2f, Color.White * 0.52f);

        // Side consoles frame the bridge and keep the center visually open for the farmer.
        Vector2 leftConsole = Game1.GlobalToLocal(Game1.viewport, new Vector2(5f * 64f, 7f * 64f));
        Vector2 rightConsole = Game1.GlobalToLocal(Game1.viewport, new Vector2(17f * 64f, 7f * 64f));
        DrawBridgeConsole(batch, leftConsole, violet, cyan, gold, phase);
        DrawBridgeConsole(batch, rightConsole, cyan, violet, gold, -phase);

        // Dormant upgrade sockets now look like actual ship infrastructure rather than debug marks.
        Point[] sockets = { new(5, 9), new(18, 9), new(8, 10), new(15, 10) };
        foreach (Point socket in sockets)
        {
            Vector2 s = Game1.GlobalToLocal(Game1.viewport, new Vector2(socket.X * 64f + 32f, socket.Y * 64f + 38f));
            DrawArcaneSigil(batch, s, 28f, new Color(116, 101, 148) * 0.46f, phase * 0.24f);
            DrawCrystalPylon(batch, new Vector2(s.X, s.Y + 18f), 24f, new Color(110, 98, 145) * 0.62f, gold * 0.38f);
        }

        DrawArcaneSigil(batch, exitCenter, 30f, cyan * 0.52f, -phase * 0.42f);
        DrawWorldMarker(batch, helm, gold * 0.76f);
        DrawWorldMarker(batch, exit, cyan * 0.66f);
    }

'''
    replace_between(path, deck_start, deck_end, deck)

    marker_start = '    private static void DrawWorldMarker(SpriteBatch batch, Point tile, Color color)\n'
    marker_end = '    private static void DrawRect(SpriteBatch batch, Rectangle rectangle, Color color)\n'
    helpers = '''    private static void DrawManaLane(SpriteBatch batch, Vector2 start, Vector2 end, Color color, float phase)
    {
        Vector2 delta = end - start;
        float length = delta.Length();
        if (length < 1f)
            return;

        float angle = MathF.Atan2(delta.Y, delta.X);
        DrawRotorStroke(batch, start, angle, length, 3f, color * 0.52f);
        for (int i = 0; i < 7; i++)
        {
            float t = (i / 7f + phase * 0.075f) % 1f;
            if (t < 0f)
                t += 1f;
            Vector2 p = Vector2.Lerp(start, end, t);
            int size = i % 2 == 0 ? 6 : 4;
            DrawRect(batch, new Rectangle((int)p.X - size / 2, (int)p.Y - size / 2, size, size), color);
        }
    }

    private static void DrawArcaneSparkles(SpriteBatch batch, Vector2 center, float radius, int count, float phase, Color color)
    {
        for (int i = 0; i < count; i++)
        {
            float angle = phase * (0.35f + (i % 3) * 0.11f) + i * MathHelper.TwoPi / Math.Max(1, count);
            float orbit = radius * (0.55f + (i % 5) * 0.09f);
            float x = center.X + MathF.Cos(angle) * orbit;
            float y = center.Y + MathF.Sin(angle) * orbit * 0.62f;
            float twinkle = 0.55f + 0.35f * MathF.Sin(phase * 2.2f + i * 1.7f);
            int size = i % 4 == 0 ? 5 : 3;
            DrawRect(batch, new Rectangle((int)x - size / 2, (int)y - size / 2, size, size), color * twinkle);
        }
    }

    private static void DrawDiamondRune(SpriteBatch batch, Vector2 center, float radius, Color color)
    {
        float r = Math.Max(5f, radius);
        float side = r * 0.72f;
        DrawRotorStroke(batch, new Vector2(center.X, center.Y - r), MathHelper.PiOver4, side * 1.45f, 3f, color);
        DrawRotorStroke(batch, new Vector2(center.X + r, center.Y), MathHelper.PiOver4 * 3f, side * 1.45f, 3f, color);
        DrawRotorStroke(batch, new Vector2(center.X, center.Y + r), -MathHelper.PiOver4 * 3f, side * 1.45f, 3f, color);
        DrawRotorStroke(batch, new Vector2(center.X - r, center.Y), -MathHelper.PiOver4, side * 1.45f, 3f, color);
        DrawRect(batch, new Rectangle((int)center.X - 3, (int)center.Y - 3, 7, 7), Color.White * 0.48f);
    }

    private static void DrawBridgeConsole(SpriteBatch batch, Vector2 origin, Color primary, Color secondary, Color gold, float phase)
    {
        DrawRect(batch, new Rectangle((int)origin.X - 58, (int)origin.Y - 34, 116, 70), new Color(45, 37, 58) * 0.96f);
        DrawRect(batch, new Rectangle((int)origin.X - 48, (int)origin.Y - 24, 96, 48), new Color(77, 62, 91) * 0.94f);
        DrawRect(batch, new Rectangle((int)origin.X - 38, (int)origin.Y - 14, 76, 5), gold * 0.56f);
        DrawRect(batch, new Rectangle((int)origin.X - 30, (int)origin.Y + 4, 60, 5), secondary * 0.58f);
        DrawArcaneSigil(batch, new Vector2(origin.X, origin.Y + 30f), 22f, primary * 0.54f, phase * 0.45f);
    }

    private static void DrawCloudBand(SpriteBatch batch, Rectangle bounds, int yOffset, float drift, Color color)
    {
        int period = 340;
        int shift = ((int)drift % period + period) % period;
        for (int i = -1; i < 5; i++)
        {
            int x = bounds.X + i * period + shift - 80;
            int y = bounds.Y + yOffset + (i % 2) * 16;
            DrawRect(batch, new Rectangle(x, y, 118, 13), color * 0.72f);
            DrawRect(batch, new Rectangle(x + 24, y - 11, 72, 15), color * 0.82f);
            DrawRect(batch, new Rectangle(x + 57, y + 8, 96, 10), color * 0.58f);
        }
    }

    private static void DrawStarfield(SpriteBatch batch, Rectangle bounds, int count, float phase, Color color)
    {
        int drift = (int)(phase * 9f);
        for (int i = 0; i < count; i++)
        {
            int x = bounds.X + ((i * 79 + drift) % Math.Max(1, bounds.Width) + bounds.Width) % bounds.Width;
            int y = bounds.Y + ((i * 47 + i * i * 3) % Math.Max(1, bounds.Height));
            float twinkle = 0.48f + 0.42f * MathF.Sin(phase * 2.1f + i * 0.83f);
            int size = i % 7 == 0 ? 4 : 2;
            DrawRect(batch, new Rectangle(x, y, size, size), color * twinkle);
        }
    }

    private static void DrawWorldMarker(SpriteBatch batch, Point tile, Color color)
    {
        Vector2 screen = Game1.GlobalToLocal(Game1.viewport, new Vector2(tile.X * 64f + 32f, tile.Y * 64f + 44f));
        DrawRect(batch, new Rectangle((int)screen.X - 16, (int)screen.Y + 8, 32, 4), color * 0.58f);
        DrawDiamondRune(batch, new Vector2(screen.X, screen.Y), 8f, color * 0.82f);
    }

'''
    replace_between(path, marker_start, marker_end, helpers)


def main() -> None:
    patch_version_and_metadata()
    patch_visuals()
    print("Cardcha 0.3.0-alpha.28.0.4.13 Arcane Dock + Bridge visual polish applied")


if __name__ == "__main__":
    main()

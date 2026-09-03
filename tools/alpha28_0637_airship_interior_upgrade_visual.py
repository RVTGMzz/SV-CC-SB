from pathlib import Path
import json
import re

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
ASSETS = SRC / "assets"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.6"
CELL = 96
ATLAS = ASSETS / "airship_upgrade_visuals.png"

# Palette stays inside the existing Cardcha Airship language: warm wood/brass structure,
# violet/cyan arcane hardware, restrained highlights, and dark ship framing.
transparent = (0, 0, 0, 0)
frame = (44, 35, 46, 255)
frame2 = (67, 47, 49, 255)
wood = (108, 67, 48, 255)
wood_hi = (143, 91, 56, 255)
brass = (190, 131, 64, 255)
gold = (232, 177, 84, 255)
cyan = (91, 220, 241, 255)
cyan_dim = (70, 151, 174, 220)
violet = (190, 111, 246, 255)
violet_dim = (119, 76, 156, 220)
blue = (130, 157, 225, 255)
white = (244, 238, 219, 255)
shadow = (22, 17, 27, 180)


def rect(d, xy, fill, outline=None, width=1):
    d.rectangle(xy, fill=fill, outline=outline, width=width)


def line(d, points, fill, width=1):
    d.line(points, fill=fill, width=width)


def glow_block(d, x, y, w, h, color):
    # Pixel-art glow: stepped translucent blocks, never blurred.
    r, g, b, _ = color
    rect(d, (x-4, y-3, x+w+3, y+h+2), (r, g, b, 32))
    rect(d, (x-2, y-2, x+w+1, y+h+1), (r, g, b, 62))
    rect(d, (x, y, x+w-1, y+h-1), color)


def draw_base(d, level, accent):
    rect(d, (14, 73, 82, 88), shadow)
    rect(d, (18, 67, 78, 82), frame, brass, 2)
    rect(d, (23, 62, 73, 70), wood, wood_hi, 1)
    rect(d, (29, 58, 67, 63), brass)
    # Level pips are part of the physical station itself.
    for i in range(3):
        c = accent if i < level else (80, 70, 92, 180)
        rect(d, (36 + i * 10, 78, 42 + i * 10, 81), c)


def engine(d, level):
    draw_base(d, level, (247, 179, 82, 255))
    # Core housing.
    rect(d, (31, 36, 65, 61), frame2, brass, 2)
    rect(d, (38, 40, 58, 57), wood_hi)
    glow_block(d, 44, 43, 8, 10, (247, 179, 82, 255))
    # Turbine blades / intake.
    if level >= 1:
        rect(d, (22, 42, 31, 54), frame, brass, 1)
        rect(d, (65, 42, 74, 54), frame, brass, 1)
        line(d, [(26, 39), (26, 31), (34, 31)], brass, 3)
        line(d, [(70, 39), (70, 31), (62, 31)], brass, 3)
    if level >= 2:
        for y in (30, 36, 42, 48):
            rect(d, (11, y, 20, y+3), brass)
            rect(d, (76, y, 85, y+3), brass)
        line(d, [(16, 28), (16, 18), (36, 18)], cyan_dim, 3)
        line(d, [(80, 28), (80, 18), (60, 18)], cyan_dim, 3)
    if level >= 3:
        glow_block(d, 41, 18, 14, 12, cyan)
        rect(d, (35, 13, 61, 17), brass)
        rect(d, (31, 9, 65, 12), frame, brass, 1)
        for x in (27, 69):
            line(d, [(x, 22), (x, 57)], gold, 2)


def navigation(d, level):
    draw_base(d, level, cyan)
    rect(d, (34, 44, 62, 62), frame2, brass, 2)
    glow_block(d, 41, 48, 14, 8, cyan)
    # Mechanical astrolabe. Ellipses stay pixel-sharp.
    d.ellipse((31, 20, 65, 54), outline=brass, width=3)
    if level >= 1:
        d.ellipse((36, 24, 60, 50), outline=cyan, width=2)
        line(d, [(28, 37), (68, 37)], brass, 2)
    if level >= 2:
        d.ellipse((25, 15, 71, 59), outline=violet, width=2)
        line(d, [(48, 11), (48, 62)], cyan_dim, 2)
        rect(d, (21, 31, 27, 42), frame, brass, 1)
        rect(d, (69, 31, 75, 42), frame, brass, 1)
    if level >= 3:
        for x, y in [(18,22),(76,22),(18,52),(76,52)]:
            glow_block(d, x, y, 4, 4, gold)
        line(d, [(22, 17), (35, 9), (61, 9), (74, 17)], violet_dim, 2)
        rect(d, (43, 5, 53, 11), brass)
        glow_block(d, 46, 7, 4, 4, white)


def hull(d, level):
    draw_base(d, level, blue)
    # Shield plate / hull brace.
    d.polygon([(48, 17), (69, 27), (65, 55), (48, 68), (31, 55), (27, 27)], fill=frame2, outline=brass)
    d.polygon([(48, 24), (61, 31), (58, 50), (48, 58), (38, 50), (35, 31)], fill=(91, 108, 165, 230))
    if level >= 1:
        line(d, [(25, 22), (15, 16), (15, 55), (27, 61)], brass, 3)
        line(d, [(71, 22), (81, 16), (81, 55), (69, 61)], brass, 3)
    if level >= 2:
        for y in (23, 38, 53):
            rect(d, (8, y, 15, y+5), frame, blue, 1)
            rect(d, (81, y, 88, y+5), frame, blue, 1)
        d.ellipse((30, 15, 66, 66), outline=blue, width=2)
    if level >= 3:
        d.ellipse((22, 8, 74, 72), outline=cyan, width=2)
        d.ellipse((18, 4, 78, 76), outline=(112, 204, 243, 110), width=1)
        glow_block(d, 44, 34, 8, 8, cyan)


def reactor(d, level):
    draw_base(d, level, violet)
    # Crystal core.
    rect(d, (37, 34, 59, 61), frame2, brass, 2)
    d.polygon([(48, 12), (59, 29), (55, 54), (48, 63), (41, 54), (37, 29)], fill=violet, outline=brass)
    glow_block(d, 45, 27, 6, 20, (218, 132, 246, 255))
    if level >= 1:
        d.ellipse((30, 20, 66, 58), outline=brass, width=2)
        line(d, [(26, 39), (70, 39)], violet_dim, 2)
    if level >= 2:
        d.ellipse((23, 13, 73, 65), outline=cyan, width=2)
        line(d, [(48, 6), (48, 69)], cyan_dim, 2)
        rect(d, (18, 27, 24, 51), frame, brass, 1)
        rect(d, (72, 27, 78, 51), frame, brass, 1)
    if level >= 3:
        d.ellipse((15, 5, 81, 73), outline=violet, width=2)
        for x, y in [(20,14),(72,14),(14,44),(78,44),(28,68),(64,68)]:
            glow_block(d, x, y, 4, 4, cyan if x % 2 == 0 else gold)
        rect(d, (38, 5, 58, 9), brass)


systems = [engine, navigation, hull, reactor]
atlas = Image.new("RGBA", (CELL * 4, CELL * 4), transparent)
for row in range(4):
    for col, painter in enumerate(systems):
        tile = Image.new("RGBA", (CELL, CELL), transparent)
        painter(ImageDraw.Draw(tile), row)
        atlas.alpha_composite(tile, (col * CELL, row * CELL))
atlas.save(ATLAS, format="PNG", optimize=False)

service_path = SRC / "Services" / "AirshipFoundationService.cs"
service = service_path.read_text(encoding="utf-8")

if 'private const string AirshipUpgradeVisualPath = "assets/airship_upgrade_visuals.png";' not in service:
    service = service.replace(
        '    private const string AirshipVisualPath = "assets/airship_visual.png";\n',
        '    private const string AirshipVisualPath = "assets/airship_visual.png";\n'
        '    private const string AirshipUpgradeVisualPath = "assets/airship_upgrade_visuals.png";\n',
        1,
    )

if 'private Texture2D? AirshipUpgradeVisuals;' not in service:
    service = service.replace(
        '    private Texture2D? AirshipVisual;\n    private bool AirshipVisualLoadFailed;\n',
        '    private Texture2D? AirshipVisual;\n'
        '    private Texture2D? AirshipUpgradeVisuals;\n'
        '    private bool AirshipUpgradeVisualsLoadFailed;\n'
        '    private bool AirshipVisualLoadFailed;\n',
        1,
    )

# Add integrated upgrade conduits before the four system stations are drawn.
loop = '''        foreach ((AirshipUpgradeSystem system, Point socket) in ResolveDeckUpgradeSockets())\n        {\n            Vector2 s = Game1.GlobalToLocal(Game1.viewport, new Vector2(socket.X * 64f + 32f, socket.Y * 64f + 38f));\n            DrawUpgradeSocket(batch, s, system, this.GetAirshipUpgradeLevel(system), phase, gold);\n        }'''
replacement_loop = '''        DrawUpgradeConduitNetwork(batch, helmCenter, phase, gold);\n\n        foreach ((AirshipUpgradeSystem system, Point socket) in ResolveDeckUpgradeSockets())\n        {\n            Vector2 s = Game1.GlobalToLocal(Game1.viewport, new Vector2(socket.X * 64f + 32f, socket.Y * 64f + 38f));\n            this.DrawUpgradeSocket(batch, s, system, this.GetAirshipUpgradeLevel(system), phase, gold);\n        }'''
if loop in service:
    service = service.replace(loop, replacement_loop, 1)
elif 'DrawUpgradeConduitNetwork(batch, helmCenter' not in service:
    raise SystemExit('Could not find Airship upgrade socket loop for .5.6 integration.')

# Insert texture loader beside the official Airship loader.
loader_marker = '''    private Texture2D? GetAirshipVisual()\n    {'''
loader = '''    private Texture2D? GetAirshipUpgradeVisuals()\n    {\n        if (this.AirshipUpgradeVisuals is not null)\n            return this.AirshipUpgradeVisuals;\n        if (this.AirshipUpgradeVisualsLoadFailed)\n            return null;\n\n        try\n        {\n            this.AirshipUpgradeVisuals = this.Helper.ModContent.Load<Texture2D>(AirshipUpgradeVisualPath);\n            return this.AirshipUpgradeVisuals;\n        }\n        catch (Exception ex)\n        {\n            this.AirshipUpgradeVisualsLoadFailed = true;\n            this.Monitor.Log(\n                $"Couldn't load Airship interior upgrade visuals; procedural sockets remain active. {ex.GetType().Name}: {ex.Message}",\n                LogLevel.Warn\n            );\n            return null;\n        }\n    }\n\n    private Texture2D? GetAirshipVisual()\n    {'''
if 'private Texture2D? GetAirshipUpgradeVisuals()' not in service:
    if loader_marker not in service:
        raise SystemExit('Could not locate GetAirshipVisual for .5.6 loader injection.')
    service = service.replace(loader_marker, loader, 1)

# Add conduit network helper immediately before DrawUpgradeSocket.
upgrade_marker = '''    private static void DrawUpgradeSocket(\n        SpriteBatch batch,'''
conduit_helper = '''    private static void DrawUpgradeConduitNetwork(SpriteBatch batch, Vector2 helmCenter, float phase, Color gold)\n    {\n        // Four independent infrastructure feeds converge beneath the central navigation dais.\n        // These are visual-only conduits: no gameplay bonus is enabled by this pass.\n        (Vector2 Offset, Color Color)[] feeds =\n        {\n            (new Vector2(-448f, 300f), new Color(247, 179, 82)),\n            (new Vector2(384f, 300f), new Color(92, 207, 232)),\n            (new Vector2(-256f, 364f), new Color(127, 151, 220)),\n            (new Vector2(192f, 364f), new Color(205, 113, 232)),\n        };\n\n        foreach ((Vector2 offset, Color color) in feeds)\n        {\n            Vector2 start = helmCenter + offset;\n            Vector2 elbow = new(start.X, helmCenter.Y + 122f);\n            Vector2 end = new(helmCenter.X, helmCenter.Y + 122f);\n            DrawLine(batch, start, elbow, 7f, new Color(41, 31, 42) * 0.80f);\n            DrawLine(batch, elbow, end, 7f, new Color(41, 31, 42) * 0.80f);\n            DrawLine(batch, start, elbow, 3f, color * 0.50f);\n            DrawLine(batch, elbow, end, 3f, color * 0.50f);\n\n            for (int i = 0; i < 4; i++)\n            {\n                float t = (phase * 0.045f + i * 0.25f) % 1f;\n                Vector2 p = Vector2.Lerp(elbow, end, t);\n                DrawDiamondRune(batch, p, 5f, color * 0.46f);\n            }\n        }\n\n        DrawArcaneSigil(batch, new Vector2(helmCenter.X, helmCenter.Y + 122f), 34f, gold * 0.34f, -phase * 0.16f);\n    }\n\n    private void DrawUpgradeSocket(\n        SpriteBatch batch,'''
if upgrade_marker in service:
    service = service.replace(upgrade_marker, conduit_helper, 1)
elif 'private void DrawUpgradeSocket(' not in service:
    raise SystemExit('Could not locate DrawUpgradeSocket for .5.6 replacement.')

# Draw the authored 4x4 station atlas before the existing sigil/crystal feedback. Existing feedback
# remains additive and gives the machinery a subtle active pulse.
needle = '''        float active = level <= 0 ? 0.28f : 0.48f + level * 0.13f;\n        DrawArcaneSigil(batch, center, 28f + level * 3f, systemColor * active, phase * (0.22f + level * 0.09f));'''
replacement = '''        Texture2D? visual = this.GetAirshipUpgradeVisuals();\n        if (visual is not null)\n        {\n            const int cell = 96;\n            Rectangle source = new((int)system * cell, level * cell, cell, cell);\n            Vector2 origin = new(cell / 2f, 72f);\n            float bob = level <= 0 ? 0f : MathF.Sin(phase * (0.9f + level * 0.08f) + (int)system) * 1.5f;\n            batch.Draw(\n                visual,\n                center + new Vector2(0f, 10f + bob),\n                source,\n                Color.White * (level <= 0 ? 0.76f : 0.96f),\n                0f,\n                origin,\n                1f,\n                SpriteEffects.None,\n                1f\n            );\n        }\n\n        float active = level <= 0 ? 0.18f : 0.34f + level * 0.10f;\n        DrawArcaneSigil(batch, center, 28f + level * 3f, systemColor * active, phase * (0.22f + level * 0.09f));'''
if needle in service:
    service = service.replace(needle, replacement, 1)
elif 'Texture2D? visual = this.GetAirshipUpgradeVisuals();' not in service:
    raise SystemExit('Could not locate DrawUpgradeSocket body for atlas draw injection.')

# The authored station now carries the physical body, so the old generic pylon becomes a restrained
# energy spine instead of visually competing with the new system-specific machinery.
service = service.replace(
    '''            24f + level * 5f,\n            systemColor * (0.54f + level * 0.12f),\n            gold * (0.34f + level * 0.14f)''',
    '''            14f + level * 3f,\n            systemColor * (0.34f + level * 0.10f),\n            gold * (0.24f + level * 0.10f)''',
    1,
)

service_path.write_text(service, encoding="utf-8")

# Version metadata.
manifest_path = SRC / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["Version"] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

csproj_path = SRC / "Cardcha.csproj"
csproj = csproj_path.read_text(encoding="utf-8")
csproj = re.sub(r"<Version>[^<]+</Version>", f"<Version>{VERSION}</Version>", csproj, count=1)
csproj_path.write_text(csproj, encoding="utf-8")

(SRC / "Directory.Build.targets").write_text(f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .4.14.4.5.6 Airship Interior Upgrade Visual Pass. -->\n  <Target Name="CardchaAlpha280414456Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n''', encoding="utf-8")

# Milestone handoff for future chats.
doc = ROOT / "docs" / "alpha28-0637-airship-interior-upgrade-visual.md"
doc.write_text(f'''# Cardcha {VERSION} — Airship Interior Upgrade Visual Pass\n\n## Scope\n- Adds a real authored `airship_upgrade_visuals.png` atlas: four systems × levels 0–3.\n- Aether Engine, Navigation Core, Hull & Shield, and Arcane Reactor now have distinct physical machinery silhouettes.\n- Level 0→3 changes the actual station art, not only glow/pips.\n- Adds visible conduit feeds from the four infrastructure stations toward the central navigation dais.\n- Keeps the existing upgrade UI, Magic Dust spending, persistence, travel flow, and save-facing system IDs unchanged.\n\n## Intentionally unchanged\n- No permanent gameplay bonuses are enabled yet.\n- Existing layered exterior Airship assets remain unchanged.\n- Gate relocation and Boss Energy x1/3 pacing remain unchanged.\n- MiMi attic visual rebuild is the next separate milestone.\n\n## Test\nUse `cardcha_test_airship` to warp directly to the bridge. Use `cardcha_give_dust 100` to test level 0→3 visuals quickly.\n''', encoding="utf-8")

print(f"Prepared {VERSION} Airship interior upgrade visual pass")
print(f"Generated {ATLAS.name}: {atlas.size}")

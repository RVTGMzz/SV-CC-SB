from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
ASSETS = CARDCHA / "assets"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.6"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.7"

EXPECTED_INPUT_HASHES = {
    "airship_deck_stardew.png": "b0fbe6046a2555c8c2a1ccf69e40bcd91592a38dd334162ed3c454b348e889f5",
    "sky_dock_stardew.png": "9a261a09f633cbe37a5d2bf333b0d806fcff5cf777ce98e7da86258c63ad03d1",
    "airship_upgrade_visuals.png": "f86b7b69f6a8305189eb9049a78fba115f6c508917dd914695b851426723a16f",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    require(old in text, f"missing anchor for {label}: {old[:120]}")
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# Preconditions + version bump.
# -----------------------------------------------------------------------------
for name, digest in EXPECTED_INPUT_HASHES.items():
    p = ASSETS / name
    require(p.is_file(), f"missing 0648 input asset {name}")
    require(sha256(p) == digest, f"unexpected 0648 input hash for {name}: {sha256(p)}")

for rel in ("manifest.json", "Cardcha.csproj", "Directory.Build.targets"):
    p = CARDCHA / rel
    text = read(p)
    if NEW_VERSION not in text:
        require(OLD_VERSION in text, f"missing version anchor in {rel}")
        write(p, text.replace(OLD_VERSION, NEW_VERSION))

# -----------------------------------------------------------------------------
# TMX acceptance fix: a real wall/floor split, closed side/bottom shell, only the two-tile
# doorway lane remains open. Collision is represented by the same backdrop GID so there are no
# invisible substitute tiles or pickup objects.
# -----------------------------------------------------------------------------
def patch_collision(path: Path, wall_last_row: int) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    width = int(root.attrib["width"])
    height = int(root.attrib["height"])
    layers = {layer.attrib["name"]: layer for layer in root.findall("layer")}
    require("Back" in layers and "Buildings" in layers, f"{path.name}: missing Back/Buildings")

    def parse(layer):
        data = layer.find("data")
        require(data is not None and data.attrib.get("encoding") == "csv", f"{path.name}: non-CSV layer")
        tokens = [int(t.strip()) for t in (data.text or "").strip().split(",")]
        require(len(tokens) == width * height, f"{path.name}: bad token count {len(tokens)}")
        return data, tokens

    _, back = parse(layers["Back"])
    buildings_data, buildings = parse(layers["Buildings"])

    def block(x: int, y: int) -> None:
        if 0 <= x < width and 0 <= y < height:
            buildings[y * width + x] = back[y * width + x]

    # Everything above the floor line is architecture, not walkable floor.
    for y in range(0, wall_last_row + 1):
        for x in range(width):
            block(x, y)

    # Side walls are closed all the way down.
    for y in range(height):
        block(0, y)
        block(width - 1, y)

    # Bottom edge is completely sealed except the exact two-tile doorway recognized by
    # IsBottomDoorwayZone: center-1 and center. This removes the old third gap that let the
    # farmer slip into the black void and walk sideways outside the room.
    center = width // 2
    bottom = height - 1
    for x in range(width):
        buildings[bottom * width + x] = back[bottom * width + x]
    for x in (center - 1, center):
        buildings[bottom * width + x] = 0

    rows = []
    for y in range(height):
        rows.append(",".join(str(v) for v in buildings[y * width:(y + 1) * width]))
    buildings_data.text = "\n" + ",\n".join(rows) + "\n  "

    # Keep metadata explicit for future regression checks.
    props = root.find("properties")
    if props is not None:
        for prop in props.findall("property"):
            if prop.attrib.get("name") == "CardchaAirshipVersion":
                prop.attrib["value"] = "alpha.28.0.4.14.4.5.12.7"
            if prop.attrib.get("name") == "CardchaArchitecture":
                value = prop.attrib.get("value", "")
                if "sealed-room-shell" not in value:
                    prop.attrib["value"] = value + "|sealed-room-shell|two-tile-doorway"

    tree.write(path, encoding="UTF-8", xml_declaration=True)


patch_collision(ASSETS / "airship_deck.tmx", wall_last_row=7)
patch_collision(ASSETS / "sky_dock_interior.tmx", wall_last_row=8)

# -----------------------------------------------------------------------------
# Backdrop polish: visibly separate wall from floor, align service pads to the exact runtime
# machine centers, and raise ambient readability without returning to neon fantasy colors.
# -----------------------------------------------------------------------------
OUTLINE = (42, 29, 30, 255)
FLOOR_DARK = (67, 44, 38, 255)
FLOOR = (101, 66, 50, 255)
FLOOR_HI = (126, 82, 57, 255)
WOOD_DARK = (74, 46, 39, 255)
BRASS_DARK = (122, 82, 45, 255)
BRASS = (191, 137, 72, 255)
BRASS_HI = (224, 177, 105, 255)
TEAL = (105, 181, 184, 255)
BLUE = (99, 144, 166, 255)
VIOLET = (151, 116, 155, 255)
CREAM = (229, 205, 164, 255)
SHADOW = (47, 33, 34, 255)


def warm_lift(im: Image.Image, factor: float = 1.10) -> Image.Image:
    im = ImageEnhance.Brightness(im).enhance(factor)
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            # Tiny warm lift only in the darker half of the palette.
            lum = (r + g + b) / 3
            if lum < 135:
                r = min(255, int(r * 0.98 + 9))
                g = min(255, int(g * 0.98 + 7))
                b = min(255, int(b * 0.97 + 4))
            px[x, y] = (r, g, b, a)
    return im


def rect(draw: ImageDraw.ImageDraw, xy, fill, outline=None, width=1):
    draw.rectangle(xy, fill=fill)
    if outline is not None:
        x0, y0, x1, y1 = xy
        for i in range(width):
            draw.rectangle((x0 + i, y0 + i, x1 - i, y1 - i), outline=outline)


def line(draw: ImageDraw.ImageDraw, pts, fill, width=1):
    draw.line(pts, fill=fill, width=width)


def draw_floor(draw: ImageDraw.ImageDraw, width: int, y0: int, y1: int):
    rect(draw, (1, y0, width - 2, y1), FLOOR)
    line(draw, [(1, y0), (width - 2, y0)], BRASS_DARK, 2)
    # Stardew-like board rhythm: strong vertical boards, staggered short seams.
    for x in range(8, width - 1, 16):
        line(draw, [(x, y0 + 2), (x, y1)], FLOOR_DARK, 1)
        if x + 1 < width:
            line(draw, [(x + 1, y0 + 2), (x + 1, y1)], FLOOR_HI, 1)
    row = 0
    for y in range(y0 + 16, y1, 16):
        offset = 8 if row % 2 else 0
        for x in range(offset, width, 32):
            line(draw, [(x, y), (min(width - 2, x + 16), y)], FLOOR_DARK, 1)
        row += 1


def draw_station_pad(draw: ImageDraw.ImageDraw, cx: int, cy: int, accent):
    # The center is the exact TMX tile center used by the runtime machine renderer.
    rect(draw, (cx - 24, cy - 13, cx + 24, cy + 18), SHADOW, OUTLINE, 1)
    rect(draw, (cx - 21, cy - 10, cx + 21, cy + 14), WOOD_DARK, BRASS_DARK, 1)
    rect(draw, (cx - 18, cy + 9, cx + 18, cy + 13), BRASS)
    rect(draw, (cx - 16, cy - 7, cx - 11, cy - 4), accent)
    rect(draw, (cx + 11, cy - 7, cx + 16, cy - 4), accent)
    rect(draw, (cx - 5, cy + 14, cx + 5, cy + 17), BRASS_HI)


# Airship: floor begins exactly at row 8, matching the new collision boundary.
deck_path = ASSETS / "airship_deck_stardew.png"
deck = warm_lift(Image.open(deck_path).convert("RGBA"), 1.11)
d = ImageDraw.Draw(deck)
draw_floor(d, deck.width, 128, 222)

# Central transit runner is floor furniture, not a doorway painted into a wall.
rect(d, (174, 128, 210, 222), (82, 54, 59, 255), OUTLINE, 1)
rect(d, (176, 130, 178, 220), BRASS_DARK)
rect(d, (206, 130, 208, 220), BRASS_DARK)
for y in range(140, 216, 24):
    d.polygon([(192, y - 3), (195, y), (192, y + 3), (189, y)], fill=BRASS_DARK)

# Exact machine centers for sockets (5,9), (18,9), (8,10), (15,10).
# 0648 had all four pads shifted -8px/-8px, which made the machine sprite look pasted off-table.
for cx, cy, accent in [
    (88, 152, TEAL),
    (296, 152, BLUE),
    (136, 168, VIOLET),
    (248, 168, (160, 120, 158, 255)),
]:
    draw_station_pad(d, cx, cy, accent)

# ChaCha resonance alcove is moved to the far-right wall so the right system console no longer
# sits directly under the station and blocks the approach lane.
rect(d, (338, 61, 376, 102), SHADOW, OUTLINE, 1)
line(d, [(341, 96), (341, 76), (346, 68), (357, 63), (368, 68), (373, 76), (373, 96)], BRASS, 2)
rect(d, (345, 91, 369, 98), WOOD_DARK, BRASS_DARK, 1)
rect(d, (354, 76, 360, 83), VIOLET, OUTLINE, 1)
d.point((357, 79), fill=CREAM)

deck.save(deck_path, optimize=True)

# Sky Dock: floor starts at row 9. The route board/boarding frame remain wall-mounted above it.
dock_path = ASSETS / "sky_dock_stardew.png"
dock = warm_lift(Image.open(dock_path).convert("RGBA"), 1.10)
d = ImageDraw.Draw(dock)
draw_floor(d, dock.width, 144, 286)

# Boarding runner stays visually obvious on the floor.
rect(d, (224, 144, 255, 286), (82, 57, 56, 255), OUTLINE, 1)
rect(d, (226, 146, 229, 284), BRASS_DARK)
rect(d, (250, 146, 253, 284), BRASS_DARK)
for y in range(156, 276, 24):
    d.polygon([(240, y - 4), (244, y), (240, y + 4), (236, y)], fill=BRASS)

# Baked utility props, never Furniture items.
rect(d, (38, 170, 66, 191), WOOD_DARK, OUTLINE, 1)
line(d, [(42, 174), (62, 187)], BRASS_DARK, 1)
line(d, [(62, 174), (42, 187)], BRASS_DARK, 1)
rect(d, (401, 177, 433, 202), WOOD_DARK, OUTLINE, 1)
for x in (407, 416, 425):
    line(d, [(x, 181), (x, 197)], BRASS, 1)

dock.save(dock_path, optimize=True)

# Upgrade atlas: retain silhouettes/levels but lift dark values so active equipment reads in the
# room. Alpha remains untouched and no smoothing/resampling occurs.
atlas_path = ASSETS / "airship_upgrade_visuals.png"
atlas = Image.open(atlas_path).convert("RGBA")
px = atlas.load()
for y in range(atlas.height):
    for x in range(atlas.width):
        r, g, b, a = px[x, y]
        if a == 0:
            continue
        lum = (r + g + b) / 3
        boost = 1.16 if lum < 125 else 1.08
        r = min(255, int(r * boost + 3))
        g = min(255, int(g * boost + 3))
        b = min(255, int(b * boost + 2))
        px[x, y] = (r, g, b, a)
atlas.save(atlas_path, optimize=True)

# -----------------------------------------------------------------------------
# Runtime visual alignment + always-on low machine glow.
# -----------------------------------------------------------------------------
renderer_path = CARDCHA / "Services" / "AirshipInteriorStardewRenderer.cs"
renderer = read(renderer_path)
renderer = replace_once(
    renderer,
    'Vector2 center = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 34f);',
    'Vector2 center = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 54f);',
    "machine vertical mount alignment",
)
renderer = replace_once(
    renderer,
    '            Rectangle shadow = new((int)center.X - 56, (int)center.Y + 31, 112, 15);\n            DrawRect(batch, shadow, new Color(28, 21, 28) * 0.42f);\n\n            Rectangle dst = new((int)center.X - 56, (int)center.Y - 76, 112, 112);\n            batch.Draw(atlas, dst, src, Color.White);\n\n            if (level > 0)\n            {\n                float pulse = 0.55f + 0.20f * MathF.Sin(phase * 2.0f + column * 1.3f);',
    '            float idlePulse = 0.52f + 0.12f * MathF.Sin(phase * 1.65f + column * 1.1f);\n            // A soft pixel glow exists even at level 0 so every machine reads as powered equipment.\n            DrawRect(batch, new Rectangle((int)center.X - 43, (int)center.Y - 48, 86, 58), accent * (0.055f + idlePulse * 0.035f));\n            DrawRect(batch, new Rectangle((int)center.X - 31, (int)center.Y - 37, 62, 39), accent * (0.060f + idlePulse * 0.040f));\n\n            Rectangle shadow = new((int)center.X - 56, (int)center.Y + 31, 112, 15);\n            DrawRect(batch, shadow, new Color(28, 21, 28) * 0.42f);\n\n            Rectangle dst = new((int)center.X - 56, (int)center.Y - 76, 112, 112);\n            batch.Draw(atlas, dst, src, Color.White);\n            DrawRect(batch, new Rectangle((int)center.X - 15, (int)center.Y - 25, 30, 3), accent * (0.34f + idlePulse * 0.18f));\n\n            if (level > 0)\n            {\n                float pulse = 0.55f + 0.20f * MathF.Sin(phase * 2.0f + column * 1.3f);',
    "always-on machine glow",
)
write(renderer_path, renderer)

# -----------------------------------------------------------------------------
# Airship logic: helm interaction target is on the walkable floor edge, not inside the wall.
# Decor marker bumps so old runtime room state cannot masquerade as 0648A.
# -----------------------------------------------------------------------------
air_path = CARDCHA / "Services" / "AirshipFoundationService.cs"
air = read(air_path)
air = replace_once(
    air,
    'private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12.6";',
    'private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12.7";',
    "Airship decor version",
)
air = replace_once(
    air,
    'return new Point(Math.Clamp(width / 2, 2, width - 3), Math.Clamp(4, 2, height - 3));',
    'return new Point(Math.Clamp(width / 2, 2, width - 3), Math.Clamp(8, 2, height - 3));',
    "helm floor interaction target",
)
write(air_path, air)

# -----------------------------------------------------------------------------
# ChaCha station: separate wall visual from the floor interaction point. The old (19,5) station
# shared space with the right console/collision block, making the player squeeze into furniture.
# -----------------------------------------------------------------------------
chacha_path = CARDCHA / "Services" / "ChaChaSkillMaterialService.cs"
chacha = read(chacha_path)
chacha = replace_once(
    chacha,
    '    private static readonly Point StationTile = new(19, 5);',
    '    private static readonly Point StationVisualTile = new(21, 5);\n    private static readonly Point StationInteractionTile = new(21, 8);',
    "ChaCha station split anchors",
)
chacha = chacha.replace('StationTile.X', 'StationInteractionTile.X').replace('StationTile.Y', 'StationInteractionTile.Y')
# The drawing center must use the visual anchor, not the floor interaction anchor.
chacha = replace_once(
    chacha,
    'new Vector2(StationInteractionTile.X * 64f + 32f, StationInteractionTile.Y * 64f + 34f)',
    'new Vector2(StationVisualTile.X * 64f + 32f, StationVisualTile.Y * 64f + 34f)',
    "ChaCha visual anchor",
)
chacha = replace_once(
    chacha,
    'return $"AirshipStation={StationInteractionTile.X},{StationInteractionTile.Y} | RegionDropRegular=',
    'return $"AirshipStationVisual={StationVisualTile.X},{StationVisualTile.Y} | AirshipStationUse={StationInteractionTile.X},{StationInteractionTile.Y} | RegionDropRegular=',
    "ChaCha station diagnostics",
)
write(chacha_path, chacha)

# -----------------------------------------------------------------------------
# MiMi clock acceptance fix. cardcha_test_attic now enables a runtime-only routine preview, so
# world_settime 1720/1730/2000/2200 visibly exercises HOME/TV/TV/LATE without mutating hearts or
# story progression. Normal gameplay still requires six hearts for the TV routine.
# -----------------------------------------------------------------------------
home_path = CARDCHA / "Services" / "MimiHomeService.cs"
home = read(home_path)
home = replace_once(home, 'private static readonly Point DefaultHomeTile = new(10, 6);', 'private static readonly Point DefaultHomeTile = new(9, 8);', "MiMi home anchor")
home = replace_once(home, 'private static readonly Point[] HomeIdleTiles = { new(10, 6), new(9, 7), new(10, 7), new(11, 7), new(10, 8) };', 'private static readonly Point[] HomeIdleTiles = { new(9, 8), new(8, 8), new(10, 8), new(9, 9), new(10, 9) };', "MiMi home idle pool")
home = replace_once(
    home,
    '    private string? DebugRoutineOverride;\n    private string? ActiveHomeRoutineState;',
    '    private string? DebugRoutineOverride;\n    private bool TestAtticRoutinePreview;\n    private int LastObservedRoutineTime = -1;\n    private string? ActiveHomeRoutineState;',
    "MiMi preview runtime fields",
)
home = replace_once(
    home,
    '        if (!this.Save.Data.MimiMeetupCompleted)\n            return;',
    '        if (!this.Save.Data.MimiMeetupCompleted && !this.TestAtticRoutinePreview)\n            return;',
    "MiMi preview update bypass",
)
home = replace_once(
    home,
    '        if (!this.Save.Data.MimiMeetupCompleted\n            || this.StoryOwnsMimiActor()\n            || this.MysteryOwnsMimiActor())',
    '        if ((!this.Save.Data.MimiMeetupCompleted && !this.TestAtticRoutinePreview)\n            || this.StoryOwnsMimiActor()\n            || this.MysteryOwnsMimiActor())',
    "MiMi preview schedule bypass",
)
home = replace_once(
    home,
    '        bool weekday = IsWeekday();\n        bool workHours = weekday && Game1.timeOfDay >= WorkStart && Game1.timeOfDay < WorkEnd;',
    '        bool weekday = IsWeekday();\n        bool workHours = !this.TestAtticRoutinePreview && weekday && Game1.timeOfDay >= WorkStart && Game1.timeOfDay < WorkEnd;',
    "MiMi preview stays home",
)
home = replace_once(
    home,
    '            string state = this.IsSecretTvRoutineNow()\n                ? "tv"\n                : this.IsSecretTvRoutineUnlocked() && Game1.timeOfDay >= SecretTvEnd\n                    ? "late"\n                    : "home";',
    '            bool routineUnlocked = this.IsSecretTvRoutineUnlocked() || this.TestAtticRoutinePreview;\n            string state = routineUnlocked && Game1.timeOfDay >= SecretTvStart && Game1.timeOfDay < SecretTvEnd\n                ? "tv"\n                : routineUnlocked && Game1.timeOfDay >= SecretTvEnd\n                    ? "late"\n                    : "home";\n            if (this.LastObservedRoutineTime != Game1.timeOfDay)\n            {\n                this.LastObservedRoutineTime = Game1.timeOfDay;\n                this.NextHomeWanderDecisionAtMs = 0;\n            }',
    "MiMi clock-derived state",
)
home = replace_once(
    home,
    '        this.DebugRoutineOverride = null;\n        this.ResetHomeWanderRuntime();',
    '        this.DebugRoutineOverride = null;\n        this.TestAtticRoutinePreview = false;\n        this.LastObservedRoutineTime = -1;\n        this.ResetHomeWanderRuntime();',
    "MiMi title reset",
)
# Enter/leave cardcha_test_attic: runtime-only clock preview follows the test room session.
home = replace_once(
    home,
    '            Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);\n            return "Attic TEST bypass: returned to WizardHouse. Normal progression was not changed.";',
    '            this.TestAtticRoutinePreview = false;\n            this.LastObservedRoutineTime = -1;\n            this.ResetHomeWanderRuntime();\n            Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);\n            this.EnforceSchedule();\n            return "Attic TEST bypass: returned to WizardHouse. Runtime clock preview disabled; normal progression was not changed.";',
    "MiMi test attic leave",
)
home = replace_once(
    home,
    '        Point arrival = this.ResolveAtticStairTile(attic);\n        this.AtticAutoExitBlockedUntilMs = Environment.TickCount64 + 850;\n        Game1.warpFarmer(AtticLocationName, arrival.X, Math.Max(1, arrival.Y - 1), 0);\n        return "Attic TEST bypass: warped to Cardcha_MiMiAttic. Run cardcha_test_attic again to leave. Normal progression was not changed.";',
    '        Point arrival = this.ResolveAtticStairTile(attic);\n        this.TestAtticRoutinePreview = true;\n        this.LastObservedRoutineTime = -1;\n        this.ResetHomeWanderRuntime();\n        this.AtticAutoExitBlockedUntilMs = Environment.TickCount64 + 850;\n        this.EnforceSchedule();\n        Game1.warpFarmer(AtticLocationName, arrival.X, Math.Max(1, arrival.Y - 1), 0);\n        return "Attic TEST bypass: warped to Cardcha_MiMiAttic. Runtime clock preview ON, so world_settime 1720/1730/2000/2200 tests HOME/TV/TV/LATE without changing hearts/story. Run cardcha_test_attic again to leave.";',
    "MiMi test attic enter",
)
home = replace_once(
    home,
    'return $"MiMiHome=Attic({attic is not null}) | AtticAccess={this.GetMimiHearts()}/{AtticAccessHearts} hearts | WizardStair={wizardStair.X},{wizardStair.Y} | WorkRoute={route} | WorkHours=11:00-17:00 | SecretTV={secretTv} 17:30-22:00 | DebugRoutine={this.DebugRoutineOverride ?? "auto"} | RoutineState={this.ActiveHomeRoutineState ?? "<none>"} | WanderTarget={wanderTile.X},{wanderTile.Y} | Actor={actorTile}";',
    'return $"MiMiHome=Attic({attic is not null}) | AtticAccess={this.GetMimiHearts()}/{AtticAccessHearts} hearts | WizardStair={wizardStair.X},{wizardStair.Y} | WorkRoute={route} | WorkHours=11:00-17:00 | SecretTV={secretTv} 17:30-22:00 | TestClockPreview={this.TestAtticRoutinePreview} | Clock={Game1.timeOfDay} | DebugRoutine={this.DebugRoutineOverride ?? "auto"} | RoutineState={this.ActiveHomeRoutineState ?? "<none>"} | WanderTarget={wanderTile.X},{wanderTile.Y} | Actor={actorTile}";',
    "MiMi routine diagnostics",
)
# State transitions are acceptance-critical; log them at Trace so a screenshot/log proves what owns MiMi.
home = replace_once(
    home,
    '        if (stateChanged || actorNeedsRecovery)\n        {\n            PlaceMimi(mimi, attic, anchor, anchorFacing);',
    '        if (stateChanged || actorNeedsRecovery)\n        {\n            if (stateChanged)\n                this.Monitor.Log($"MiMi attic routine -> {state.ToUpperInvariant()} at {Game1.timeOfDay} (preview={this.TestAtticRoutinePreview}, hearts={this.GetMimiHearts()}).", LogLevel.Trace);\n            PlaceMimi(mimi, attic, anchor, anchorFacing);',
    "MiMi transition trace",
)
write(home_path, home)

# -----------------------------------------------------------------------------
# Audit snapshot for CI/package inspection.
# -----------------------------------------------------------------------------
audit = {
    "version": NEW_VERSION,
    "scope": "0648A acceptance hotfix",
    "airship": {
        "wallCollisionRows": "0-7",
        "bottomDoorway": [11, 12],
        "helmUseTile": [12, 8],
        "machinePadCentersNative": [[88, 152], [296, 152], [136, 168], [248, 168]],
        "machineGlow": "always-on-soft-pixel",
        "machineVerticalMountOffset": 54,
    },
    "skyDock": {
        "wallCollisionRows": "0-8",
        "bottomDoorway": [14, 15],
    },
    "chacha": {
        "visualTile": [21, 5],
        "interactionTile": [21, 8],
    },
    "mimi": {
        "homeAnchor": [9, 8],
        "testClockPreview": True,
        "clockStates": {"1720": "home", "1730": "tv", "2000": "tv", "2200": "late"},
        "normalTvHeartRequirement": 6,
    },
    "hashes": {
        "airship_deck_stardew.png": sha256(deck_path),
        "sky_dock_stardew.png": sha256(dock_path),
        "airship_upgrade_visuals.png": sha256(atlas_path),
    },
}
(ASSETS / "airship_0648a_acceptance_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
print(f"Prepared Cardcha {NEW_VERSION}: sealed Airship rooms, aligned/glowing machines, clear ChaCha station, and MiMi clock-preview acceptance fix.")

from pathlib import Path
from collections import deque
from PIL import Image, ImageDraw
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
ASSETS = CARDCHA / "assets"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.5"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.6"

EXPECTED_INPUT_HASHES = {
    "airship_deck_stardew.png": "090ae974a3e745e0cc076535e0be4a65be3fbbc2edfa67afca307f70a689b7c5",
    "sky_dock_stardew.png": "451625532b1c9914fcfd17e824a6f2bc293a2b0d31ccb4c9af1dbf811ebed3e8",
    "airship_upgrade_visuals.png": "adb9ae6cd91a516651c5c6fc8a2c3fd962ba5878e083317064bcbc44bdd065ac",
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


# -----------------------------------------------------------------------------
# Preconditions + version bump.
# -----------------------------------------------------------------------------
for name, digest in EXPECTED_INPUT_HASHES.items():
    p = ASSETS / name
    require(p.is_file(), f"missing input asset {name}")
    require(sha256(p) == digest, f"unexpected 0647E input hash for {name}: {sha256(p)}")

for rel in ("manifest.json", "Cardcha.csproj", "Directory.Build.targets"):
    p = CARDCHA / rel
    text = read(p)
    if NEW_VERSION not in text:
        require(OLD_VERSION in text, f"missing version anchor in {rel}")
        write(p, text.replace(OLD_VERSION, NEW_VERSION))

# Keep the Airship service decor marker version in sync without touching gameplay logic.
service_path = CARDCHA / "Services" / "AirshipFoundationService.cs"
service = read(service_path)
service = service.replace(
    'private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12.5";',
    'private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12.6";'
)

# Forest Gate palette: lower neon, warmer stone/brass, softer portal colors. Geometry, route,
# 160px action radius and farmer-depth ownership stay untouched.
replacements = {
    'float pulse = 0.62f + 0.16f * (float)Math.Sin(Environment.TickCount64 / 260.0);':
        'float pulse = 0.52f + 0.08f * (float)Math.Sin(Environment.TickCount64 / 300.0);',
    'Color violet = new Color(176, 105, 255) * pulse;':
        'Color violet = new Color(148, 112, 166) * pulse;',
    'Color cyan = new Color(87, 222, 246) * (pulse * 0.94f);':
        'Color cyan = new Color(110, 181, 188) * (pulse * 0.86f);',
    'Color gold = new Color(224, 171, 82) * 0.96f;':
        'Color gold = new Color(199, 151, 78) * 0.94f;',
    'Color stoneDark = new Color(47, 43, 56) * 0.98f;':
        'Color stoneDark = new Color(57, 48, 51) * 0.98f;',
    'Color stone = new Color(82, 76, 91) * 0.98f;':
        'Color stone = new Color(90, 77, 74) * 0.98f;',
    'Color stoneLight = new Color(118, 108, 119) * 0.88f;':
        'Color stoneLight = new Color(126, 111, 102) * 0.86f;',
    'new Color(84, 72, 171) * 0.92f,':
        'new Color(77, 82, 129) * 0.90f,',
    'new Color(85, 159, 218) * 0.90f,':
        'new Color(105, 151, 174) * 0.88f,',
    'new Color(226, 175, 197) * 0.78f);':
        'new Color(190, 161, 163) * 0.72f);',
    'DrawPortalClouds(batch, aperture, phase, Color.White * 0.48f);':
        'DrawPortalClouds(batch, aperture, phase, new Color(235, 222, 201) * 0.40f);',
    'DrawArcaneSparkles(batch, new Vector2(center.X, center.Y - 24f), 73f, 14, phase, Color.White * 0.62f);':
        'DrawArcaneSparkles(batch, new Vector2(center.X, center.Y - 24f), 70f, 10, phase, new Color(235, 222, 201) * 0.42f);',
    'DrawCrystalPylon(batch, new Vector2(center.X - 104f, center.Y + 48f), 58f, cyan, gold);':
        'DrawCrystalPylon(batch, new Vector2(center.X - 102f, center.Y + 48f), 48f, cyan, gold);',
    'DrawCrystalPylon(batch, new Vector2(center.X + 104f, center.Y + 48f), 58f, violet, gold);':
        'DrawCrystalPylon(batch, new Vector2(center.X + 102f, center.Y + 48f), 48f, violet, gold);',
}
for old, new in replacements.items():
    require(old in service, f"missing gate visual anchor: {old[:70]}")
    service = service.replace(old, new, 1)
write(service_path, service)

# -----------------------------------------------------------------------------
# TMX metadata only. Collision and CSV data are intentionally untouched.
# -----------------------------------------------------------------------------
for name in ("airship_deck.tmx", "sky_dock_interior.tmx"):
    p = ASSETS / name
    text = read(p)
    text = text.replace("alpha.28.0.4.14.4.5.12.5", "alpha.28.0.4.14.4.5.12.6")
    text = text.replace(
        'cardcha-backdrop|physical-buildings-collision|dynamic-machines|no-pickup-props',
        'cardcha-backdrop|physical-buildings-collision|dynamic-machines|no-pickup-props|stardew-visual-pass1'
    )
    if name == "airship_deck.tmx":
        text = text.replace(
            'stardew-airship-bridge|warm-wood-brass|panoramic-canopy|physical-machinery',
            'stardew-airship-bridge|warm-wood-brass|panoramic-canopy|physical-machinery|cozy-control-room'
        )
    else:
        text = text.replace(
            'stardew-airship-dock|service-platform|physical-console|boarding-aperture',
            'stardew-airship-dock|service-platform|physical-console|boarding-aperture|transit-station'
        )
    write(p, text)

# -----------------------------------------------------------------------------
# Pixel-art helpers. Everything stays at the native 1x TMX pixel scale. No smoothing.
# -----------------------------------------------------------------------------
COMMON_MAP = {
    (100, 57, 43, 255): (112, 66, 46, 255),
    (48, 29, 35, 255): (52, 33, 34, 255),
    (22, 15, 23, 255): (27, 20, 22, 255),
    (74, 42, 37, 255): (82, 48, 40, 255),
    (62, 36, 42, 255): (69, 41, 42, 255),
    (126, 73, 49, 255): (139, 83, 53, 255),
    (104, 68, 43, 255): (116, 78, 47, 255),
    (151, 91, 58, 255): (164, 103, 62, 255),
    (163, 109, 55, 255): (184, 129, 67, 255),
    (181, 117, 72, 255): (194, 136, 80, 255),
    (211, 153, 70, 255): (215, 158, 81, 255),
    (55, 36, 66, 255): (67, 47, 53, 255),
    (79, 48, 90, 255): (91, 61, 70, 255),
    (38, 49, 88, 255): (48, 58, 88, 255),
    (55, 79, 125, 255): (68, 91, 126, 255),
    (74, 120, 158, 255): (92, 133, 159, 255),
    (117, 158, 181, 255): (139, 170, 184, 255),
    (45, 92, 109, 255): (68, 106, 113, 255),
    (75, 190, 205, 255): (102, 181, 187, 255),
    (154, 95, 174, 255): (151, 110, 160, 255),
    (111, 67, 126, 255): (112, 81, 116, 255),
}

OUTLINE = (38, 27, 29, 255)
WOOD_DARK = (72, 43, 37, 255)
WOOD = (124, 73, 48, 255)
BRASS_DARK = (118, 78, 42, 255)
BRASS = (192, 136, 69, 255)
BRASS_HI = (224, 173, 98, 255)
CREAM = (221, 194, 151, 255)
TEAL = (97, 171, 177, 255)
BLUE = (88, 130, 156, 255)
VIOLET = (144, 105, 153, 255)
SHADOW = (44, 31, 32, 255)


def recolor(im: Image.Image, mapping: dict) -> Image.Image:
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            color = px[x, y]
            if color in mapping:
                px[x, y] = mapping[color]
    return im


def rect(draw, xy, fill, outline=None, width=1):
    draw.rectangle(xy, fill=fill)
    if outline is not None:
        x0, y0, x1, y1 = xy
        for i in range(width):
            draw.rectangle((x0 + i, y0 + i, x1 - i, y1 - i), outline=outline)


def line(draw, pts, fill, width=1):
    draw.line(pts, fill=fill, width=width)


def rivet(draw, x, y, color=BRASS_HI):
    draw.point((x, y), fill=color)
    draw.point((x + 1, y), fill=BRASS_DARK)


def lamp(draw, x, y, glow=CREAM):
    rect(draw, (x - 2, y, x + 2, y + 7), BRASS_DARK)
    rect(draw, (x - 4, y - 2, x + 4, y + 1), BRASS)
    rect(draw, (x - 3, y - 7, x + 3, y - 2), OUTLINE)
    rect(draw, (x - 2, y - 6, x + 2, y - 3), glow)


def panel(draw, x, y, w, h, accent=TEAL):
    rect(draw, (x, y, x + w - 1, y + h - 1), SHADOW, OUTLINE, 1)
    rect(draw, (x + 2, y + 2, x + w - 3, y + h - 3), WOOD_DARK, BRASS_DARK, 1)
    rect(draw, (x + 5, y + 5, x + w - 6, y + 7), accent)
    for i in range(3):
        rect(draw, (x + 5 + i * 6, y + h - 7, x + 8 + i * 6, y + h - 5), BRASS_HI if i == 0 else CREAM)


def crate(draw, x, y, w=20, h=16):
    rect(draw, (x, y, x + w - 1, y + h - 1), WOOD_DARK, OUTLINE, 1)
    rect(draw, (x + 2, y + 2, x + w - 3, y + h - 3), WOOD, BRASS_DARK, 1)
    line(draw, [(x + 4, y + 3), (x + w - 5, y + h - 4)], BRASS_DARK, 1)
    line(draw, [(x + w - 5, y + 3), (x + 4, y + h - 4)], BRASS_DARK, 1)
    rect(draw, (x + 7, y + h - 5, x + w - 8, y + h - 3), BRASS_DARK)


def rope(draw, cx, cy, r=7):
    for rr in (r, r - 2, r - 4):
        draw.rectangle((cx - rr, cy - rr, cx + rr, cy + rr), outline=BRASS_DARK if rr == r else (159, 109, 58, 255))
    rect(draw, (cx - 2, cy - 1, cx + 2, cy + 1), SHADOW)


# -----------------------------------------------------------------------------
# Airship Deck backdrop: cozy control-room hierarchy, four readable service pads, warm hardware.
# -----------------------------------------------------------------------------
deck_path = ASSETS / "airship_deck_stardew.png"
deck = recolor(Image.open(deck_path).convert("RGBA"), COMMON_MAP)
d = ImageDraw.Draw(deck)

for x in range(28, 360, 28):
    rivet(d, x, 12)
lamp(d, 26, 53, (222, 188, 118, 255))
lamp(d, 358, 53, (222, 188, 118, 255))

# C1: central helm/navigator body. The animated astrolabe renders on top at the exact same anchor.
rect(d, (163, 54, 220, 91), SHADOW, OUTLINE, 1)
rect(d, (167, 58, 216, 87), WOOD_DARK, BRASS_DARK, 1)
rect(d, (174, 63, 209, 69), BLUE, OUTLINE, 1)
for x in (178, 186, 194, 202):
    rect(d, (x, 75, x + 3, 78), BRASS_HI if x in (178, 202) else TEAL)
rect(d, (188, 81, 197, 87), WOOD, BRASS_DARK, 1)
line(d, [(169, 56), (214, 56)], BRASS_HI, 1)
rivet(d, 171, 59)
rivet(d, 212, 59)

# C2/C3: left/right system consoles.
panel(d, 50, 99, 56, 27, TEAL)
panel(d, 278, 99, 56, 27, BLUE)
for bx in (56, 284):
    rect(d, (bx, 108, bx + 8, 113), CREAM, OUTLINE, 1)
    rect(d, (bx + 13, 108, bx + 21, 113), BLUE if bx == 56 else TEAL, OUTLINE, 1)
    line(d, [(bx + 30, 116), (bx + 35, 106)], BRASS_HI, 2)

# C4: four upgrade service pads. The actual level sprites draw above these and collision is TMX-owned.
pads = [
    (80, 144, TEAL),
    (288, 144, BLUE),
    (128, 160, VIOLET),
    (240, 160, (157, 112, 157, 255)),
]
for cx, cy, accent in pads:
    rect(d, (cx - 22, cy - 15, cx + 22, cy + 17), SHADOW, OUTLINE, 1)
    rect(d, (cx - 19, cy - 12, cx + 19, cy + 14), WOOD_DARK, BRASS_DARK, 1)
    rect(d, (cx - 16, cy + 10, cx + 16, cy + 13), BRASS)
    rect(d, (cx - 15, cy - 8, cx - 11, cy - 5), accent)
    rect(d, (cx + 11, cy - 8, cx + 15, cy - 5), accent)
    rivet(d, cx - 18, cy + 12)
    rivet(d, cx + 17, cy + 12)

# C5: ChaCha resonance alcove, clearly equipment rather than household furniture.
rect(d, (294, 63, 334, 96), SHADOW, OUTLINE, 1)
line(d, [(297, 91), (297, 74), (302, 67), (312, 63), (322, 67), (331, 74), (331, 91)], BRASS, 2)
rect(d, (301, 85, 327, 92), WOOD_DARK, BRASS_DARK, 1)
rect(d, (311, 73, 317, 80), VIOLET, OUTLINE, 1)
d.point((314, 76), fill=(219, 176, 215, 255))

# C6: transit lane. Dark wine runner + brass edging reads as Stardew furniture/floor trim, not neon.
rect(d, (174, 100, 210, 222), (77, 49, 57, 255), OUTLINE, 1)
rect(d, (176, 102, 178, 220), BRASS_DARK)
rect(d, (206, 102, 208, 220), BRASS_DARK)
for y in range(112, 214, 24):
    d.polygon([(192, y - 3), (195, y), (192, y + 3), (189, y)], fill=BRASS_DARK)

# Small wall placards balance the bridge without filling the walking lane.
rect(d, (20, 72, 44, 87), WOOD_DARK, OUTLINE, 1)
rect(d, (22, 74, 42, 78), CREAM)
rect(d, (340, 72, 364, 87), WOOD_DARK, OUTLINE, 1)
rect(d, (342, 74, 362, 78), CREAM)

deck.save(deck_path, optimize=True)

# -----------------------------------------------------------------------------
# Sky Dock backdrop: transit station identity, route board, boarding gantry, utility clutter.
# -----------------------------------------------------------------------------
dock_path = ASSETS / "sky_dock_stardew.png"
dock = recolor(Image.open(dock_path).convert("RGBA"), COMMON_MAP)
d = ImageDraw.Draw(dock)

rect(d, (8, 10, 470, 29), (64, 43, 42, 255), OUTLINE, 1)
for x in range(24, 462, 28):
    rivet(d, x, 19)
for x in (30, 240, 450):
    lamp(d, x, 54, (221, 190, 123, 255))

# B2: large route board + standing console.
rect(d, (119, 84, 205, 132), SHADOW, OUTLINE, 1)
rect(d, (123, 88, 201, 128), WOOD_DARK, BRASS_DARK, 1)
rect(d, (130, 94, 194, 100), CREAM)
for yy in (107, 116):
    for i, color in enumerate((TEAL, BRASS_HI, VIOLET, BLUE)):
        rect(d, (131 + i * 14, yy, 139 + i * 14, yy + 4), color)
rect(d, (129, 124, 195, 130), BRASS_DARK)
rect(d, (132, 130, 136, 145), WOOD_DARK, OUTLINE, 1)
rect(d, (188, 130, 192, 145), WOOD_DARK, OUTLINE, 1)

# B3: boarding gantry frame. Preserve the original sky aperture; only hardware surrounds it.
rect(d, (334, 46, 451, 55), SHADOW, OUTLINE, 1)
rect(d, (334, 140, 451, 149), SHADOW, OUTLINE, 1)
rect(d, (334, 55, 344, 140), SHADOW, OUTLINE, 1)
rect(d, (441, 55, 451, 140), SHADOW, OUTLINE, 1)
rect(d, (339, 52, 446, 57), BRASS_DARK)
rect(d, (339, 138, 446, 143), BRASS_DARK)
rect(d, (339, 57, 344, 138), BRASS_DARK)
rect(d, (441, 57, 446, 138), BRASS_DARK)
rect(d, (356, 38, 431, 48), WOOD_DARK, OUTLINE, 1)
for i, color in enumerate((CREAM, TEAL, CREAM, BRASS_HI)):
    rect(d, (362 + i * 16, 41, 371 + i * 16, 44), color)
lamp(d, 349, 93, (202, 190, 126, 255))
lamp(d, 438, 93, (202, 190, 126, 255))

# B1/B3: central boarding lane from entrance to bay.
rect(d, (224, 116, 255, 286), (76, 53, 53, 255), OUTLINE, 1)
rect(d, (226, 118, 229, 284), BRASS_DARK)
rect(d, (250, 118, 253, 284), BRASS_DARK)
for y in range(132, 274, 24):
    d.polygon([(240, y - 4), (244, y), (240, y + 4), (236, y)], fill=BRASS)
for yy in (88, 104):
    line(d, [(232, yy), (240, yy - 4), (248, yy)], CREAM, 1)

# B4: utility/service clutter. These are painted into the map, never pickup Furniture objects.
crate(d, 42, 149, 24, 18)
crate(d, 59, 173, 22, 16)
rope(d, 52, 203, 8)
rect(d, (87, 150, 118, 174), WOOD_DARK, OUTLINE, 1)
for x in (92, 101, 110):
    line(d, [(x, 155), (x, 168)], BRASS, 1)
    d.point((x, 154), fill=TEAL if x == 101 else CREAM)
crate(d, 400, 158, 24, 18)
rect(d, (430, 150, 455, 208), WOOD_DARK, OUTLINE, 1)
for yy in (157, 170, 183, 196):
    rect(d, (434, yy, 451, yy + 5), WOOD, BRASS_DARK, 1)
rivet(d, 447, 160)

# B5: dock beacon and low rail/service pads.
rect(d, (234, 63, 246, 78), SHADOW, OUTLINE, 1)
rect(d, (238, 58, 242, 65), BRASS)
d.polygon([(240, 53), (245, 58), (240, 63), (235, 58)], fill=TEAL)
rect(d, (101, 206, 169, 222), SHADOW, OUTLINE, 1)
rect(d, (311, 206, 379, 222), SHADOW, OUTLINE, 1)
for x in range(108, 164, 14):
    rect(d, (x, 210, x + 8, 213), BRASS_DARK)
for x in range(318, 374, 14):
    rect(d, (x, 210, x + 8, 213), BRASS_DARK)

dock.save(dock_path, optimize=True)

# -----------------------------------------------------------------------------
# Upgrade atlas: remove edge-connected purple cell rectangles and mute neon accents.
# This leaves actual machine outlines intact because only background connected to cell edges clears.
# -----------------------------------------------------------------------------
atlas_path = ASSETS / "airship_upgrade_visuals.png"
atlas = Image.open(atlas_path).convert("RGBA")
px = atlas.load()
old_bg = (47, 15, 47, 255)
for cy in range(4):
    for cx in range(4):
        x0, y0 = cx * 96, cy * 96
        seen = set()
        queue = deque()
        for x in range(x0, x0 + 96):
            for y in (y0, y0 + 95):
                if px[x, y] == old_bg and (x, y) not in seen:
                    seen.add((x, y))
                    queue.append((x, y))
        for y in range(y0, y0 + 96):
            for x in (x0, x0 + 95):
                if px[x, y] == old_bg and (x, y) not in seen:
                    seen.add((x, y))
                    queue.append((x, y))
        while queue:
            x, y = queue.popleft()
            px[x, y] = (0, 0, 0, 0)
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if x0 <= nx < x0 + 96 and y0 <= ny < y0 + 96 and (nx, ny) not in seen and px[nx, ny] == old_bg:
                    seen.add((nx, ny))
                    queue.append((nx, ny))

ATLAS_MAP = {
    (48, 29, 35, 255): (52, 33, 34, 255),
    (175, 143, 79, 255): (186, 146, 82, 255),
    (79, 47, 47, 255): (89, 53, 46, 255),
    (143, 79, 47, 255): (155, 91, 52, 255),
    (111, 79, 47, 255): (123, 88, 50, 255),
    (79, 111, 175, 255): (91, 126, 165, 255),
    (79, 207, 239, 255): (104, 188, 196, 255),
    (175, 111, 239, 255): (155, 118, 178, 255),
    (143, 143, 239, 255): (128, 143, 187, 255),
    (239, 175, 79, 255): (221, 165, 88, 255),
    (207, 143, 239, 255): (179, 135, 189, 255),
    (79, 143, 143, 255): (97, 151, 147, 255),
    (47, 47, 79, 255): (51, 53, 74, 255),
    (79, 47, 79, 255): (82, 56, 72, 255),
    (47, 79, 111, 255): (59, 87, 105, 255),
}
atlas = recolor(atlas, ATLAS_MAP)
atlas.save(atlas_path, optimize=True)

# -----------------------------------------------------------------------------
# Runtime accents: small pixel details only. Heavy room hierarchy lives in the physical map art.
# -----------------------------------------------------------------------------
renderer_path = CARDCHA / "Services" / "AirshipInteriorStardewRenderer.cs"
renderer = r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// 0648 Stardew Visual Pass 1.
/// Heavy architecture lives in TMX/backdrop assets with real Buildings collision.
/// This renderer owns only small animated accents and the four level-aware upgrade machines.
/// </summary>
internal static class AirshipInteriorStardewRenderer
{
    private const string UpgradeAtlasPath = "assets/airship_upgrade_visuals.png";
    private const int CellSize = 96;

    private static Texture2D? UpgradeAtlas;
    private static bool AtlasLoadFailed;

    public static bool TryDrawDeck(SpriteBatch batch, GameLocation deck, SaveService save)
    {
        if (batch is null || deck is null || save is null)
            return false;

        float phase = (float)(Environment.TickCount64 / 1000.0);
        DrawDeckWindowLife(batch, phase);
        DrawWarmDeckAmbient(batch, phase);
        DrawHelmAccent(batch, phase);
        DrawSideConsoleAccent(batch, new Point(5, 7), new Color(100, 174, 176), phase);
        DrawSideConsoleAccent(batch, new Point(18, 7), new Color(101, 139, 164), -phase);
        DrawUpgradeStations(batch, save, phase);
        DrawChaChaPedestalAccent(batch, phase);
        DrawDoorwayThreshold(batch, new Point(12, 12), new Color(173, 133, 72) * 0.48f);
        return true;
    }

    public static bool TryDrawSkyDock(SpriteBatch batch, GameLocation dock)
    {
        if (batch is null || dock is null)
            return false;

        float phase = (float)(Environment.TickCount64 / 1000.0);
        DrawRouteBoardAccent(batch, phase);
        DrawBoardingGantryAccent(batch, phase);
        DrawServiceCornerAccent(batch, phase);
        DrawConsoleLamp(batch, new Point(10, 6), new Color(188, 132, 70), new Color(145, 112, 156), phase);
        DrawConsoleLamp(batch, new Point(24, 6), new Color(188, 132, 70), new Color(96, 168, 174), -phase);
        DrawDoorwayThreshold(batch, new Point(15, 16), new Color(173, 133, 72) * 0.46f);
        return true;
    }

    private static void DrawDeckWindowLife(SpriteBatch batch, float phase)
    {
        Color star = new Color(238, 225, 194) * 0.48f;
        Color blue = new Color(103, 158, 181) * 0.28f;
        for (int i = 0; i < 12; i++)
        {
            int tx = 3 + ((i * 7 + 2) % 18);
            int ty = 1 + ((i * 5 + 1) % 3);
            Vector2 p = WorldToScreen(tx * 64f + 13f + (i % 3) * 12f, ty * 64f + 9f + (i % 2) * 13f);
            float pulse = 0.38f + 0.12f * MathF.Sin(phase * 1.35f + i * 0.9f);
            DrawRect(batch, new Rectangle((int)p.X, (int)p.Y, 3, 3), (i % 4 == 0 ? blue : star) * pulse);
        }
    }

    private static void DrawWarmDeckAmbient(SpriteBatch batch, float phase)
    {
        Color brass = new Color(199, 148, 78) * 0.54f;
        Color warm = new Color(230, 196, 126) * (0.34f + 0.05f * MathF.Sin(phase * 1.6f));
        foreach (Point tile in new[] { new Point(2, 4), new Point(21, 4) })
        {
            Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 18f);
            DrawRect(batch, new Rectangle((int)c.X - 8, (int)c.Y - 3, 16, 3), brass);
            DrawRect(batch, new Rectangle((int)c.X - 3, (int)c.Y - 8, 6, 5), warm);
        }
    }

    private static void DrawHelmAccent(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(12f * 64f + 32f, 4f * 64f + 18f);
        Color dark = new Color(48, 33, 34) * 0.90f;
        Color brass = new Color(199, 148, 78) * 0.82f;
        Color teal = new Color(100, 174, 176) * 0.58f;
        Color violet = new Color(145, 112, 156) * 0.42f;

        DrawPixelRing(batch, c, 22, dark);
        DrawPixelRing(batch, c, 18, brass);
        DrawPixelRing(batch, c, 12, violet);
        int needle = (int)(MathF.Sin(phase * 1.1f) * 7f);
        DrawRect(batch, new Rectangle((int)c.X - 2, (int)c.Y - 14 + needle / 4, 4, 28), teal);
        DrawRect(batch, new Rectangle((int)c.X - 13, (int)c.Y - 2, 26, 4), brass * 0.70f);
        DrawDiamond(batch, c, 7, teal);
    }

    private static void DrawSideConsoleAccent(SpriteBatch batch, Point tile, Color accent, float phase)
    {
        Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 24f);
        Color brass = new Color(197, 145, 76) * 0.58f;
        float blink = 0.36f + 0.10f * MathF.Sin(phase * 1.9f + tile.X * 0.3f);
        DrawRect(batch, new Rectangle((int)c.X - 18, (int)c.Y - 5, 9, 4), accent * blink);
        DrawRect(batch, new Rectangle((int)c.X - 4, (int)c.Y - 5, 8, 4), brass);
        DrawRect(batch, new Rectangle((int)c.X + 9, (int)c.Y - 5, 9, 4), accent * (blink * 0.85f));
    }

    private static void DrawUpgradeStations(SpriteBatch batch, SaveService save, float phase)
    {
        Texture2D? atlas = GetUpgradeAtlas();
        if (atlas is null)
            return;

        (Point Tile, int Column, int Level, Color Accent)[] stations =
        {
            (new Point(5, 9), 0, Math.Clamp(save.Data.AirshipEngineLevel, 0, 3), new Color(98, 171, 174)),
            (new Point(18, 9), 1, Math.Clamp(save.Data.AirshipNavigationLevel, 0, 3), new Color(94, 145, 171)),
            (new Point(8, 10), 2, Math.Clamp(save.Data.AirshipHullLevel, 0, 3), new Color(132, 126, 169)),
            (new Point(15, 10), 3, Math.Clamp(save.Data.AirshipReactorLevel, 0, 3), new Color(151, 111, 157)),
        };

        foreach ((Point tile, int column, int level, Color accent) in stations)
        {
            Vector2 center = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 34f);
            Rectangle src = new(column * CellSize, level * CellSize, CellSize, CellSize);
            Rectangle shadow = new((int)center.X - 55, (int)center.Y + 30, 110, 13);
            DrawRect(batch, shadow, new Color(34, 25, 25) * 0.34f);

            Rectangle dst = new((int)center.X - 56, (int)center.Y - 76, 112, 112);
            batch.Draw(atlas, dst, src, Color.White);

            float pulse = 0.40f + 0.12f * MathF.Sin(phase * 1.7f + column * 1.2f);
            DrawRect(batch, new Rectangle((int)center.X - 15, (int)center.Y + 28, 30, 3), new Color(199, 148, 78) * 0.48f);
            if (level > 0)
                DrawRect(batch, new Rectangle((int)center.X - 9, (int)center.Y + 24, 18, 2), accent * pulse);
            if (level >= 3)
            {
                DrawRect(batch, new Rectangle((int)center.X - 2, (int)center.Y - 54, 4, 6), accent * (pulse + 0.08f));
                DrawRect(batch, new Rectangle((int)center.X - 12, (int)center.Y - 45, 3, 3), accent * pulse);
                DrawRect(batch, new Rectangle((int)center.X + 9, (int)center.Y - 40, 3, 3), accent * pulse);
            }
        }
    }

    private static void DrawChaChaPedestalAccent(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(19f * 64f + 32f, 5f * 64f + 34f);
        Color violet = new Color(145, 112, 156) * (0.34f + 0.08f * MathF.Sin(phase * 1.8f));
        Color teal = new Color(99, 173, 175) * (0.32f + 0.08f * MathF.Sin(phase * 1.5f + 1f));
        Color brass = new Color(197, 145, 76) * 0.48f;
        DrawRect(batch, new Rectangle((int)c.X - 23, (int)c.Y + 19, 17, 3), brass);
        DrawRect(batch, new Rectangle((int)c.X + 6, (int)c.Y + 19, 17, 3), brass);
        DrawDiamond(batch, c + new Vector2(-19f, 9f), 4, violet);
        DrawDiamond(batch, c + new Vector2(19f, 9f), 4, teal);
    }

    private static void DrawRouteBoardAccent(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(10f * 64f + 32f, 6f * 64f + 16f);
        Color brass = new Color(198, 145, 76) * 0.56f;
        Color[] chips =
        {
            new Color(98, 171, 174),
            new Color(210, 158, 83),
            new Color(145, 112, 156),
            new Color(94, 145, 171),
        };
        for (int i = 0; i < chips.Length; i++)
        {
            float pulse = 0.32f + 0.07f * MathF.Sin(phase * 1.4f + i * 0.8f);
            DrawRect(batch, new Rectangle((int)c.X - 26 + i * 17, (int)c.Y - 5, 9, 4), chips[i] * pulse);
        }
        DrawRect(batch, new Rectangle((int)c.X - 30, (int)c.Y + 4, 60, 2), brass);
    }

    private static void DrawBoardingGantryAccent(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(24f * 64f + 32f, 6f * 64f + 24f);
        Color brass = new Color(198, 145, 76) * 0.54f;
        Color teal = new Color(99, 173, 175) * (0.30f + 0.08f * MathF.Sin(phase * 1.6f));
        DrawRect(batch, new Rectangle((int)c.X - 34, (int)c.Y - 12, 68, 3), brass);
        DrawDiamond(batch, c + new Vector2(-28f, -15f), 3, teal);
        DrawDiamond(batch, c + new Vector2(28f, -15f), 3, teal);
    }

    private static void DrawServiceCornerAccent(SpriteBatch batch, float phase)
    {
        Color warm = new Color(220, 184, 111) * (0.28f + 0.05f * MathF.Sin(phase * 1.3f));
        foreach (Point tile in new[] { new Point(4, 10), new Point(26, 10) })
        {
            Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 22f);
            DrawRect(batch, new Rectangle((int)c.X - 3, (int)c.Y - 8, 6, 5), warm);
        }
    }

    private static void DrawConsoleLamp(SpriteBatch batch, Point tile, Color brass, Color glow, float phase)
    {
        Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 20f);
        DrawRect(batch, new Rectangle((int)c.X - 9, (int)c.Y - 3, 18, 6), new Color(48, 34, 34) * 0.78f);
        DrawRect(batch, new Rectangle((int)c.X - 6, (int)c.Y - 1, 12, 2), brass * 0.72f);
        float pulse = 0.38f + 0.10f * MathF.Sin(phase * 1.8f + tile.X * 0.2f);
        DrawRect(batch, new Rectangle((int)c.X - 2, (int)c.Y - 10, 4, 4), glow * pulse);
    }

    private static void DrawDoorwayThreshold(SpriteBatch batch, Point tile, Color color)
    {
        Vector2 c = WorldToScreen(tile.X * 64f, tile.Y * 64f + 54f);
        DrawRect(batch, new Rectangle((int)c.X - 58, (int)c.Y, 116, 3), color);
        DrawDiamond(batch, new Vector2(c.X - 50f, c.Y + 1f), 3, color * 0.72f);
        DrawDiamond(batch, new Vector2(c.X + 50f, c.Y + 1f), 3, color * 0.72f);
    }

    private static Texture2D? GetUpgradeAtlas()
    {
        if (UpgradeAtlas is not null)
            return UpgradeAtlas;
        if (AtlasLoadFailed || ModEntry.StaticHelper is null)
            return null;

        try
        {
            UpgradeAtlas = ModEntry.StaticHelper.ModContent.Load<Texture2D>(UpgradeAtlasPath);
            return UpgradeAtlas;
        }
        catch
        {
            AtlasLoadFailed = true;
            return null;
        }
    }

    private static Vector2 WorldToScreen(float x, float y)
        => Game1.GlobalToLocal(Game1.viewport, new Vector2(x, y));

    private static void DrawPixelRing(SpriteBatch batch, Vector2 center, int radius, Color color)
    {
        int x = (int)center.X;
        int y = (int)center.Y;
        DrawRect(batch, new Rectangle(x - radius, y - 2, radius * 2 + 1, 4), color);
        DrawRect(batch, new Rectangle(x - 2, y - radius, 4, radius * 2 + 1), color);
        int d = Math.Max(2, radius / 2);
        DrawRect(batch, new Rectangle(x - radius + 3, y - d, 3, d * 2), color * 0.78f);
        DrawRect(batch, new Rectangle(x + radius - 5, y - d, 3, d * 2), color * 0.78f);
        DrawRect(batch, new Rectangle(x - d, y - radius + 3, d * 2, 3), color * 0.78f);
        DrawRect(batch, new Rectangle(x - d, y + radius - 5, d * 2, 3), color * 0.78f);
    }

    private static void DrawDiamond(SpriteBatch batch, Vector2 center, int radius, Color color)
    {
        radius = Math.Max(2, radius);
        for (int y = -radius; y <= radius; y++)
        {
            int half = radius - Math.Abs(y);
            DrawRect(batch, new Rectangle((int)center.X - half, (int)center.Y + y, half * 2 + 1, 1), color);
        }
    }

    private static void DrawRect(SpriteBatch batch, Rectangle rect, Color color)
    {
        if (rect.Width <= 0 || rect.Height <= 0)
            return;
        batch.Draw(Game1.staminaRect, rect, color);
    }
}
'''
write(renderer_path, renderer)

# Small build fingerprint for CI/handoff diagnostics.
fingerprint = {
    "version": NEW_VERSION,
    "profile": "0648-stardew-visual-pass1",
    "deck_sha256": sha256(deck_path),
    "dock_sha256": sha256(dock_path),
    "upgrade_sha256": sha256(atlas_path),
    "visual_contract": [
        "gate-warm-muted-palette",
        "sky-dock-transit-station",
        "deck-cozy-control-room",
        "four-readable-upgrade-stations",
        "no-pickup-props",
        "physical-collision-preserved",
    ],
}
write(ASSETS / "airship_visual_0648_audit.json", json.dumps(fingerprint, indent=2) + "\n")

print(
    f"Prepared Cardcha {NEW_VERSION}: 0648 Stardew Visual Pass 1 with warmer palette, transit-station Sky Dock, cozy Airship bridge hierarchy, and cleaned upgrade machine silhouettes."
)

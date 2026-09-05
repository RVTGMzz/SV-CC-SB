from pathlib import Path
from PIL import Image, ImageDraw
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
ASSETS = CARDCHA / "assets"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.7"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.8"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    require(old in text, f"missing anchor for {label}: {old[:120]}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    require(a >= 0, f"missing start for {label}")
    b = text.find(end, a + len(start))
    require(b >= 0, f"missing end for {label}")
    return text[:a] + replacement.rstrip() + "\n\n" + text[b:]


# -----------------------------------------------------------------------------
# Version bump.
# -----------------------------------------------------------------------------
for rel in ("manifest.json", "Cardcha.csproj", "Directory.Build.targets"):
    p = CARDCHA / rel
    s = read(p)
    require(OLD_VERSION in s, f"missing old version in {rel}")
    write(p, s.replace(OLD_VERSION, NEW_VERSION))


# -----------------------------------------------------------------------------
# Rebuild Airship/Sky Dock maps around a VANILLA townInterior shell.
# The custom PNGs now contain only transparent decor, not fake full-room floors/walls.
# -----------------------------------------------------------------------------
OUTLINE = (57, 36, 39, 255)
WOOD_DARK = (91, 52, 41, 255)
WOOD = (139, 84, 54, 255)
WOOD_HI = (181, 118, 70, 255)
BRASS_DARK = (129, 83, 38, 255)
BRASS = (201, 145, 65, 255)
BRASS_HI = (238, 190, 102, 255)
TEAL = (91, 177, 181, 255)
BLUE = (89, 144, 181, 255)
VIOLET = (151, 105, 171, 255)
CREAM = (236, 214, 166, 255)
GLASS = (62, 91, 132, 235)
SHADOW = (52, 32, 39, 235)


def rect(d, box, fill, outline=None, width=1):
    d.rectangle(box, fill=fill)
    if outline:
        for i in range(width):
            d.rectangle((box[0]+i, box[1]+i, box[2]-i, box[3]-i), outline=outline)


def line(d, pts, fill, width=1):
    d.line(pts, fill=fill, width=width)


def diamond(d, cx, cy, r, fill, outline=None):
    pts = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
    d.polygon(pts, fill=fill)
    if outline:
        d.line(pts + [pts[0]], fill=outline, width=1)


def lamp(d, x, y, accent=CREAM):
    rect(d, (x-5, y-2, x+5, y+3), WOOD_DARK, OUTLINE)
    rect(d, (x-3, y-7, x+3, y-2), BRASS, OUTLINE)
    rect(d, (x-2, y-11, x+2, y-7), accent)
    d.point((x, y-9), fill=(255, 245, 199, 255))


def panel(d, x, y, w, h, accent):
    rect(d, (x, y, x+w-1, y+h-1), SHADOW, OUTLINE)
    rect(d, (x+3, y+3, x+w-4, y+h-4), WOOD_DARK, BRASS_DARK)
    rect(d, (x+7, y+7, x+w-8, y+11), accent)
    for i in range(3):
        rect(d, (x+7+i*8, y+h-10, x+11+i*8, y+h-7), BRASS_HI if i == 0 else CREAM)


def station_base(d, cx, cy, accent):
    # Wide enough to visually support the 112px runtime machine sprite.
    rect(d, (cx-25, cy-12, cx+25, cy+19), SHADOW, OUTLINE)
    rect(d, (cx-22, cy-9, cx+22, cy+15), WOOD_DARK, BRASS_DARK)
    rect(d, (cx-19, cy+11, cx+19, cy+15), BRASS)
    rect(d, (cx-17, cy-5, cx-11, cy-2), accent)
    rect(d, (cx+11, cy-5, cx+17, cy-2), accent)
    rect(d, (cx-5, cy+4, cx+5, cy+7), WOOD_HI)


def make_airship_decor():
    w, h = 384, 224
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Panoramic forward canopy. Large, readable and framed like Stardew carpentry.
    rect(d, (22, 13, 361, 72), GLASS, OUTLINE, 2)
    rect(d, (25, 16, 358, 69), (55, 83, 123, 225), BRASS_DARK)
    for x in (78, 134, 192, 250, 306):
        rect(d, (x-2, 17, x+2, 68), WOOD_DARK)
        rect(d, (x-1, 18, x+1, 67), BRASS_DARK)
    rect(d, (24, 69, 359, 76), WOOD_DARK, OUTLINE)
    line(d, [(30, 73), (353, 73)], BRASS, 2)

    # Helm console is unmistakably centered, with physical body and wheel cradle.
    panel(d, 156, 76, 72, 38, TEAL)
    rect(d, (171, 108, 213, 123), WOOD_DARK, OUTLINE)
    line(d, [(177, 112), (207, 112)], BRASS_HI, 2)
    diamond(d, 192, 117, 5, VIOLET, OUTLINE)

    # Side system consoles. They sit on the wall, never in the walking lane.
    panel(d, 34, 89, 70, 31, TEAL)
    panel(d, 280, 89, 70, 31, BLUE)
    lamp(d, 18, 105, CREAM)
    lamp(d, 366, 105, CREAM)

    # ChaCha resonance alcove moved farther right and higher, clear of its use tile.
    rect(d, (310, 38, 362, 79), SHADOW, OUTLINE)
    rect(d, (314, 42, 358, 75), WOOD_DARK, BRASS_DARK)
    line(d, [(318, 69), (318, 52), (325, 45), (336, 41), (347, 45), (354, 52), (354, 69)], BRASS, 2)
    diamond(d, 336, 58, 6, VIOLET, OUTLINE)

    # Four separate infrastructure foundations, using lower room space instead of clogging center.
    for cx, cy, accent in [
        (4*16+8, 8*16+8, TEAL),
        (19*16+8, 8*16+8, BLUE),
        (7*16+8, 11*16+5, (126, 126, 173, 255)),
        (16*16+8, 11*16+5, VIOLET),
    ]:
        station_base(d, cx, cy, accent)

    # Center aisle is intentionally clear. Add only slim trim/runes at its edges.
    rect(d, (177, 124, 207, 216), (96, 54, 66, 150), OUTLINE)
    line(d, [(180, 126), (180, 212)], BRASS_DARK, 1)
    line(d, [(204, 126), (204, 212)], BRASS_DARK, 1)
    for yy in (142, 166, 190):
        diamond(d, 192, yy, 3, BRASS_DARK)

    # Small service details to break up emptiness without becoming obstacles.
    rect(d, (24, 149, 47, 170), WOOD_DARK, OUTLINE)
    line(d, [(28, 154), (43, 166)], BRASS_DARK, 2)
    line(d, [(43, 154), (28, 166)], BRASS_DARK, 2)
    rect(d, (336, 151, 359, 169), WOOD_DARK, OUTLINE)
    for x in (341, 349, 357):
        line(d, [(x, 155), (x, 165)], BRASS, 1)

    # Bottom threshold. Last 16x16 tile intentionally remains fully transparent for collision gid.
    rect(d, (174, 215, 210, 220), BRASS_DARK, OUTLINE)
    return im


def make_dock_decor():
    w, h = 480, 288
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Route board left.
    panel(d, 72, 64, 108, 58, TEAL)
    rect(d, (83, 76, 169, 83), CREAM)
    for y in (91, 104):
        for i, c in enumerate((TEAL, BRASS_HI, VIOLET, BLUE)):
            rect(d, (84+i*19, y, 94+i*19, y+5), c)
    rect(d, (98, 122, 106, 147), WOOD_DARK, OUTLINE)
    rect(d, (145, 122, 153, 147), WOOD_DARK, OUTLINE)

    # Visible boarding gate and floor pad. Walking onto the pad is the ONLY auto transition.
    rect(d, (345, 47, 443, 126), SHADOW, OUTLINE, 2)
    rect(d, (351, 53, 437, 120), (55, 83, 123, 220), BRASS_DARK)
    line(d, [(357, 115), (357, 70), (368, 58), (394, 49), (420, 58), (431, 70), (431, 115)], BRASS, 3)
    diamond(d, 394, 83, 10, TEAL, OUTLINE)
    lamp(d, 336, 102, CREAM)
    lamp(d, 452, 102, CREAM)
    rect(d, (360, 128, 428, 143), WOOD_DARK, OUTLINE)
    line(d, [(365, 133), (423, 133)], BRASS_HI, 2)
    diamond(d, 394, 137, 5, VIOLET, OUTLINE)

    # Waiting/service furniture painted into decor, no pickup objects.
    rect(d, (38, 166, 90, 179), WOOD_DARK, OUTLINE)
    rect(d, (42, 180, 48, 193), WOOD_DARK)
    rect(d, (80, 180, 86, 193), WOOD_DARK)
    rect(d, (104, 174, 128, 194), WOOD_DARK, OUTLINE)
    line(d, [(108, 179), (124, 190)], BRASS_DARK, 2)
    rect(d, (411, 172, 445, 196), WOOD_DARK, OUTLINE)
    for x in (418, 428, 438):
        line(d, [(x, 177), (x, 190)], BRASS, 1)

    # Central transit runner and beacon lamps.
    rect(d, (224, 135, 255, 278), (100, 59, 67, 145), OUTLINE)
    line(d, [(228, 138), (228, 274)], BRASS_DARK, 1)
    line(d, [(251, 138), (251, 274)], BRASS_DARK, 1)
    for yy in (153, 181, 209, 237):
        diamond(d, 240, yy, 3, BRASS_DARK)
    lamp(d, 206, 145, CREAM)
    lamp(d, 273, 145, CREAM)

    # Keep the bottom-right tile completely transparent for collision reuse.
    return im


def csv_text(values, w):
    rows = []
    for y in range(len(values)//w):
        rows.append(",".join(str(v) for v in values[y*w:(y+1)*w]))
    return "\n" + ",\n".join(rows) + "\n"


def vanilla_shell(w, h):
    back = [0]*(w*h)
    def setv(x,y,v): back[y*w+x]=v
    # Warm Stardew wall shell adapted from MiMi attic's proven townInterior IDs.
    for x in range(1,w-1):
        setv(x,1,171); setv(x,2,171); setv(x,3,113); setv(x,4,200)
    for y in range(5,h-1):
        for x in range(1,w-1):
            setv(x,y, (232 if x%2 else 233) if y%2 else (264 if x%2 else 265))
    # doorway continuation on final row only.
    c=w//2
    setv(c-1,h-1,264); setv(c,h-1,265)
    return back


def make_map(path: Path, w: int, h: int, decor_name: str, role: str, profile: str, architecture: str, blocked, properties_extra=None):
    custom_first=4096
    transparent_gid=custom_first + w*h - 1
    root=ET.Element("map", {
        "version":"1.10","tiledversion":"1.10.2","orientation":"orthogonal","renderorder":"right-down",
        "width":str(w),"height":str(h),"tilewidth":"16","tileheight":"16","infinite":"0","nextlayerid":"5","nextobjectid":"1"
    })
    props=ET.SubElement(root,"properties")
    base_props={
        "CardchaAirshipVersion":"alpha.28.0.4.14.4.5.12.8",
        "CardchaAirshipRole":role,
        "CardchaVisualProfile":profile,
        "CardchaArchitecture":architecture,
    }
    if properties_extra: base_props.update(properties_extra)
    for k,v in base_props.items(): ET.SubElement(props,"property",{"name":k,"value":v})
    ts=ET.SubElement(root,"tileset",{"firstgid":"1","name":"townInterior","tilewidth":"16","tileheight":"16","tilecount":"2176","columns":"32"})
    ET.SubElement(ts,"image",{"source":".townInterior.png","width":"512","height":"1088"})
    ts2=ET.SubElement(root,"tileset",{"firstgid":str(custom_first),"name":f"cardchaDecor_{decor_name}","tilewidth":"16","tileheight":"16","tilecount":str(w*h),"columns":str(w)})
    ET.SubElement(ts2,"image",{"source":decor_name,"width":str(w*16),"height":str(h*16)})

    back=vanilla_shell(w,h)
    decor=[custom_first+i for i in range(w*h)]
    buildings=[0]*(w*h)
    for x,y in blocked:
        if 0<=x<w and 0<=y<h: buildings[y*w+x]=transparent_gid
    front=[0]*(w*h)

    for lid,name,vals in [(1,"Back",back),(2,"BackDecor",decor),(3,"Buildings",buildings),(4,"Front",front)]:
        layer=ET.SubElement(root,"layer",{"id":str(lid),"name":name,"width":str(w),"height":str(h)})
        data=ET.SubElement(layer,"data",{"encoding":"csv"}); data.text=csv_text(vals,w)

    ET.indent(root, space=" ")
    ET.ElementTree(root).write(path, encoding="UTF-8", xml_declaration=True)


# Airship collision: only visible wall/boundary + actual consoles/machines. No giant invisible wall rows.
deck_w, deck_h = 24,14
deck_block=set()
for x in range(deck_w):
    if x not in (11,12): deck_block.add((x,deck_h-1))
for y in range(1,deck_h-1):
    deck_block.add((0,y)); deck_block.add((deck_w-1,y))
for y in range(1,5):
    for x in range(1,deck_w-1): deck_block.add((x,y))
# visible helm/side console wall footprints
for x in range(9,15): deck_block.add((x,6))
for x in range(2,7): deck_block.add((x,6))
for x in range(17,22): deck_block.add((x,6))
# visible machine centers only; renderer + bases make these blockers obvious
for p in [(4,8),(19,8),(7,11),(16,11)]: deck_block.add(p)
# ChaCha wall alcove only
for x in range(20,23): deck_block.add((x,5))

dock_w,dock_h=30,18
dock_block=set()
for x in range(dock_w):
    if x not in (14,15): dock_block.add((x,dock_h-1))
for y in range(1,dock_h-1):
    dock_block.add((0,y)); dock_block.add((dock_w-1,y))
for y in range(1,5):
    for x in range(1,dock_w-1): dock_block.add((x,y))
# route board and boarding gate visible footprints
for x in range(4,12): dock_block.add((x,6))
for x in range(21,28): dock_block.add((x,6))
# service objects matching painted decor
for p in [(3,11),(4,11),(6,11),(26,11),(27,11)]: dock_block.add(p)

make_airship_decor().save(ASSETS/"airship_deck_stardew.png", optimize=True)
make_dock_decor().save(ASSETS/"sky_dock_stardew.png", optimize=True)
make_map(
    ASSETS/"airship_deck.tmx", deck_w, deck_h, "airship_deck_stardew.png",
    "airship-bridge|navigation-core|four-independent-upgrade-stations|chacha-resonance|arcane-dock-return",
    "vanilla-townInterior-shell|warm-wood-brass|magic-lamps|panoramic-canopy",
    "vanilla-shell|transparent-decor-layer|visible-only-collision|two-tile-doorway|no-pickup-props",
    deck_block,
)
make_map(
    ASSETS/"sky_dock_interior.tmx", dock_w, dock_h, "sky_dock_stardew.png",
    "airship-transit-dock|route-board|visible-boarding-pad|service-zone|forest-return",
    "vanilla-townInterior-shell|transit-station|warm-wood-brass|visible-use-points",
    "vanilla-shell|transparent-decor-layer|visible-only-collision|two-tile-doorway|no-pickup-props",
    dock_block,
)


# -----------------------------------------------------------------------------
# Airship runtime: exact visible interactions, stable Forest portal, weather/time flight sky.
# -----------------------------------------------------------------------------
air_path = CARDCHA/"Services"/"AirshipFoundationService.cs"
air = read(air_path)
air = replace_once(air, 'private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12.7";', 'private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12.8";', "decor version")
air = replace_once(
    air,
    '            if (Touches(interiorAction, route) || PlayerIsNear(route, 176f))',
    '            if (interiorAction == route)',
    "route exact interaction",
)
air = replace_once(
    air,
    '            if (Touches(interiorAction, bay) || PlayerIsNear(bay, 176f))',
    '            if (interiorAction == bay)',
    "bay exact interaction",
)
air = replace_once(
    air,
    '            if (Touches(interiorAction, interiorExit) || PlayerIsNear(interiorExit))',
    '            if (interiorAction == interiorExit)',
    "dock exit exact interaction",
)
air = replace_once(
    air,
    '        if (Touches(action, helm) || PlayerIsNear(helm, 160f))',
    '        if (action == helm)',
    "helm exact interaction",
)
air = replace_once(
    air,
    '            if (!Touches(action, tile) && !PlayerIsNear(tile, 176f))\n                continue;',
    '            if (!ActionTouchesStation(action, tile))\n                continue;',
    "machine exact visible interaction",
)
air = replace_once(
    air,
    '        if (!Touches(action, exit) && !PlayerIsNear(exit))\n            return;',
    '        if (action != exit)\n            return;',
    "deck exit exact interaction",
)
air = replace_once(
    air,
    '            if (IsPortalZone(playerTile, bay, radiusX: 1, radiusY: 1))\n                return this.WarpToAirshipBridge();',
    '            if (playerTile == bay)\n                return this.WarpToAirshipBridge();',
    "boarding pad exact auto transition",
)
air = replace_once(
    air,
    '        return new Point(Math.Clamp(width / 3, 3, width - 4), Math.Clamp(7, 3, height - 5));',
    '        return new Point(Math.Clamp(width / 4, 3, width - 4), Math.Clamp(7, 3, height - 5));',
    "route point",
)
air = replace_once(
    air,
    '        return new Point(Math.Clamp(width - 6, 4, width - 3), Math.Clamp(7, 3, height - 5));',
    '        return new Point(Math.Clamp(width - 7, 4, width - 3), Math.Clamp(8, 3, height - 5));',
    "boarding pad point",
)
air = replace_once(
    air,
    '        return new Point(Math.Clamp(width / 2, 2, width - 3), Math.Clamp(8, 2, height - 3));',
    '        return new Point(Math.Clamp(width / 2, 2, width - 3), Math.Clamp(6, 2, height - 3));',
    "helm visible use point",
)
air = replace_between(
    air,
    '    private static (AirshipUpgradeSystem System, Point Tile)[] ResolveDeckUpgradeSockets()',
    '    private int GetAirshipUpgradeLevel',
    '''    private static (AirshipUpgradeSystem System, Point Tile)[] ResolveDeckUpgradeSockets()
        => new[]
        {
            (AirshipUpgradeSystem.Engine, new Point(4, 8)),
            (AirshipUpgradeSystem.Navigation, new Point(19, 8)),
            (AirshipUpgradeSystem.Hull, new Point(7, 11)),
            (AirshipUpgradeSystem.Reactor, new Point(16, 11)),
        };

    private static bool ActionTouchesStation(Point action, Point station)
        => action.Y == station.Y && Math.Abs(action.X - station.X) <= 1;''',
    "independent machine sockets",
)

stable_gate = r'''    private void DrawSkyDock(SpriteBatch batch, Point tile)
    {
        Vector2 center = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(tile.X * 64f + 32f, tile.Y * 64f - 34f)
        );

        (Color skyTop, Color skyMid, Color skyLow) = ResolveOutdoorSkyPalette();
        Color gold = new Color(199, 151, 78) * 0.94f;
        Color stoneDark = new Color(57, 48, 51) * 0.98f;
        Color stone = new Color(90, 77, 74) * 0.98f;
        Color stoneLight = new Color(126, 111, 102) * 0.86f;
        Color violet = new Color(148, 112, 166) * 0.62f;
        Color cyan = new Color(110, 181, 188) * 0.58f;

        // Stable presentation: the portal no longer rotates/rebuilds its sigil while the farmer moves.
        DrawRect(batch, new Rectangle((int)center.X - 104, (int)center.Y + 63, 208, 18), new Color(20, 20, 27) * 0.48f);
        DrawRect(batch, new Rectangle((int)center.X - 92, (int)center.Y + 49, 184, 18), stoneDark * 0.84f);
        DrawRect(batch, new Rectangle((int)center.X - 82, (int)center.Y + 40, 164, 13), stone * 0.86f);
        DrawRect(batch, new Rectangle((int)center.X - 70, (int)center.Y + 32, 140, 10), stoneLight * 0.72f);

        Rectangle aperture = new((int)center.X - 57, (int)center.Y - 105, 114, 143);
        DrawRect(batch, new Rectangle(aperture.X - 7, aperture.Y - 7, aperture.Width + 14, aperture.Height + 14), new Color(48, 27, 54) * 0.94f);
        DrawVerticalGradient(batch, aperture, skyTop * 0.94f, skyMid * 0.92f, skyLow * 0.88f);
        // Fixed magical glass lines. Only brightness gently pulses; geometry never moves.
        DrawRect(batch, new Rectangle(aperture.X + 13, aperture.Y + 28, aperture.Width - 26, 2), cyan * 0.26f);
        DrawRect(batch, new Rectangle(aperture.X + 21, aperture.Y + 73, aperture.Width - 42, 2), violet * 0.24f);
        DrawDiamondRune(batch, new Vector2(aperture.Center.X, aperture.Center.Y), 9f, cyan * 0.42f);
        DrawDiamondRune(batch, new Vector2(aperture.Center.X - 27f, aperture.Center.Y + 31f), 4f, violet * 0.34f);
        DrawDiamondRune(batch, new Vector2(aperture.Center.X + 29f, aperture.Center.Y - 35f), 4f, gold * 0.32f);

        DrawRect(batch, new Rectangle((int)center.X - 81, (int)center.Y - 77, 24, 127), stoneDark);
        DrawRect(batch, new Rectangle((int)center.X + 57, (int)center.Y - 77, 24, 127), stoneDark);
        DrawRect(batch, new Rectangle((int)center.X - 74, (int)center.Y - 73, 14, 119), stone);
        DrawRect(batch, new Rectangle((int)center.X + 60, (int)center.Y - 73, 14, 119), stone);
        DrawEllipticArc(batch, new Vector2(center.X, center.Y - 74f), 69f, 65f, MathHelper.Pi, MathHelper.TwoPi, 18, 17f, stoneDark);
        DrawEllipticArc(batch, new Vector2(center.X, center.Y - 74f), 61f, 58f, MathHelper.Pi, MathHelper.TwoPi, 18, 9f, stone);
        DrawEllipticArc(batch, new Vector2(center.X, center.Y - 74f), 53f, 51f, MathHelper.Pi, MathHelper.TwoPi, 18, 4f, gold * 0.82f);
        DrawRect(batch, new Rectangle((int)center.X - 72, (int)center.Y + 43, 144, 6), gold * 0.72f);

        DrawDiamondRune(batch, new Vector2(center.X, center.Y - 147f), 18f, gold);
        DrawCrystalPylon(batch, new Vector2(center.X - 102f, center.Y + 48f), 48f, cyan, gold);
        DrawCrystalPylon(batch, new Vector2(center.X + 102f, center.Y + 48f), 48f, violet, gold);
        DrawBrassLamp(batch, new Vector2(center.X - 137f, center.Y + 55f), 0f, gold, cyan);
        DrawBrassLamp(batch, new Vector2(center.X + 137f, center.Y + 55f), 0f, gold, violet);
    }'''
air = replace_between(air, '    private void DrawSkyDock(SpriteBatch batch, Point tile)', '    private void DrawSkyDockInteriorDetails', stable_gate, "stable Forest gate")

flight = r'''    private static (Color Top, Color Mid, Color Low) ResolveOutdoorSkyPalette()
    {
        int time = Game1.timeOfDay;
        bool night = time >= 2000 || time < 600;
        bool dusk = time >= 1700 && time < 2000;
        bool dawn = time >= 600 && time < 800;

        Color top;
        Color mid;
        Color low;
        if (night)
        {
            top = new Color(18, 30, 65);
            mid = new Color(37, 49, 92);
            low = new Color(67, 64, 108);
        }
        else if (dusk)
        {
            top = new Color(72, 101, 160);
            mid = new Color(190, 118, 132);
            low = new Color(244, 176, 119);
        }
        else if (dawn)
        {
            top = new Color(94, 132, 181);
            mid = new Color(209, 156, 160);
            low = new Color(247, 204, 149);
        }
        else
        {
            top = new Color(78, 145, 207);
            mid = new Color(126, 190, 224);
            low = new Color(214, 225, 226);
        }

        if (Game1.isLightning)
            return (new Color(41, 49, 69), new Color(62, 68, 85), new Color(94, 96, 108));
        if (Game1.isRaining)
            return (new Color(48, 66, 91), new Color(70, 85, 105), new Color(101, 111, 120));
        if (Game1.isSnowing)
            return (new Color(95, 112, 139), new Color(141, 154, 174), new Color(201, 207, 211));
        if (Game1.isDebrisWeather)
            return (new Color(97, 127, 144), new Color(141, 160, 154), new Color(192, 190, 164));
        return (top, mid, low);
    }

    private static void DrawFlightWeather(SpriteBatch batch, Rectangle sky, float phase)
    {
        if (Game1.isRaining || Game1.isLightning)
        {
            Color rain = new Color(183, 204, 221) * 0.50f;
            for (int i = 0; i < 34; i++)
            {
                int x = sky.X + (int)((i * 73 + phase * 210f) % Math.Max(1, sky.Width));
                int y = sky.Y + (int)((i * 41 + phase * 330f) % Math.Max(1, sky.Height));
                DrawRect(batch, new Rectangle(x, y, 2, 10), rain);
            }
            if (Game1.isLightning)
            {
                float flash = Math.Max(0f, (float)Math.Sin(phase * 7.5f) - 0.86f) * 2.4f;
                if (flash > 0f)
                    DrawRect(batch, sky, Color.White * Math.Min(0.22f, flash));
            }
            return;
        }
        if (Game1.isSnowing)
        {
            Color snow = new Color(244, 245, 238) * 0.72f;
            for (int i = 0; i < 30; i++)
            {
                int x = sky.X + (int)((i * 83 + phase * 34f) % Math.Max(1, sky.Width));
                int y = sky.Y + (int)((i * 47 + phase * 58f) % Math.Max(1, sky.Height));
                int s = 2 + (i % 3);
                DrawRect(batch, new Rectangle(x, y, s, s), snow);
            }
            return;
        }
        if (Game1.isDebrisWeather)
        {
            Color leaf = new Color(164, 133, 73) * 0.62f;
            for (int i = 0; i < 22; i++)
            {
                int x = sky.X + (int)((i * 91 + phase * 120f) % Math.Max(1, sky.Width));
                int y = sky.Y + (int)((i * 53 + phase * 46f) % Math.Max(1, sky.Height));
                DrawRect(batch, new Rectangle(x, y, 4, 2), leaf);
            }
        }
    }

    private void DrawFlightCutscene(SpriteBatch batch)
    {
        float p = Math.Clamp(
            (Environment.TickCount64 - this.FlightCutsceneStartedAtMs) / (float)FlightCutsceneDurationMs,
            0f,
            1f
        );
        float eased = MathHelper.SmoothStep(0f, 1f, p);
        int w = Game1.viewport.Width;
        int h = Game1.viewport.Height;
        Rectangle sky = new(0, 0, w, h);
        float phase = (float)(Environment.TickCount64 / 1000.0);
        (Color top, Color mid, Color low) = ResolveOutdoorSkyPalette();
        DrawVerticalGradient(batch, sky, top, mid, low);

        bool night = Game1.timeOfDay >= 2000 || Game1.timeOfDay < 600;
        if (!Game1.isRaining && !Game1.isLightning && !Game1.isSnowing && !Game1.isDebrisWeather)
        {
            if (night)
                DrawStarfield(batch, sky, 54, phase, new Color(247, 235, 204) * 0.78f);
            else
            {
                DrawCloudBand(batch, sky, h / 5, phase * 16f, Color.White * 0.48f);
                DrawCloudBand(batch, sky, h * 2 / 5, -phase * 10f, Color.White * 0.30f);
            }
        }
        DrawFlightWeather(batch, sky, phase);

        // Thin lower haze only. The old fake wooden stage / straight cloud bars are gone.
        DrawRect(batch, new Rectangle(0, h - 52, w, 52), low * 0.24f);

        float crest = (float)Math.Sin(p * Math.PI);
        float travel = this.FlightCutsceneReturning ? 1f - eased : eased;
        float shipX = MathHelper.Lerp(w * 0.24f, w * 0.76f, travel);
        float bob = (float)Math.Sin(p * MathHelper.TwoPi * 1.25f) * (3f + crest * 8f);
        float lift = crest * 24f;
        float shipY = h * 0.43f - lift + bob;
        float direction = this.FlightCutsceneReturning ? -1f : 1f;
        float rotation = -direction * CutsceneTiltRadians * (0.30f + crest * 0.70f);
        float verticalScale = 1f + (float)Math.Sin(p * MathHelper.TwoPi * 1.75f) * CutsceneScalePulse;
        SpriteEffects directionEffect = this.FlightCutsceneReturning ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
        float targetWidth = Math.Min(720f, w * 0.62f);

        bool spriteDrawn = this.TryDrawAirshipSprite(
            batch, new Vector2(shipX, shipY), targetWidth, Color.White * 0.98f,
            directionEffect, rotation, verticalScale
        );
        if (spriteDrawn)
        {
            this.DrawAirshipPropellerMotion(
                batch, new Vector2(shipX, shipY), targetWidth,
                directionEffect, rotation, verticalScale, spinDirection: direction
            );
        }
        else
        {
            this.DrawCinematicAirship(batch, new Vector2(shipX, shipY), 1.15f);
        }

        string title = ModEntry.T(this.FlightCutsceneReturning ? "airship.cutscene.return" : "airship.cutscene.departure");
        Vector2 size = Game1.smallFont.MeasureString(title);
        batch.DrawString(Game1.smallFont, title, new Vector2((w - size.X) / 2f, 26f), Color.White * 0.92f);
    }'''
air = replace_between(air, '    private void DrawFlightCutscene(SpriteBatch batch)', '    private bool TryDrawAirshipSprite(', flight, "weather/time flight cutscene")
write(air_path, air)


# -----------------------------------------------------------------------------
# Renderer: brighter magical control room, visible lamps/sparkles, new station positions.
# -----------------------------------------------------------------------------
renderer = r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// 0648B. Vanilla townInterior owns the room shell. This renderer only adds magical light,
/// weather-aware glass ambience and four independent level-aware machine sprites.
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
        DrawWindowMagic(batch, phase);
        DrawAmbientLamps(batch, phase);
        DrawHelmMagic(batch, phase);
        DrawUpgradeStations(batch, save, phase);
        DrawChaChaMagic(batch, phase);
        DrawDoorwayThreshold(batch, new Point(12, 12), new Color(210, 161, 79) * 0.60f);
        return true;
    }

    public static bool TryDrawSkyDock(SpriteBatch batch, GameLocation dock)
    {
        if (batch is null || dock is null)
            return false;
        float phase = (float)(Environment.TickCount64 / 1000.0);
        DrawDockMagic(batch, phase);
        DrawDoorwayThreshold(batch, new Point(15, 16), new Color(210, 161, 79) * 0.54f);
        return true;
    }

    private static void DrawWindowMagic(SpriteBatch batch, float phase)
    {
        bool night = Game1.timeOfDay >= 2000 || Game1.timeOfDay < 600;
        Color warm = new Color(244, 209, 138) * 0.35f;
        Color teal = new Color(103, 205, 207) * 0.30f;
        for (int i = 0; i < 14; i++)
        {
            int x = 2 + ((i * 7) % 20);
            Vector2 p = WorldToScreen(x * 64f + 26f, 2f * 64f + 24f + (i % 3) * 13f);
            float pulse = 0.45f + 0.18f * MathF.Sin(phase * 1.4f + i * 0.85f);
            DrawRect(batch, new Rectangle((int)p.X, (int)p.Y, night ? 4 : 3, night ? 4 : 3), (i % 4 == 0 ? teal : warm) * pulse);
        }
    }

    private static void DrawAmbientLamps(SpriteBatch batch, float phase)
    {
        foreach ((Point tile, Color glow) in new[]
        {
            (new Point(2,6), new Color(248, 211, 132)),
            (new Point(21,6), new Color(248, 211, 132)),
            (new Point(10,7), new Color(116, 219, 215)),
            (new Point(14,7), new Color(179, 132, 211)),
        })
        {
            Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 25f);
            float pulse = 0.58f + 0.08f * MathF.Sin(phase * 1.55f + tile.X);
            // Pixel halo, intentionally chunky instead of smooth neon.
            DrawRect(batch, new Rectangle((int)c.X - 30, (int)c.Y - 20, 60, 40), glow * (0.055f * pulse));
            DrawRect(batch, new Rectangle((int)c.X - 18, (int)c.Y - 12, 36, 24), glow * (0.085f * pulse));
            DrawDiamond(batch, c, 5, glow * (0.52f + pulse * 0.12f));
            DrawRect(batch, new Rectangle((int)c.X - 2, (int)c.Y + 7, 4, 6), new Color(190, 135, 60) * 0.82f);
        }
    }

    private static void DrawHelmMagic(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(12f * 64f + 32f, 6f * 64f + 10f);
        Color brass = new Color(218, 163, 79) * 0.82f;
        Color teal = new Color(109, 220, 216) * 0.72f;
        Color violet = new Color(184, 133, 216) * 0.58f;
        float pulse = 0.58f + 0.10f * MathF.Sin(phase * 1.8f);
        DrawRect(batch, new Rectangle((int)c.X - 46, (int)c.Y - 32, 92, 64), teal * (0.045f + pulse * 0.035f));
        DrawPixelRing(batch, c, 23, brass);
        DrawPixelRing(batch, c, 16, violet);
        DrawDiamond(batch, c, 7, teal * pulse);
        int needle = (int)(MathF.Sin(phase * 0.9f) * 7f);
        DrawRect(batch, new Rectangle((int)c.X + needle - 1, (int)c.Y - 14, 3, 28), teal * 0.62f);
        for (int i = 0; i < 4; i++)
        {
            float a = phase * 0.45f + i * MathHelper.PiOver2;
            Vector2 s = c + new Vector2(MathF.Cos(a) * 35f, MathF.Sin(a) * 22f);
            DrawRect(batch, new Rectangle((int)s.X, (int)s.Y, 3, 3), (i % 2 == 0 ? teal : violet) * 0.60f);
        }
    }

    private static void DrawUpgradeStations(SpriteBatch batch, SaveService save, float phase)
    {
        Texture2D? atlas = GetUpgradeAtlas();
        if (atlas is null)
            return;
        (Point Tile, int Column, int Level, Color Accent)[] stations =
        {
            (new Point(4,8), 0, Math.Clamp(save.Data.AirshipEngineLevel,0,3), new Color(104,205,200)),
            (new Point(19,8), 1, Math.Clamp(save.Data.AirshipNavigationLevel,0,3), new Color(98,166,211)),
            (new Point(7,11), 2, Math.Clamp(save.Data.AirshipHullLevel,0,3), new Color(151,151,210)),
            (new Point(16,11), 3, Math.Clamp(save.Data.AirshipReactorLevel,0,3), new Color(190,133,207)),
        };
        foreach ((Point tile, int column, int level, Color accent) in stations)
        {
            Vector2 center = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 52f);
            Rectangle src = new(column * CellSize, level * CellSize, CellSize, CellSize);
            float pulse = 0.62f + 0.16f * MathF.Sin(phase * 2.05f + column * 1.1f);
            DrawRect(batch, new Rectangle((int)center.X - 54, (int)center.Y - 55, 108, 72), accent * (0.075f + pulse * 0.045f));
            DrawRect(batch, new Rectangle((int)center.X - 38, (int)center.Y - 42, 76, 52), accent * (0.085f + pulse * 0.055f));
            Rectangle dst = new((int)center.X - 56, (int)center.Y - 76, 112, 112);
            batch.Draw(atlas, dst, src, Color.White);
            DrawRect(batch, new Rectangle((int)center.X - 19, (int)center.Y - 26, 38, 4), accent * (0.42f + pulse * 0.22f));
            DrawDiamond(batch, new Vector2(center.X, center.Y - 44), 4 + level, accent * (0.58f + pulse * 0.22f));
            for (int i = 0; i < 3 + level; i++)
            {
                float a = phase * (0.5f + column * 0.05f) + i * 2.1f;
                Vector2 s = center + new Vector2(MathF.Cos(a) * 31f, -31f + MathF.Sin(a) * 17f);
                DrawRect(batch, new Rectangle((int)s.X, (int)s.Y, 3, 3), accent * 0.56f);
            }
        }
    }

    private static void DrawChaChaMagic(SpriteBatch batch, float phase)
    {
        Vector2 c = WorldToScreen(21f * 64f + 32f, 5f * 64f + 34f);
        Color violet = new Color(190, 132, 218) * (0.50f + 0.10f * MathF.Sin(phase * 1.8f));
        Color teal = new Color(111, 218, 209) * (0.46f + 0.10f * MathF.Sin(phase * 1.5f + 1f));
        DrawRect(batch, new Rectangle((int)c.X - 38, (int)c.Y - 30, 76, 60), violet * 0.055f);
        DrawDiamond(batch, c + new Vector2(-18f, 4f), 5, violet);
        DrawDiamond(batch, c + new Vector2(18f, 4f), 5, teal);
        DrawDiamond(batch, c + new Vector2(0f, -15f), 4, Color.White * 0.46f);
    }

    private static void DrawDockMagic(SpriteBatch batch, float phase)
    {
        // Route board indicator.
        Vector2 route = WorldToScreen(7f * 64f + 32f, 7f * 64f + 10f);
        DrawDiamond(batch, route, 5, new Color(109,210,204) * (0.58f + 0.10f*MathF.Sin(phase*1.6f)));
        // Boarding pad is deliberately bright so the warp trigger is never invisible.
        Vector2 bay = WorldToScreen(23f * 64f + 32f, 8f * 64f + 34f);
        Color teal = new Color(103,221,214);
        DrawRect(batch, new Rectangle((int)bay.X - 38, (int)bay.Y - 18, 76, 36), teal * 0.08f);
        DrawPixelRing(batch, bay, 20, teal * 0.56f);
        DrawDiamond(batch, bay, 8, teal * 0.70f);
        for (int i=0;i<5;i++)
        {
            float a=phase*0.55f+i*MathHelper.TwoPi/5f;
            Vector2 s=bay+new Vector2(MathF.Cos(a)*31f,MathF.Sin(a)*14f);
            DrawRect(batch,new Rectangle((int)s.X,(int)s.Y,3,3),Color.White*0.52f);
        }
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
        if (UpgradeAtlas is not null && !UpgradeAtlas.IsDisposed)
            return UpgradeAtlas;
        UpgradeAtlas = null;
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
        => Game1.GlobalToLocal(Game1.viewport, new Vector2(x,y));

    private static void DrawPixelRing(SpriteBatch batch, Vector2 c, int r, Color color)
    {
        DrawRect(batch,new Rectangle((int)c.X-r,(int)c.Y-r,r*2+1,3),color);
        DrawRect(batch,new Rectangle((int)c.X-r,(int)c.Y+r-2,r*2+1,3),color);
        DrawRect(batch,new Rectangle((int)c.X-r,(int)c.Y-r,3,r*2+1),color);
        DrawRect(batch,new Rectangle((int)c.X+r-2,(int)c.Y-r,3,r*2+1),color);
    }

    private static void DrawDiamond(SpriteBatch batch, Vector2 c, int r, Color color)
    {
        for (int y=-r;y<=r;y++)
        {
            int half=r-Math.Abs(y);
            DrawRect(batch,new Rectangle((int)c.X-half,(int)c.Y+y,half*2+1,1),color);
        }
    }

    private static void DrawRect(SpriteBatch batch, Rectangle rect, Color color)
    {
        if (rect.Width<=0 || rect.Height<=0 || color.A==0) return;
        batch.Draw(Game1.staminaRect,rect,color);
    }
}
'''
write(CARDCHA/"Services"/"AirshipInteriorStardewRenderer.cs", renderer)


# -----------------------------------------------------------------------------
# Four PHYSICAL machines now open four dedicated one-system upgrade panels.
# -----------------------------------------------------------------------------
menu = r'''using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

internal enum AirshipUpgradeSystem
{
    Engine = 0,
    Navigation = 1,
    Hull = 2,
    Reactor = 3,
}

/// <summary>0648B: one physical station, one upgrade system, one panel.</summary>
internal sealed class AirshipUpgradeMenu : IClickableMenu
{
    internal const int MaxLevel = 3;
    private readonly SaveService Save;
    private readonly ControllerProfileService Controller;
    private readonly AirshipUpgradeSystem System;
    private readonly Rectangle UpgradeButton;
    private readonly Rectangle CloseButton;
    private string Status;

    public AirshipUpgradeMenu(SaveService save, ControllerProfileService controller, AirshipUpgradeSystem system)
        : base(
            Game1.uiViewport.Width/2 - Math.Min(880, Game1.uiViewport.Width-24)/2,
            Game1.uiViewport.Height/2 - Math.Min(560, Game1.uiViewport.Height-24)/2,
            Math.Min(880, Game1.uiViewport.Width-24),
            Math.Min(560, Game1.uiViewport.Height-24),
            showUpperRightCloseButton:false)
    {
        this.Save=save;
        this.Controller=controller;
        this.System=system;
        this.Status=ModEntry.T("airship.upgrade.status.ready");
        this.UpgradeButton=new Rectangle(this.xPositionOnScreen+this.width-286,this.yPositionOnScreen+this.height-80,210,48);
        this.CloseButton=new Rectangle(this.xPositionOnScreen+42,this.yPositionOnScreen+this.height-80,160,48);
    }

    internal static int GetTestCostForCurrentLevel(int currentLevel)
        => currentLevel switch { 0=>5, 1=>10, 2=>20, _=>0 };

    public override void receiveLeftClick(int x,int y,bool playSound=true)
    {
        if(this.UpgradeButton.Contains(x,y)){ this.TryUpgrade(); return; }
        if(this.CloseButton.Contains(x,y)) this.CloseMenu();
    }

    public override void receiveKeyPress(Keys key)
    {
        if(key==Keys.Escape){ this.CloseMenu(); return; }
        if(key is Keys.Enter or Keys.Space){ this.TryUpgrade(); return; }
        base.receiveKeyPress(key);
    }

    public override void receiveGamePadButton(Buttons b)
    {
        if(this.Controller.IsExit(b)||this.Controller.IsDeselect(b)){ this.CloseMenu(); return; }
        if(this.Controller.IsConfirm(b)){ this.TryUpgrade(); return; }
        base.receiveGamePadButton(b);
    }

    private void TryUpgrade()
    {
        int level=this.GetLevel();
        if(level>=MaxLevel){ this.Status=ModEntry.T("airship.upgrade.status.max"); Game1.playSound("cancel"); return; }
        int cost=GetTestCostForCurrentLevel(level);
        if(this.Save.Data.SuspiciousDust<cost)
        {
            this.Status=ModEntry.T("airship.upgrade.status.not_enough",new{cost,dust=this.Save.Data.SuspiciousDust});
            Game1.playSound("cancel"); return;
        }
        this.Save.Data.SuspiciousDust-=cost;
        this.SetLevel(level+1);
        this.Save.Save();
        this.Status=ModEntry.T("airship.upgrade.status.success",new{system=this.GetSystemName(),level=level+1,cost});
        Game1.playSound("discoverMineral");
    }

    private int GetLevel()=>this.System switch
    {
        AirshipUpgradeSystem.Engine=>this.Save.Data.AirshipEngineLevel,
        AirshipUpgradeSystem.Navigation=>this.Save.Data.AirshipNavigationLevel,
        AirshipUpgradeSystem.Hull=>this.Save.Data.AirshipHullLevel,
        AirshipUpgradeSystem.Reactor=>this.Save.Data.AirshipReactorLevel,
        _=>0,
    };

    private void SetLevel(int level)
    {
        level=Math.Clamp(level,0,MaxLevel);
        switch(this.System)
        {
            case AirshipUpgradeSystem.Engine:this.Save.Data.AirshipEngineLevel=level;break;
            case AirshipUpgradeSystem.Navigation:this.Save.Data.AirshipNavigationLevel=level;break;
            case AirshipUpgradeSystem.Hull:this.Save.Data.AirshipHullLevel=level;break;
            case AirshipUpgradeSystem.Reactor:this.Save.Data.AirshipReactorLevel=level;break;
        }
    }

    private string Token()=>this.System switch
    {
        AirshipUpgradeSystem.Engine=>"engine",
        AirshipUpgradeSystem.Navigation=>"navigation",
        AirshipUpgradeSystem.Hull=>"hull",
        AirshipUpgradeSystem.Reactor=>"reactor",
        _=>"engine",
    };
    private string GetSystemName()=>ModEntry.T($"airship.upgrade.system.{this.Token()}.name");
    private string GetSystemDesc()=>ModEntry.T($"airship.upgrade.system.{this.Token()}.desc");

    private void CloseMenu(){ Game1.playSound("bigDeSelect"); Game1.exitActiveMenu(); }

    public override void draw(SpriteBatch b)
    {
        b.Draw(Game1.fadeToBlackRect,Game1.graphics.GraphicsDevice.Viewport.Bounds,Color.Black*0.70f);
        Rectangle panel=new(this.xPositionOnScreen,this.yPositionOnScreen,this.width,this.height);
        CardchaUi.DrawInsetPanel(b,panel,new Color(53,42,61),new Color(178,126,84),5,8);
        Rectangle inner=new(panel.X+22,panel.Y+22,panel.Width-44,panel.Height-44);
        CardchaUi.DrawInsetPanel(b,inner,new Color(238,224,204),new Color(126,83,62),3,5);

        string title=ModEntry.T("airship.upgrade.title");
        Vector2 ts=Game1.dialogueFont.MeasureString(title);
        b.DrawString(Game1.dialogueFont,title,new Vector2(inner.Center.X-ts.X/2f,inner.Y+18),new Color(67,47,55));

        string name=this.GetSystemName();
        Vector2 ns=Game1.dialogueFont.MeasureString(name);
        b.DrawString(Game1.dialogueFont,name,new Vector2(inner.Center.X-ns.X/2f,inner.Y+94),new Color(75,53,65));

        Rectangle card=new(inner.X+60,inner.Y+150,inner.Width-120,178);
        CardchaUi.DrawInsetPanel(b,card,new Color(224,207,187),new Color(145,99,69),2,4);
        int level=this.GetLevel();
        int cost=GetTestCostForCurrentLevel(level);
        b.DrawString(Game1.smallFont,this.GetSystemDesc(),new Vector2(card.X+24,card.Y+22),new Color(74,57,58));
        b.DrawString(Game1.smallFont,ModEntry.T("airship.upgrade.level",new{level,max=MaxLevel}),new Vector2(card.X+24,card.Y+84),new Color(84,60,67));
        b.DrawString(Game1.smallFont,ModEntry.T("airship.upgrade.dust",new{amount=this.Save.Data.SuspiciousDust}),new Vector2(card.X+24,card.Y+116),new Color(84,60,67));
        string costText=level>=MaxLevel?ModEntry.T("airship.upgrade.cost.max"):ModEntry.T("airship.upgrade.cost",new{cost});
        b.DrawString(Game1.smallFont,costText,new Vector2(card.Right-220,card.Y+100),new Color(99,67,70));

        b.DrawString(Game1.smallFont,this.Status,new Vector2(inner.X+60,inner.Bottom-118),new Color(75,58,67));
        DrawButton(b,this.CloseButton,ModEntry.T("airship.upgrade.button.close"),true);
        DrawButton(b,this.UpgradeButton,level<MaxLevel?ModEntry.T("airship.upgrade.button.upgrade"):ModEntry.T("airship.upgrade.button.max"),level<MaxLevel);
        drawMouse(b);
    }

    private static void DrawButton(SpriteBatch b,Rectangle r,string text,bool enabled)
    {
        Color fill=enabled?new Color(126,83,70):new Color(116,108,105);
        CardchaUi.DrawInsetPanel(b,r,fill,new Color(72,52,55),2,3);
        Vector2 s=Game1.smallFont.MeasureString(text);
        b.DrawString(Game1.smallFont,text,new Vector2(r.Center.X-s.X/2f,r.Center.Y-s.Y/2f),Color.White*0.94f);
    }
}
'''
write(CARDCHA/"UI"/"AirshipUpgradeMenu.cs", menu)


# -----------------------------------------------------------------------------
# MiMi portrait: GameContent owns the compatibility texture. Never retain a Texture2D that SMAPI
# can dispose behind us. mimi_portraits.png remains the single master source.
# -----------------------------------------------------------------------------
mimi_path=CARDCHA/"Services"/"MimiMysteryTownService.cs"
mimi=read(mimi_path)
mimi=mimi.replace('    private Texture2D? MasterPortraitSheet;\n    private Texture2D? RuntimePortraitSheet;\n','')
mimi=replace_once(mimi,'        this.EnsureTextures();\n        this.WorldActors.EnsureMimiActor();','        this.WorldActors.EnsureMimiActor();',"remove portrait prewarm")
mimi=replace_between(
    mimi,
    '    internal void PrepareCrispPortrait(NPC speaker)',
    '    private static Texture2D CreateRuntimePortraitSheet',
    r'''    internal void PrepareCrispPortrait(NPC speaker)
    {
        Texture2D portrait = this.GetLivePortraitTexture();
        AssignPortraitTexture(speaker, portrait);
    }

    private Texture2D GetNativePortraitCompatibilitySheet()
    {
        // IMPORTANT: this texture is returned to GameContent, which owns/disposes it.
        // Never store this instance in a service field.
        Texture2D master = this.Helper.ModContent.Load<Texture2D>(MimiPortraitsPath);
        return CreateRuntimePortraitSheet(master);
    }

    internal bool TryShowCrispPortraitDialogue(NPC speaker, string text)
        => this.TryShowDialogueWithPortrait(speaker, text);

    private Texture2D GetLivePortraitTexture()
    {
        Texture2D portrait = Game1.content.Load<Texture2D>(PortraitAsset);
        if (!portrait.IsDisposed)
            return portrait;

        // A Content Patcher / portrait mod can invalidate the asset while a Cardcha NPC object
        // still exists. Force a fresh GameContent-owned instance rather than drawing a stale pointer.
        this.Helper.GameContent.InvalidateCache(PortraitAsset);
        portrait = Game1.content.Load<Texture2D>(PortraitAsset);
        if (portrait.IsDisposed)
            throw new ObjectDisposedException(PortraitAsset, "MiMi portrait reloaded as disposed.");
        return portrait;
    }

    private bool TryShowDialogueWithPortrait(NPC speaker, string text)
    {
        try
        {
            Texture2D portrait = this.GetLivePortraitTexture();
            AssignPortraitTexture(speaker, portrait);
            Dialogue dialogue = new Dialogue(speaker, "Mods/Ronvotri.Cardcha:RuntimeDialogue", text)
            {
                overridePortrait = portrait,
                showPortrait = true
            };
            Game1.activeClickableMenu = new DialogueBox(dialogue);
            return true;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"MiMi portrait dialogue failed: {ex}", LogLevel.Error);
            return false;
        }
    }''',
    "GameContent portrait ownership",
)
# remove obsolete EnsureTextures method
obsolete='''    private void EnsureTextures()\n    {\n        this.MasterPortraitSheet ??= this.Helper.ModContent.Load<Texture2D>(MimiPortraitsPath);\n        this.RuntimePortraitSheet ??= CreateRuntimePortraitSheet(this.MasterPortraitSheet);\n    }\n\n'''
require(obsolete in mimi,"missing obsolete EnsureTextures")
mimi=mimi.replace(obsolete,'',1)
write(mimi_path,mimi)


# -----------------------------------------------------------------------------
# WizardHouse: NEVER delete vanilla/modded Buildings/Front tiles to make room for the attic marker.
# Pick one deterministic clear floor position and draw the stairs there without map mutation.
# -----------------------------------------------------------------------------
visual_path=CARDCHA/"Services"/"MimiAtticVisualService.cs"
visual=read(visual_path)
visual=replace_once(visual,'            PrepareWizardStairArea(location, stair);\n            this.DrawStairMarker(e.SpriteBatch, stair);','            this.DrawStairMarker(e.SpriteBatch, stair);',"stop WizardHouse tile deletion")
write(visual_path,visual)

home_path=CARDCHA/"Services"/"MimiHomeService.cs"
home=read(home_path)
home=replace_between(
    home,
    '    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)',
    '    private static Point ResolveWizardLandingTile',
    r'''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)
    {
        int width = wizard.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 12;
        int height = wizard.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 10;

        // Deterministic right-half floor scan. We never erase WizardHouse tiles to force a spot.
        // Cached by the caller, so the marker cannot "run" as NPCs or temporary objects move.
        int startY = Math.Clamp((int)Math.Round(height * 0.58f), 3, Math.Max(3, height - 3));
        for (int dy = 0; dy < Math.Max(2, height / 3); dy++)
        {
            int y = Math.Clamp(startY + dy, 2, Math.Max(2, height - 3));
            for (int x = Math.Max(2, width - 4); x >= Math.Max(2, width / 2); x--)
            {
                Point p = new(x, y);
                if (!IsTileClear(wizard, p))
                    continue;
                // Keep the landing tile below clear too, so the stair never pins the farmer to decor.
                Point below = new(x, Math.Min(height - 2, y + 1));
                if (IsTileClear(wizard, below))
                    return p;
            }
        }

        return FindClearTileNear(wizard, new Point(Math.Max(2, width - 4), Math.Max(2, height / 2)));
    }''',
    "safe WizardHouse stair",
)
write(home_path,home)


# Audit.
audit={
    "version":NEW_VERSION,
    "scope":"0648B visual architecture + portrait lifecycle",
    "gate":"stable geometry; no rotating sigil/cloud animation",
    "deckShell":"vanilla townInterior + transparent Cardcha decor",
    "dockShell":"vanilla townInterior + visible boarding pad",
    "deckStations":{"engine":[4,8],"navigation":[19,8],"hull":[7,11],"reactor":[16,11]},
    "upgradeUi":"one station -> one system only",
    "flight":"time/weather palette + rain/snow/lightning/debris + clear night stars",
    "mimiPortrait":"GameContent-owned runtime compatibility texture generated from mimi_portraits.png",
    "wizardHouse":"zero tile deletion",
}
(ASSETS/"airship_0648b_visual_portrait_audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
print(json.dumps(audit,indent=2))

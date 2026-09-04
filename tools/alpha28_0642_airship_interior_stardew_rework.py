from __future__ import annotations

from pathlib import Path
import json
import math
import re
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "src" / "Cardcha"
ASSETS = MOD / "assets"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.8"
CUSTOM_FIRST_GID = 4096

# Compact Stardew-friendly palette. Major objects use dark plum/brown outlines, warm wood,
# muted brass, violet, cyan, and a small number of highlight colors.
P = {
    "void": (22, 15, 23, 255),
    "outline": (48, 29, 35, 255),
    "outline2": (62, 36, 42, 255),
    "wood0": (74, 42, 37, 255),
    "wood1": (100, 57, 43, 255),
    "wood2": (126, 73, 49, 255),
    "wood3": (151, 91, 58, 255),
    "woodhi": (181, 117, 72, 255),
    "brass0": (104, 68, 43, 255),
    "brass1": (163, 109, 55, 255),
    "brass2": (211, 153, 70, 255),
    "brass3": (240, 192, 101, 255),
    "purple0": (55, 36, 66, 255),
    "purple1": (79, 48, 90, 255),
    "purple2": (111, 67, 126, 255),
    "purple3": (154, 95, 174, 255),
    "purplehi": (195, 132, 210, 255),
    "cyan0": (45, 92, 109, 255),
    "cyan1": (55, 139, 159, 255),
    "cyan2": (75, 190, 205, 255),
    "cyan3": (125, 226, 226, 255),
    "sky0": (38, 49, 88, 255),
    "sky1": (55, 79, 125, 255),
    "sky2": (74, 120, 158, 255),
    "sky3": (117, 158, 181, 255),
    "cloud0": (143, 157, 175, 255),
    "cloud1": (190, 190, 197, 255),
    "cream": (226, 203, 157, 255),
    "paper": (218, 190, 143, 255),
    "green0": (48, 84, 61, 255),
    "green1": (72, 116, 72, 255),
    "green2": (105, 151, 82, 255),
}


def rect(d: ImageDraw.ImageDraw, xy, fill, outline=None, width=1):
    d.rectangle(xy, fill=fill, outline=outline, width=width)


def line(d: ImageDraw.ImageDraw, pts, fill, width=1):
    d.line(pts, fill=fill, width=width)


def pixel_diamond(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, fill, outline=None):
    pts = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
    d.polygon(pts, fill=fill, outline=outline)


def rivets(d: ImageDraw.ImageDraw, x0, y0, x1, y1, step=13, color=None):
    color = color or P["brass2"]
    for x in range(x0, x1+1, step):
        rect(d, (x, y0, x+1, y0+1), color)
        rect(d, (x, y1, x+1, y1+1), P["brass0"])


def draw_plank_floor(d: ImageDraw.ImageDraw, box, base_key="wood1"):
    x0, y0, x1, y1 = box
    rect(d, box, P[base_key])
    for y in range(y0, y1+1, 16):
        line(d, [(x0, y), (x1, y)], P["outline2"], 1)
        if y + 1 <= y1:
            line(d, [(x0, y+1), (x1, y+1)], P["wood3"], 1)
    for row, y in enumerate(range(y0, y1+1, 16)):
        offset = 0 if row % 2 == 0 else 12
        for x in range(x0 + offset, x1+1, 32):
            line(d, [(x, y), (x, min(y+16, y1))], P["outline2"], 1)
            if x + 1 <= x1:
                line(d, [(x+1, y+2), (x+1, min(y+14, y1))], P["wood2"], 1)
    # knots and nicks keep the floor from reading as a flat fill
    for x, y in [(41, 123), (73, 173), (111, 142), (145, 199), (218, 156), (280, 190), (334, 133)]:
        if x0 < x < x1 and y0 < y < y1:
            rect(d, (x, y, x+2, y+1), P["outline2"])
            rect(d, (x+1, y, x+1, y), P["woodhi"])


def draw_window_sky(d: ImageDraw.ImageDraw, box, night=False):
    x0, y0, x1, y1 = box
    colors = [P["sky0"], P["sky1"], P["sky2"] if not night else P["purple1"], P["sky3"] if not night else P["purple2"]]
    h = y1 - y0 + 1
    band = max(1, h // len(colors))
    for i, c in enumerate(colors):
        yy0 = y0 + i * band
        yy1 = y1 if i == len(colors)-1 else min(y1, yy0 + band - 1)
        rect(d, (x0, yy0, x1, yy1), c)
    # pixel clouds/islands
    for cx, cy, w in [(34, y0+31, 34), (108, y0+48, 42), (218, y0+27, 30), (302, y0+54, 44)]:
        if x0 <= cx <= x1:
            rect(d, (cx, cy, min(cx+w, x1), cy+3), P["cloud0"])
            rect(d, (cx+7, cy-3, min(cx+w-9, x1), cy+1), P["cloud1"])
    for cx, cy in [(58, y0+18), (151, y0+13), (264, y0+17), (335, y0+25)]:
        if x0 < cx < x1:
            rect(d, (cx, cy, cx+1, cy+1), P["cream"])


def draw_bridge_console(d, cx, cy, accent):
    # chunky 24-ish pixel furniture, scaled by Stardew's map zoom later
    rect(d, (cx-24, cy-10, cx+24, cy+11), P["outline"])
    rect(d, (cx-21, cy-8, cx+21, cy+8), P["wood1"])
    rect(d, (cx-18, cy-6, cx+18, cy-1), P["wood2"])
    rect(d, (cx-15, cy-5, cx-3, cy-2), P["cyan0"])
    rect(d, (cx+1, cy-5, cx+15, cy-2), accent)
    rect(d, (cx-19, cy+7, cx+19, cy+9), P["brass1"])
    for x in (cx-14, cx+14):
        rect(d, (x-2, cy+10, x+2, cy+18), P["outline"])
        rect(d, (x-1, cy+10, x+1, cy+17), P["brass1"])


def draw_station_pad(d, cx, cy, accent):
    # background plinth only. Runtime station art sits on top.
    rect(d, (cx-18, cy-6, cx+18, cy+7), P["outline"])
    rect(d, (cx-15, cy-4, cx+15, cy+4), P["wood0"])
    rect(d, (cx-11, cy-2, cx+11, cy+1), P["brass0"])
    rect(d, (cx-7, cy+3, cx+7, cy+4), accent)
    for x in (cx-13, cx+12):
        rect(d, (x, cy+5, x+1, cy+6), P["brass2"])


def draw_banner(d, x, y):
    rect(d, (x, y, x+16, y+24), P["outline"])
    rect(d, (x+2, y+2, x+14, y+20), P["purple1"])
    pixel_diamond(d, x+8, y+10, 4, P["purple3"], P["brass1"])
    rect(d, (x+4, y+18, x+12, y+19), P["brass2"])
    d.polygon([(x+2,y+20),(x+8,y+24),(x+14,y+20)], fill=P["purple1"], outline=P["outline"])


def draw_airship_deck() -> Image.Image:
    W, H = 384, 224
    im = Image.new("RGBA", (W, H), P["void"])
    d = ImageDraw.Draw(im)

    # Outer hull shadow and warm wall mass.
    rect(d, (8, 6, W-9, H-7), P["outline"])
    rect(d, (11, 9, W-12, H-10), P["wood0"])

    # Panoramic window with a real Stardew-style dark/brass frame.
    win = (30, 16, W-31, 79)
    rect(d, (win[0]-5, win[1]-5, win[2]+5, win[3]+6), P["outline"])
    rect(d, (win[0]-2, win[1]-2, win[2]+2, win[3]+3), P["brass0"])
    draw_window_sky(d, win)
    for x in [75, 120, 165, 219, 264, 309]:
        rect(d, (x-2, win[1], x+2, win[3]), P["outline"])
        rect(d, (x-1, win[1]+2, x, win[3]-2), P["brass1"])
    rect(d, (win[0], win[3]-4, win[2], win[3]), P["outline"])
    rect(d, (win[0]+2, win[3]-2, win[2]-2, win[3]-1), P["brass2"])

    # Curved canopy impression with stepped pixel ribs.
    for inset, col in [(0, P["outline"]), (3, P["brass0"]), (5, P["wood2"])]:
        line(d, [(22+inset, 15+inset), (42+inset, 7+inset), (W-43-inset, 7+inset), (W-23-inset, 15+inset)], col, 2 if inset == 0 else 1)
    rivets(d, 34, 9, W-34, 12, 18, P["brass2"])

    # Wall strip between window and floor.
    rect(d, (14, 82, W-15, 103), P["wood1"])
    rect(d, (14, 82, W-15, 84), P["brass1"])
    for x in range(22, W-20, 16):
        rect(d, (x, 88, x+8, 96), P["wood2"])
        rect(d, (x+1, 89, x+7, 90), P["woodhi"])
    draw_banner(d, 18, 70)
    draw_banner(d, W-35, 70)

    # Floor.
    draw_plank_floor(d, (12, 104, W-13, H-12), "wood1")
    rect(d, (12, 103, W-13, 107), P["outline"])
    rect(d, (14, 105, W-15, 106), P["brass1"])

    # Central runner, deliberately below the farmer layer because this is part of Back.
    rect(d, (171, 106, 213, H-14), P["outline2"])
    rect(d, (174, 108, 210, H-16), P["purple1"])
    rect(d, (176, 109, 178, H-17), P["brass1"])
    rect(d, (206, 109, 208, H-17), P["brass1"])
    for y in range(122, H-22, 25):
        pixel_diamond(d, 192, y, 4, P["purple2"], P["brass0"])

    # Helm dais: solid furniture mass lives in the map, animated astrolabe comes from runtime.
    rect(d, (150, 76, 234, 105), P["outline"])
    rect(d, (154, 79, 230, 102), P["wood1"])
    rect(d, (160, 81, 224, 91), P["wood2"])
    rect(d, (164, 82, 220, 84), P["woodhi"])
    rect(d, (160, 95, 224, 99), P["brass0"])
    for x in [168, 181, 203, 216]:
        rect(d, (x, 88, x+5, 92), P["outline2"])
        rect(d, (x+1, 89, x+4, 90), P["cyan1"] if x < 192 else P["purple2"])

    # Side consoles and instrument bays.
    draw_bridge_console(d, 78, 117, P["purple2"])
    draw_bridge_console(d, 306, 117, P["cyan1"])
    for cx in (46, 338):
        rect(d, (cx-14, 109, cx+14, 130), P["outline"])
        rect(d, (cx-11, 112, cx+11, 127), P["wood0"])
        for yy in (115, 121):
            rect(d, (cx-7, yy, cx-2, yy+2), P["cyan1"])
            rect(d, (cx+2, yy, cx+7, yy+2), P["brass2"])

    # ChaCha alcove, upper-right. No foreground arch crossing the farmer.
    rect(d, (286, 68, 350, 101), P["outline"])
    rect(d, (289, 71, 347, 98), P["purple0"])
    rect(d, (292, 74, 344, 76), P["brass1"])
    pixel_diamond(d, 304, 88, 6, P["purple3"], P["outline"])
    pixel_diamond(d, 333, 88, 6, P["cyan2"], P["outline"])
    rect(d, (311, 82, 326, 95), P["wood1"], P["outline"], 1)
    rect(d, (314, 84, 323, 87), P["brass2"])

    # Upgrade pads at the canonical runtime sockets: Engine, Navigation, Hull, Reactor.
    draw_station_pad(d, 5*16+8, 9*16+10, P["cyan1"])
    draw_station_pad(d, 18*16+8, 9*16+10, P["cyan2"])
    draw_station_pad(d, 8*16+8, 10*16+10, P["purple2"])
    draw_station_pad(d, 15*16+8, 10*16+10, P["purple3"])

    # Pipes/conduits are chunky, low-contrast background details, never translucent lines over player.
    for pts, accent in [
        ([(88,152),(88,138),(149,138),(149,118)], P["cyan0"]),
        ([(296,152),(296,138),(235,138),(235,118)], P["cyan0"]),
        ([(136,169),(154,169),(154,147)], P["purple1"]),
        ([(248,169),(230,169),(230,147)], P["purple1"]),
    ]:
        line(d, pts, P["outline"], 4)
        line(d, pts, accent, 2)
        for px, py in pts[1:-1]:
            rect(d, (px-2, py-2, px+2, py+2), P["brass1"])

    # Service clutter at wall edges, leaving center path clean.
    rect(d, (22, 151, 52, 181), P["outline"])
    rect(d, (25, 154, 49, 178), P["wood2"])
    line(d, [(27,156),(47,176)], P["outline2"], 2)
    line(d, [(47,156),(27,176)], P["outline2"], 2)
    rect(d, (332, 151, 360, 180), P["outline"])
    rect(d, (335, 154, 357, 177), P["wood2"])
    for yy in (157,163,169):
        rect(d, (339, yy, 352, yy+2), P["brass0"])

    # Hull frame and base trim.
    rect(d, (8, H-12, W-9, H-7), P["outline"])
    rect(d, (13, H-11, W-14, H-9), P["brass1"])
    rivets(d, 24, H-10, W-24, H-8, 20, P["brass2"])
    return im


def draw_coil(d, cx, cy, color):
    for r in (10, 7, 4):
        d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=P["outline"] if r == 10 else color, width=2 if r == 10 else 1)


def draw_crate(d, x, y, w=28, h=24):
    rect(d, (x, y, x+w, y+h), P["outline"])
    rect(d, (x+3, y+3, x+w-3, y+h-3), P["wood2"])
    line(d, [(x+5,y+5),(x+w-5,y+h-5)], P["outline2"], 2)
    line(d, [(x+w-5,y+5),(x+5,y+h-5)], P["outline2"], 2)
    rect(d, (x+6, y+2, x+w-6, y+4), P["brass1"])


def draw_lamp(d, x, y, glow):
    rect(d, (x-2, y-14, x+2, y), P["outline"])
    rect(d, (x-1, y-13, x+1, y-1), P["brass1"])
    rect(d, (x-6, y-22, x+6, y-13), P["outline"])
    rect(d, (x-3, y-19, x+3, y-15), glow)
    rect(d, (x-7, y-23, x+7, y-21), P["brass2"])


def draw_sky_dock() -> Image.Image:
    W, H = 480, 288
    im = Image.new("RGBA", (W, H), P["void"])
    d = ImageDraw.Draw(im)

    rect(d, (7, 7, W-8, H-7), P["outline"])
    rect(d, (10, 10, W-11, H-10), P["wood0"])

    # Upper warehouse/dock wall.
    rect(d, (12, 12, W-13, 88), P["purple0"])
    for y in (14, 30, 46, 62, 78):
        line(d, [(14,y),(W-15,y)], P["outline2"], 1)
    for x in range(20, W-18, 32):
        rect(d, (x, 16, x+13, 26), P["wood1"])
        rect(d, (x+2, 18, x+11, 19), P["wood3"])
    rect(d, (12, 86, W-13, 91), P["outline"])
    rect(d, (14, 87, W-15, 89), P["brass1"])

    # Floor and broad central boarding strip.
    draw_plank_floor(d, (12, 92, W-13, H-12), "wood1")
    rect(d, (219, 92, 261, H-14), P["outline2"])
    rect(d, (222, 94, 258, H-16), P["purple1"])
    for y in range(110, H-25, 30):
        pixel_diamond(d, 240, y, 4, P["purple2"], P["brass0"])

    # Big boarding arch on the right, directly around canonical bay tile (24,7).
    bx, by = 24*16+8, 7*16+8
    rect(d, (bx-49, 52, bx+49, 145), P["outline"])
    rect(d, (bx-45, 56, bx+45, 141), P["brass0"])
    rect(d, (bx-40, 61, bx+40, 136), P["purple0"])
    # Open sky beyond boarding door.
    draw_window_sky(d, (bx-34, 66, bx+34, 125))
    rect(d, (bx-36, 64, bx+36, 67), P["outline"])
    rect(d, (bx-36, 124, bx+36, 129), P["outline"])
    for x in (bx-34, bx+32):
        rect(d, (x, 68, x+2, 123), P["brass1"])
    pixel_diamond(d, bx, 56, 6, P["cyan2"], P["outline"])
    rect(d, (bx-25, 132, bx+25, 138), P["outline"])
    rect(d, (bx-21, 132, bx+21, 134), P["brass2"])

    # Route console on left, canonical tile (10,7), styled as a solid Stardew desk.
    rx, ry = 10*16+8, 7*16+8
    rect(d, (rx-39, ry-23, rx+39, ry+22), P["outline"])
    rect(d, (rx-35, ry-19, rx+35, ry+18), P["wood1"])
    rect(d, (rx-29, ry-15, rx+29, ry-3), P["wood2"])
    rect(d, (rx-25, ry-13, rx-2, ry-7), P["purple1"])
    rect(d, (rx+3, ry-13, rx+25, ry-7), P["cyan0"])
    pixel_diamond(d, rx, ry+3, 7, P["purple3"], P["brass0"])
    rect(d, (rx-30, ry+14, rx+30, ry+18), P["brass0"])
    for x in (rx-29, rx+25):
        rect(d, (x, ry+19, x+4, ry+31), P["outline"])
        rect(d, (x+1, ry+19, x+3, ry+30), P["wood2"])

    # Side service zones: crates, rope, shelves, lanterns, maps. Central route remains empty.
    draw_crate(d, 28, 130, 30, 26)
    draw_crate(d, 62, 145, 26, 22)
    draw_coil(d, 49, 181, P["brass1"])
    draw_lamp(d, 30, 114, P["cyan2"])
    draw_lamp(d, W-31, 113, P["purple3"])

    # Tool cabinet and spare crystals on right wall.
    rect(d, (430, 150, 459, 218), P["outline"])
    rect(d, (433, 153, 456, 215), P["wood0"])
    for y in range(159, 207, 12):
        rect(d, (437, y, 452, y+3), P["brass0"])
    pixel_diamond(d, 441, 227, 7, P["cyan2"], P["outline"])
    pixel_diamond(d, 455, 230, 6, P["purple3"], P["outline"])

    # Map/notice board and parcel shelf on left wall.
    rect(d, (25, 41, 106, 80), P["outline"])
    rect(d, (29, 45, 102, 76), P["wood1"])
    rect(d, (34, 49, 63, 68), P["paper"])
    line(d, [(38,53),(56,64)], P["purple2"], 1)
    line(d, [(39,64),(57,54)], P["cyan1"], 1)
    rect(d, (69, 49, 97, 54), P["paper"])
    rect(d, (70, 58, 95, 62), P["paper"])
    rect(d, (71, 66, 90, 70), P["paper"])

    # Dock rail zones at sides only, no bars across the farmer.
    for x0, x1 in [(112, 192), (288, 356)]:
        line(d, [(x0, 199), (x1, 199)], P["outline"], 4)
        line(d, [(x0, 198), (x1, 198)], P["brass1"], 1)
        for x in range(x0, x1+1, 20):
            rect(d, (x, 184, x+3, 201), P["outline"])
            rect(d, (x+1, 185, x+2, 198), P["brass1"])

    # Bottom return threshold.
    rect(d, (212, H-23, 268, H-12), P["outline"])
    rect(d, (218, H-21, 262, H-16), P["brass0"])
    pixel_diamond(d, 240, H-20, 4, P["cyan2"], P["outline"])

    # Warm clutter and greenery make this a used dock rather than a demo room.
    rect(d, (112, 48, 134, 80), P["outline"])
    rect(d, (115, 51, 131, 77), P["wood0"])
    for yy in (55,62,69):
        rect(d, (118, yy, 128, yy+2), P["brass0"])
    rect(d, (137, 61, 151, 78), P["outline"])
    rect(d, (140, 65, 148, 76), P["green0"])
    for px, py in [(140,62),(145,58),(150,61),(143,55)]:
        rect(d, (px, py, px+4, py+4), P["green1"])

    return im


def stardewize_upgrade_atlas(path: Path):
    im = Image.open(path).convert("RGBA")
    if im.size != (384, 384):
        raise RuntimeError(f"unexpected upgrade atlas size: {im.size}")
    out = Image.new("RGBA", im.size, (0,0,0,0))
    for row in range(4):
        for col in range(4):
            cell = im.crop((col*96, row*96, col*96+96, row*96+96))
            # Collapse fine anti-concept detail into 24x24 pixel clusters, then nearest-upscale.
            small = cell.resize((24,24), Image.Resampling.NEAREST)
            # Quantize visible RGB while preserving alpha.
            rgba = small.getdata()
            q = []
            for r,g,b,a in rgba:
                if a < 18:
                    q.append((0,0,0,0))
                else:
                    # 32-step channel quantization, warmer darks.
                    rr = min(255, (r // 32) * 32 + 15)
                    gg = min(255, (g // 32) * 32 + 15)
                    bb = min(255, (b // 32) * 32 + 15)
                    q.append((rr,gg,bb,255))
            small.putdata(q)

            # Dark one-pixel outline at 24x24 scale.
            alpha = small.getchannel("A")
            dil = alpha.filter(__import__('PIL').ImageFilter.MaxFilter(3)) if False else None
            outlined = Image.new("RGBA", (24,24), (0,0,0,0))
            od = ImageDraw.Draw(outlined)
            pix = small.load()
            for y in range(24):
                for x in range(24):
                    if pix[x,y][3] > 0:
                        continue
                    hit = False
                    for oy in (-1,0,1):
                        for ox in (-1,0,1):
                            xx, yy = x+ox, y+oy
                            if 0 <= xx < 24 and 0 <= yy < 24 and pix[xx,yy][3] > 0:
                                hit = True
                    if hit:
                        od.point((x,y), fill=P["outline"])
            outlined.alpha_composite(small)
            big = outlined.resize((96,96), Image.Resampling.NEAREST)
            out.alpha_composite(big, (col*96,row*96))
    out.save(path)


def patch_tmx(path: Path, image_name: str, width_tiles: int, height_tiles: int, role_value: str):
    tree = ET.parse(path)
    root = tree.getroot()
    # Remove prior generated backdrop tileset on reruns.
    for ts in list(root.findall("tileset")):
        if ts.attrib.get("name", "").startswith("cardchaStardewBackdrop"):
            root.remove(ts)

    tileset = ET.Element("tileset", {
        "firstgid": str(CUSTOM_FIRST_GID),
        "name": f"cardchaStardewBackdrop_{path.stem}",
        "tilewidth": "16",
        "tileheight": "16",
        "tilecount": str(width_tiles * height_tiles),
        "columns": str(width_tiles),
    })
    ET.SubElement(tileset, "image", {
        "source": image_name,
        "width": str(width_tiles * 16),
        "height": str(height_tiles * 16),
    })
    # Add after existing vanilla tileset so old Buildings/Front gids remain intact.
    existing = root.findall("tileset")
    if existing:
        idx = list(root).index(existing[-1]) + 1
        root.insert(idx, tileset)
    else:
        root.insert(0, tileset)

    back = next(layer for layer in root.findall("layer") if layer.attrib.get("name") == "Back")
    data = back.find("data")
    gids = []
    for y in range(height_tiles):
        row = [str(CUSTOM_FIRST_GID + y * width_tiles + x) for x in range(width_tiles)]
        gids.append(",".join(row))
    data.attrib["encoding"] = "csv"
    data.text = "\n" + ",\n".join(gids) + "\n"

    props = root.find("properties")
    if props is None:
        props = ET.Element("properties")
        root.insert(0, props)
    # replace/add visual profile properties
    prop_map = {p.attrib.get("name"): p for p in props.findall("property")}
    for name, value in {
        "CardchaStardewInteriorRework": VERSION,
        "CardchaVisualProfile": role_value,
        "CardchaAssetPolicy": "cardcha-owned-map|custom-pixel-backdrop|stardew-outline|no-foreground-player-occlusion",
    }.items():
        if name in prop_map:
            prop_map[name].set("value", value)
        else:
            ET.SubElement(props, "property", {"name": name, "value": value})

    ET.indent(tree, space=" ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)


def patch_runtime_source():
    svc = MOD / "Services" / "AirshipFoundationService.cs"
    text = svc.read_text(encoding="utf-8")
    deck_marker = "// .5.8 Stardew interior renderer owns Bridge visual staging."
    if deck_marker not in text:
        needle = "    private void DrawDeckMarkers(SpriteBatch batch, GameLocation deck)\n    {\n"
        replacement = needle + f"        {deck_marker}\n        if (AirshipInteriorStardewRenderer.TryDrawDeck(batch, deck, this.Save))\n            return;\n\n"
        if needle not in text:
            raise RuntimeError("DrawDeckMarkers signature not found")
        text = text.replace(needle, replacement, 1)

    dock_marker = "// .5.8 Stardew interior renderer owns Sky Dock visual staging."
    if dock_marker not in text:
        needle = "    private void DrawSkyDockInteriorDetails(SpriteBatch batch, GameLocation interior)\n    {\n"
        replacement = needle + f"        {dock_marker}\n        if (AirshipInteriorStardewRenderer.TryDrawSkyDock(batch, interior))\n            return;\n\n"
        if needle not in text:
            raise RuntimeError("DrawSkyDockInteriorDetails signature not found")
        text = text.replace(needle, replacement, 1)
    svc.write_text(text, encoding="utf-8")

    depth = MOD / "Patches" / "AirshipVisualDepthPatch.cs"
    text = depth.read_text(encoding="utf-8")
    marker = "// .5.8: Sky Dock props are baked into the pixel backdrop; do not post-render furniture over the farmer."
    if marker not in text:
        needle = "    private static void AfterSkyDockInterior(SpriteBatch batch, GameLocation interior)\n    {\n"
        replacement = needle + f"        {marker}\n        return;\n\n"
        if needle not in text:
            raise RuntimeError("AfterSkyDockInterior signature not found")
        text = text.replace(needle, replacement, 1)
        depth.write_text(text, encoding="utf-8")


def patch_version():
    manifest_path = MOD / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["Version"] = VERSION
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csproj = MOD / "Cardcha.csproj"
    text = csproj.read_text(encoding="utf-8")
    text = re.sub(r"<Version>[^<]+</Version>", f"<Version>{VERSION}</Version>", text, count=1)
    csproj.write_text(text, encoding="utf-8")

    targets = MOD / "Directory.Build.targets"
    text = targets.read_text(encoding="utf-8")
    text = re.sub(r"<Version>[^<]+</Version>", f"<Version>{VERSION}</Version>", text, count=1)
    text = re.sub(r"0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.6\.1\.[0-9]+", VERSION, text)
    targets.write_text(text, encoding="utf-8")


def main():
    deck = draw_airship_deck()
    dock = draw_sky_dock()
    deck.save(ASSETS / "airship_deck_stardew.png")
    dock.save(ASSETS / "sky_dock_stardew.png")

    stardewize_upgrade_atlas(ASSETS / "airship_upgrade_visuals.png")
    patch_tmx(ASSETS / "airship_deck.tmx", "airship_deck_stardew.png", 24, 14,
              "stardew-airship-bridge|pixel-outline|warm-wood-brass|panoramic-canopy|integrated-upgrade-pads")
    patch_tmx(ASSETS / "sky_dock_interior.tmx", "sky_dock_stardew.png", 30, 18,
              "stardew-airship-dock|pixel-outline|boarding-arch|route-desk|service-clutter|clear-center-lane")
    patch_runtime_source()
    patch_version()
    print(f"Generated Cardcha {VERSION} Airship interior Stardew rework")


if __name__ == "__main__":
    main()

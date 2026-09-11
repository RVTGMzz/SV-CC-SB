#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
import random

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/Cardcha/assets"
OUT = ASSETS / "airship_props/density_0693"
OUT.mkdir(parents=True, exist_ok=True)

C = {
    "outline": (63,30,24,255), "outline2": (93,44,28,255),
    "wood_dark": (96,47,29,255), "wood": (139,73,36,255),
    "wood_light": (188,111,51,255), "wood_hi": (225,151,70,255),
    "brass_dark": (143,77,28,255), "brass": (214,140,51,255),
    "brass_hi": (248,199,91,255), "purple_dark": (76,41,92,255),
    "purple": (111,57,136,255), "purple_light": (163,96,184,255),
    "teal_dark": (39,112,116,255), "teal": (73,176,176,255),
    "teal_hi": (143,229,214,255), "cream": (239,217,166,255),
    "paper": (232,211,173,255), "paper_dark": (180,147,105,255),
    "green_dark": (39,92,54,255), "green": (47,137,74,255),
    "green_hi": (93,183,90,255), "red": (181,67,61,255),
    "blue": (75,119,165,255),
}

def rect(d, xy, c): d.rectangle(xy, fill=c)
def line(d, pts, c, w=1): d.line(pts, fill=c, width=w)
def panel(d, box, fill, border=None, hi=True):
    x0,y0,x1,y1 = box; border = border or C["outline"]
    rect(d,(x0,y0,x1,y1),border); rect(d,(x0+2,y0+2,x1-2,y1-2),fill)
    if hi:
        line(d,[(x0+3,y0+3),(x1-3,y0+3)],C["wood_hi"])
        line(d,[(x0+3,y0+3),(x0+3,y1-3)],C["wood_light"])

def lantern(d,cx,cy):
    rect(d,(cx-5,cy-7,cx+5,cy+8),C["outline"]); rect(d,(cx-4,cy-6,cx+4,cy+7),C["brass_dark"])
    rect(d,(cx-3,cy-4,cx+3,cy+4),C["cream"]); rect(d,(cx-2,cy-3,cx+2,cy+3),C["brass_hi"])
    rect(d,(cx-1,cy-2,cx+1,cy+2),(255,233,154,255)); rect(d,(cx-5,cy-10,cx+5,cy-7),C["brass"])
    rect(d,(cx-3,cy+8,cx+3,cy+11),C["brass_dark"])

def banner(d,x,y,w=16,h=34):
    rect(d,(x,y,x+w,y+h),C["outline"]); rect(d,(x+2,y+1,x+w-2,y+h-4),C["purple"])
    cx=x+w//2; cy=y+h//2-1
    rect(d,(cx-1,cy-6,cx+1,cy+6),C["brass_hi"]); rect(d,(cx-6,cy-1,cx+6,cy+1),C["brass_hi"])
    d.polygon([(x+2,y+h-4),(x+w-2,y+h-4),(cx,y+h+2)],fill=C["purple_dark"])

def plant(d,x,y,w=26,h=34):
    rect(d,(x+7,y+h-12,x+w-7,y+h-2),C["outline"]); rect(d,(x+9,y+h-11,x+w-9,y+h-3),C["wood"])
    rect(d,(x+5,y+h-14,x+w-5,y+h-11),C["brass"]); cx=x+w//2
    for dx,dy,col in [(-9,-18,"green"),(-3,-26,"green_hi"),(5,-24,"green"),(9,-17,"green_hi"),(-11,-10,"green_dark"),(3,-13,"green"),(0,-20,"green_hi")]:
        d.ellipse((cx+dx-4,y+h+dy-5,cx+dx+4,y+h+dy+4),fill=C[col])
    line(d,[(cx,y+h-13),(cx,y+h-28)],C["green_dark"],2)

def schedule(d,x,y,w=120,h=88):
    panel(d,(x,y,x+w-1,y+h-1),C["wood_dark"]); rect(d,(x+8,y+8,x+w-9,y+22),C["purple_dark"])
    line(d,[(x+12,y+10),(x+w-13,y+10)],C["brass_hi"])
    for i in range(7): rect(d,(x+22+i*10,y+13,x+28+i*10,y+16),C["brass_hi"])
    lantern(d,x+9,y+36); lantern(d,x+w-10,y+36)
    rect(d,(x+18,y+26,x+w-19,y+h-12),C["outline"]); rect(d,(x+20,y+28,x+w-21,y+h-14),(41,52,61,255))
    rows=[("cream","teal"),("paper","teal_hi"),("paper_dark","red"),("cream","teal"),("paper","teal_hi")]
    for i,(a,b) in enumerate(rows):
        yy=y+34+i*9; rect(d,(x+26,yy,x+56,yy+3),C[a]); rect(d,(x+66,yy,x+w-28,yy+3),C[b])
    plant(d,x+w-34,y+h-39,24,32)

def harbor_desk(d,x,y,w=150,h=100):
    panel(d,(x+20,y+6,x+w-10,y+58),C["wood_dark"])
    d.ellipse((x+w//2-14,y+1,x+w//2+14,y+29),fill=C["outline"]); d.ellipse((x+w//2-11,y+4,x+w//2+11,y+26),fill=C["cream"])
    line(d,[(x+w//2,y+15),(x+w//2+7,y+11)],C["outline"],2); line(d,[(x+w//2,y+15),(x+w//2-1,y+8)],C["outline"])
    for px in [x+28,x+50,x+w-52,x+w-30]:
        rect(d,(px,y+20,px+14,y+42),C["paper"]); line(d,[(px+2,y+25),(px+12,y+25)],C["paper_dark"]); line(d,[(px+2,y+31),(px+10,y+31)],C["paper_dark"])
    banner(d,x+w//2-9,y+24,18,36); panel(d,(x+6,y+55,x+w-4,y+h-4),C["wood"])
    for px in range(x+13,x+w-18,28):
        rect(d,(px,y+66,px+20,y+h-10),C["wood_dark"]); rect(d,(px+2,y+68,px+18,y+h-12),C["wood"])
    lantern(d,x+13,y+47); lantern(d,x+w-14,y+48); plant(d,x+2,y+28,28,34); plant(d,x+w-32,y+26,28,34)
    for bx,by,bw,bh in [(x+4,y+h-24,24,20),(x+w-28,y+h-22,24,18)]:
        panel(d,(bx,by,bx+bw,by+bh),C["blue"]); rect(d,(bx+6,by-4,bx+bw-6,by),C["brass"])

def waiting_nook(d,x,y,w=122,h=88):
    panel(d,(x+15,y+35,x+82,y+68),C["wood_dark"]); rect(d,(x+20,y+39,x+77,y+56),C["purple"])
    for sx in [x+22,x+50]:
        rect(d,(sx,y+41,sx+23,y+54),C["purple_light"]); line(d,[(sx+1,y+42),(sx+22,y+42)],C["brass"])
    rect(d,(x+12,y+50,x+18,y+75),C["wood_dark"]); rect(d,(x+80,y+50,x+86,y+75),C["wood_dark"])
    rect(d,(x+20,y+68,x+26,y+80),C["wood_dark"]); rect(d,(x+70,y+68,x+76,y+80),C["wood_dark"])
    plant(d,x-1,y+35,30,46); lantern(d,x+98,y+28); panel(d,(x+88,y+55,x+118,y+80),C["wood"])
    rect(d,(x+96,y+47,x+105,y+55),C["red"]); rect(d,(x+108,y+47,x+114,y+55),C["cream"])

def luggage(d,x,y,w=88,h=88):
    line(d,[(x+10,y+10),(x+10,y+72),(x+80,y+72),(x+80,y+15)],C["brass_hi"],3); line(d,[(x+8,y+12),(x+80,y+12)],C["brass"],2)
    for bx,by,bw,bh,col in [(x+20,y+30,34,30,C["blue"]),(x+46,y+38,28,26,C["purple"]),(x+28,y+17,32,20,C["wood"])]:
        panel(d,(bx,by,bx+bw,by+bh),col); rect(d,(bx+bw//2-6,by-3,bx+bw//2+6,by+1),C["brass"]); rect(d,(bx+4,by+5,bx+8,by+8),C["brass_hi"])
    banner(d,x+62,y+5,14,32)
    for cx in [x+22,x+68]:
        d.ellipse((cx-6,y+70,cx+6,y+82),fill=C["outline"]); d.ellipse((cx-3,y+73,cx+3,y+79),fill=C["brass"])

def bookshelf(d,x,y,w=88,h=104):
    panel(d,(x+6,y+5,x+w-4,y+h-4),C["wood_dark"])
    for sy in [y+34,y+57,y+80]:
        rect(d,(x+11,sy,x+w-9,sy+4),C["wood"]); line(d,[(x+12,sy+1),(x+w-10,sy+1)],C["wood_hi"])
    rng=random.Random(3); cols=[C["purple"],C["blue"],C["red"],C["cream"],C["teal"],C["wood_light"]]
    for sy in [y+15,y+38,y+61]:
        xx=x+13
        while xx<x+w-12:
            bw=rng.choice([5,6,7]); bh=rng.choice([14,16,18]); rect(d,(xx,sy+18-bh,xx+bw,sy+18),rng.choice(cols)); rect(d,(xx,sy+18-bh,xx+bw,sy+19-bh),C["brass_dark"]); xx += bw+2
    d.ellipse((x+w-30,y+1,x+w-10,y+21),outline=C["brass_hi"],width=2); line(d,[(x+w-20,y+2),(x+w-20,y+20)],C["brass"])
    lantern(d,x+w-9,y+58); plant(d,x-2,y+h-42,26,38)

def telescope(d,x,y,w=72,h=88):
    d.ellipse((x+8,y+66,x+w-4,y+84),fill=C["purple_dark"]); d.ellipse((x+12,y+69,x+w-8,y+81),outline=C["brass"],width=2)
    rect(d,(x+34,y+34,x+40,y+72),C["outline"]); rect(d,(x+35,y+35,x+39,y+70),C["brass"]); rect(d,(x+24,y+66,x+50,y+71),C["brass_dark"])
    d.polygon([(x+16,y+29),(x+53,y+12),(x+60,y+20),(x+22,y+38)],fill=C["outline"]); d.polygon([(x+20,y+29),(x+51,y+16),(x+56,y+20),(x+23,y+34)],fill=C["brass"])
    rect(d,(x+52,y+14,x+63,y+22),C["brass_hi"]); rect(d,(x+14,y+28,x+22,y+36),C["brass_dark"])
    panel(d,(x+4,y+54,x+24,y+72),C["wood"]); rect(d,(x+6,y+50,x+20,y+53),C["purple"]); panel(d,(x+50,y+50,x+68,y+68),C["wood_dark"]); rect(d,(x+51,y+45,x+67,y+49),C["blue"]); rect(d,(x+53,y+41,x+68,y+44),C["paper_dark"])

def teacart(d,x,y,w=58,h=58):
    panel(d,(x+10,y+20,x+47,y+48),C["wood"]); rect(d,(x+6,y+16,x+51,y+21),C["brass"]); rect(d,(x+14,y+28,x+43,y+31),C["wood_dark"]); rect(d,(x+14,y+37,x+43,y+40),C["wood_dark"])
    d.ellipse((x+16,y+4,x+31,y+18),fill=C["cream"],outline=C["outline"]); rect(d,(x+19,y+2,x+27,y+5),C["brass"]); line(d,[(x+30,y+10),(x+36,y+7)],C["brass"],2)
    plant(d,x+29,y-2,24,28); banner(d,x+2,y+22,12,26)
    for cx in [x+16,x+42]:
        d.ellipse((cx-4,y+46,cx+4,y+54),fill=C["outline"]); d.ellipse((cx-2,y+48,cx+2,y+52),fill=C["brass"])

def gramophone(d,x,y,w=58,h=58):
    panel(d,(x+7,y+30,x+48,y+52),C["wood"]); d.polygon([(x+20,y+8),(x+45,y+2),(x+54,y+10),(x+28,y+22)],fill=C["brass_dark"]); d.polygon([(x+25,y+9),(x+45,y+5),(x+50,y+10),(x+28,y+18)],fill=C["brass_hi"])
    rect(d,(x+20,y+16,x+26,y+34),C["brass"]); d.ellipse((x+16,y+32,x+35,y+45),fill=C["outline"]); d.ellipse((x+19,y+35,x+32,y+42),fill=(30,25,35,255)); plant(d,x+36,y+22,22,30); rect(d,(x+10,y+25,x+16,y+31),C["purple"]); rect(d,(x+12,y+21,x+15,y+24),C["cream"])

def rug(d,x,y,w=108,h=58):
    rect(d,(x+2,y+2,x+w-3,y+h-3),C["outline"]); rect(d,(x+5,y+5,x+w-6,y+h-6),C["purple_dark"]); rect(d,(x+9,y+9,x+w-10,y+h-10),C["purple"])
    for xx in range(x+13,x+w-13,14):
        rect(d,(xx,y+7,xx+5,y+9),C["brass"]); rect(d,(xx,y+h-10,xx+5,y+h-8),C["brass"])
    cx=x+w//2; cy=y+h//2; d.polygon([(cx,cy-12),(cx+18,cy),(cx,cy+12),(cx-18,cy)],fill=C["brass_dark"]); d.polygon([(cx,cy-7),(cx+11,cy),(cx,cy+7),(cx-11,cy)],fill=C["brass_hi"]); rect(d,(cx-2,cy-2,cx+2,cy+2),C["teal"])

def ensure_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")

# Full-map native-resolution decor. No tiny source is enlarged.
dock = ensure_rgba(ASSETS / "sky_dock_stardew.png")
dd = ImageDraw.Draw(dock)
schedule(dd,28,18,120,88)
harbor_desk(dd,25,92,150,100)
waiting_nook(dd,10,188,122,88)
luggage(dd,382,184,88,88)
plant(dd,188,48,28,40)
lantern(dd,364,76)
panel(dd,(330,150,365,176),C["wood"]); banner(dd,337,142,12,24)
dock.save(OUT / "sky_dock_density_0693.png", optimize=True, compress_level=9)

deck = ensure_rgba(ASSETS / "airship_deck_stardew.png")
de = ImageDraw.Draw(deck)
bookshelf(de,8,18,88,104)
telescope(de,296,18,72,88)
teacart(de,8,146,58,58)
gramophone(de,314,146,58,58)
rug(de,138,154,108,58)
plant(de,98,42,28,40)
plant(de,258,42,28,40)
de.ellipse((18,116,50,148),fill=C["outline"]); de.ellipse((22,120,46,144),fill=C["cream"])
line(de,[(34,132),(34,123)],C["outline"],2); line(de,[(34,132),(42,136)],C["outline"],2)
deck.save(OUT / "airship_deck_density_0693.png", optimize=True, compress_level=9)

print("0693 native Airship density assets materialized:", OUT)

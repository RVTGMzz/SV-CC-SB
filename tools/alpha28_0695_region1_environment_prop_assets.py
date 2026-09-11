#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, random
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/Cardcha/assets/region1_rooms"
OUT.mkdir(parents=True, exist_ok=True)
PNG = OUT / "region1_environment_props_0695.png"
MANIFEST = OUT / "region1_environment_props_0695_manifest.json"
W, H, TILE = 256, 128, 16
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Compact Stardew-faithful forest palette. No antialiasing: every mark lands on the native pixel grid.
C = {
    "outline": (47, 42, 39, 255),
    "outline2": (66, 52, 45, 255),
    "bark_dark": (91, 61, 44, 255),
    "bark": (126, 84, 55, 255),
    "bark_light": (166, 116, 73, 255),
    "moss_dark": (52, 89, 55, 255),
    "moss": (73, 121, 67, 255),
    "fern": (99, 146, 78, 255),
    "leaf_light": (139, 173, 94, 255),
    "stone_dark": (69, 79, 70, 255),
    "stone": (101, 111, 94, 255),
    "stone_light": (139, 145, 118, 255),
    "cream": (225, 213, 164, 255),
    "mush_red": (166, 78, 74, 255),
    "briar": (73, 75, 48, 255),
    "thorn": (125, 112, 66, 255),
    "teal_dark": (54, 105, 105, 255),
    "teal": (91, 167, 151, 255),
    "lavender": (154, 130, 177, 255),
    "magic": (194, 190, 196, 255),
}

def O(col: int, row: int) -> tuple[int, int]:
    return col * TILE, row * TILE

def px(col:int,row:int,x:int,y:int,color:str|tuple[int,int,int,int]):
    ox,oy=O(col,row); d.point((ox+x,oy+y), fill=C[color] if isinstance(color,str) else color)

def rect(col:int,row:int,box,fill:str,outline:str|None=None):
    ox,oy=O(col,row); b=(ox+box[0],oy+box[1],ox+box[2],oy+box[3])
    d.rectangle(b, fill=C[fill], outline=C[outline] if outline else None)

def line(col:int,row:int,points,fill:str,width:int=1):
    ox,oy=O(col,row); d.line([(ox+x,oy+y) for x,y in points], fill=C[fill], width=width)

def poly(col:int,row:int,points,fill:str):
    ox,oy=O(col,row); d.polygon([(ox+x,oy+y) for x,y in points], fill=C[fill])

def ellipse(col:int,row:int,box,fill:str,outline:str|None=None):
    ox,oy=O(col,row); b=(ox+box[0],oy+box[1],ox+box[2],oy+box[3])
    d.ellipse(b, fill=C[fill], outline=C[outline] if outline else None)

# R0: P01 moss/root/fern ground clusters, transparent non-colliding BackDecor tiles.
for c in range(16):
    rng=random.Random(69500+c)
    x=2+rng.randrange(0,5); y=12+rng.randrange(0,2)
    line(c,0,[(x,y),(x+3,y-1),(x+5,y),(x+8,y-2)],"bark_dark")
    line(c,0,[(x+1,y-1),(x+4,y-2),(x+7,y-1)],"bark")
    for j in range(2+(c%2)):
        bx=2+((c*3+j*5)%11); by=13-(j%2)
        line(c,0,[(bx,by),(bx,by-5-(c+j)%3)],"moss_dark")
        for dy in (2,4,6):
            if by-dy <= 1: continue
            px(c,0,max(0,bx-1),by-dy,"fern"); px(c,0,min(15,bx+1),by-dy+1,"leaf_light")
    if c%3==0:
        px(c,0,13,13,"cream"); px(c,0,12,14,"moss")

# R1: P03 forage clusters, mushrooms, clover, tiny stones.
for c in range(16):
    rng=random.Random(69520+c)
    for j in range(4):
        bx=2+rng.randrange(0,12); by=10+rng.randrange(0,5)
        if (c+j)%3==0:
            rect(c,1,(bx,by,bx+1,by+2),"cream")
            ellipse(c,1,(bx-1,by-2,bx+2,by),"mush_red","outline")
        elif (c+j)%3==1:
            px(c,1,bx,by,"moss_dark"); px(c,1,bx-1,by-1,"fern"); px(c,1,bx+1,by-1,"leaf_light")
        else:
            ellipse(c,1,(bx-1,by-1,bx+1,by+1),"stone","stone_dark")
    if c%4==0:
        line(c,1,[(3,13),(7,12),(11,13)],"moss")

# R2: P02 fallen log/stump solid bases. Pair-friendly horizontal pieces.
for c in range(16):
    if c%4 in (0,1):
        rect(c,2,(1,7,15,13),"outline")
        rect(c,2,(2,8,14,12),"bark")
        line(c,2,[(3,9),(12,9)],"bark_light")
        line(c,2,[(5,12),(10,12)],"bark_dark")
        if c%4==1:
            ellipse(c,2,(10,7,15,13),"bark_light","outline")
            ellipse(c,2,(12,9,14,11),"bark_dark")
        for x in (3,7,11):
            if (c+x)%3==0: px(c,2,x,7,"moss")
    else:
        ellipse(c,2,(3,6,13,13),"outline")
        rect(c,2,(4,8,12,14),"bark","outline")
        ellipse(c,2,(5,6,11,9),"bark_light","outline")
        ellipse(c,2,(7,7,10,9),"bark_dark")
        px(c,2,4,7,"moss"); px(c,2,5,6,"fern")

# R3: P02/P05 upper silhouettes: branches, log moss, trail signs and charms.
for c in range(16):
    if c < 8:
        line(c,3,[(3,14),(5,8),(7,5),(9,3)],"outline",2)
        line(c,3,[(4,14),(6,8),(8,5),(10,3)],"bark")
        poly(c,3,[(6,7),(3,5),(5,10)],"moss")
        poly(c,3,[(9,4),(12,3),(10,7)],"fern")
        if c%2==0: ellipse(c,3,(10,9,13,12),"mush_red","outline")
    else:
        rect(c,3,(6,7,9,15),"bark_dark","outline")
        rect(c,3,(2,2,13,9),"bark","outline")
        line(c,3,[(4,4),(11,4)],"bark_light")
        if c%2==0:
            poly(c,3,[(7,4),(10,6),(7,8),(4,6)],"teal_dark")
            px(c,3,7,6,"teal")
        else:
            line(c,3,[(3,7),(12,3)],"cream")

# R4: P04 mossy field-stone ruin bases.
for c in range(16):
    if c%3==0:
        rect(c,4,(1,8,15,14),"stone_dark")
        rect(c,4,(2,7,8,13),"stone","outline")
        rect(c,4,(9,9,14,13),"stone_light","outline")
    elif c%3==1:
        poly(c,4,[(2,14),(3,8),(6,6),(10,7),(13,11),(13,14)],"stone_dark")
        poly(c,4,[(3,13),(4,9),(7,7),(10,8),(12,12)],"stone")
    else:
        ellipse(c,4,(3,7,13,14),"stone","stone_dark")
        rect(c,4,(6,9,10,13),"stone_light")
    line(c,4,[(2,8),(5,7),(7,8)],"moss")
    px(c,4,4,7,"leaf_light"); px(c,4,11,10,"moss_dark")

# R5: P04 ruin tops / broken marker stones.
for c in range(16):
    if c < 8:
        poly(c,5,[(3,15),(3,5),(6,2),(11,3),(12,15)],"stone_dark")
        poly(c,5,[(4,14),(4,6),(7,3),(10,4),(11,14)],"stone")
        line(c,5,[(5,7),(8,6),(10,8)],"stone_light")
        line(c,5,[(4,5),(7,4)],"moss")
    else:
        poly(c,5,[(5,15),(5,6),(7,3),(10,5),(11,15)],"stone_dark")
        poly(c,5,[(6,14),(6,7),(8,4),(10,6),(10,14)],"stone")
        if c%2==0:
            px(c,5,8,7,"teal_dark"); px(c,5,8,8,"teal")
        else:
            line(c,5,[(7,8),(9,6),(9,10)],"moss")

# R6: P06 briar/hollow growth, dark and compact.
for c in range(16):
    base=[(2,14),(3,9),(6,12),(8,6),(10,11),(13,7),(14,14)]
    line(c,6,base,"outline",2)
    line(c,6,[(3,14),(4,10),(7,12),(9,7),(11,11),(13,8)],"briar")
    for x,y in ((4,10),(8,7),(11,11),(13,8)):
        poly(c,6,[(x,y),(x-2,y-2),(x-1,y+1)],"moss_dark")
        if (c+x)%2==0: px(c,6,min(15,x+1),max(0,y-1),"thorn")
    if c>=8:
        ellipse(c,6,(5,7,11,14),"outline")
        ellipse(c,6,(6,8,10,14),"bark_dark")
        rect(c,6,(7,10,9,14),"outline")

# R7: P07 Card Shrine relics + restrained magical accents.
for c in range(16):
    mode=c%4
    if mode==0:
        rect(c,7,(4,10,12,14),"stone_dark")
        rect(c,7,(5,8,11,11),"stone","outline")
        rect(c,7,(6,4,10,9),"stone_light","outline")
        poly(c,7,[(8,5),(10,7),(8,9),(6,7)],"lavender")
        px(c,7,8,7,"magic")
    elif mode==1:
        poly(c,7,[(4,14),(5,5),(8,2),(11,5),(12,14)],"stone_dark")
        poly(c,7,[(5,13),(6,6),(8,3),(10,6),(11,13)],"stone")
        line(c,7,[(7,8),(8,6),(9,8),(8,10),(7,8)],"teal")
    elif mode==2:
        rect(c,7,(5,11,11,13),"stone_dark")
        ellipse(c,7,(4,8,12,12),"outline")
        ellipse(c,7,(5,8,11,10),"stone")
        px(c,7,7,8,"lavender"); px(c,7,9,8,"teal")
    else:
        rect(c,7,(6,4,10,13),"outline")
        rect(c,7,(7,5,9,12),"bark")
        poly(c,7,[(8,6),(9,8),(8,10),(7,8)],"teal")
        line(c,7,[(8,1),(8,4)],"cream")
        px(c,7,5,13,"moss"); px(c,7,11,13,"moss")

img.save(PNG, format="PNG")
manifest = {
    "schema": 1,
    "build": "0695",
    "image": PNG.name,
    "size": [W, H],
    "tileSize": 16,
    "columns": 16,
    "tileCount": 128,
    "staticPhysicalOwner": "TMX map layers",
    "runtimeOverlays": [],
    "families": {
        "P01": {"rows": [0], "name": "Moss Root Cluster", "defaultLayer": "BackDecor"},
        "P03": {"rows": [1], "name": "Fern / Mushroom Forage Cluster", "defaultLayer": "BackDecor"},
        "P02": {"rows": [2,3], "name": "Fallen Log / Stump Workset", "defaultLayers": ["Buildings","Front"]},
        "P04": {"rows": [4,5], "name": "Mossy Field-Stone Ruin", "defaultLayers": ["Buildings","Front"]},
        "P06": {"rows": [6], "name": "Briar / Hollow Growth", "defaultLayers": ["Buildings","Front"]},
        "P07": {"rows": [7], "name": "Card Shrine Relic Set", "defaultLayers": ["Buildings","Front"]},
        "P05": {"rows": [3], "columns": [8,9,10,11,12,13,14,15], "name": "Trail Sign / Expedition Marker", "defaultLayers": ["Buildings","Front"]}
    },
    "paletteContract": "Stardew forest: moss/fern + warm wood + gray-green stone + restrained teal/lavender Cardcha magic",
    "thirdPartyAssets": False
}
MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"0695 Region I prop sheet materialized: {PNG} ({W}x{H} RGBA)")

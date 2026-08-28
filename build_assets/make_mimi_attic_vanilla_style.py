from pathlib import Path
from PIL import Image, ImageDraw

W, H = 352, 224
img = Image.new("RGBA", (W, H), (6, 5, 10, 255))
d = ImageDraw.Draw(img)

BLACK=(13,9,16,255); OUT=(38,25,34,255); WOOD_D=(87,49,39,255); WOOD_L=(190,123,76,255)
WALL=(210,174,139,255); WALL2=(194,148,118,255); TRIM=(104,57,45,255); FLOOR=(107,82,74,255)
PURPLE=(83,57,103,255); PURPLE2=(116,77,133,255); GOLD=(226,184,91,255); BLUE=(67,100,127,255)
TEAL=(73,127,126,255); GREEN=(70,116,73,255); CREAM=(229,207,161,255); RED=(129,55,57,255)

# Room shell: visible black void, heavy dark edge, wall trim and a proper bottom doorway/stair opening.
room=(14,10,337,207)
d.rounded_rectangle(room, radius=5, fill=OUT)
d.rectangle((18,14,333,203), fill=WALL)
for y in range(18,65):
    d.line((20,y,331,y), fill=WALL if y % 4 else WALL2)
for x in range(28,326,28):
    for y in (28,44):
        d.rectangle((x,y,x+2,y+2), fill=PURPLE2)
        d.point((x+1,y-2), fill=GOLD)

d.rectangle((20,66,331,201), fill=FLOOR)
for y in range(70,201,16):
    d.line((20,y,331,y), fill=(86,65,61,255))
for row,y in enumerate(range(70,201,16)):
    off=8 if row % 2 else 0
    for x in range(20+off,332,32):
        d.line((x,y,x,y+15), fill=(91,69,64,255))

d.rectangle((18,60,333,69), fill=TRIM)
d.line((20,61,331,61), fill=WOOD_L)
d.line((20,68,331,68), fill=BLACK)
for box in ((14,10,337,207),(18,14,333,203)):
    d.rectangle(box, outline=BLACK, width=2)
for x in (18,324):
    d.rectangle((x,14,x+9,202), fill=WOOD_D)
    d.line((x+2,16,x+2,200), fill=WOOD_L)

# Doorway / stairwell.
d.rectangle((158,188,194,223), fill=(4,3,7,255))
d.rectangle((153,183,158,223), fill=WOOD_D)
d.rectangle((194,183,199,223), fill=WOOD_D)
d.rectangle((153,180,199,186), fill=WOOD_D)
d.line((155,181,197,181), fill=WOOD_L)
d.line((155,186,197,186), fill=BLACK)
for i,y in enumerate(range(190,222,6)):
    inset=i*2
    d.rectangle((160+inset,y,192-inset,y+3), fill=(72,47,42,255))
    d.line((161+inset,y,191-inset,y), fill=(151,98,68,255))

d.rounded_rectangle((145,164,207,188), radius=5, fill=BLACK)
d.rounded_rectangle((148,166,204,186), radius=5, fill=(110,62,87,255))
d.rectangle((156,170,196,182), outline=GOLD, width=2)

# Night window.
d.rectangle((133,23,211,56), fill=BLACK)
d.rectangle((137,27,207,53), fill=(45,65,91,255))
for x in range(139,205,11):
    d.point((x,33+(x%3)*4), fill=(230,220,178,255))
d.ellipse((165,31,176,42), fill=(221,207,158,255))
d.line((171,28,171,52), fill=WOOD_D, width=2)
d.line((137,42,207,42), fill=WOOD_D, width=2)

# Bed / personal corner.
d.rounded_rectangle((28,77,112,132), radius=7, fill=BLACK)
d.rounded_rectangle((31,80,109,129), radius=7, fill=PURPLE)
for x in range(38,104,12):
    d.line((x,84,x-14,124), fill=PURPLE2)
d.rectangle((35,70,101,77), fill=BLACK)
d.rectangle((38,73,98,81), fill=WOOD_D)
d.rectangle((40,78,96,111), fill=BLACK)
d.rounded_rectangle((43,80,93,106), radius=5, fill=CREAM)
d.rectangle((43,91,93,108), fill=(164,83,96,255))
d.line((46,96,90,96), fill=(208,122,126,255), width=2)
d.rectangle((38,106,98,112), fill=WOOD_D)
d.rounded_rectangle((47,82,70,91), radius=2, fill=(240,220,184,255))
d.line((50,84,67,84), fill=(255,239,202,255))
d.rectangle((104,92,111,111), fill=WOOD_D)
d.ellipse((99,84,116,97), fill=GOLD)
d.rectangle((106,96,109,105), fill=BLACK)

# Bookshelf between bed and center.
d.rectangle((108,75,133,127), fill=BLACK)
d.rectangle((111,78,130,124), fill=WOOD_D)
for yy in (88,101,114):
    d.line((113,yy,128,yy), fill=WOOD_L, width=2)
books=[RED,BLUE,GREEN,PURPLE2,GOLD]
for j,yy in enumerate((80,91,104,117)):
    x=114
    for k in range(4):
        col=books[(j+k)%len(books)]; h=6+(k%2)*2
        d.rectangle((x,yy+8-h,x+3,yy+8), fill=col)
        x += 4

# Research desk.
d.rectangle((29,134,105,141), fill=BLACK)
d.rectangle((32,132,102,139), fill=WOOD_L)
d.rectangle((34,139,39,176), fill=WOOD_D)
d.rectangle((95,139,100,176), fill=WOOD_D)
d.rectangle((41,141,92,157), fill=WOOD_D)
d.line((43,146,90,146), fill=WOOD_L)
for x,y in ((42,125),(54,129),(66,124),(84,129),(93,123),(51,159)):
    d.rectangle((x,y,x+8,y+5), fill=CREAM)
    d.line((x+2,y+2,x+6,y+2), fill=(99,76,65,255))
d.polygon(((76,136),(81,127),(86,136)), fill=(177,130,226,255))
d.point((81,129), fill=(239,214,255,255))
d.rectangle((57,143,69,154), fill=BLACK)
d.rectangle((59,145,67,152), fill=BLUE)
d.point((63,148), fill=GOLD)
d.rectangle((58,158,75,174), fill=BLACK)
d.rectangle((61,160,72,171), fill=(123,61,78,255))
d.rectangle((62,172,65,183), fill=WOOD_D)
d.rectangle((69,172,72,183), fill=WOOD_D)

# Left plant.
d.rectangle((22,154,32,169), fill=WOOD_D)
d.rectangle((20,166,34,178), fill=(128,78,50,255))
for cx,cy in ((27,151),(23,145),(31,143),(26,137),(34,150)):
    d.ellipse((cx-5,cy-6,cx+5,cy+4), fill=GREEN)

# Center rug / low table keeps the room lived-in instead of workshop-like.
d.rounded_rectangle((117,82,221,151), radius=10, fill=BLACK)
d.rounded_rectangle((120,85,218,148), radius=9, fill=(67,60,91,255))
d.ellipse((153,99,184,130), fill=GOLD)
d.ellipse((161,96,188,125), fill=(67,60,91,255))
for x,y in ((134,101),(198,111),(147,137),(204,132)):
    d.rectangle((x,y,x+2,y+2), fill=CREAM)
d.rectangle((139,133,198,143), fill=BLACK)
d.rectangle((142,130,195,140), fill=WOOD_L)
d.rectangle((147,140,151,149), fill=WOOD_D)
d.rectangle((187,140,191,149), fill=WOOD_D)
d.rectangle((158,132,169,136), fill=BLUE)
d.rectangle((175,132,187,136), fill=CREAM)

# TV secret corner, visually tucked behind a divider.
d.rectangle((238,70,244,136), fill=BLACK)
d.rectangle((240,73,242,133), fill=WOOD_L)
for yy in range(76,132,12):
    d.line((243,yy,251,yy+7), fill=PURPLE2, width=2)
d.rectangle((270,73,325,80), fill=BLACK)
d.rectangle((273,76,322,84), fill=WOOD_D)
d.rectangle((282,82,316,107), fill=BLACK)
d.rectangle((285,85,313,104), fill=(32,58,68,255))
d.ellipse((295,89,304,98), fill=TEAL)
d.rectangle((296,106,302,112), fill=WOOD_D)
d.rectangle((312,112,325,143), fill=BLACK)
d.rectangle((314,114,323,141), fill=WOOD_D)
d.rectangle((316,118,321,122), fill=GOLD)
d.rectangle((316,127,322,132), fill=RED)
d.rectangle((249,124,274,143), fill=BLACK)
d.rounded_rectangle((252,126,271,140), radius=3, fill=(113,63,89,255))
d.rectangle((254,141,258,151), fill=WOOD_D)
d.rectangle((266,141,270,151), fill=WOOD_D)
d.ellipse((296,126,325,145), fill=BLACK)
d.ellipse((299,128,322,142), fill=WOOD_L)
d.rectangle((308,141,312,151), fill=WOOD_D)
d.rectangle((303,126,309,132), fill=CREAM)
d.rectangle((313,130,319,134), fill=GOLD)

# ChaCha / future upgrade corner.
d.rounded_rectangle((233,151,325,194), radius=8, fill=BLACK)
d.rounded_rectangle((236,154,322,191), radius=7, fill=(72,70,95,255))
d.ellipse((245,166,275,187), fill=BLACK)
d.ellipse((248,168,272,184), fill=PURPLE2)
d.line((252,176,268,176), fill=CREAM)
d.rectangle((292,159,322,187), fill=BLACK)
d.rectangle((295,162,319,184), fill=BLUE)
d.rectangle((299,166,315,176), fill=(30,48,63,255))
for x in (301,307,313):
    d.ellipse((x,178,x+3,181), fill=GOLD)
d.rectangle((285,181,291,188), fill=CREAM)
d.rectangle((282,178,289,181), fill=GOLD)
d.rectangle((278,162,286,178), fill=BLACK)
d.rectangle((280,164,284,176), fill=(161,119,209,255))
d.point((282,167), fill=(244,229,255,255))

# Right plant.
d.rectangle((320,158,329,174), fill=WOOD_D)
for cx,cy in ((324,155),(320,149),(328,148),(326,142)):
    d.ellipse((cx-5,cy-6,cx+5,cy+4), fill=GREEN)

# Wall art and mushroom pins.
d.rectangle((48,27,91,53), fill=BLACK)
d.rectangle((51,30,88,50), fill=(105,128,116,255))
d.rectangle((56,34,83,46), fill=(141,175,146,255))
d.rectangle((67,36,75,42), fill=BLUE)
d.rectangle((250,27,279,55), fill=BLACK)
d.rectangle((253,30,276,52), fill=PURPLE)
d.ellipse((260,34,269,43), fill=GOLD)
d.rectangle((258,45,271,48), fill=CREAM)

def mushroom(x,y,c):
    d.ellipse((x,y,x+10,y+6), fill=BLACK)
    d.ellipse((x+1,y+1,x+9,y+5), fill=c)
    d.rectangle((x+4,y+5,x+6,y+10), fill=CREAM)

for x,y,c in ((102,34,RED),(116,41,PURPLE2),(225,37,PURPLE2)):
    mushroom(x,y,c)
for x,y in ((108,166),(213,170),(225,116),(129,159),(221,187)):
    d.rectangle((x,y,x+5,y+3), fill=CREAM)

out = Path("src/Cardcha/assets/mimi_attic_tiles.png")
out.parent.mkdir(parents=True, exist_ok=True)
img.save(out)
print(f"generated {out} ({W}x{H})")
